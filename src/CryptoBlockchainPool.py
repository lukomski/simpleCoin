from CryptoBlockchainTree import BlockchainTree
from CryptoBlock import Block
from logging import Logger
from CryptoBlockchain import BlockChain

class BlockchainPool:
    
    __blockchain_tree: BlockchainTree = None
    __orphan_blocks: list[Block] = []
    __logger: Logger = None
    
    def __init__(self, genesis_block: Block | None, logger: Logger) -> None:
        self.__blockchain_tree = BlockchainTree(genesis_block, logger)
        self.__logger = logger
            
    def add_block(self, block: Block) -> bool:
        if self.__blockchain_tree is None:
            self.__blockchain_tree = BlockchainTree(block, self.__logger)
            return
        success = self.__blockchain_tree.add_block(block)
        if success:
            # Find childs of added block among orphans
            while True:
                added_orphan_block = False 
                for idx in range(len(self.__orphan_blocks)):
                    orphan_block = self.__orphan_blocks[idx]
                    if self.__blockchain_tree.add_block(orphan_block):
                        self.__orphan_blocks.remove(orphan_block)
                        self.__logger.info('Added new block from orphan list')
                        added_orphan_block = True
                        break
                if not added_orphan_block:
                    break
        else:
            self.__orphan_blocks.append(block)
            
    def get_blockchain_tree(self) -> BlockchainTree:
        return self.__blockchain_tree
    
    def get_blockchain(self) -> BlockChain | None:
        if self.__blockchain_tree is None:
            return
        return self.__blockchain_tree.get_blockchain()
    
    def get_all_blocks(self) -> list[Block]:
        if self.__blockchain_tree is None:
            return []
        blocks = self.__blockchain_tree.get_all_blocks()
        blocks.extend(self.__orphan_blocks)
        return blocks
    
    @staticmethod
    def create_blockchain_pool(blocks: list[Block], logger: Logger):
        blockchain_pool = BlockchainPool(genesis_block=None, logger=logger)
        for block in blocks:
            blockchain_pool.add_block(block=block)
        return blockchain_pool