set address=172.20.0.2:5000
docker run --env REFERENCE_ADDRESS=%address% -p 5001:5000 --network scnetwork simplecoin_node0