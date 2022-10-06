set address=172.19.0.2:5000
docker run --env REFERENCE_ADDRESS=%address% --env FLASK_DEBUG=1 -p 5001:5000 --network scnetwork simplecoin_node0