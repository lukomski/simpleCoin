import requests
import json
import time

response = requests.request(
    "GET", 'http://localhost:5000/nodes', headers={}, data={})
fetched_nodes = response.json()
nodes = [
    {
        'id': f'node{idx}',
        'url': f'http://localhost:500{idx}',
        'payloads': [],
        'pub_key': None,
        'ignore': False
    }
    for idx in range(len(fetched_nodes))]

TIMEOUT = 2

headers = {
    'Content-Type': 'application/json'
}

# get public key
pub_keys = []
for idx in range(len(nodes)):
    if nodes[idx]['ignore']:
        continue
    response = requests.request(
        "GET", f'{nodes[idx]["url"]}/public-key', headers=headers, data={})
    nodes[idx]['pub_key'] = response.json()['public_key']

# create payloads
nodes[0]['payloads'] = [
    {
        "message": "Some transaction message 1",
        "amount": 4,
        "sender": nodes[0]['pub_key'],
        "receiver": nodes[1]['pub_key']
    }
]
nodes[1]['payloads'] = []
[
    {
        "message": "Some transaction message 2",
        "amount": 3,
        "sender": nodes[1]['pub_key'],
        "receiver": nodes[2]['pub_key']
    }
]
nodes[2]['payloads'] = [
    {
        "message": "Some transaction message 3",
        "amount": 1,
        "sender": nodes[2]['pub_key'],
        "receiver": nodes[0]['pub_key']
    },
    {
        "message": "Some transaction message 3",
        "amount": 1,
        "sender": nodes[2]['pub_key'],
        "receiver": nodes[1]['pub_key']
    }
]


for node in nodes:
    if node['ignore']:
        continue
    for payload in node['payloads']:
        print(f'Sending transaction to {node["id"]}')
        response = requests.request(
            "POST", f'{node["url"]}/transaction', headers=headers, data=json.dumps(payload))
        print(f'{node["id"]}: {response.text}')
        time.sleep(TIMEOUT)

for node in nodes:
    if node['ignore']:
        continue
    response = requests.request(
        "GET", f'{node["url"]}/wallet', headers=headers, data=json.dumps(payload))
    print(f'wallet {node["id"]}:')
    print(json.dumps(response.json(), indent=2))
