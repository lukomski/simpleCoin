
class Transaction:
    _data: dict = None

    def __init__(self, data: dict):
        self._data = data

    def to_json(self):
        data = dict(sorted(self._data.items()))
        return data

TR_NUM_TO_CONSUME = 5

class TransactionPool:
    _transactions: list[Transaction] = None
    _should_start_dig = None
    _digging = None

    def __init__(self):
        self._transactions = []
        self._should_start_dig = False
        self._digging = False

    def add_transaction(self, transaction: Transaction):
        self._transactions.append(transaction)
        if len(self._transactions) >= TR_NUM_TO_CONSUME:
            self._should_start_dig = True

    def should_dig(self):
        return self._should_start_dig
    
    def is_dig_state(self):
        return self._digging

    def set_dig_state(self, value):
        self._digging = value
    
    def to_json(self):
        json_data = {}
        for i in range(len(self._transactions)):
            json_data[f"transaction_{str(i + 1)}"] = self._transactions[i].to_json()
        return json_data