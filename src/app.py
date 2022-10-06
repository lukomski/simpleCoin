from flask import Flask
import os
import requests

app = Flask(__name__)


@app.route('/publicKey')
def get_public_key():
    return "OK"

# node0 IP - 172.19.0.2 - FIRST NODE
# node1 IP - 172.19.0.3


@app.route('/make_request_to_other_app')
def f():
    # The request get public key of Node1.
    # It works if is invoked by node1/make_request_to_node_0
    # Do NOT works if is invoked by node1 on start applicatio for example like in the statement 4 lines below.
    # Here cannot reach node1 from node0
    requests.get(url=f"http://172.19.0.3:5000/publicKey")
    return "Git"


@app.route('/make_request_to_node_0')
def make_request_to_node_0():
    requests.get(url=f"http://172.19.0.2:5000/make_request_to_other_app")
    return "Git"

# Problem:
#   - When node1 call node0/make_request_to_other_app on init application - it does not work
#   - When node1 call node0/make_request_to_other_app invoked manually - it does work correcly
# Tried add timeout but not helped.


if os.environ.get("REFERENCE_ADDRESS", None) != None:
    # Action performed by node1.
    # Make request to node0.
    # The reqest is the same like in /make_request_to_node_0 endpoint
    requests.get(url=f"http://172.19.0.2:5000/make_request_to_other_app")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000, threaded=True)
