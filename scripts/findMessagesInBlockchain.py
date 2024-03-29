import requests
import json
node = {
    'id': 'node0',
    'url': "http://localhost:5000/blocks"
}
payload = {}
headers = {}

finding_message = 'Some transaction'


response = requests.request(
    "GET", node['url'], headers=headers, data=payload)


print(node['id'], end=' ')
blockchain = response.json()
print('count_blocks: ', len(blockchain))

found_blocks = []
for block in blockchain:
    if block['data'] is None:
        continue
    if 'transactions' not in block['data'] or block['data']['transactions'] is None:
        continue
    for transaction in block['data']['transactions']:
        if 'message' in transaction and finding_message in transaction['message']:
            found_blocks.append(block)
print(f'Found blocks ({len(found_blocks)}):')
print(json.dumps(found_blocks, indent=1))
