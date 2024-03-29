from CryptoNodeInfo import NodeInfo
from flask import Flask, request, render_template
import os
from logging.config import dictConfig

import requests
from CryptoNode import Node, OK, BAD_REQUEST
import json
from CryptoTransaction import Transaction
import random

dictConfig({
    'version': 1,
    'formatters': {'default': {
        'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
    }},
    'handlers': {'wsgi': {
        'class': 'logging.StreamHandler',
        'stream': 'ext://flask.logging.wsgi_errors_stream',
        'formatter': 'default'
    }},
    'root': {
        'level': 'INFO',
        'handlers': ['wsgi']
    }
})


app = Flask(__name__)
reference_address = os.environ.get("REFERENCE_ADDRESS", None)
secret_key = os.environ.get("SECRET_KEY", None)
ignore_address = os.environ.get("IGNORE_ADDRESS", None)
if secret_key == None:
    raise AssertionError('Need SECRET_KEY defined to store keys in secure way')

def fetch_probability_value_from_env_vars(var_name):
    env_var_value = os.environ.get(var_name, None)
    if env_var_value is None:
        raise ValueError(f"Required '{var_name}' environment variable was not specified - correct it and try again")
    try:
        env_var_value = float(env_var_value)
    except Exception:
        raise ValueError(f"Provided '{var_name}' parameter must be float number - correct it and try again")
    if env_var_value > 1.0 or env_var_value < 0.0:
        raise ValueError(f"Provided '{var_name}' value is out of allowed range. It must be value between [0, 1]")
    return env_var_value

# fetch block accept probability from environment variables
BLOCK_ACCEPT_PROBABILITY = fetch_probability_value_from_env_vars("CANDIDATE_BLOCK_ACCEPT_CHANCE")
# fetch transaction accept probability from environment variables
TRANSACTION_RECEIVE_CHANCE = fetch_probability_value_from_env_vars("TRANSACTION_ACCEPT_CHANCE")

node = Node(reference_address,
            secret_key, app,
            ignore_address=ignore_address,
            block_accept_probability=BLOCK_ACCEPT_PROBABILITY,
            transaction_process_chance=TRANSACTION_RECEIVE_CHANCE)
print(node.pub_list)

app.node = node


@app.route('/')
def hello_geek():
    return render_template('home.html')


@app.route('/blocks:tree')
def visualize():
    tree_struct = app.node.get_blockchain_tree_struct()
    return render_template('graph.html', tree_struct=json.dumps(tree_struct))


@app.route('/nodes')
def get_nodes():
    pub_list = []
    for nodeInfo in node.pub_list:
        pub_list.append(nodeInfo.to_JSON())
    return pub_list


@app.route('/blocks')
def get_blocks():
    blocks = None
    if node.get_digger() is not None:
        blocks = [block.to_json() for block in node.get_digger().get_all_blocks()]

    if blocks is None:
        return [], 500
    return blocks


@app.route('/public-key')
def get_public_key():
    return {
        'public_key': node.get_public_key()
    }


def serialize_updated_nodes(node):
    updated_connections = []
    for nodeInfo in node.pub_list:
        updated_connections.append(
            nodeInfo.to_JSON()
        )

    return updated_connections


@app.route("/connect-node", methods=['POST'])
def connect_node():
    request_ip = request.remote_addr
    request_addr = f"{request_ip}:5000"

    # check if request was received from node that is already connected (its IP address is in nodes list)
    node_idx = -1
    for i in range(0, len(node.pub_list)):
        if (node.pub_list[i].address == request_addr):
            node_idx = i

    pubkey_response = None
    try:
        pubkey_response = requests.get(
            url="http://" + request_addr + "/public-key")
    except Exception:
        pubkey_response = None

    # somehow node is down and doesn't respond, but it's still on our list
    if pubkey_response is None:
        if node_idx != -1:
            updated_nodes = [*node.pub_list]
            updated_nodes.pop(node_idx)

            # update pub list and send update request to all existing nodes
            node.update_pub_list(updated_nodes)

            updated_connections = serialize_updated_nodes(node)
            for nodeInfo in node.pub_list:
                if nodeInfo.public_key == node.get_public_key():
                    continue
                try:
                    requests.post(
                        url="http://" + nodeInfo.address + "/update-pub-list",
                        json=updated_connections
                    )
                except Exception:
                    pass

        return {'message': 'Could not connect node'}, 400

    # node responds, but it has other public key
    pubkey_response_obj = pubkey_response.json()

    new_node_info = NodeInfo(request_addr, pubkey_response_obj['public_key'])
    # node found and it needs to be updated
    if node_idx != -1:
        updated_nodes = [*node.pub_list]
        updated_nodes.pop(node_idx)

        updated_nodes.append(new_node_info)
        node.update_pub_list(updated_nodes)
    else:  # node wasn't found
        node.update_pub_list(
            [*node.pub_list, new_node_info]
        )

    updated_connections = []
    for nodeInfo in node.pub_list:
        updated_connections.append(nodeInfo.to_JSON())

    app.logger.info(f"updated_connections: {updated_connections}")

    for nodeInfo in node.pub_list:
        if nodeInfo.public_key == node.get_public_key():
            continue
        try:
            requests.post(
                url="http://" + nodeInfo.address + "/update-pub-list",
                json=updated_connections
            )
        except Exception:
            pass

    return {
        'message': 'OK',
        'status': 200
    }


@app.route("/update-pub-list", methods=['POST'])
def update_pub_list():
    current_connections_list = request.get_json()  # json.loads(request.form)
    app.logger.info(f"current_connections_list: {current_connections_list}")

    update_nodes = []
    for connection in current_connections_list:
        # rewrite existing (and valid) connections
        should_skip = False
        for nodeInfo in node.pub_list:
            if (nodeInfo.address == connection['address'] and nodeInfo.public_key == connection['public_key']):
                update_nodes.append(nodeInfo)
                should_skip = True
                break
        if should_skip:
            continue

        app.logger.info(f"new connection: {str(connection)}")

        # check if we need to update existing item from our list (because its public key changed)
        ip_found_idx = -1
        for i in range(0, len(node.pub_list)):
            if (node.pub_list[i].address == connection['address']):
                ip_found_idx = i
                break

        nodeInfo = NodeInfo(connection['address'], connection['public_key'])
        # need to update public_key for specific ip address
        if ip_found_idx != -1 and node.pub_list[ip_found_idx].public_key != connection['public_key']:
            update_nodes.append(nodeInfo)
            continue

        # connection is not on our list, so add it as it is
        update_nodes.append(nodeInfo)

    # ping all nodes (to check if they are available)
    indices_to_remove = []
    for i in range(0, len(update_nodes)):
        try:
            requests.get(url="http://" +
                         update_nodes[i].address + "/public-key")
        except Exception:
            indices_to_remove.append(i)

    final_nodes_list = []
    for i in range(0, len(update_nodes)):
        if i not in indices_to_remove:
            final_nodes_list.append(update_nodes[i])

    node.update_pub_list(final_nodes_list)

    return {'message': 'OK'}, 200


@app.route("/message:invoke", methods=['POST'])
def send_message():

    object = request.get_json()

    message = object["message"]

    receiver_pkey_hex = object["public_key"]
    if receiver_pkey_hex == None:
        return {
            "message": "Nie ma takiego klucza publicznego w bazie",
            "address": receiver_pkey_hex

        }
    node.send_message(message, receiver_pkey_hex)
    return "ok"


@app.route('/transaction', methods=['POST'])
def create_next_transaction():
    # get transaction data
    data = request.get_json()
    # propagate transaction to other nodes
    message, status = node.propagate_transaction(data)
    return message, status


@app.route('/save-to-file', methods=['POST'])
def save_blockchain_to_file():
    node.save_blockchain()
    return "ok"


@app.route("/message", methods=["POST"])
def read_message():
    request_addr = f"{request.remote_addr}:5000"
    object = request.get_json()


    sender_pkey_hex = node.get_public_key_by_address(request_addr)

    message, status = node.read_message(object, sender_pkey_hex)
    return message, status


@app.route("/last-block-hash", methods=["GET"])
def last_block_hash():
    return node.blockchain._blocks[-1].get_block_hash()

@app.route("/wallet", methods=['GET'])
def get_wallet_balance():
    return node.get_wallet_balance(), 200

@app.route("/make-double-spending", methods=['POST'])
def make_double_spending():
    data = request.get_json()
    message, status = node.make_double_spending(data)
    return message, status


if __name__ == "__main__":
    app.run(debug=True)
