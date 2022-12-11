from logging import Logger
from nacl.signing import SigningKey
from CryptoUtils import encrypt_by_secret_key, decrypt_by_secret_key
import json
KEYS_FILE_PATH = 'keys.json'


class KeyManager:
    # Hex representation of public key
    public_key: str = None

    def __init__(self, logger: Logger, secret_key: str) -> None:
        self.__logger = logger
        self.__secret_key = secret_key
        seed = self.get_seed_from_file()
        if seed is None:
            self.__private_key = SigningKey.generate()
        else:
            self.__private_key = SigningKey(seed)
        self.__public_key = self.__private_key.verify_key
        self.public_key = self.__public_key.encode().hex()
        self.save_keys()
        pass

    def sign(self, payload_bytes: bytes):
        '''
        Get signature for payload bytes.
        Returned value is hex representation of the signature.
        '''
        signature = self.__private_key.sign(payload_bytes).signature.hex()
        return signature

    def save_keys(self):
        keys_data = {
            'seed': encrypt_by_secret_key(self.__secret_key, self.__private_key._seed.hex()),
            'public_key': self.public_key
        }
        with open(KEYS_FILE_PATH, "w") as f:
            f.write(json.dumps(keys_data))

    def get_seed_from_file(self):
        try:
            seed = None
            with open(KEYS_FILE_PATH, "r") as f:
                keys_data = f.read()
                seed = decrypt_by_secret_key(
                    self.__secret_key, keys_data['seed'])
            return bytes.fromhex(seed)
        except Exception:
            return None
