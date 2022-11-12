import hashlib

max_nonce = 2 ** 32  # 4 billion
difficulty_bits = 10      # 0 to 24 bits
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
    _header: dict = None

    _data: dict = None
    _nonce: str = None

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
        # TODO what to do when nonce is invalid
        (nonce, is_valid) = candidate_block.__proof_of_work()
        # assign found nonce value to block
        candidate_block._header['nonce'] = nonce
        candidate_block._nonce = nonce

        # calculate hash from prev_block_hash value + nonce to keep consistency in blockchain
        candidate_block._header['hash_prev_nonce'] = candidate_block.__calculate_hash_prev_block_nonce(
        )
        return candidate_block

    @staticmethod
    def load(candidate_block_object: dict):
        candidate_block = Block(
            candidate_block_object['header']['prev_block_hash'],
            candidate_block_object['data'],
            candidate_block_object['header']['miner_pub_key']
        )
        candidate_block._header['nonce'] = candidate_block_object['header']['nonce']
        candidate_block._header['hash_prev_nonce'] = candidate_block_object['header']['hash_prev_nonce']
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
        self._header = {
            'prev_block_hash': prev_block_hash,
            # 'nonce'           : <str>
            # 'hash_prev_nonce' : <str>
            'miner_pub_key': miner_pub_key
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
        for nonce in range(max_nonce):  # check all possible nonce values
            if self.__verify_nonce(nonce):  # verify specific nonce value
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

        pow_obj = self.get_pow_data()
        # find hash value for header
        hash_result = hashlib.sha256(str(pow_obj).encode('utf-8') +
                                     str(nonce).encode('utf-8')).hexdigest()
        # check if it's valid (lesser than target)
        is_nonce_valid = int(hash_result, 16) < target
        return is_nonce_valid

    def __calculate_hash_prev_block_nonce(self):
        nonce = self._header['nonce']
        prev_block_hash = self.get_prev_hash()

        hash_prev_block_nonce = hashlib.sha256(
            (str(prev_block_hash) + str(nonce)).encode('utf-8')
        ).hexdigest()

        return hash_prev_block_nonce

    def get_pow_data(self):
        return {
            'data': dict(sorted(self._data.items())),
            'header': {
                'miner_pub_key': self._header['miner_pub_key'],
                'prev_block_hash': self.get_prev_hash(),
            }
        }

    def get_prev_hash(self):
        return self._header['prev_block_hash']

    def verify_block(self):
        '''
        Verifies block consistency that is:
        1) Check if nonce placed in header solves proof of work
        2) Check if hash_prev_nonce value is valid - h(prev. hash + nonce)

        :returns: True if block is correct, otherwise False
        '''
        # check if nonce value solves proof of work
        is_valid = self.__verify_nonce(self._header['nonce'])
        # if not is_valid:
        #    pow_obj = self.get_pow_data()
        #    find hash value for header
        #    hash_result = hashlib.sha256(str(pow_obj).encode('utf-8') +
        #                              str(self._header['nonce']).encode('utf-8')).hexdigest()
        #    raise ValueError(f"hash_result = {hash_result}")

        # check if calculated h(prev. block hash + nonce) matches value placed in header
        prev_block_nonce_hash_calculated = self.__calculate_hash_prev_block_nonce()
        prev_block_nonce_hash = self._header['hash_prev_nonce']

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
        block_object = {
            'data': dict(sorted({**self._data}.items())),
            'header': dict(sorted({**self._header}.items()))
        }
        return block_object

    def create_next_block(self, data: dict, miner_public_key: str):
        return Block.create(self.get_block_hash(), data, miner_public_key)
