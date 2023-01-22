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


def is_valid(config, data):
    out = {}
    for requested_field in config.keys():
        # check for needed fiels
        if not requested_field in data:
            if 'optional' in config[requested_field] and config[requested_field]['optional']:
                continue
            return f'Field "{requested_field}" is required', False
        # check type
        if 'list' in config[requested_field] and config[requested_field]['list']:
            for field_item in data[requested_field]:
                message, is_valid = config[requested_field]['type'].is_valid(
                    field_item)
                if not is_valid:
                    return f'In "{requested_field}" list element {field_item}: {message}', False
        elif not isinstance(data[requested_field], config[requested_field]['type']):
            return f'Field "{requested_field}" should be instance {str(config[requested_field]["type"])} but is {str(type(data[requested_field]))}', False
        out[requested_field] = data[requested_field]
    # check for not needed fields
    for requested_field in data.keys():
        if requested_field not in config:
            return f'Found illicit field {requested_field}', False
    return 'ok', True

def is_double_spending_transaction_request_valid(transaction_data: dict) -> tuple[str, bool]:
    config = {
        'amount': {
            'type': int,
        },
        'message': {
            'type': str,
            'optional': True
        },
        'sender': {
            'type': str
        },
        'receiver1': {
            'type': str
        },
        'receiver2': {
            'type': str
        }
    }
    return is_valid(config, transaction_data)
