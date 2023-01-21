
from CryptoUtils import get_order_directory_recursively, is_valid
from CryptoInput import Input
from CryptoOutput import Output
from logging import Logger
from CryptoKeyManager import KeyManager
from logging import Logger
import json

class Transaction:
    __data: dict = None

    def __init__(self, transaction_id: str, transaction_fee: int, signature: str, inputs: list[Input], outputs: list[Output], message: str):
        self.__data = {
            'transaction_id': transaction_id,
            'transaction_fee': transaction_fee,
            'signature': signature,
            'inputs': inputs,
            'outputs': outputs,
            'message': message
        }

    def get_data_without_signature(self):
        data = {
            'transaction_id': self.__data['transaction_id'],
            'transaction_fee': self.__data['transaction_fee'],
            'inputs': [input.to_json() for input in self.__data['inputs']],
            'outputs': [output.to_json() for output in self.__data['outputs']],
            'message': self.__data['message']
        }
        data = get_order_directory_recursively(data)
        return data

    def get_transaction_fee(self):
        return int(self.__data['transaction_fee'])

    def get_signature(self):
        return self.__data['signature']

    def set_signature(self, signature):
        self.__data['signature'] = signature

    @staticmethod
    def is_transaction_request_valid(data: dict, logger: Logger = None) -> tuple[str, bool]:
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
            'receiver': {
                'type': str
            }
        }
        return is_valid(config, data)

    @staticmethod
    def is_valid(data: dict, logger: Logger = None) -> tuple[str, bool]:
        config = {
            'transaction_id': {
                'type': str,
            },
            'transaction_fee': {
                'type': int,
            },
            'signature': {
                'type': str,
            },
            'inputs': {
                'type': Input,
                'list': True
            },
            'outputs': {
                'type': Output,
                'list': True
            },
            'message': {
                'type': str,
                'optional': True
            }
        }
        return is_valid(config, data)

    def to_json(self):
        return get_order_directory_recursively({
            **self.__data,
            'inputs': [input.to_json() for input in self.__data['inputs']],
            'outputs': [output.to_json() for output in self.__data['outputs']]
        })

    def get_inputs(self) -> list[Input]:
        return self.__data['inputs']

    def get_outputs(self) -> list[Output]:
        return self.__data['outputs']

    def get_transaction_id(self) -> str:
        return self.__data['transaction_id']

    @staticmethod
    def create_from_json(transaction_json: dict):
        inputs = transaction_json['inputs']
        outputs = transaction_json['outputs']

        inputObjects = [Input(**input) for input in inputs]
        outputObjects = [Output.load(output) for output in outputs]

        transaction = Transaction(transaction_id=transaction_json['transaction_id'],
                                  transaction_fee=transaction_json['transaction_fee'],
                                  signature=transaction_json['signature'],
                                  inputs=inputObjects,
                                  outputs=outputObjects,
                                  message=transaction_json['message'])
        return transaction

    @staticmethod
    def create_transaction(key_manager: KeyManager, logger: Logger, transaction_id: str, transaction_fee: int, inputs: list[Input], outputs: list[Output], message: str):
        '''
        This method is prepared for 'Transaction' class instances without signature - it's calculated down here.
        '''
        # create data without signature
        transaction = Transaction(transaction_id=transaction_id, transaction_fee=transaction_fee,
                                  signature=None, inputs=inputs, outputs=outputs, message=message)
        data = transaction.get_data_without_signature()

        signature = key_manager.sign(json.dumps(data).encode('utf-8'))
        # add signature to data
        data = {**data, 'signature': signature}
        message, is_valid = Transaction.is_valid(data, logger)

        if not is_valid:
            return None, message, False

        transaction.set_signature(signature)
        return transaction, message, True
