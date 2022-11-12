from CryptoBlock import Block

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
    
    def add_block(self, new_block: Block): #TODO
        last_block = self._blocks[-1]

        prev_block_hash = last_block.get_block_hash()
        prev_hash = new_block.get_prev_hash()

        if prev_block_hash != prev_hash:
            raise ValueError("Inconsistency found in provided blockchain - " +
                             "Invalid blockchain, try again with another.")

        block_valid = new_block.verify_block()
        if not block_valid:
            raise ValueError("Invalid block")

        self._blocks.append(new_block)
    
    def add_block_from_data(self, data: dict, miner_pub_key: str):
        block = Block.create(self._blocks[-1].get_block_hash(), data, miner_pub_key)
        self.add_block(block)

    # @staticmethod
    # def validate_blockchain(blockchain: list[Block]):
    #     # proof of work - solution for nonce
    #     # h(prev. hash + nonce)
    #     if len(blockchain) == 1:
    #         block = blockchain[0]
            
    #     else:
    #         for i in range(1, len(blockchain)):
    #             validate_block(block)

    def to_json(self):
        blocks = []
        for block in self._blocks:
            blocks.append(block.to_json())
        return blocks

    @staticmethod
    def create_blockchain(blockchain_list: list[Block]):
        if len(blockchain_list) == 0:
            raise ValueError("Provided blockchain is empty. Could not create blockchain.")
        
        generic_block_valid = blockchain_list[0].verify_block()
        if not generic_block_valid:
            raise ValueError("Generic block is invalid.")

        blockchain = BlockChain(blockchain_list[0])

        for i in range(1, len(blockchain_list)):
            try:
                blockchain.add_block(blockchain_list[i])
            except ValueError as err:
                raise err
            print("Block added successfully")

        return blockchain