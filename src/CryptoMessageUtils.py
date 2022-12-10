import json
from nacl.signing import VerifyKey
from CryptoKeyManager import KeyManager


class MessageUtils:

    def __init__(self, key_manager: KeyManager):
        self.__key_manager = key_manager
        pass

    def wrap_message(self, payload: dict):
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = self.__key_manager.sign(payload_bytes)
        return {
            'payload': payload,
            'signature': signature
        }

    def verify_message(self, frame: dict, sender_pk_bytes):
        payload = frame['payload']
        payload_bytes = json.dumps(payload).encode('utf-8')
        signature = bytes.fromhex(frame['signature'])
        verify_key = VerifyKey(sender_pk_bytes)
        # throw error if not correct
        verify_key.verify(payload_bytes, signature)

    def getPayload(self, frame: dict):
        return frame['payload']
