from CryptoUtils import get_order_directory_recursively
from CryptoTransactionPool import Transaction
import hashlib
import json

difficulty_bits = 20    # 0 to 24 bits
target = 2 ** (256 - difficulty_bits)


class Block:
    '''
    Blockchain node class.
    '''

    # Header structure
    # ------------------
    # {
    #   'prev_block_hash' : <str>
    #   'nonce'           : <str>
    #   'hash_prev_nonce' : <str>
    #   'miner_pub_key'   : <str>
    # }
    __header: dict = None
    __data: dict = None

    @staticmethod
    def load(candidate_block_object: dict):
        candidate_block = Block(
            candidate_block_object['header']['prev_block_hash'],
            candidate_block_object['data'],
            candidate_block_object['header']['miner_pub_key']
        )
        candidate_block.__header['nonce'] = candidate_block_object['header']['nonce']
        candidate_block.__header['hash_prev_nonce'] = candidate_block_object['header']['hash_prev_nonce']
        return candidate_block

    @staticmethod
    def load_list(blocks_json: list[dict]):
        blocks = []
        for block_dict in blocks_json:
            blocks.append(Block.load(block_dict))
        return blocks

    def __init__(self, prev_block_hash: str, block_data: dict, miner_pub_key: str):
        '''
        Initiates Block node class instance.

        :param prev_block_hash: Hash of previous block in blockchain.
        :type  prev_block_hash: str

        :param block_data: Dictionary with block data.
        :type  block_data: dict

        :param miner_pub_key: Miner public key.
        :type  miner_pub_key: str
        '''
        self.__header = {
            'prev_block_hash': prev_block_hash,
            # 'nonce'           : <str>
            # 'hash_prev_nonce' : <str>
            'miner_pub_key': miner_pub_key
        }
        self.__data = block_data

    def get_block_hash(self):
        '''
        Calculates block hash.

        :returns: Calculated block hash
        '''
        block_json_bytes = str(self.to_json()).encode('utf-8')
        block_hash = hashlib.sha256(block_json_bytes).hexdigest()
        return block_hash

    def verify_nonce(self, nonce: int):
        '''
        Verifies if provided nonce solves proof of work problem.

        :param nonce: Nonce value to be verified.
        :type  nonce: int

        :returns: True if provided nonce value is valid, otherwise False.
        '''

        pow_obj = self.get_pow_data()
        # find hash value for header
        hash_result = hashlib.sha256(str(pow_obj).encode('utf-8') +
                                     str(nonce).encode('utf-8')).hexdigest()
        # check if it's valid (lesser than target)
        is_nonce_valid = int(hash_result, 16) < target
        return is_nonce_valid

    def calculate_hash_prev_block_nonce(self):
        nonce = self.__header['nonce']
        prev_block_hash = self.get_prev_hash()

        hash_prev_block_nonce = hashlib.sha256(
            (str(prev_block_hash) + str(nonce)).encode('utf-8')
        ).hexdigest()

        return hash_prev_block_nonce

    def get_pow_data(self):
        return get_order_directory_recursively({
            'data': self.__data,
            'header': {
                'miner_pub_key': self.__header['miner_pub_key'],
                'prev_block_hash': self.get_prev_hash(),
            }
        })

    def get_prev_hash(self):
        return self.__header['prev_block_hash']

    def verify_block(self):
        '''
        Verifies block consistency that is:
        1) Check if nonce placed in header solves proof of work
        2) Check if hash_prev_nonce value is valid - h(prev. hash + nonce)

        :returns: True if block is correct, otherwise False
        '''
        # check if nonce value solves proof of work
        is_valid = self.verify_nonce(self.__header['nonce'])
        # if not is_valid:
        #    pow_obj = self.get_pow_data()
        #    find hash value for header
        #    hash_result = hashlib.sha256(str(pow_obj).encode('utf-8') +
        #                              str(self._header['nonce']).encode('utf-8')).hexdigest()
        #    raise ValueError(f"hash_result = {hash_result}")

        # check if calculated h(prev. block hash + nonce) matches value placed in header
        prev_block_nonce_hash_calculated = self.calculate_hash_prev_block_nonce()
        prev_block_nonce_hash = self.__header['hash_prev_nonce']

        # final verification
        valid_block = is_valid and (
            prev_block_nonce_hash == prev_block_nonce_hash_calculated)
        return valid_block

    def to_json(self):
        '''
        Converts blockchain block instance to json.

        :returns: Block dictionary object
        '''
        # restore block object as dictionary
        block_object = get_order_directory_recursively({
            'data': self.__data,
            'header': self.__header
        })
        return block_object

    def get_transactions(self) -> list[Transaction]:
        if self.__data == None:
            return []
        if 'transactions' not in self.__data:
            return []
        if self.__data['transactions'] is None:
            return []
        transactions = []
        for transaction_dict in self.__data['transactions']:
            _, valid = Transaction.is_valid(transaction_dict)
            if valid:
                transaction = Transaction.create_from_json(transaction_dict)
                transactions.append(transaction)
        return transactions

    def set_nonce(self, nonce: str) -> None:
        self.__header['nonce'] = nonce

    def set_prev_hash_nonce(self, prev_hash_nonce: str) -> None:
        self.__header['hash_prev_nonce'] = prev_hash_nonce

    def get_miner(self) -> str:
        return self.__header['miner_pub_key']
    
    @staticmethod
    def load_blocks(filename: str):
        try:
            with open(filename, "r") as f:
                file_content = f.read()
                parsed_blockchain = json.loads(file_content)
                return Block.load_list(parsed_blockchain)
        except FileNotFoundError:
            return None
        except ValueError:
            return None
