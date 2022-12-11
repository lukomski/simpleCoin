from nacl.signing import SigningKey

import socket
import requests

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils
from CryptoBlock import Block
from CryptoBlockchain import BlockChain
from CryptoKeyManager import KeyManager
from threading import Thread
import multiprocessing
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoUtils import get_order_directory_recursively, encrypt_by_secret_key, decrypt_by_secret_key
import uuid
import time
from datetime import datetime
BLOCKCHAIN_FILE_PATH = "blockchain.json"


class Node():
    __message_utils = None

    pub_list = list[NodeInfo]
    blockchain: BlockChain = None
    ip = None
    port = None
    app = None
    transaction_pool = None
    _processed_transaction_pools = None
    __counter = 0

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

    def __setup(self, network_node_address):
        self.__logger.error('Node::__setup')
        if network_node_address is not None:
            self.pub_list = []

            self.__logger.info("Sending request to connect new node")
            requests.post(
                url=f'http://{network_node_address}/connect-node', json={})

            block_list = requests.get(
                url=f'http://{network_node_address}/blocks').json()

            block_list = Block.load_list(block_list)
            self.blockchain = BlockChain.create_blockchain(block_list)
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__key_manager.public_key)
            ]
            initial_prev_hash_hex = None  # uuid.uuid4().hex
            body = {
                'message': 'Initial block',
            }
            block = Block.create(initial_prev_hash_hex,
                                 body, self.__key_manager.public_key)

            if os.path.exists(BLOCKCHAIN_FILE_PATH):
                self.blockchain = BlockChain.load_blockchain(
                    BLOCKCHAIN_FILE_PATH)
                if self.blockchain is None:
                    raise ValueError(
                        "Could not load/parse existing blockchain - remove file or correct it to start node.")
            else:
                self.blockchain = BlockChain.create_blockchain([block])

        self.__logger.info('Setup done')
        self.infinite_dig_id = str(uuid.uuid4())
        self.__mining = multiprocessing.Process(
            target=self.__invoke_infinite_dig)
        self.__mining.start()

    def __init__(self, network_node_address, secret_key, app):
        self.__key_manager = KeyManager(app.logger, secret_key)

        self.app = app
        self.__logger = app.logger
        self.__message_utils = MessageUtils(self.__key_manager)

        self.transaction_pool = TransactionPool()
        self._processed_transaction_pools = []

        miner_thread = Thread(target=self.__setup,
                              args=(network_node_address,))
        miner_thread.start()

    def infinite_dig(self):
        self.__logger.info(f'Start mining id: {str(self.infinite_dig_id)}')
        self.__processing_incoming_candidate_block = False
        uuid_copy = self.infinite_dig_id

        while True:
            self.__logger.info('digging next block')
            next_transaction = self.transaction_pool.get_next_transaction_json()
            block_data = next_transaction if next_transaction else {
                "random_message": str(uuid.uuid4())}

            # start digging for new block and after that broadcast result
            block_added = self.create_block(block_data)

            if uuid_copy != self.infinite_dig_id:
                break
            if next_transaction and block_added:
                self.app.logger.error(f'Message Added to block: {block_data}')
                self.transaction_pool.pop_next_transaction()
        self.__logger.info(
            f'Stop mining id: {str(uuid_copy)}, current id: {str(self.infinite_dig_id)}')

    def get_public_key(self):
        return self.__key_manager.public_key

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
                # wait 2 seconds and start new dig process
                if sender_pk_hex != self.get_public_key():
                    self.infinite_dig_id = str(uuid.uuid4())
                    self.__mining = Thread(
                        target=self.__invoke_infinite_dig)
                    self.__mining.start()

            # unblock adding new blocks
            self.__processing_incoming_candidate_block = False

        elif payload['type'] == 'start-digging':
            self.infinite_dig()
        else:
            return 'Unhandled message type'

    def create_block(self, data) -> bool:
        begin = datetime.now()
        # actual mining
        new_block = self.blockchain._blocks[-1].create_next_block(
            data, self.get_public_key())

        counter = 0
        while self.__processing_incoming_candidate_block:
            time.sleep(0.001)
            if counter % 1000 == 0:
                self.__logger.warning(
                    'waiting for processing incoming candidate block begin completed')
        end = datetime.now()
        diff = end - begin
        self.__logger.info(
            f'spread - mining duration: {diff.total_seconds()} sec.')
        # spread
        payload = {
            'type': 'new_block',
            'block': new_block.to_json()
        }
        frame = self.__message_utils.wrap_message(payload)
        sender_address = self.get_address_by_public_key(
            self.__key_manager.public_key)
        # send to other nodes
        for node in self.pub_list:
            if node.address == sender_address:
                continue
            response = requests.post(
                url=f'http://{node.address}/message', json=frame)
            if not response.ok:
                return False
        # send to myself
        response = requests.post(
            url=f'http://{sender_address}/message', json=frame)
        if not response.ok:
            return False
        return True

    def add_transaction(self, data: dict):
        transaction = Transaction(get_order_directory_recursively(data))
        self.transaction_pool.add_transaction(transaction)

    def save_blockchain(self):
        self.blockchain.save(BLOCKCHAIN_FILE_PATH)
