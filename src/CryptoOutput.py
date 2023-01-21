
from CryptoUtils import get_order_directory_recursively, is_valid
from logging import Logger


class Output:
    __owner: str = None
    __amount: int = 0

    def __init__(self, owner: str, amount: int) -> None:
        self.__owner = owner
        self.__amount = amount

    @staticmethod
    def is_valid(data: dict, logger: Logger = None) -> bool:
        config = {
            'owner': {
                'type': str,
            },
            'amount': {
                'type': int,
            }
        }
        return is_valid(config, data)

    def load(data: dict, logger: Logger = None):
        _, is_valid = Output.is_valid(data)
        if not is_valid:
            return None
        return Output(**data)

    def get_owner(self) -> str:
        return self.__owner

    def get_amount(self) -> int:
        return self.__amount

    def to_json(self):
        return get_order_directory_recursively({
            'owner': self.__owner,
            'amount': self.__amount
        })
