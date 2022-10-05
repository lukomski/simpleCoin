from nacl.public import PrivateKey, Box
import socket
import requests

class Node():
    __private_key = None # TODO symmetrical encryption 
    __public_key = None
    
    pub_list = None
    ip = None
    port = None

    def __init__(self, network_node_address):
        self.__private_key = PrivateKey.generate()
        self.__public_key = self.__private_key.public_key
        
        if network_node_address is not None:
            self.pub_list = []
            requests.post(url = 'http://' + network_node_address + "/connect-node", json = {})
        else:
            self.pub_list = [
                (socket.gethostbyname(socket.gethostname()), str(self.__public_key))
            ]

    def get_public_key(self):
        return self.__public_key

    def get_private_key(self):
        return self.__private_key

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list
