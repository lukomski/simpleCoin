from CryptoBlock import Block
from CryptoTransaction import Transaction
from CryptoInput import Input, BLOCK_PRICE_ID
import json
from logging import Logger

FILE_NAME = "blockchain.json"
BLOCK_PRICE_AMOUNT = 5


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

    def get_length(self):
        return len(self._blocks)

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

    def get_mined_blocks(self, owner: str) -> list[Block]:
        blocks = []
        for block in self._blocks:
            if block.get_miner() != owner:
                continue
            blocks.append(block)
        return blocks

    def get_blocks(self) -> list[Block]:
        return self._blocks
    
    def get_inputs(self, target_owner: str, logger: Logger | None = None) -> list[Input]:
        '''
        Return valid inputs for target owner.
        '''
        all_transactions = self.get_transactions()
        mined_blocks = len(self.get_mined_blocks(target_owner))
        if logger:
            logger.info(
                f'mined_blocks: found {mined_blocks} mined_blocks')
            logger.info(f'Found all_transactions: {len(all_transactions)}')
        transaction_sources = {}
        for transaction in all_transactions:
            inputs = transaction.get_inputs()
            outputs = transaction.get_outputs()
            # remove from sources used outputs
            for input in inputs:
                source_transaction_id = input.get_transaction_id()
                if input.get_owner() != target_owner:
                    continue
                if source_transaction_id == BLOCK_PRICE_ID:
                    if mined_blocks > 0:
                        mined_blocks -= 1
                    else:
                        if logger:
                            logger(
                                f'Input {input.to_json()} in transaction {transaction.to_json()} get block mining price which does not have')
                    continue
                elif source_transaction_id not in transaction_sources:
                    if logger:
                        logger.warning(
                            f'In transaction_sources {transaction.to_json()} input {input.to_json()} has no valid previous source')
                    continue
                transaction_sources.pop(source_transaction_id)
            # add to sources outputs from block
            transaction_id = transaction.get_transaction_id()
            for output in outputs:
                owner = output.get_owner()
                if owner != target_owner:
                    continue
                if logger:
                    logger.info(
                        f'Found output for owner {output.to_json()}')
                if transaction_id in transaction_sources:
                    if logger:
                        logger.warning(
                            f'In transaction_sources {transaction.to_json()} output {output.to_json()} try to add the same transaction - transaction id should be unique')
                    continue
                if logger:
                    logger.info(
                        f'CryptoInputs::get_inputs output: {output.to_json()} transaction_id: {transaction_id}')
                new_input = Input.output_to_input(
                    output, transaction_id, logger=logger)
                transaction_sources[transaction_id] = new_input

        if logger:
            logger.info(f'After mined_blocks: {mined_blocks}')
        inputs = list(transaction_sources.values())
        for _ in range(mined_blocks):
            new_input = Input(transaction_id=BLOCK_PRICE_ID,
                              owner=target_owner, amount=BLOCK_PRICE_AMOUNT)
            inputs.append(new_input)
        return inputs

    def is_valid_transaction_candidate(self, transaction: Transaction, logger: Logger | None = None) -> tuple[str, bool]:
        '''
        Checks if inputs are still available.
        '''
        message, is_consistent = transaction.is_consistent()
        if not is_consistent:
            if logger:
                logger.info(f'{message}')
            return message, False
    
        sender = transaction.get_sender()
        # Get available inputs
        inputs = self.get_inputs(sender, logger)
        # build str of json input to compare it later
        inputs_json_str_list = [str(input.to_json()) for input in inputs]
        
        for transaction_input in transaction.get_inputs():
            transaction_input_json_str = str(transaction_input.to_json())
            if transaction_input_json_str not in inputs_json_str_list:
                msg = f'{inputs_json_str_list} not in {inputs_json_str_list}'
                if logger:
                    logger.info(msg)
                return msg, False
        return 'Ok', True
            
        
