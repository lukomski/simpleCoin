from nacl.public import PrivateKey, PublicKey, SealedBox, Box
from nacl.encoding import HexEncoder
from nacl.signing import SigningKey, VerifyKey
from nacl.hash import sha256
from nacl.utils import random
import socket
import requests
import threading

from CryptoNodeInfo import NodeInfo


class Node():
    __private_key = None  # TODO symmetrical encryption
    __public_key = None
    __signing_key = None

    pub_list = list[NodeInfo]
    ip = None
    port = None
    app = None

    def __init__(self, network_node_address, app):

        self.__signing_key = SigningKey.generate()
        privateKey = self.__signing_key.to_curve25519_private_key()
        publicKey = privateKey.public_key

        private_encode_key = privateKey.encode(HexEncoder)
        public_encode_key = publicKey.encode(HexEncoder)

        self.__private_key = private_encode_key
        self.__public_key = public_encode_key
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

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def getAddressByPublicKey(self, public_key: bytes):
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
        object = self.__sign_message(message, reveiver_public_key)
        address = self.getAddressByPublicKey(reveiver_public_key)
        requests.post(
            url=f"http://{address}/message", json=object)

    def read_message(self, encrypted_object: object, sender_public_key: bytes):
        trusted = True
        if not self.__verifyMessage(encrypted_object, sender_public_key):
            self.app.logger.error("Message sender must not be trusted")
            trusted = False

        private_key = PrivateKey(self.__private_key, HexEncoder)
        public_key = PublicKey(sender_public_key, HexEncoder)
        box = Box(private_key, public_key)
        message = box.decrypt(str.encode(
            encrypted_object["message"], 'utf8'), None, HexEncoder).decode("utf8")

        self.app.logger.error(f'READ message: {message}')

        return {
            "trusted": trusted,
            "message": message
        }

    def __sign_message(self, message: bytes, reveiver_public_key: bytes):
        # encrypt message
        private_key = PrivateKey(self.__private_key, HexEncoder)
        public_key = PublicKey(reveiver_public_key, HexEncoder)
        box = Box(private_key, public_key)
        encrypted_message = box.encrypt(message, encoder=HexEncoder)

        return {
            "message": encrypted_message.decode("utf8"),
        }

    def __verifyMessage(self, received_object, sender_verify_key: bytes):
        return True
        verify_key_bytes = str.encode(received_object["hash"], 'utf8')
        verify_key = VerifyKey(sender_verify_key)

        # encrypt digest
        public_key = PublicKey(sender_public_key, HexEncoder)
        box = SealedBox(public_key)
        decrypted_digest = box.encrypt(digest_to_decrypt)

        self.app.logger.error(f"decrypted_digest: {str(decrypted_digest)}")
        self.app.logger.error(
            f"expected_digest: {str(expected_digest)}")

        return False if decrypted_digest != expected_digest else True
