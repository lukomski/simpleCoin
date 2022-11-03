class NodeInfo:
    address: str

    public_key_hex = None

    def __init__(self, address: str, public_key_hex: str):
        self.address = address
        self.public_key_hex = public_key_hex

    def toJSON(self):
        return {
            "address": self.address,
            "public_key": self.public_key_hex
        }
