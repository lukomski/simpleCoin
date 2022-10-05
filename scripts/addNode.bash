#/etc/bash
address=$1
address=localhost:5000
docker run \
    --publish 5003:5000 \
    --env DOORMAN_ADDRESS=address \
    --env FLASK_DEBUG=1 \
    simplecoin_node0