from CryptoNodeInfo import NodeInfo
from flask import Flask, request, render_template
import os

import requests
from CryptoNode import Node


app = Flask(__name__)

node = Node(os.environ.get("REFERENCE_ADDRESS", None), app)
print(node.pub_list)

app.node = node


@app.route('/')
def hello_geek():
    return render_template('home.html')


@app.route('/nodes')
def get_nodes():
    pub_list = []
    for nodeInfo in node.pub_list:
        pub_list.append(nodeInfo.toJSON())
    return pub_list


@app.route('/publicKey')
def get_public_key():
    return {
        'public_key': node.get_public_key().decode('utf8')
    }


def serialize_updated_nodes(node):
    updated_connections = []
    for nodeInfo in node.pub_list:
        updated_connections.append(
            nodeInfo.toJSON()
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
            url="http://" + request_addr + "/publicKey")
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

    new_node_info = NodeInfo(request_addr, str.encode(
        pubkey_response_obj['public_key'], 'utf8'))
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
        updated_connections.append(nodeInfo.toJSON())

    app.logger.error(f"updated_connections: {updated_connections}")

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
    app.logger.error(f"current_connections_list: {current_connections_list}")

    update_nodes = []
    for connection in current_connections_list:
        # rewrite existing (and valid) connections
        should_skip = False
        for nodeInfo in node.pub_list:
            if (nodeInfo.address == connection['address'] and nodeInfo.public_key.decode("utf8") == connection['public_key']):
                update_nodes.append(nodeInfo)
                should_skip = True
                break
        if should_skip:
            continue

        app.logger.error(f"new connection: {str(connection)}")

        # check if we need to update existing item from our list (because its public key changed)
        ip_found_idx = -1
        for i in range(0, len(node.pub_list)):
            if (node.pub_list[i].address == connection['address']):
                ip_found_idx = i
                break

        nodeInfo = NodeInfo(connection['address'], str.encode(
            connection['public_key'], 'utf8'))
        # need to update public_key for specific ip address
        if ip_found_idx != -1 and node.pub_list[ip_found_idx].public_key.encode('utf8') != connection['public_key']:
            update_nodes.append(nodeInfo)
            continue

        # connection is not on our list, so add it as it is
        update_nodes.append(nodeInfo)

    # ping all nodes (to check if they are available)
    indices_to_remove = []
    for i in range(0, len(update_nodes)):
        try:
            requests.get(url="http://" +
                         update_nodes[i].address + "/publicKey")
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

    message = str.encode(object["message"], 'utf8')

    address = object["address"]
    sender_pkey = node.getPublicKeyByAddress(address)
    if sender_pkey == None:
        return {
            "message": "Nie ma takiego adresu w bazie",
            "address": address

        }
    app.logger.error('sender_pkey:' + str(sender_pkey))
    node.send_message(message, sender_pkey)
    return "ok"


@ app.route("/message", methods=["POST"])
def read_message():
    request_addr = f"{request.remote_addr}:5000"
    object = request.get_json()

    sender_pkey = node.getPublicKeyByAddress(request_addr)
    object = node.read_message(object, sender_pkey)
    return {
        "trusted": object["trusted"]
    }, 200 if object["trusted"] else 400


if __name__ == "__main__":
    app.run(debug=True)
