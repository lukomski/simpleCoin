import hashlib
import json

max_nonce       = 2 ** 32 # 4 billion
difficulty_bits = 10      # 0 to 24 bits
target          = 2 ** (256 - difficulty_bits)
    
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
    _header: dict = None

    _data  : dict = None
    _nonce : str = None

    @staticmethod
    def create(prev_block_hash: str, block_data: dict, miner_pub_key_hex: str):
        '''
        Creates blockchain block.

        :param prev_block_hash: Previous blockchain block hash.
        :type  prev_block_hash: str

        :param block_data: Data to be stored in new blockchain block.
        :type  block_data: dict

        :param miner_pub_key_hex: Node public key (digging process executer).
        :type  miner_pub_key_hex: str

        :returns: New blockchain block instance.
        '''

        # create block with basic data
        candidate_block = Block(prev_block_hash, block_data, miner_pub_key_hex)
        # solve proof of work
        (nonce, is_valid) = candidate_block.__proof_of_work() # TODO what to do when nonce is invalid
        # assign found nonce value to block
        candidate_block._header['nonce'] = nonce
        candidate_block._nonce = nonce

        # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
        candidate_block._header['hash_prev_nonce'] = hashlib.sha256(
            ( str(prev_block_hash) + str(nonce) ).encode('utf-8')
        ).hexdigest()
        return candidate_block

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
        self._header = {
            'prev_block_hash'   : prev_block_hash,
            # 'nonce'           : <str>
            # 'hash_prev_nonce' : <str>
            'miner_pub_key'     : miner_pub_key
        }
        self._data = block_data

    def get_block_hash(self):
        '''
        Calculates block hash.

        :returns: Calculated block hash
        '''
        block_json_bytes = str(self.to_json()).encode('utf-8')
        block_hash = hashlib.sha256(block_json_bytes).hexdigest()
        return block_hash

    def __proof_of_work(self):
        '''
        Runs proof of work.

        :returns: Tuple of valid nonce (if found, otherwise, max possible nonce value - 1) and bool (if nonce is valid).
        '''
        # TODO
        # calculate the difficulty target
        for nonce in range(max_nonce): # check all possible nonce values
            if self.__verify_nonce(nonce): # verify specific nonce value
                print(f"Success with nonce {nonce}")
                return (nonce, True)

        nonce = max_nonce - 1
        # no nonce value was valid - could not find solution for proof of work problem
        print(f'Failed after {nonce} tries')
        return (nonce, False)
    
    def __verify_nonce(self, nonce: int):
        '''
        Verifies if provided nonce solves proof of work problem.

        :param nonce: Nonce value to be verified.
        :type  nonce: int

        :returns: True if provided nonce value is valid, otherwise False.
        '''

        # find hash value for header 
        hash_result = hashlib.sha256(str(self._header).encode('utf-8') +
                                     str(nonce).encode('utf-8')).hexdigest()
        # check if it's valid (lesser than target)
        is_nonce_valid = int(hash_result, 16) < target
        return is_nonce_valid

    def to_json(self):
        '''
        Converts blockchain block instance to json.

        :returns: Stringified block.
        '''
        # restore block object as dictionary
        block_object = {
            'header': {
                **self._header
            },
            'data': {
                **self._data
            }
        }
        # serialize block object
        block_json = str(block_object)
        return block_json

class BlockChain:
    _blocks: list[Block] = None

    def __init__(self, generic_block: Block):
        '''
        Initializes 'BlockChain' class instance with initial generic block.

        :param generic_block: Generic block for blockchain.
        :type  generic_block: Block
        '''
        self._blocks = [generic_block]

    def dig(self, data: dict, miner_pub_key: str):
        '''
        Looks for next block to be added to BlockChain.

        :param data: Dictionary which will hold some information \
                     injected to specific block.
        :type  data: dict

        :param miner_pub_key: Network node public key.
        :type  miner_pub_key: str

        :returns: TODO
        '''
        prev_block_hash = self._blocks[-1].get_block_hash()
        next_block      = Block.create(prev_block_hash, data, miner_pub_key)

        self._blocks.append(next_block)
        # broadcast next_block to all nodes in network
    
    def validate(self):
        pass

generic_block = Block.create(None, {}, "")
blockchain = BlockChain(generic_block)
for i in range(10):
    blockchain.dig({}, "")

for block in blockchain._blocks:
    print(block.to_json())