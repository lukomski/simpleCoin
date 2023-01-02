from CryptoBlock import Block
from CryptoBlockchain import BlockChain
from logging import Logger
import json
from functools import cmp_to_key

class BlockchainTree:
    __genesis_block: Block = None
    __blocks_map: dict[str, Block] = {}
    __logger: Logger = None

    def __init__(self, genesis_block: Block | None, logger: Logger) -> None:
        self.__genesis_block = genesis_block
        self.__logger = logger
        if self.__genesis_block != None:
            self.__blocks_map[genesis_block.get_block_hash()] = self.__genesis_block
        

    def add_block(self, block: Block) -> tuple[str, bool]:
        added_genesis_block = False
        if self.__genesis_block == None:
            self.__genesis_block = block
            added_genesis_block = True
        elif block.get_prev_hash() not in self.__blocks_map:
            return 'Previous block is not present in the tree', False
        if block.get_block_hash() in self.__blocks_map:
            self.__logger.warning(
                f'Try to add block which already exists {block.to_json()}')
            if added_genesis_block:
                self.__genesis_block = None # clear already added genesis block
            return f'Try to add block which already exists {block.to_json()}', False
        self.__blocks_map[block.get_block_hash()] = block
        return 'Ok', True

    def to_tree_structure(self):
        main_head = self.get_blockchain().get_blocks()[-1]
        all_blocks = self.__blocks_map.values()
        all_structs = []
        for block in all_blocks:
            message = ''
            if block.get_block_hash() == self.__genesis_block.get_block_hash():
                message = 'Genesis block'
            elif block.get_block_hash() == main_head.get_block_hash():
                message = 'HEAD'
            item = {'name': block.get_block_hash(),
                    'manager': block.get_prev_hash(),
                    'toolTip': '',
                    'body': block.to_json(),
                    'message': message,
                    'miner_pub_key': block.get_miner()
                    }
            all_structs.append(item)
        return all_structs
    
    def __get_heads(self) -> list[Block]:
        block_hashes = list(self.__blocks_map.keys())
        for block in list(self.__blocks_map.values()):
            if block.get_prev_hash() in block_hashes:
                block_hashes.remove(block.get_prev_hash())
        heads = [self.__blocks_map[hash] for hash in block_hashes]
        return heads
    
    def __get_block_blockchain(self, block: Block):
        blocks = [block]
        current_block = block
        while current_block.get_prev_hash() in self.__blocks_map:
            blocks.append(self.__blocks_map[current_block.get_prev_hash()])
            current_block = self.__blocks_map[current_block.get_prev_hash()]
        blocks.reverse()
        return blocks
    
    def __compare_block_blockchains(self, bcb_a: list[list[Block]], bcb_b: list[list[Block]]):
        if len(bcb_a) != len(bcb_b):
                return 1 if len(bcb_a) < len(bcb_b) else -1
        return 0
    
    def get_blockchain(self) -> BlockChain | None:
        heads = self.__get_heads()
        if len(heads) == 0:
            return None
        blockchains_blocks = [self.__get_block_blockchain(head) for head in heads]
        blockchains_blocks.sort(key=cmp_to_key(self.__compare_block_blockchains))
        selected_blockchain_blocks = blockchains_blocks[0]
        blockchain = BlockChain(selected_blockchain_blocks[0])
        for block in selected_blockchain_blocks[1:]:
            blockchain.add_block(block)
        if not blockchain.validate():
            self.__logger.warning('blockchain NOT valid')
        return blockchain

    def get_all_blocks(self) -> list[Block]:
        return [block for block in self.__blocks_map.values()]     
