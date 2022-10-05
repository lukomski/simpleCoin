#/etc/bash
address=$1
address=localhost:5000
docker run \
    --env DOORMAN_ADDRESS=address \
    --env FLASK_DEBUG=1 \
    simplecoin_node0