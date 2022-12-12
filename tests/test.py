import requests
import json
import time

nodes = [
    {
        'id': 'node0',
        'url': "http://localhost:5000",
        'payloads': [],
        'pub_key': None,
        'ignore': False
    },
    {
        'id': 'node1',
        'url': "http://localhost:5001",
        'payloads': [],
        'pub_key': None,
        'ignore': False
    },
    {
        'id': 'node2',
        'url': "http://localhost:5002",
        'payloads': [],
        'pub_key': None,
        'ignore': True
    }
]

TIMEOUT = 8

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
if not nodes[1]['ignore']:
    nodes[1]['payloads'] = []
    # [
    #     {
    #         "message": "Some transaction message 2",
    #         "amount": 3,
    #         "sender": nodes[1]['pub_key'],
    #         "receiver": nodes[2]['pub_key']
    #     }
    # ]
if not nodes[2]['ignore']:
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
