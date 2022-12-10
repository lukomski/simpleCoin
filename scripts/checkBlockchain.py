import requests
nodes = [
    {
        'id': 'node0',
        'url': "http://localhost:5000/blocks"
    },
    {
        'id': 'node1',
        'url': "http://localhost:5001/blocks"
    },
    {
        'id': 'node2',
        'url': "http://localhost:5002/blocks"
    }
]
payload = {}
headers = {}
responses = {}

for node in nodes:
    id = node['id']
    responses[id] = requests.request(
        "GET", node['url'], headers=headers, data=payload)

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
            print(other_node['id'])
    print()
