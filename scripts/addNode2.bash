#/etc/bash
address=$1
address=172.18.0.2:5000
docker run \
    --env REFERENCE_ADDRESS=$address \
    --env FLASK_DEBUG=0 \
    --env SECRET_KEY=f62b37abb9156db72a812940b9b696426d973dd937eea540ff404c167c9371a9 \
    -p 5002:5000 \
    --network scnetwork \
    simplecoin_node0