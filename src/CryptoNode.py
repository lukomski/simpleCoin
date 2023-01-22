import socket
import requests

from CryptoNodeInfo import NodeInfo
from CryptoMessageUtils import MessageUtils
from CryptoBlock import Block
from CryptoKeyManager import KeyManager
from CryptoTransaction import Transaction
from threading import Thread
from CryptoInput import Input
import os
from CryptoUtils import (
    is_double_spending_transaction_request_valid
)

import uuid
import time
from CryptoDigger import Digger
from CryptoOutput import Output
import os
import random

BLOCKCHAIN_FILE_PATH = "blockchain.json"
OK = 200
BAD_REQUEST = 400


class Node():
    __message_utils = None
    __ignore_address: str = None

    pub_list = list[NodeInfo]
    ip = None
    port = None
    app = None
    __digger: Digger = None

    __block_accept_probability: float = None
    __transaction_process_chance: float = None

    def __setup(self, network_node_address):
        self.__logger.error('Node::__setup')
        blocks = []

        if network_node_address is not None:
            self.pub_list = []

            self.__logger.info("Sending request to connect new node")
            # connect to parent
            while True:
                try:
                    response = requests.post(
                        url=f'http://{network_node_address}/connect-node', json={}, timeout=3)
                    self.__logger.info(f"Get response: {response.text}")
                    break
                except:
                    self.__logger.warning(
                        f'Unable to connect to parent address {network_node_address} - try in a few seconds')
                    time.sleep(1)

            self.__logger.info("Success connection with parent")
            # fetch blocks from parent
            block_list = []
            while len(block_list) == 0:
                try:
                    block_list = requests.get(
                        url=f'http://{network_node_address}/blocks').json()
                except:
                    self.__logger.warning(
                        f'Parent block list is empty - try again to get block list')
            self.__logger.info(
                f'Get block list: {block_list}')
            blocks = Block.load_list(block_list)
        else:
            self.pub_list = [
                NodeInfo(f"{socket.gethostbyname(socket.gethostname())}:5000",
                         self.__key_manager.public_key)
            ]
            if os.path.exists(BLOCKCHAIN_FILE_PATH):
                blocks = Block.load_blocks(BLOCKCHAIN_FILE_PATH)
                if blocks is None:
                    raise ValueError(
                        "Could not load/parse existing blocks - remove file or correct it to start node.")

        self.__digger = Digger(blocks, self.__key_manager, self.__logger, self.spread_candidate_block)
        self.__logger.info('Setup done')
        self.__digger.start_mining()

    def __init__(self, network_node_address, secret_key, app, ignore_address: str = None, block_accept_probability: float = 1.0, transaction_process_chance: float = 1.0):
        self.__key_manager = KeyManager(app.logger, secret_key)
        self.__ignore_address = ignore_address
        self.app = app
        self.__logger = app.logger
        self.__message_utils = MessageUtils(self.__key_manager)
        self.__block_accept_probability = block_accept_probability
        self.__transaction_process_chance = transaction_process_chance

        setup_thread = Thread(target=self.__setup,
                              args=(network_node_address,))
        setup_thread.start()

    def get_public_key(self):
        return self.__key_manager.public_key

    def update_pub_list(self, new_pub_list):
        self.pub_list = new_pub_list

    def get_address_by_public_key(self, public_key):
        for nodeInfo in self.pub_list:
            if (nodeInfo.public_key == public_key):
                return nodeInfo.address
        return None

    def get_public_key_by_address(self, address: str):
        for nodeInfo in self.pub_list:
            if (nodeInfo.address == address):
                return nodeInfo.public_key
        return None

    def send_message(self, message: str, receiver_public_key: str):
        payload = {
            'type': 'message',
            'message': message
        }
        frame = self.__message_utils.wrap_message(payload)
        address = self.get_address_by_public_key(receiver_public_key)
        requests.post(
            url=f"http://{address}/message", json=frame)

    def read_message(self, frame: dict, sender_pk_hex: str):
        if sender_pk_hex is None:
            self.__logger.warning(f'Sender should be str not None {str(frame)}')
        self.__message_utils.verify_message(
            frame, bytes.fromhex(sender_pk_hex))

        payload = self.__message_utils.getPayload(frame)
        if (payload['type'] == 'message'):
            message = payload['message']
            self.app.logger.error(f'READ message: {message}')
            return {
                "verified": 'correctly',
                "message": message
            }
        elif payload['type'] == 'new_block':
            # decide whether candidate block should be processed or not
            block_rng = random.random()
            # candidate block can be processed
            if block_rng < self.__block_accept_probability:
                block = Block.load(payload['block'])
                if self.__digger == None:
                    self.__logger.warning('Not ready to get block')
                    return 'Not ready to get block', OK
                if not block.verify_block():
                    self.__logger.warning('Block nounce or hash_prev_nonce is wrong')
                    return 'Block nounce or hash_prev_nonce is wrong', BAD_REQUEST
                message, is_valid_block = self.__digger.add_block(block=block)

                status = OK if is_valid_block else BAD_REQUEST
                return message, status
            # candidate block will be ignored
            else:
                self.__logger.info("Received candidate block will be ignored")
                return "Candidate block ignored", BAD_REQUEST
        elif payload['type'] == 'new_transaction':
            transaction_rng = random.random()
            if transaction_rng < self.__transaction_process_chance:
                transaction_data = payload['transaction']

                self.__logger.info(f"Received transaction candidate: {str(transaction_data)}")

                message, is_valid = Transaction.is_valid(transaction_data, logger=self.__logger)

                if not is_valid:
                    self.__logger.info(f"Transaction validated... {message}")
                    return message, BAD_REQUEST

                # add restored transaction
                restored_transaction = Transaction.create_from_json(transaction_data)
                message, is_valid = Transaction.is_consistent(restored_transaction)
                if not is_valid:
                    self.__logger.info(f"Transaction validated... {message}")
                    return message, BAD_REQUEST
                
                # check if is valid for main blockchain
                message, is_valid = self.__digger.get_blockchain_tree().get_blockchain().is_valid_transaction_candidate(restored_transaction)
                if not is_valid:
                    return f'Not valid for main blockchain: {message} - transaction: {restored_transaction.to_json()}', BAD_REQUEST

                self.__digger.add_transaction(restored_transaction)

                self.__logger.info(f"Transaction added to transaction pool... {message}")
                return message, OK
            else:
                self.__logger.info("Transaction ignored")
                return "Transaction ignored", BAD_REQUEST
        else:
            self.__logger.warning('Unhandled message type')
            return 'Unhandled message type', BAD_REQUEST

    def save_blockchain(self):
        self.__digger.__blockchain.save(BLOCKCHAIN_FILE_PATH)

    def spread_candidate_block(self, candidate_block: Block) -> None:
        '''
        Spread candidate block to all nodes with new transaction.
        '''
        self.spread_message({
            'type': 'new_block',
            'block': candidate_block.to_json()
        })
    
    def spread_candidate_transaction(self, transaction: Transaction) -> None:
        '''
        Spread message to all nodes with new transaction.
        '''
        self.spread_message({
            'type': 'new_transaction',
            'transaction': transaction.to_json()
        })
    
    def spread_message(self, payload: dict) -> None:
        '''
        Spread message to all known nodes.
        Ignore 'Ignore address' if set.
        '''
        if (payload['type'] == 'new_transaction'):
            self.__logger.info(f"Spreading transaction candidate... {payload}")
        frame = self.__message_utils.wrap_message(payload)

        nodes_that_reject = []
        for node in self.pub_list:

            # we can be mean for some digger :)
            # We are sending new block to everone except him.
            if node.address == self.__ignore_address:
                continue

            response = requests.post(
                url=f'http://{node.address}/message', json=frame)

            if not response.ok:
                nodes_that_reject.append(node)

    def get_digger(self):
        return self.__digger

    def get_wallet_balance(self):
        owner = self.__key_manager.public_key
        valid_inputs = self.__digger.get_inputs(owner)

        available_balance = 0
        for input in valid_inputs:
            available_balance += input.get_amount()

        mining_inputs = 0
        for valid_input in valid_inputs:
            if valid_input.get_transaction_id() == Digger.get_block_price_id():
                mining_inputs += 1

        return {
            'available_balance': available_balance,
            'valid_inputs': [valid_input.to_json() for valid_input in valid_inputs if valid_input.get_transaction_id() != Digger.get_block_price_id()],
            'additional_mining_inputs': {
                'amount_blocks': mining_inputs,
                'summary_balance': mining_inputs * Digger.get_block_price_amount()
            }
        }

    def get_blockchain_tree_struct(self):
        blockchain_tree = self.__digger.get_blockchain_tree()
        tree_structure = blockchain_tree.to_tree_structure()
        tree_structure = [  {**element,
                            'miner_name': f'Node {int(str(self.get_address_by_public_key(element["miner_pub_key"]))[-6])-2}'
                            } for element in tree_structure
                         ]
        return tree_structure

    def propagate_transaction(self, transaction_data: dict):
        '''
        Prepare transaction ready to add to blockchain and spread to all nodes.
        '''
        self.__logger.info("Propagating transaction to all nodes")
        # check if structure of transaction request is valid
        message, is_valid = Transaction.is_transaction_request_valid(transaction_data, self.__logger)
        if not is_valid:
            self.__logger.info(message)
            return message, BAD_REQUEST
         
            
        transaction_id = str(uuid.uuid4())
        transaction_fee = Transaction.calculate_transaction_fee(transaction_data['amount'])
        
        # set inputs
        inputs = None
        if 'inputs' in transaction_data:
            # convert inputs to object class
            msg, is_valid = Input.is_list_valid(transaction_data['inputs'])
            if not is_valid:
                return msg, BAD_REQUEST
            inputs = Input.from_list_json(transaction_data['inputs'])
        else:
            inputs = self.__digger.get_inputs(transaction_data['sender'])
           
        self.__logger.info(f'inputs: {len(inputs)}')
                            
        available_balance = sum([input.get_amount() for input in inputs])

        spend_amount = transaction_fee + transaction_data['amount']
        if available_balance <= spend_amount:
            return f'Not enough account balance need {spend_amount} but has {available_balance}', BAD_REQUEST
        
        
        # set outputs
        outputs = [
            Output(owner=transaction_data['receiver'], amount=transaction_data['amount']),
        ]
        change_amount = available_balance - spend_amount
        if change_amount > 0:
            outputs.append(Output(owner=transaction_data['sender'], amount=change_amount))
            
        # Create transaction object
        transaction, msg, is_valid = Transaction.create_transaction(
            key_manager = self.__key_manager,
            logger = self.__logger,
            transaction_id = transaction_id,
            transaction_fee = transaction_fee,
            inputs = inputs,
            outputs = outputs,
            message = transaction_data['message']
        )
        if not is_valid:
            self.__logger.info(msg)
            return f'Unable to create transaction: {msg}', BAD_REQUEST
        
        msg, is_valid = Transaction.is_consistent(transaction)
        if not is_valid:
            return f'Created transaction is inconsistent: {msg}', BAD_REQUEST
        
        # check if is valid for main blockchain
        msg, is_valid = self.__digger.get_blockchain_tree().get_blockchain().is_valid_transaction_candidate(transaction)
        if not is_valid:
            return f'Not valid for main blockchain: {msg} - transaction: {transaction.to_json()}', BAD_REQUEST

        self.__logger.info("Attempting to broadcast transaction...")

        self.spread_candidate_transaction(transaction)
        return "ok", OK

    def make_double_spending(self, transaction_data: dict):
        # check if structure of transaction request is valid
        message, is_valid = is_double_spending_transaction_request_valid(transaction_data)
        if not is_valid:
            self.__logger.info(message)
            return message, BAD_REQUEST

        # create transactions from received data
        transaction_fee = Transaction.calculate_transaction_fee(transaction_data['amount'])

        # set inputs
        inputs = None
        if 'inputs' in transaction_data:
            # convert inputs to object class
            msg, is_valid = Input.is_list_valid(transaction_data['inputs'])
            if not is_valid:
                return msg, BAD_REQUEST
            inputs = Input.from_list_json(transaction_data['inputs'])
        else:
            inputs = self.__digger.get_inputs(transaction_data['sender'])

        self.__logger.info(f'inputs: {len(inputs)}')

        available_balance = sum([input.get_amount() for input in inputs])

        spend_amount = transaction_fee + transaction_data['amount']
        if available_balance <= spend_amount:
            return f'Not enough account balance need {spend_amount} but has {available_balance}', BAD_REQUEST

        transactions_to_spread = []
        amount = transaction_data['amount']
        for i in range(1, 3):
            transaction_id = str(uuid.uuid4())
            receiver = transaction_data['receiver' + str(i)]

            # set outputs
            outputs = [
                Output(owner=receiver, amount=amount),
            ]
            change_amount = available_balance - spend_amount
            if change_amount > 0:
                outputs.append(Output(owner=transaction_data['sender'], amount=change_amount))

            # Create transaction object
            transaction, msg, is_valid = Transaction.create_transaction(
                key_manager = self.__key_manager,
                logger = self.__logger,
                transaction_id = transaction_id,
                transaction_fee = transaction_fee,
                inputs = inputs,
                outputs = outputs,
                message = transaction_data['message']
            )
            if not is_valid:
                self.__logger.info(msg)
                return f'Unable to create transaction: {msg}', BAD_REQUEST

            msg, is_valid = Transaction.is_consistent(transaction)
            if not is_valid:
                return f'Created transaction is inconsistent: {msg}', BAD_REQUEST

            # check if is valid for main blockchain
            msg, is_valid = self.__digger.get_blockchain_tree().get_blockchain().is_valid_transaction_candidate(transaction)
            if not is_valid:
                return f'Not valid for main blockchain: {msg} - transaction: {transaction.to_json()}', BAD_REQUEST

            transactions_to_spread.append(transaction)

        self.__digger.add_double_spending_transactions(transactions_to_spread)

        for transaction in transactions_to_spread:
            self.__digger.add_transaction(transaction)
        # # send double spending transactions info only to myself
        # own_address = self.get_address_by_public_key(self.get_public_key())
        # for transaction in transactions_to_spread:
        #     unwrapped_message = {
        #         'type': 'new_transaction',
        #         'transaction': transaction.to_json()
        #     }
        #     frame = self.__message_utils.wrap_message(unwrapped_message)
        #     requests.post(url=f'http://{own_address}/message', json=frame)

        return "ok", OK
