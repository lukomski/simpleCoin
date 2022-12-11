import requests
import json

nodes = [
    {
        'id': 'node0',
        'url': "http://localhost:5000/transaction",
        'payloads': [
            {
                "message": "Some transaction message 1",
                "amount": 0.000425,
                "source_coinbase": "source_coinbase",
                "destination_coinbase": "destination_coinbase"
            }
        ]
    },
    {
        'id': 'node1',
        'url': "http://localhost:5001/transaction",
        'payloads': [
            {
                "message": "Some transaction message 2",
                "amount": 0.000425,
                "source_coinbase": "source_coinbase",
                "destination_coinbase": "destination_coinbase"
            }
        ]
    },
    {
        'id': 'node2',
        'url': "http://localhost:5002/transaction",
        'payloads': [
            {
                "message": "Some transaction message 3",
                "amount": 0.000425,
                "source_coinbase": "source_coinbase",
                "destination_coinbase": "destination_coinbase"
            },
            {
                "message": "Some transaction message 4",
                "amount": 0.000425,
                "source_coinbase": "source_coinbase",
                "destination_coinbase": "destination_coinbase"
            }
        ]
    }
]

headers = {
    'Content-Type': 'application/json'
}

for node in nodes:
    for payload in node['payloads']:
        response = requests.request(
            "POST", node['url'], headers=headers, data=json.dumps(payload))
        print(response.text)
