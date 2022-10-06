class NodeInfo:
    address: str

    public_key: bytes

    def __init__(self, address: str, public_key: bytes):
        self.address = address
        self.public_key = public_key

    def toJSON(self):
        return {
            "address": self.address,
            "public_key": self.public_key.decode("utf-8")
        }
