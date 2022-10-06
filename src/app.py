from flask import Flask, request, render_template
import os

import requests
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
    return pub_list


@app.route('/publicKey')
def get_public_key():
    return {
        'public_key': str(node.get_public_key())
    }


@app.route('/node', methods=['POST'])
def get_node():
    return store['publicKey']


@app.route("/connect-node", methods=['POST'])
def connect_node():
    request_ip = request.remote_addr
    request_addr = f"{request_ip}:5000"

    pubkey_response = requests.get(url="http://" + request_addr + "/publicKey")
    print(pubkey_response.__dict__)
    app.logger.info(f"pubkey_response: {pubkey_response.json()}")

    pubkey_response_obj = pubkey_response.json()

    node.update_pub_list(
        [*node.pub_list, (request_addr, pubkey_response_obj['public_key'])])

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
            url="http://" + connection[0] + "/update-pub-list",
            json=updated_connections
        )

    return {
        'message': 'OK',
        'status': 200
    }


@ app.route("/update-pub-list", methods=['POST'])
def update_pub_list():
    # updated_connections = request.get_json() #json.loads(request.form)
    return {
        'message': 'OK'
    }


if __name__ == "__main__":
    app.run(debug=True)
