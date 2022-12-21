from CryptoBlock import Block
from CryptoBlockchain import BlockChain
from logging import Logger
import json


class BlockchainTree:
    __genesis_block: Block = None
    __blocks: dict[str, Block] = {}
    __logger: Logger = None

    def __init__(self, genesis_block: Block, logger: Logger) -> None:
        self.__genesis_block = genesis_block
        self.__blocks[genesis_block.get_block_hash()] = self.__genesis_block
        self.__logger = logger

    def add_block(self, block: Block) -> bool:
        if self.__blocks[block.get_prev_hash()] is None:
            return False
        if block.get_block_hash() in self.__blocks:
            self.__logger.warning(
                f'Try to add block which already exists {block.to_json()}')
            return False
        self.__blocks[block.get_block_hash()] = block
        return True

    def to_tree_structure(self):
        all_blocks = self.__blocks.values()
        all_structs = []
        for block in all_blocks:
            message = ''
            if block.get_block_hash() == self.__genesis_block.get_block_hash():
                message = 'Genesis block'
            item = {'name': block.get_block_hash(),
                    'manager': block.get_prev_hash(),
                    'toolTip': '',
                    'body': block.to_json(),
                    'message': message
                    }
            all_structs.append(item)
        return all_structs
