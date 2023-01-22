from CryptoBlock import Block
from CryptoBlockchain import BlockChain
import threading
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoKeyManager import KeyManager
from CryptoBlockchainPool import BlockchainPool
from CryptoBlockchain import BLOCK_PRICE_AMOUNT
from CryptoInput import BLOCK_PRICE_ID
import time
from logging import Logger
from datetime import datetime
from CryptoInput import Input

max_nonce = 2 ** 32     # 4 billion

class Digger():
    __is_waiting: bool = None
    __is_terminated: bool = None
    __blockchain_pool: BlockchainPool = None
    __worker = None
    __transaction_pool: TransactionPool = None
    __key_manager: KeyManager = None
    __logger: Logger = None

    __spread_candidate_block_function = None

    # double spending stuff
    __double_spending_pairs = [
        # {
        #     'transaction1': 'transaction_1_id',
        #     'transaction2': 'transaction_2_id',
        #     'previous_block_hash': 'hash'
        # }
    ]

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

    def add_double_spending_transactions(self, transactions: list[Transaction]) -> None:
        self.__double_spending_pairs.append(
            {
                'transaction_ids': [transaction.get_transaction_id() for transaction in transactions],
                'previous_block_hash': None
            }
        )

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
            lost_transactions = self.__blockchain_pool.get_blockchain_tree().get_lost_transactions_ready_to_apply()
            aplied_transaction_ids = [transaction.get_transaction_id() for transaction in self.__blockchain_pool.get_blockchain().get_transactions()]
            transaction_data_obj = self.__transaction_pool.get_next_transaction(lost_transactions, aplied_transaction_ids)
            block_data = {
                'transactions': transaction_data_obj if transaction_data_obj is None else [transaction_data_obj.to_json()]
            }

            begin = datetime.now()

            # calculate previous block hash
            previous_block_hash = self.__blockchain_pool.get_blockchain().get_blocks()[-1].get_block_hash()
            double_spending_record_idx = -1
            current_transaction_id = None
            if transaction_data_obj is not None:
                current_transaction_id = transaction_data_obj.get_transaction_id()
                self.__logger.info(f"Previous block hash: {previous_block_hash}")
                for i in range(len(self.__double_spending_pairs)):
                    if current_transaction_id in self.__double_spending_pairs[i]['transaction_ids']:
                        if self.__double_spending_pairs[i]['previous_block_hash'] is None:
                            self.__double_spending_pairs[i]['previous_block_hash'] = previous_block_hash
                            self.__logger.info(f"Assigning previous block hash as {previous_block_hash}")
                        else:
                            self.__logger.info(f"Using existing previous block hash - {previous_block_hash}")
                            previous_block_hash = self.__double_spending_pairs[i]['previous_block_hash']
                        double_spending_record_idx = i
                        break

            candidate_block = Block(previous_block_hash,
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
                if double_spending_record_idx == -1:
                    continue

            self.__propagate_candidate_block(candidate_block)
            if transaction_data_obj is not None:
                self.__logger.info(f'Pop transaction: {str(transaction_data_obj.to_json())}')
                self.__transaction_pool.pop_next_transaction()
                self.__logger.info(f"Transaction pool status after popping: {self.__transaction_pool.count()}")

                # remove redundancy for currently processed transaction
                if double_spending_record_idx != -1:
                    self.__logger.info(f"Double spending transaction ids list length before redundancy: {len(self.__double_spending_pairs[double_spending_record_idx]['transaction_ids'])}")
                    self.__double_spending_pairs[double_spending_record_idx]['transaction_ids'].remove(current_transaction_id)
                    self.__logger.info(f"Double spending transaction ids list length after redundancy: {len(self.__double_spending_pairs[double_spending_record_idx]['transaction_ids'])}")
                    if len(self.__double_spending_pairs[double_spending_record_idx]['transaction_ids']) == 0:
                        self.__logger.info(f"Number of double spending records before redundancy- {len(self.__double_spending_pairs)}")
                        self.__double_spending_pairs.remove(self.__double_spending_pairs[double_spending_record_idx])
                        self.__logger.info(f"Number of double spending records after redundancy- {len(self.__double_spending_pairs)}")

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
        self.__logger.info(f"Transaction pool status after transaction adding: {str(self.__transaction_pool.count())}")

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
                if len(self.__double_spending_pairs) == 0:
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
        return self.__blockchain_pool.get_blockchain().get_inputs(target_owner, self.__logger)
    
    def add_block(self, block: Block) -> tuple[str, bool]:
        self.__blockchain_pool.add_block(block=block)
        return 'Ok', True

    @staticmethod
    def get_block_price_id():
        return BLOCK_PRICE_ID

    @staticmethod
    def get_block_price_amount():
        return BLOCK_PRICE_AMOUNT
