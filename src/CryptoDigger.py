from CryptoBlock import Block
from CryptoBlockchain import BlockChain
import threading
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoKeyManager import KeyManager
from CryptoBlockchainPool import BlockchainPool
import time
from logging import Logger
from datetime import datetime
from CryptoInput import Input
from CryptoMessageUtils import MessageUtils

max_nonce = 2 ** 32     # 4 billion

BLOCK_PRICE_ID = 'block_mining_price'
BLOCK_PRICE_AMOUNT = 5


class Digger():
    __is_waiting: bool = None
    __is_terminated: bool = None
    __blockchain_pool: BlockchainPool = None
    __worker = None
    __transaction_pool: TransactionPool = None
    __key_manager: KeyManager = None
    __logger: Logger = None

    __spread_candidate_block_function = None

    def __init__(self, blocks: list[Block], key_manager: KeyManager, logger: Logger, spread_block_function):
        self.__is_waiting = False
        self.__is_terminated = False
        self.__transaction_pool = TransactionPool()
        self.__key_manager = key_manager
        self.__logger = logger
        self.__spread_candidate_block_function = spread_block_function
        self.__blockchain_pool = BlockchainPool.create_blockchain_pool(blocks=blocks, logger=self.__logger)

    def start_mining(self) -> None:
        self.__is_waiting = False
        self.__worker = threading.Thread(target=self.__w_start, args=())
        self.__worker.start()

    def __w_start(self) -> None:
        if len(self.__blockchain_pool.get_all_blocks()) == 0:
            initial_prev_hash_hex = None  # uuid.uuid4().hex
            body = {'message': 'Initial block'}
            genesis_block = Block(initial_prev_hash_hex,
                                  body, self.__key_manager.public_key)

            (nonce, is_successfull) = self.__proof_of_work(genesis_block)
            genesis_block.set_nonce(nonce)
            # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
            genesis_block.set_prev_hash_nonce(genesis_block.calculate_hash_prev_block_nonce())
            self.__blockchain_pool.add_block(genesis_block)
            self.__logger.info('Created blockchain_Tree')

        while not self.__is_terminated:
            transaction_data = self.__transaction_pool.get_next_transaction_json()
            block_data = {
                'transactions': transaction_data if transaction_data is None else [transaction_data]
            }

            begin = datetime.now()

            candidate_block = Block(self.__blockchain_pool.get_blockchain().get_blocks()[-1].get_block_hash(),
                                    block_data,
                                    self.__key_manager.public_key)

            (nonce, is_successfull) = self.__proof_of_work(candidate_block)

            end = datetime.now()
            diff = end - begin
            self.__logger.info(f'Mining duration: {diff.total_seconds()} sec.')

            if not is_successfull:
                self.__logger.warning('Proof of work unsuccessfull')
                continue

            candidate_block.set_nonce(nonce)
            # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
            candidate_block.set_prev_hash_nonce(candidate_block.calculate_hash_prev_block_nonce())

            counter = 0
            while self.__is_waiting and not self.__is_terminated:
                time.sleep(0.001)
                if counter % 1000 == 0:
                    self.__logger.info(
                        "Waiting another second for processing candidate block")
                counter += 1

            if self.__is_terminated:
                self.__logger.warning('Is terminated')
                continue

            if candidate_block.get_prev_hash() != self.__blockchain_pool.get_blockchain().get_blocks()[-1].get_block_hash():
                self.__logger.warning('Not actual last block')
                continue

            propagated_successfully = self.__propagate_candidate_block(candidate_block)
            if propagated_successfully and transaction_data is not None:
                if transaction_data is not None and 'message' in transaction_data and 'Some transaction' in transaction_data['message']:
                    self.__logger.info(
                        f'Pop transaction {transaction_data["message"]}')
                self.__transaction_pool.pop_next_transaction()
        self.__logger.info("Mining terminated...")

    def pause_mining(self) -> None:
        self.__is_waiting = True

    def resume_mining(self) -> None:
        self.__is_waiting = False

    def terminate_mining(self) -> None:
        self.__is_terminated = True

    def __propagate_candidate_block(self, candidate_block: Block) -> bool:
        if self.__spread_candidate_block_function is not None:
            is_spread_successful = self.__spread_candidate_block_function(
                candidate_block)
            return is_spread_successful
        else:
            return False

    def add_transaction(self, transaction: Transaction) -> None:
        self.__transaction_pool.add_transaction(transaction)

    def __proof_of_work(self, block: Block) -> tuple[int, bool]:
        '''
        Runs proof of work.

        :returns: Tuple of valid nonce (if found, otherwise, max possible nonce value - 1) and bool (if nonce is valid).
        '''
        # calculate the difficulty target
        for nonce in range(max_nonce):  # check all possible nonce values
            # there was added new block to blockchain during mining
            blockchain = self.__blockchain_pool.get_blockchain()
            if blockchain is not None and len(blockchain.get_blocks()) > 0:
                if block.get_prev_hash() != blockchain.get_blocks()[-1].get_block_hash():
                    return (nonce, False)

            if block.verify_nonce(nonce):  # verify specific nonce value
                print(f"Success with nonce {nonce}")
                return (nonce, True)
        nonce = max_nonce - 1
        # no nonce value was valid - could not find solution for proof of work problem
        print(f'Failed after {nonce} tries')
        return (nonce, False)

    def get_all_blocks(self):
        return self.__blockchain_pool.get_all_blocks()
    
    def get_blockchain_tree(self):
        return self.__blockchain_pool.get_blockchain_tree()

    def get_inputs(self, target_owner: str) -> list[Input]:
        self.__logger.info(f'get_inputs for owner: "{target_owner}"')
        all_transactions = self.__blockchain_pool.get_blockchain().get_transactions()
        mined_blocks = len(self.__blockchain_pool.get_blockchain().get_mined_blocks(target_owner))
        self.__logger.info(
            f'mined_blocks: found {mined_blocks} mined_blocks')
        self.__logger.info(f'Found all_transactions: {len(all_transactions)}')
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
                        self.__logger(
                            f'Input {input.to_json()} in transaction {transaction.to_json()} get block mining price which does not have')
                    continue
                elif source_transaction_id not in transaction_sources:
                    self.__logger.warning(
                        f'In transaction_sources {transaction.to_json()} input {input.to_json()} has no valid previous source')
                    continue
                transaction_sources.pop(source_transaction_id)
            # add to sources outputs from block
            transaction_id = transaction.get_transaction_id()
            for output in outputs:
                owner = output.get_owner()
                if owner != target_owner:
                    continue
                self.__logger.info(
                    f'Found output for owner {output.to_json()}')
                if transaction_id in transaction_sources:
                    self.__logger.warning(
                        f'In transaction_sources {transaction.to_json()} output {output.to_json()} try to add the same transaction - transaction id should be unique')
                    continue
                self.__logger.info(
                    f'CryptoInputs::get_inputs output: {output.to_json()} transaction_id: {transaction_id}')
                new_input = Input.output_to_input(
                    output, transaction_id, logger=self.__logger)
                transaction_sources[transaction_id] = new_input

        self.__logger.info(f'After mined_blocks: {mined_blocks}')
        inputs = list(transaction_sources.values())
        for _ in range(mined_blocks):
            new_input = Input(transaction_id=BLOCK_PRICE_ID,
                              owner=target_owner, amount=BLOCK_PRICE_AMOUNT)
            inputs.append(new_input)
        return inputs
    
    def add_block(self, block: Block) -> tuple[str, bool]:
        self.__blockchain_pool.add_block(block=block)
        return 'Ok', True

    def verify_candidate_block(self, candidate_block: Block):
        is_valid = self.__blockchain.validate_candidate_block(candidate_block)
        if not is_valid:
            return False
        
        candidate_block_transactions = candidate_block.get_transactions()

        # verify transactions in candidate block
        for transaction in candidate_block_transactions:
            transaction_inputs = transaction.get_inputs()
            transaction_input_targets = []

            for transaction_input in transaction_inputs:
                if transaction_input.get_owner() not in transaction_input_targets:
                    transaction_input_targets.append(transaction_input.get_owner())
            
            if len(transaction_input_targets) != 1:
                return False
            
            # there is only one transaction owner
            sender = transaction_input_targets[0]
            target_valid_inputs = self.get_inputs(sender)

            # verify non-mining-price blocks
            for transaction_input in transaction_inputs:
                if transaction_input.get_transaction_id() == BLOCK_PRICE_ID:
                    continue
                transaction_found_counter = 0
                # previous id consistent and not doubled
                for valid_input in target_valid_inputs:
                    if valid_input.get_transaction_id() == transaction_input.get_transaction_id() and valid_input.get_amount() == transaction_input.get_amount():
                        transaction_found_counter += 1
                if transaction_found_counter != 1:
                    return False
            
            # checking mining prices sums
            transaction_input_total_amount = 0
            for transaction_input in transaction_inputs:
                if transaction_input.get_transaction_id() == BLOCK_PRICE_ID:
                    transaction_input_total_amount += transaction_input.get_amount()

            target_valid_input_total_amount = 0
            for target_valid_input in target_valid_inputs:
                if target_valid_input.get_transaction_id() == BLOCK_PRICE_ID:
                    target_valid_input_total_amount += target_valid_input.get_amount()
            
            # check if sum of transaction inputs is greater than total valid inputs amount sum (price for mining)
            if transaction_input_total_amount > target_valid_input_total_amount:
                return False

            transaction_outputs = transaction.get_outputs()
            outputs_sum = 0
            for transaction_output in transaction_outputs:
                outputs_sum += transaction_output.get_amount()

            # check if sum of inputs = sum of outputs + transaction fee
            if outputs_sum + transaction.get_transaction_fee() != transaction_input_total_amount:
                return False

            # verify transaction signature
            try:
                MessageUtils.verifyTransactionSignature(transaction, sender)
            except Exception as err:
                self.__logger.info(str(err))
                return False

        return True

    @staticmethod
    def get_block_price_id():
        return BLOCK_PRICE_ID

    @staticmethod
    def get_block_price_amount():
        return BLOCK_PRICE_AMOUNT
