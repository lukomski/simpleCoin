
from CryptoTransaction import Transaction


class TransactionPool:
    _transactions: list[Transaction] = None

    def __init__(self):
        self._transactions = []

    def add_transaction(self, transaction: Transaction):
        self._transactions.insert(0, transaction)

    def get_next_transaction_json(self, lost_transactions: list[Transaction], applied_tranaction_ids = list[str]):
        next_transaction = None
        # Get transaction from transaction list
        while len(self._transactions) != 0:
            transaction = self._transactions[0]
            if transaction.get_transaction_id() in applied_tranaction_ids:
                self._transactions.pop()
                continue
            next_transaction = transaction
            break
        if next_transaction is not None:
            return next_transaction.to_json()
        
        # Get lost transaction
        if len(lost_transactions) > 0:
            next_transaction = lost_transactions[0]
            return next_transaction.to_json()
        
        return None
            

    def pop_next_transaction(self):
        if len(self._transactions) == 0:
            return
        return self._transactions.pop()

    def to_json(self):
        json_data = {}
        for i in range(len(self._transactions)):
            json_data[f"transaction_{str(i + 1)}"] = self._transactions[i].to_json()
        return json_data
