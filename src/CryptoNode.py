from nacl.public import PrivateKey, PublicKey, Box
from nacl.utils import random, EncryptedMessage
from nacl.encoding import HexEncoder
import socket
import requests
import threading

from CryptoNodeInfo import NodeInfo


class Node():
    __private_key = None  # TODO symmetrical encryption
    __public_key = None

    pub_list = list[NodeInfo]
    ip = None
    port = None
    app = None
    nonce = None

    def __init__(self, network_node_address, app):
        privateKey = PrivateKey.generate()
        publicKey = privateKey.public_key

        private_encode_key = privateKey.encode(HexEncoder)
        public_encode_key = publicKey.encode(HexEncoder)

        self.__private_key = private_encode_key
        self.__public_key = public_encode_key
        # self.nonce = random(Box.NONCE_SIZE)
        self.app = app
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
                         self.__public_key)
            ]

    def get_public_key(self):
        return self.__public_key

    # def get_private_key(self):
    #    return self.__private_key

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def getAddressByPublicKey(self, public_key: str):
        for nodeInfo in self.pub_list:
            if (nodeInfo.public_key == public_key):
                return nodeInfo.address
        return None

    def getPublicKeyByAddress(self, address: str):
        for nodeInfo in self.pub_list:
            if (nodeInfo.address == address):
                return nodeInfo.public_key
        return None

    def send_message(self, message: bytes, reveiver_public_key: bytes):
        # return {"message": str(message), "reveiver_public_key": str(reveiver_public_key)}
        private_key = PrivateKey(self.__private_key, HexEncoder)
        public_key = PublicKey(reveiver_public_key, HexEncoder)
        box = Box(private_key, public_key)
        encrypted = box.encrypt(message, self.nonce, HexEncoder)

        address = self.getAddressByPublicKey(reveiver_public_key)
        requests.get(
            url=f"http://{address}/read", params={"message": encrypted, "nounce": self.nonce})

    def read_message(self, encrypted_message: bytes, sender_public_key: bytes, nonce=None):
        private_key = PrivateKey(self.__private_key, HexEncoder)
        public_key = PublicKey(sender_public_key, HexEncoder)

        box = Box(private_key, public_key)
        message = box.decrypt(encrypted_message, None, HexEncoder)
        self.app.logger.error(f'READ message: {message.decode("utf-8")}')
