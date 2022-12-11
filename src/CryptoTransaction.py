
from CryptoUtils import get_order_directory_recursively, is_valid
from CryptoInput import Input
from CryptoOutput import Output
from logging import Logger


class Transaction:
    __data: dict = None

    def __init__(self, transaction_id: str, transaction_fee: int, signature: str, inputs: list[dict], outputs: list[dict], message: str):
        self.__data = {
            'transaction_id': transaction_id,
            'transaction_fee': transaction_fee,
            'signature': signature,
            'inputs': inputs,
            'outputs': outputs,
            'message': message
        }

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
        return get_order_directory_recursively(self.__data)

    def get_inputs(self) -> list[Input]:
        return [Input(**input) for input in self.__data['inputs']]

    def get_outputs(self) -> list[Output]:
        return [Output(**output) for output in self.__data['outputs']]

    def get_transaction_id(self) -> str:
        return self.__data['transaction_id']
