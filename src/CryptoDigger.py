import hashlib
from CryptoBlock import Block
from CryptoBlockchain import BlockChain
import threading
import os
from CryptoTransactionPool import TransactionPool, Transaction
from CryptoKeyManager import KeyManager
import time
from logging import Logger
import requests
from datetime import datetime

max_nonce = 2 ** 32     # 4 billion

class Digger():
    __is_waiting: bool = None
    __is_terminated: bool = None
    __blockchain: BlockChain = None
    __worker = None
    __transaction_pool: TransactionPool = None
    __key_manager: KeyManager = None
    __logger: Logger = None

    __spread_candidate_block_function = None

    def __init__(self, blockchain: BlockChain, key_manager: KeyManager, logger: Logger, spread_block_function):
        self.__is_waiting = False
        self.__is_terminated = False
        self.__blockchain = blockchain
        self.__transaction_pool = TransactionPool()
        self.__key_manager = key_manager
        self.__logger = logger
        self.__spread_candidate_block_function = spread_block_function

    def start_mining(self) -> None:
        self.__is_waiting = False
        self.__worker = threading.Thread(target=self.__w_start, args=())
        self.__worker.start()

    def __w_start(self) -> None:
        if len(self.__blockchain._blocks) == 0:
            initial_prev_hash_hex = None  # uuid.uuid4().hex
            body = { 'message': 'Initial block' }
            generic_block = Block(initial_prev_hash_hex, body, self.__key_manager.public_key)

            (nonce, is_successfull) = self.__proof_of_work(generic_block)
            generic_block._header['nonce'] = nonce
            # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
            generic_block._header['hash_prev_nonce'] = generic_block.calculate_hash_prev_block_nonce()
            self.__blockchain.add_block(generic_block)

        while not self.__is_terminated:
            block_data = self.__transaction_pool.get_next_transaction_json()

            begin = datetime.now()

            candidate_block = Block(self.__blockchain._blocks[-1].get_block_hash(),
                                    block_data,
                                    self.__key_manager.public_key)
            
            (nonce, is_successfull) = self.__proof_of_work(candidate_block)

            end = datetime.now()
            diff = end - begin
            self.__logger.info(f'Mining duration: {diff.total_seconds()} sec.')

            if not is_successfull:
                continue
        
            candidate_block._header['nonce'] = nonce
            # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
            candidate_block._header['hash_prev_nonce'] = candidate_block.calculate_hash_prev_block_nonce()

            counter = 0
            while self.__is_waiting:
                time.sleep(0.001)
                if counter % 1000 == 0:
                    self.__logger.info("Waiting another second for processing candidate block")
                counter += 1
            
            if candidate_block.get_prev_hash() != self.__blockchain._blocks[-1].get_block_hash():
                continue

            propagated_successfully = self.__propagate_candidate_block(candidate_block)
            if propagated_successfully:
                self.__transaction_pool.pop_next_transaction()

    def pause_mining(self) -> None:
        self.__is_waiting = True

    def resume_mining(self) -> None:
        self.__is_waiting = False

    def terminate_mining(self) -> None:
        self.__is_terminated = True

    def __propagate_candidate_block(self, candidate_block: Block) -> bool:
        if self.__spread_candidate_block_function is not None:
            is_spread_successful = self.__spread_candidate_block_function(candidate_block)
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
            if len(self.__blockchain._blocks) > 0:
                if block.get_prev_hash() != self.__blockchain._blocks[-1].get_block_hash():
                    return (nonce, False)

            if block.verify_nonce(nonce):  # verify specific nonce value
                print(f"Success with nonce {nonce}")
                return (nonce, True)
        nonce = max_nonce - 1
        # no nonce value was valid - could not find solution for proof of work problem
        print(f'Failed after {nonce} tries')
        return (nonce, False)

    def get_blockchain(self):
        return self.__blockchain
