import hashlib
import json

max_nonce = 2 ** 32  # 4 billion
difficulty_bits = 10  # 0 to 24 bits
target = 2 ** (256-difficulty_bits)


class Block:
    header: dict = None
    body: dict = None
    riddle_result = None

    # Create new candidate
    @staticmethod
    def create(prev_hash_hex: str, body: dict, miner_pub_key_hex: str):
        candidate_block = Block()
        candidate_block.body = body
        candidate_block.header = {
            'prev_hash': prev_hash_hex,
            'miner': miner_pub_key_hex,
        }
        nonce = candidate_block.__proof_of_work(candidate_block.get_POW_data())
        candidate_block.set_nonce(nonce)
        return candidate_block

    @staticmethod
    def load(candidate_block_object: dict):
        candidate_block = Block()
        candidate_block.set_header(
            {
                'prev_hash': candidate_block_object['header']['prev_hash'],
                'miner': candidate_block_object['header']['miner'],
            })
        candidate_block.set_nonce(candidate_block_object['header']['nonce'])
        candidate_block.set_body(candidate_block_object['body'])

        return candidate_block

    def set_nonce(self, nonce):
        self.header['nonce'] = nonce

    def set_header(self, header: dict):
        self.header = header

    def set_body(self, body: dict):
        self.body = body

    def get_POW_data(self):
        return {
            'prev_hash': self.header['prev_hash'],
            'miner': self.header['miner'],
            'body': self.body,
        }

    def __proof_of_work(self, data):
        # calculate the difficulty target
        for nonce in range(max_nonce):
            if self.__verify_nonce(nonce, data):
                print(f"Success with nonce {nonce}")
                return nonce
        print(f'Failed after {nonce} tries')
        return nonce

    def __verify_nonce(self, nonce, pow_data):
        hash_result = hashlib.sha256(str(pow_data).encode(
            'utf-8') + str(nonce).encode('utf-8')).hexdigest()
        return True if int(hash_result, 16) < target else False

    def verify(self):
        # check nonce
        return self.__verify_nonce(self.header['nonce'], self.get_POW_data())

    def to_JSON(self):
        return {
            'header': self.header,
            'body': self.body,
        }

    def get_hash(self):
        block_json = self.to_JSON()
        block_bytes = json.dumps(block_json).encode('utf-8')
        hash = hashlib.sha256(block_bytes).hexdigest()
        return hash

    def get_prev_hash(self):
        return self.header['prev_hash']
