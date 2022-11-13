import nacl.secret


def get_order_directory_recursively(directory: dict):
    new_dict = dict(sorted({**directory}.items()))
    for (key, value) in new_dict.items():
        if type(value) is dict:
            new_dict[key] = get_order_directory_recursively(
                value)
    return new_dict


def encrypt_by_secret_key(secret_key_hex: str, text: str) -> str:
    '''
    Encrypt text by secret key returning encrypted message as hex.
    '''
    key_bytes = bytes.fromhex(secret_key_hex)
    text_bytes = text.encode('utf-8')
    box = nacl.secret.SecretBox(key_bytes)
    encrypted = box.encrypt(text_bytes).hex()
    return encrypted


def decrypt_by_secret_key(secret_key_hex: str, encrypted_text_hex: str) -> str:
    '''
    Decrypt hex text by secret key returning original text.
    '''
    key_bytes = bytes.fromhex(secret_key_hex)
    encrypted_text_bytes = bytes.fromhex(encrypted_text_hex)
    box = nacl.secret.SecretBox(key_bytes)
    decrypted_bytes = box.decrypt(encrypted_text_bytes)
    decrypted = decrypted_bytes.decode('utf-8')
    return decrypted
