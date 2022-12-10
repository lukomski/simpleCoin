from nacl.signing import SigningKey

import socket
import requests
import threading

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils
from CryptoBlock import Block
from CryptoBlockchain import BlockChain
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoUtils import get_order_directory_recursively, encrypt_by_secret_key, decrypt_by_secret_key
import uuid
import json

BLOCKCHAIN_FILE_PATH = "blockchain.json"

KEYS_FILE_PATH = 'keys.json'


class Node():
    __secret_key = None
    __private_key = None
    __public_key = None
    __message_utils = None

    __public_key_hex = None

    pub_list = list[NodeInfo]
    blockchain: BlockChain = None
    ip = None
    port = None
    app = None
    transaction_pool = None
    _processed_transaction_pools = None

    dig_process = None
    infinite_dig_id = None
    __processing_incoming_candidate_block = None
    __digging_terminated = None

    def __invoke_infinite_dig(self):
        payload = {
            'type': 'start-digging',
        }
        frame = self.__message_utils.wrap_message(payload)
        for node in self.pub_list:
            requests.post(url=f'http://{node.address}/message', json=frame)

    def __init__(self, network_node_address, secret_key, app):
        self.__secret_key = secret_key

        seed = self.get_seed_from_file()
        if seed is None:
            self.__private_key = SigningKey.generate()
        else:
            self.__private_key = SigningKey(seed)
        self.__public_key = self.__private_key.verify_key
        self.save_keys()

        self.__public_key_hex = self.__public_key.encode().hex()
        self.app = app
        self.__message_utils = MessageUtils(self.__private_key)

        self.transaction_pool = TransactionPool()
        self._processed_transaction_pools = []

        if network_node_address is not None:
            self.pub_list = []

            def f():
                self.app.logger.info("Sending request to connect new node")
                requests.post(
                    url=f'http://{network_node_address}/connect-node', json={})
            start_time = threading.Timer(1, f)
            start_time.start()

            block_list = requests.get(
                url=f'http://{network_node_address}/blocks').json()

            block_list = Block.load_list(block_list)
            self.blockchain = BlockChain.create_blockchain(block_list)
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__public_key_hex)
            ]
            initial_prev_hash_hex = None  # uuid.uuid4().hex
            body = {
                'message': 'Initial block',
            }
            block = Block.create(initial_prev_hash_hex,
                                 body, self.__public_key_hex)

            if os.path.exists(BLOCKCHAIN_FILE_PATH):
                self.blockchain = BlockChain.load_blockchain(BLOCKCHAIN_FILE_PATH)
                if self.blockchain is None:
                    raise ValueError("Could not load/parse existing blockchain - remove file or correct it to start node.")
            else:
                self.blockchain = BlockChain.create_blockchain([block])

        dig_time = threading.Timer(1, self.__invoke_infinite_dig)
        dig_time.start()

    def infinite_dig(self):
        self.__processing_incoming_candidate_block = False
        self.__digging_terminated = False

        while not self.__digging_terminated:
            next_transaction = self.transaction_pool.get_next_transaction_json()
            block_data = next_transaction if next_transaction else {}

            # start digging for new block and after that broadcast result
            self.create_block(block_data)

            if next_transaction and not self.__processing_incoming_candidate_block:
                self.transaction_pool.pop_next_transaction()

    def get_public_key(self):
        return self.__public_key_hex

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def get_address_by_public_key(self, public_key):
        for nodeInfo in self.pub_list:
            if (nodeInfo.public_key_hex == public_key):
                return nodeInfo.address
        return None

    def get_public_key_by_address(self, address: str):
        for nodeInfo in self.pub_list:

            if (nodeInfo.address == address):
                return nodeInfo.public_key_hex
        return None

    def send_message(self, message: str, receiver_public_key_hex: str):
        payload = {
            'type': 'message',
            'message': message
        }
        frame = self.__message_utils.wrap_message(payload)
        address = self.get_address_by_public_key(receiver_public_key_hex)
        requests.post(
            url=f"http://{address}/message", json=frame)

    def read_message(self, frame: dict, sender_pk_hex: str):
        self.__message_utils.verify_message(
            frame, bytes.fromhex(sender_pk_hex))

        payload = self.__message_utils.getPayload(frame)
        if (payload['type'] == 'message'):
            message = payload['message']
            self.app.logger.error(f'READ message: {message}')
            return {
                "verified": 'correctly',
                "message": message
            }
        elif payload['type'] == 'new_block':
            block = Block.load(payload['block'])
            # stop digging
            self.__processing_incoming_candidate_block = True

            # validate block candidate
            is_valid_block = self.blockchain.validate_candidate_block(block)
            if is_valid_block:
                self.blockchain.add_block(block)
                self.__digging_terminated = True
                # wait 2 seconds and start new dig process
                dig_time = threading.Timer(2, self.__invoke_infinite_dig)
                dig_time.start()

                # current digging needs to be terminated and start new digging
                # if sender_pk_hex != self.get_public_key():
                #     self.__digging_terminated = True
                #     # wait 2 seconds and start new dig process
                #     dig_time = threading.Timer(2, self.__invoke_infinite_dig)
                #     dig_time.start()
                # else: # block came from me
                #     # nothing to do - digging process continues
                #     self.__processing_incoming_candidate_block = False

            else: # block is invalid, can resume digging
                self.__processing_incoming_candidate_block = False

        elif payload['type'] == 'start-digging':
            self.infinite_dig()
        else:
            return 'Unhandled message type'

    def create_block(self, data):
        # actual mining
        new_block = self.blockchain._blocks[-1].create_next_block(
            data, self.get_public_key())

        if not self.__processing_incoming_candidate_block:
            # spread
            payload = {
                'type': 'new_block',
                'block': new_block.to_json()
            }
            frame = self.__message_utils.wrap_message(payload)
            for node in self.pub_list:
                requests.post(url=f'http://{node.address}/message', json=frame)

    def add_transaction(self, data: dict):
        transaction = Transaction(get_order_directory_recursively(data))
        self.transaction_pool.add_transaction(transaction)

    def save_keys(self):
        keys_data = {
            'seed': encrypt_by_secret_key(self.__secret_key, self.__private_key._seed.hex()),
            'public_key': self.__public_key_hex
        }
        with open(KEYS_FILE_PATH, "w") as f:
            f.write(json.dumps(keys_data))

    def save_blockchain(self):
        self.blockchain.save(BLOCKCHAIN_FILE_PATH)

    def get_seed_from_file(self):
        try:
            seed = None
            with open(KEYS_FILE_PATH, "r") as f:
                keys_data = f.read()
                seed = decrypt_by_secret_key(
                    self.__secret_key, keys_data['seed'])
            return bytes.fromhex(seed)
        except Exception:
            return None
