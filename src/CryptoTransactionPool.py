
from CryptoUtils import get_order_directory_recursively


class Transaction:
    _data: dict = None

    def __init__(self, data: dict):
        self._data = data

    def to_json(self):
        return get_order_directory_recursively(self._data)


class TransactionPool:
    _transactions: list[Transaction] = None

    def __init__(self):
        self._transactions = []

    def add_transaction(self, transaction: Transaction):
        self._transactions.append(transaction)

    def get_next_transaction_json(self):
        return self._transactions[-1].to_json() if len(self._transactions) > 0 else None

    def pop_next_transaction(self):
        return self._transactions.pop()

    def to_json(self):
        json_data = {}
        for i in range(len(self._transactions)):
            json_data[f"transaction_{str(i + 1)}"] = self._transactions[i].to_json()
        return json_data
