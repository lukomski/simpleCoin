
from CryptoUtils import get_order_directory_recursively, is_valid
from CryptoOutput import Output
from logging import Logger

BLOCK_PRICE_ID = 'block_mining_price'

class Input(Output):
    __transaction_id: str = None

    def __init__(self, transaction_id: str, owner: str, amount: int) -> None:
        super().__init__(owner, amount)
        self.__transaction_id = transaction_id

    def to_json(self):
        return get_order_directory_recursively({
            **super().to_json(),
            'transaction_id': self.__transaction_id
        })

    def get_transaction_id(self) -> str:
        return self.__transaction_id
    
    def is_block_price(self):
        return self.__transaction_id == BLOCK_PRICE_ID

    @staticmethod
    def output_to_input(output: Output, transaction_id: str, logger: Logger = None):
        message, is_valid = Input.is_valid({
            'transaction_id': transaction_id,
            'owner': output.get_owner(),
            'amount': output.get_amount()
        })
        if logger:
            logger.info(f'is_valid: {is_valid}, message: {message}')
        return Input(transaction_id=transaction_id, owner=output.get_owner(), amount=output.get_amount())

    @staticmethod
    def is_valid(data: dict, logger: Logger = None) -> tuple[str, bool]:
        config = {
            'owner': {
                'type': str,
            },
            'amount': {
                'type': int,
            },
            'transaction_id': {
                'type': str
            }
        }
        return is_valid(config, data)
    
    @staticmethod
    def is_list_valid(list_of_inputs: list[dict]) -> tuple[str, bool]:
        for data in list_of_inputs:
            msg, is_valid = Input.is_valid(data)
            if not is_valid:
                return msg, False
        return 'Ok', True
    
    @staticmethod
    def from_json(data: dict):
        return Input(amount=data['amount'], transaction_id=data['transaction_id'], owner=data['owner'])
    
    @staticmethod
    def from_list_json(data_list: list[dict]):
        return [Input.from_json({**input}) for input in data_list]
