from flask import Flask, request, render_template
import os
import json 
import utils
import socket
app = Flask(__name__)

store = {}
store["nodes"] = []
store["nodeName"] = os.environ.get('NODE_NAME')
store["ip"] = socket.gethostbyname(socket.gethostname())

def initialization():
    store["privateKey"], store["publicKey"] = utils.generatePrivateAndPublicKeys()
    if os.environ.get('FIRST_NODE') == "true":
        print('FIRST NODE')
        # add myself to the list of nodes
        store["nodes"] = [{
            "publicKey": str(store["publicKey"]),
            "ip": str(store["ip"])
        }]
        pass
    else:
        print('NEXT NODE')
        doorman_address = os.environ.get('DOORMAN_ADDRESS')
        utils.enterToNetwork(doorman_address)
        pass
    pass

initialization()

@app.route('/')
def hello_geek():
    return render_template('home.html')

@app.route('/nodes')
def get_nodes():
    return json.dumps(store['nodes'])

@app.route('/nodeName')
def get_node_name():
    return store['nodeName']

@app.route('/publicKey')
def get_public_key():
    return store['publicKey']

@app.route('/node', methods=['POST'])
def get_node():
    return store['publicKey']

# for tests
@app.route('/endecrypt')
def endecrypt_message():
    message = request.args.get('message')
    return utils.encryptMessage(message, store['privateKey'])

@app.route('/sign')
def sign_message():
    message = request.args.get('message')
    return utils.signMessage(message, store['privateKey'])

if __name__ == "__main__":
    app.run(debug=True)