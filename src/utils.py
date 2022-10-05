
import rsa
from Crypto.PublicKey import RSA

def generatePrivateAndPublicKeys():
    # key = RSA.generate(2048)
    # f = open('mykey.pem','wb')
    # f.write(key.export_key('PEM'))
    # f.close()
    # publicKey = key.public_key()
    # privateKey = key.p
    # publicKey, privateKey = rsa.newkeys(512)   
    # return privateKey, publicKey
    return "privateKey", "publicKey"

from urllib import request
def enterToNetwork(address: str):
    newNodeEndpoint = f'{address}/addNode'
    req = request.Request(newNodeEndpoint, method='POST')
    req.add_header('Content-Type', 'application/json')
    
def encryptMessage(message: str, key):
    encMessage = rsa.encrypt(message.encode(), key)
    print("original string: ", message)
    print("encrypted string: ", encMessage)
    return encMessage

def decryptMessage(message: str, key):
    decMessage = rsa.decrypt(message, key).decode()
    return decMessage

from Crypto.Signature import PKCS1_v1_5
from Crypto.Hash import SHA256
import base64
def signMessage(message: str, key:str):
    # h = SHA256.new(message.encode())
    # signature = PKCS1_v1_5.new(key).sign(h)
    # result = base64.b64encode(signature).decode()
    # return result
    pass