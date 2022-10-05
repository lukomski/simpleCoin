set address=localhost:5000
docker run --env REFERENCE_ADDRESS=%address% --env FLASK_DEBUG=1 simplecoin_node0