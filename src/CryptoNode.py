from nacl.signing import SigningKey

import socket
import requests
import threading

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils
from CryptoBlock import Block
from CryptoBlockchain import BlockChain


class Node():
    __private_key = None
    __public_key = None
    __message_utils = None

    __public_key_hex = None

    pub_list = list[NodeInfo]
    blockchain: BlockChain = None
    ip = None
    port = None
    app = None

    def __init__(self, network_node_address, app):

        self.__private_key = SigningKey.generate()
        self.__public_key = self.__private_key.verify_key

        self.__public_key_hex = self.__public_key.encode().hex()
        self.app = app
        self.__message_utils = MessageUtils(self.__private_key)
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
            self.blockchain = BlockChain.create_blockchain([block])

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
            try:
                self.blockchain.add_block(block)
            except ValueError as err:
                raise err
        else:
            return 'Unhandled message type'

    def create_block(self, data):
        new_block = self.blockchain._blocks[-1].create_next_block(
            data, self.get_public_key())

        # spread
        payload = {
            'type': 'new_block',
            'block': new_block.to_json()
        }
        frame = self.__message_utils.wrap_message(payload)
        for node in self.pub_list:
            requests.post(url=f'http://{node.address}/message', json=frame)
