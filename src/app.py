from flask import Flask, request, render_template
import os
import json
import socket
from CryptoNode import Node

app = Flask(__name__)
node = Node(None)

@app.route('/')
def hello_geek():
    return render_template('home.html')

@app.route('/nodes')
def get_nodes():
    pub_list = []
    for address, pub_key in node.pub_list:
        pub_list.append(
            {
                'address': address,
                'public_key': str(pub_key)
            }
        )
    return json.dumps(pub_list)

@app.route('/nodeName')
def get_node_name():
    return store['nodeName']

@app.route('/publicKey')
def get_public_key():
    return store['publicKey']

@app.route('/node', methods=['POST'])
def get_node():
    return store['publicKey']

# # for tests
# @app.route('/endecrypt')
# def endecrypt_message():
#     message = request.args.get('message')
#     return utils.encryptMessage(message, store['privateKey'])

# @app.route('/sign')
# def sign_message():
#     message = request.args.get('message')
#     return utils.signMessage(message, store['privateKey'])

if __name__ == "__main__":
    app.run(debug=True)