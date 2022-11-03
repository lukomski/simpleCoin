from nacl.signing import SigningKey

import socket
import requests
import threading

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils


class Node():
    __private_key = None
    __public_key = None
    __message_utils = None

    __public_key_hex = None

    pub_list = list[NodeInfo]
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
                requests.post(url='http://' +
                              network_node_address + "/connect-node", json={})
            start_time = threading.Timer(1, f)
            start_time.start()
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__public_key_hex)
            ]

    def get_public_key(self):
        return self.__public_key_hex

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def getAddressByPublicKey(self, public_key):
        for nodeInfo in self.pub_list:
            if (nodeInfo.public_key_hex == public_key):
                return nodeInfo.address
        return None

    def getPublicKeyByAddress(self, address: str):
        for nodeInfo in self.pub_list:

            if (nodeInfo.address == address):
                return nodeInfo.public_key_hex
        return None

    def send_message(self, message: str, receiver_public_key_hex: str):
        payload = {
            'type': 'message',
            'message': message
        }
        frame = self.__message_utils.wrapMessage(payload)
        address = self.getAddressByPublicKey(receiver_public_key_hex)
        requests.post(
            url=f"http://{address}/message", json=frame)

    def read_message(self, frame: dict, sender_pk_hex: str):
        self.__message_utils.verifyMessage(frame, bytes.fromhex(sender_pk_hex))

        message = self.__message_utils.getPayload(frame)['message']

        self.app.logger.error(f'READ message: {message}')

        return {
            "verified": 'correctly',
            "message": message
        }
