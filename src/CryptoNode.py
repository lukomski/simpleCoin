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
from CryptoDigger import Digger

BLOCKCHAIN_FILE_PATH = "blockchain.json"

class Node():
    __message_utils = None

    pub_list = list[NodeInfo]
    ip = None
    port = None
    app = None
    __digger: Digger = None

    def __setup(self, network_node_address):
        self.__logger.error('Node::__setup')
        blockchain = None

        if network_node_address is not None:
            self.pub_list = []

            self.__logger.info("Sending request to connect new node")
            requests.post(url=f'http://{network_node_address}/connect-node', json={})
            block_list = requests.get(url=f'http://{network_node_address}/blocks').json()

            block_list = Block.load_list(block_list)
            blockchain = BlockChain.create_blockchain(block_list)
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__key_manager.public_key)
            ]
            if os.path.exists(BLOCKCHAIN_FILE_PATH):
                blockchain = BlockChain.load_blockchain(BLOCKCHAIN_FILE_PATH)
                if blockchain is None:
                    raise ValueError("Could not load/parse existing blockchain - remove file or correct it to start node.")
            else:
                blockchain = BlockChain(None)

        self.__digger = Digger(blockchain, self.__key_manager, self.__logger, self.spread_candidate_block)
        self.__logger.info('Setup done')
        self.__digger.start_mining()

    def __init__(self, network_node_address, secret_key, app):
        self.__key_manager = KeyManager(app.logger, secret_key)

        self.app = app
        self.__logger = app.logger
        self.__message_utils = MessageUtils(self.__key_manager)

        setup_thread = Thread(target=self.__setup, args=(network_node_address,))
        setup_thread.start()

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
        self.__message_utils.verify_message(frame, bytes.fromhex(sender_pk_hex))

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
            self.__digger.pause_mining()
            # validate block candidate
            is_valid_block = self.__digger.get_blockchain().validate_candidate_block(block)
            if is_valid_block:
                self.__digger.get_blockchain().add_block(block)
            self.__digger.resume_mining()
        else:
            return 'Unhandled message type'

    def add_transaction(self, data: dict):
        transaction = Transaction(get_order_directory_recursively(data))
        self.__digger.add_transaction(transaction)

    def save_blockchain(self):
        self.__digger.__blockchain.save(BLOCKCHAIN_FILE_PATH)

    def spread_candidate_block(self, candidate_block: Block):
        # spread
        payload = {
            'type': 'new_block',
            'block': candidate_block.to_json()
        }
        frame = self.__message_utils.wrap_message(payload)
        sender_address = self.get_address_by_public_key(self.__key_manager.public_key)
        # send to other nodes
        for node in self.pub_list:
            if node.address == sender_address:
                continue

            response = requests.post(url=f'http://{node.address}/message', json=frame)

            if not response.ok:
                return False
        # send to myself
        response = requests.post(url=f'http://{sender_address}/message', json=frame)
        if not response.ok:
            return False
        return True

    def get_digger(self):
        return self.__digger