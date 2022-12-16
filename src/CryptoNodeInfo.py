class NodeInfo:
    address: str

    public_key = None

    def __init__(self, address: str, public_key: str):
        self.address = address
        self.public_key = public_key

    def to_JSON(self):
        return {
            "address": self.address,
            "public_key": self.public_key
        }
