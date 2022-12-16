import requests
import json
response = requests.request(
    "GET", 'http://localhost:5000/nodes', headers={}, data={})
fetched_nodes = response.json()
nodes = [{
    'id': f'node{idx}',
    'internal_url': fetched_nodes[idx]['address'],
    'url': f'http://localhost:500{idx}',
    'public_key': fetched_nodes[idx]['public_key']
} for idx in range(len(fetched_nodes))]

# print('nodes:', json.dumps(nodes, indent=1))

payload = {}
headers = {}
responses = {}

for node in nodes:
    id = node['id']
    responses[id] = requests.request(
        "GET", f"{node['url']}/blocks", headers=headers, data=payload)

for node in nodes:
    print(node['id'], end=' ')
    response = responses[node['id']]
    print('count_blocks: ', len(response.json()), end=' ')
    print('inconsistent with:', end='')
    node_text = response.text
    for other_node in nodes:
        if other_node['id'] == node['id']:
            continue
        other_node_text = responses[other_node['id']].text
        if node_text != other_node_text:
            print(other_node['id'], end=', ')
    print()
