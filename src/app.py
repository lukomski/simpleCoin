from flask import Flask, request, render_template
import os
import json
import socket
from CryptoNode import Node

app = Flask(__name__)

node = Node(os.environ.get("REFERENCE_ADDRESS", None))
print(node.pub_list)

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
    return json.dumps(
        {
            'public_key': str(node.get_public_key())
        }
    )

@app.route('/node', methods=['POST'])
def get_node():
    return store['publicKey']

@app.route("/connect-node", methods=['POST'])
def connect_node():
    request_ip = request.remote_addr

    pubkey_response = requests.get(url = "http://" + request_ip + "/publicKey")
    pubkey_response_obj = json.loads(pubkey_response)

    node.update_pub_list([*node.pub_list, (pubkey_response_obj['address'], pubkey_response_obj['public_key'])])

    updated_connections = []
    for address, pub_key in node.pub_list:
        updated_connections.append(
            {
                'address': address,
                'public_key': pub_key
            }
        )

    for connection in node.pub_list:
        if connection[1] == node.get_public_key():
            continue
        requests.post(
            url = "http://" + connection[0] + "/update-pub-list",
            json = json.dumps(updated_connections)
        )

    return {
        'message': 'OK',
        'status': 200
    }

@app.route("/update-pub-list", methods=['POST'])
def update_pub_list():
    #updated_connections = request.get_json() #json.loads(request.form)
    return {
        'message': 'OK'
    }

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