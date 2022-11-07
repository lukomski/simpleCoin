import hashlib
import uuid
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
            'nonce': uuid.uuid4().hex,
            'miner': miner_pub_key_hex,
            'body_hash': candidate_block.get_body_hash(),
        }
        candidate_block.riddle_result = candidate_block.__proof_of_work(
            candidate_block.header)
        return candidate_block

    @staticmethod
    def load(candidate_block_object: dict):
        candidate_block = Block()
        candidate_block.set_header(
            {
                'prev_hash': candidate_block_object['header']['prev_hash'],
                'nonce': candidate_block_object['header']['nonce'],
                'miner': candidate_block_object['header']['miner'],
                'body_hash': candidate_block_object['header']['body_hash'],
            })
        candidate_block.set_body(candidate_block_object['body'])
        candidate_block.set_riddle_result(
            candidate_block_object['riddle_result'])
        return candidate_block

    def set_header(self, header: dict):
        self.header = header

    def set_body(self, body: dict):
        self.body = body

    def set_riddle_result(self, riddle_result: dict):
        self.riddle_result = riddle_result

    def get_body_hash(self):
        body_bytes = json.dumps(self.body).encode('utf-8')
        body_hash = hashlib.sha256(body_bytes).hexdigest()
        return body_hash

    def __proof_of_work(self, header: dict):
        # calculate the difficulty target
        for nonce in range(max_nonce):
            if self.__verify_riddle(nonce, header):
                print(f"Success with nonce {nonce}")
                return nonce
        print(f'Failed after {nonce} tries')
        return nonce

    def __verify_riddle(self, result, header):
        hash_result = hashlib.sha256(str(header).encode(
            'utf-8') + str(result).encode('utf-8')).hexdigest()
        return True if int(hash_result, 16) < target else False

    def verify(self):
        # check body hash
        if self.header['body_hash'] != self.get_body_hash():
            return False
        # check riddle
        return self.__verify_riddle(self.riddle_result, self.header)

    def to_JSON(self):
        return {
            'header': self.header,
            'body': self.body,
            'riddle_result': self.riddle_result
        }

    def get_hash(self):
        block_json = self.to_JSON()
        block_bytes = json.dumps(block_json).encode('utf-8')
        hash = hashlib.sha256(block_bytes).hexdigest()
        return hash

    def get_prev_hash(self):
        return self.header['prev_hash']
