from nacl.public import PrivateKey, Box
import socket
import requests
import threading


class Node():
    __private_key = None  # TODO symmetrical encryption
    __public_key = None

    pub_list = None
    ip = None
    port = None
    app = None

    def __init__(self, network_node_address, app):
        self.__private_key = PrivateKey.generate()
        self.__public_key = self.__private_key.public_key
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
                (f"{socket.gethostbyname(socket.gethostname())}:5000",
                 str(self.__public_key))
            ]

    def get_public_key(self):
        return str(self.__public_key)

    #def get_private_key(self):
    #    return self.__private_key

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list
