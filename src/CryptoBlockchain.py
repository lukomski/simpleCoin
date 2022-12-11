from CryptoBlock import Block
from CryptoTransaction import Transaction
import json

FILE_NAME = "blockchain.json"


class BlockChain:
    _blocks: list[Block] = None

    def __init__(self, generic_block: Block | None):
        '''
        Initializes 'BlockChain' class instance with initial generic block.

        :param generic_block: Generic block for blockchain.
        :type  generic_block: Block
        '''
        if generic_block is None:
            self._blocks = []
        else:
            self._blocks = [generic_block]

    def add_block(self, new_block: Block):
        self._blocks.append(new_block)

    def to_json(self):
        blocks = []
        for block in self._blocks:
            blocks.append(block.to_json())
        return blocks

    def validate_candidate_block(self, candidate_block: Block) -> bool:
        last_block_hash = self._blocks[-1].get_block_hash()
        prev_block_hash_in_candidate = candidate_block.get_prev_hash()

        # candidate block's previous hash needs to match hash of last block in current blockchain
        if (last_block_hash != prev_block_hash_in_candidate):
            return False

        is_candidate_block_consistent = candidate_block.verify_block()
        if not is_candidate_block_consistent:
            return False
        return True

    def validate(self):
        '''
        Validates whether blockchain is consistent or not.

        :returns: True if blockchain is valid, otherwise False.
        '''
        if len(self._blocks) == 1:  # single block in blockchain
            # just verify single block, there's no need to check with other block
            is_valid = self._blocks[0].verify_block()
            return is_valid
        else:  # more than one block in blockchain
            for i in range(1, len(self._blocks)):
                # check if previous block hash is assigned properly to next block
                prev_block_hash = self._blocks[i - 1].get_block_hash()
                assigned_prev_block_hash = self._blocks[i].get_prev_hash()

                # if not, blockchain is inconsistent
                if (prev_block_hash != assigned_prev_block_hash):
                    return False

                # if previous block hash is assigned properly, check other conditions
                # that is valid nonce value and hash_prev_nonce value (assigned to block header)
                is_valid = self._blocks[i].verify_block()
                if not is_valid:
                    return False
            return True

    def save(self, filename):
        with open(filename, "w") as f:
            f.write(json.dumps(self.to_json()))

    @staticmethod
    def create_blockchain(blockchain_list: list[Block]):
        '''
        Creates blockchain class instance (like blockchain factory) from given list of blocks.

        :throws: ValueError when:
        1) Provided blocks list is empty.
        2) Provided generic block for block is invalid.
        3) Could not add next (from list) block to blockchain.
        '''
        if len(blockchain_list) == 0:
            raise ValueError(
                "Provided blockchain is empty. Could not create blockchain.")

        generic_block_valid = blockchain_list[0].verify_block()
        if not generic_block_valid:
            raise ValueError("Generic block is invalid.")

        blockchain = BlockChain(blockchain_list[0])

        for i in range(1, len(blockchain_list)):
            try:
                block = blockchain_list[i]
                is_valid_block = blockchain.validate_candidate_block(block)

                if not is_valid_block:
                    raise ValueError(
                        "Found inconsistency in loaded blockchain.")

                blockchain.add_block(blockchain_list[i])
            except ValueError as err:
                raise ValueError(
                    f'Error for index {i} of the chain: {str(err)}')
            print("Block added successfully")

        return blockchain

    @staticmethod
    def load_blockchain(filename: str):
        '''
        Restores blockchain from provided file.

        :throws:\n
        ValueError - could not restore blockchain.\n
        FileNotFoundError - could not find specified file with blockchain.

        :returns: Restored from file blockchain.
        '''
        try:
            with open(filename, "r") as f:
                file_content = f.read()
                parsed_blockchain = json.loads(file_content)

                blocks = Block.load_list(parsed_blockchain)
                blockchain = BlockChain.create_blockchain(blocks)

                return blockchain
        except FileNotFoundError:
            return None
        except ValueError:
            return None

    def get_transactions(self) -> list[Transaction]:
        transactions = []
        for block in self._blocks:
            block_transactions = block.get_transactions()
            transactions.extend(block_transactions)
        return transactions
