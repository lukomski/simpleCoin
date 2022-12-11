set address=172.21.0.2:5000
set skey=23bf94bd71f9b64ae40e9289266fdbf99e71e7064732c6188c169f8f5df6ebd6
docker run --env REFERENCE_ADDRESS=%address% --env SECRET_KEY=%skey% -p 5002:5000 --network scnetwork simplecoin_node0