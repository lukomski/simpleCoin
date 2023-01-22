
from CryptoTransaction import Transaction


class TransactionPool:
    _transactions: list[Transaction] = None

    def __init__(self):
        self._transactions = []

    def add_transaction(self, transaction: Transaction):
        self._transactions.insert(0, transaction)

    def get_next_transaction_json(self, lost_transactions: list[Transaction], applied_tranaction_ids = list[str]) -> dict | None:
        transaction = self.get_next_transaction(lost_transactions, applied_tranaction_ids)
        if transaction is not None:
            return transaction.to_json()
        return None

    def get_next_transaction(self, lost_transactions: list[Transaction], applied_tranaction_ids = list[str]) -> Transaction | None:
        next_transaction = None
        # Get transaction from transaction list
        while len(self._transactions) != 0:
            transaction = self._transactions[-1]
            if transaction.get_transaction_id() in applied_tranaction_ids:
                self._transactions.pop()
                continue
            next_transaction = transaction
            break
        if next_transaction is not None:
            return next_transaction
        
        # Get lost transaction
        if len(lost_transactions) > 0:
            next_transaction = lost_transactions[0]
            return next_transaction
        
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
