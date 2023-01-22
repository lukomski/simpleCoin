
from CryptoUtils import get_order_directory_recursively, is_valid
from CryptoInput import Input
from CryptoOutput import Output
from logging import Logger
from CryptoKeyManager import KeyManager
from nacl.signing import VerifyKey
from logging import Logger
import json
import math

TRANSACTION_FEE_SHARE = 0.01

class Transaction:
    __data: dict = None

    def __init__(self, transaction_id: str, transaction_fee: int, signature: str, inputs: list[Input], outputs: list[Output], message: str):
        self.__data = {
            'transaction_id': transaction_id,
            'transaction_fee': transaction_fee,
            'signature': signature,
            'inputs': inputs,
            'outputs': outputs,
            'message': message
        }

    def get_data_without_signature(self):
        data = {
            'transaction_id': self.__data['transaction_id'],
            'transaction_fee': self.__data['transaction_fee'],
            'inputs': [input.to_json() for input in self.__data['inputs']],
            'outputs': [output.to_json() for output in self.__data['outputs']],
            'message': self.__data['message']
        }
        data = get_order_directory_recursively(data)
        return data

    def get_transaction_fee(self):
        return int(self.__data['transaction_fee'])

    def get_signature(self):
        return self.__data['signature']

    def set_signature(self, signature):
        self.__data['signature'] = signature
        
    def is_consistent(self) -> tuple[str, bool]:
        '''
        * Has one sender
        * Has one receiver
        * Check if inputs are only once on list
        * Check if sum of inputs equals sum of outputs
        * Check if transaction fee is calculated properly
        * Chekc signature
        '''
        
        try:
            self.verifyTransactionSignature()
        except Exception as err:
            return 'Signature does not match the transaction', False
    
        
        inputs = self.get_inputs()
        outputs = self.get_outputs()
        
        input_owners = [input.get_owner() for input in inputs]
        output_owners = [output.get_owner() for output in outputs]
             
        if len(inputs) == 0:
            return 'Should have at least one input', False
        
        if len(outputs) == 0:
            return 'Should have at least one output', False
        
        
        # One sender
        if not input_owners.count(input_owners[0]) == len(input_owners):
            return 'Should have only one sender', False
        
        # No more then two receiver in outputs
        # 1. sender return
        # 2. receiver
        receivers = []
        for output in outputs:
            receiver = output.get_owner()
            if receiver not in receivers:
                receivers.append(receiver)
        if len(receivers) > 2:
             return 'Too many receivers in output', False
        if len(receivers) == 2 and input_owners[0] not in receivers:
            return 'Can not have two receivers except sender', False
        
        
        sum_of_inputs = 0
        for input in inputs:
            sum_of_inputs += input.get_amount()
            
        sum_of_outputs = 0
        for output in outputs:
            sum_of_outputs += output.get_amount()
            
        # check if transaction fee is calculated properly
        amount = sum_of_inputs - self.get_transaction_fee()
        if Transaction.calculate_transaction_fee(amount) != self.get_transaction_fee():
            return 'Wrong transaction fee', False
        
        # Sum of inputs shoule be equal to sum of outputs + transaction fee
        if sum_of_inputs != sum_of_outputs + self.get_transaction_fee():
            return 'Sum of inputs should be equal to sum of outputs + transaction fee', False
        
        # Check if inputs are only once on list
        used_inputs_json_str_list = []
        for input in inputs:
            # Only block price blocks can be the same.
            if input.is_block_price():
                continue
            input_json_str = str(input.to_json())
            if input_json_str in used_inputs_json_str_list:
                return "Inputs are multiple times in input list", False
            used_inputs_json_str_list.append(input_json_str)
  
        return "Ok", True
        
    @staticmethod
    def calculate_transaction_fee(amount: int):
        return math.ceil(amount * TRANSACTION_FEE_SHARE)

    @staticmethod
    def is_transaction_request_valid(data: dict, logger: Logger = None) -> tuple[str, bool]:
        config = {
            'amount': {
                'type': int,
            },
            'message': {
                'type': str,
                'optional': True
            },
            'sender': {
                'type': str
            },
            'receiver': {
                'type': str
            },
            'inputs': {
                'type': Input,
                'list': True,
                'optional': True,
            },
        }
        return is_valid(config, data)

    @staticmethod
    def is_valid(data: dict, logger: Logger = None) -> tuple[str, bool]:
        config = {
            'transaction_id': {
                'type': str,
            },
            'transaction_fee': {
                'type': int,
            },
            'signature': {
                'type': str,
            },
            'inputs': {
                'type': Input,
                'list': True
            },
            'outputs': {
                'type': Output,
                'list': True
            },
            'message': {
                'type': str,
                'optional': True
            }
        }
        return is_valid(config, data)

    def to_json(self):
        return get_order_directory_recursively({
            **self.__data,
            'inputs': [input.to_json() for input in self.__data['inputs']],
            'outputs': [output.to_json() for output in self.__data['outputs']]
        })

    def get_inputs(self) -> list[Input]:
        return self.__data['inputs']

    def get_outputs(self) -> list[Output]:
        return self.__data['outputs']

    def get_transaction_id(self) -> str:
        return self.__data['transaction_id']
    
    def get_sender(self) -> str | None:
        input_owners = [input.get_owner() for input in self.get_inputs()]
        if len(input_owners) == 0:
            return None
        return input_owners[0]
    
    def get_receiver(self) -> str | None:
        '''
        Return receiver for the transaction.
        If transaction is broken - returns None.
        '''
        input_owners = [input.get_owner() for input in self.get_inputs()]
        output_owners = [output.get_owner() for output in self.get_outputs()]
        
        only_in_output_owners = [owner for owner in output_owners if owner not in input_owners]
        
        if len(only_in_output_owners) == 0:
            return input_owners[0]

        return only_in_output_owners[0]

    @staticmethod
    def create_from_json(transaction_json: dict):
        inputs = transaction_json['inputs']
        outputs = transaction_json['outputs']

        inputObjects = [Input.from_json({**input}) for input in inputs]
        outputObjects = [Output.load(output) for output in outputs]

        transaction = Transaction(transaction_id=transaction_json['transaction_id'],
                                  transaction_fee=transaction_json['transaction_fee'],
                                  signature=transaction_json['signature'],
                                  inputs=inputObjects,
                                  outputs=outputObjects,
                                  message=transaction_json['message'])
        return transaction

    @staticmethod
    def create_transaction(key_manager: KeyManager, logger: Logger, transaction_id: str, transaction_fee: int, inputs: list[Input], outputs: list[Output], message: str):
        '''
        This method is prepared for 'Transaction' class instances without signature - it's calculated down here.
        '''
        # create data without signature
        transaction = Transaction(transaction_id=transaction_id, transaction_fee=transaction_fee,
                                  signature=None, inputs=inputs, outputs=outputs, message=message)
        data = transaction.get_data_without_signature()

        signature = key_manager.sign(json.dumps(data).encode('utf-8'))
        # add signature to data
        data = {**data, 'signature': signature}
        message, is_valid = Transaction.is_valid(data, logger)

        if not is_valid:
            return None, message, False

        transaction.set_signature(signature)
        return transaction, message, True
    
    def verifyTransactionSignature(self):
        '''
        Throws erro if signature not valid
        '''
        transaction_owner_pub_key = self.get_sender()
        transaction_json_bytes = json.dumps(self.get_data_without_signature()).encode('utf-8')
        signature = bytes.fromhex(self.get_signature())

        transaction_owner_pub_key_bytes = bytes.fromhex(transaction_owner_pub_key)
        verify_key = VerifyKey(transaction_owner_pub_key_bytes)
        # throw error if signature is invalid
        verify_key.verify(transaction_json_bytes, signature)
