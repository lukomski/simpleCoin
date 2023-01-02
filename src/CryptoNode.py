from nacl.signing import SigningKey

import socket
import requests

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils
from CryptoBlock import Block
from CryptoBlockchain import BlockChain
from CryptoKeyManager import KeyManager
from threading import Thread
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoUtils import get_order_directory_recursively, encrypt_by_secret_key, decrypt_by_secret_key
import uuid
import time
from datetime import datetime
from CryptoDigger import Digger
import json
import math
from CryptoOutput import Output
import os
BLOCKCHAIN_FILE_PATH = "blockchain.json"
OK = 200
BAD_REQUEST = 400

TRANSACTION_FEE_SHARE = 0.01

class Node():
    __message_utils = None
    __ignore_address: str = None

    pub_list = list[NodeInfo]
    ip = None
    port = None
    app = None
    __digger: Digger = None

    def __setup(self, network_node_address):
        self.__logger.error('Node::__setup')
        blocks = []

        if network_node_address is not None:
            self.pub_list = []

            self.__logger.info("Sending request to connect new node")
            # connect to parent
            while True:
                try:
                    response = requests.post(
                        url=f'http://{network_node_address}/connect-node', json={}, timeout=3)
                    self.__logger.info(f"Get response: {response.text}")
                    break
                except:
                    self.__logger.warning(
                        f'Unable to connect to parent address {network_node_address} - try in a few seconds')
                    time.sleep(1)

            self.__logger.info("Success connection with parent")
            # fetch blocks from parent
            block_list = []
            while len(block_list) == 0:
                try:
                    block_list = requests.get(
                        url=f'http://{network_node_address}/blocks').json()
                except:
                    self.__logger.warning(
                        f'Parent block list is empty - try again to get block list')
            self.__logger.info(
                f'Get block list: {block_list}')
            blocks = Block.load_list(block_list)
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__key_manager.public_key)
            ]
            if os.path.exists(BLOCKCHAIN_FILE_PATH):
                blocks = Block.load_blocks(BLOCKCHAIN_FILE_PATH)
                if blocks is None:
                    raise ValueError(
                        "Could not load/parse existing blocks - remove file or correct it to start node.")

        self.__digger = Digger(blocks, self.__key_manager, self.__logger, self.spread_candidate_block)
        self.__logger.info('Setup done')
        self.__digger.start_mining()

    def __init__(self, network_node_address, secret_key, app, ignore_address: str = None):
        self.__key_manager = KeyManager(app.logger, secret_key)
        self.__ignore_address = ignore_address
        self.app = app
        self.__logger = app.logger
        self.__message_utils = MessageUtils(self.__key_manager)

        setup_thread = Thread(target=self.__setup,
                              args=(network_node_address,))
        setup_thread.start()

    def get_public_key(self):
        return self.__key_manager.public_key

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def get_address_by_public_key(self, public_key):
        for nodeInfo in self.pub_list:
            if (nodeInfo.public_key == public_key):
                return nodeInfo.address
        return None

    def get_public_key_by_address(self, address: str):
        for nodeInfo in self.pub_list:
            if (nodeInfo.address == address):
                return nodeInfo.public_key
        return None

    def send_message(self, message: str, receiver_public_key: str):
        payload = {
            'type': 'message',
            'message': message
        }
        frame = self.__message_utils.wrap_message(payload)
        address = self.get_address_by_public_key(receiver_public_key)
        requests.post(
            url=f"http://{address}/message", json=frame)

    def read_message(self, frame: dict, sender_pk_hex: str):
        if sender_pk_hex is None:
            self.__logger.warning(f'Sender should be str not None {str(frame)}')
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
            if self.__digger == None:
                self.__logger.warning('Not ready to get block')
                return 'Not ready to get block', OK
            if not block.verify_block():
                self.__logger.warning('Block nounce or hash_prev_nonce is wrong')
                return 'Block nounce or hash_prev_nonce is wrong', BAD_REQUEST
            message, is_valid_block = self.__digger.add_block(block=block)
            status = OK if is_valid_block else BAD_REQUEST
            return message, status
        else:
            self.__logger.warning('Unhandled message type')
            return 'Unhandled message type', BAD_REQUEST

    def add_transaction(self, sender: str, receiver: str, amount: int, message: str):
        transaction_id = str(uuid.uuid4())
        transaction_fee = math.ceil(amount * TRANSACTION_FEE_SHARE)
        valid_inputs = self.__digger.get_inputs(sender)
        self.__logger.info(f'valid_inputs: {len(valid_inputs)}')

        available_balance = 0
        for input in valid_inputs:
            available_balance += input.get_amount()

        spend_amount = transaction_fee + amount
        if available_balance < spend_amount:
            return f'Not enough account balance need {spend_amount} but has {available_balance}', BAD_REQUEST

        outputs = [
            Output(owner=receiver, amount=amount),
        ]
        change_amount = available_balance - spend_amount
        if change_amount > 0:
            outputs.append(Output(owner=sender, amount=change_amount))
        # create data without signature
        data = {
            'transaction_id': transaction_id,
            'transaction_fee': transaction_fee,
            'inputs': [input.to_json() for input in valid_inputs],
            'outputs': [output.to_json() for output in outputs],
            'message': message
        }
        signature = self.__key_manager.sign(json.dumps(data).encode('utf-8'))
        # add signature to data
        data = {**data, 'signature': signature}
        message, is_valid = Transaction.is_valid(data, self.__logger)
        if not is_valid:
            return f'Invalid transaction: {message}', BAD_REQUEST

        transaction = Transaction(transaction_id=data['transaction_id'], transaction_fee=data['transaction_fee'],
                                  signature=data['signature'], inputs=data['inputs'], outputs=data['outputs'], message=data['message'])
        self.__digger.add_transaction(transaction)
        return 'ok', OK

    def save_blockchain(self):
        self.__digger.__blockchain.save(BLOCKCHAIN_FILE_PATH)

    def spread_candidate_block(self, candidate_block: Block):
        # spread
        payload = {
            'type': 'new_block',
            'block': candidate_block.to_json()
        }
        frame = self.__message_utils.wrap_message(payload)

        nodes_that_reject = []
        for node in self.pub_list:

            # we can be mean for some digger :)
            # We are sending new block to everone except him.
            if node.address == self.__ignore_address:
                continue

            response = requests.post(
                url=f'http://{node.address}/message', json=frame)

            if not response.ok:
                nodes_that_reject.append(node)
        return True

    def get_digger(self):
        return self.__digger

    def get_wallet_balance(self):
        owner = self.__key_manager.public_key
        valid_inputs = self.__digger.get_inputs(owner)

        available_balance = 0
        for input in valid_inputs:
            available_balance += input.get_amount()

        mining_inputs = 0
        for valid_input in valid_inputs:
            if valid_input.get_transaction_id() == Digger.get_block_price_id():
                mining_inputs += 1

        return {
            'available_balance': available_balance,
            'valid_inputs': [valid_input.to_json() for valid_input in valid_inputs if valid_input.get_transaction_id() != Digger.get_block_price_id()],
            'additional_mining_inputs': {
                'amount_blocks': mining_inputs,
                'summary_balance': mining_inputs * Digger.get_block_price_amount()
            }
        }

    def get_blockchain_tree_struct(self):
        blockchain_tree = self.__digger.get_blockchain_tree()
        tree_structure = blockchain_tree.to_tree_structure()
        tree_structure = [  {**element,
                            'miner_name': f'Node {int(str(self.get_address_by_public_key(element["miner_pub_key"]))[-6])-2}'
                            } for element in tree_structure
                         ]
        return tree_structure
