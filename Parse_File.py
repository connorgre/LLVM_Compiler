from typing import List
import Parser as parser
import Instruction_Block as ib

class Parsed_File:
    """
    parses an llvm ir file
    """
    def __init__(self, filename):
        self.filename = filename
        self.Instructions: List[parser.Instruction] = []  #holds a list of all instructions
        self.blocks: List[ib.Instruction_Block] = []    #holds list of all the blocks
        return

    def Parse_File(self):
        file = open(self.filename, 'r')
        lines = file.readlines()
        line_num = 0
        instr_num = 0
        for line in lines:
            line_num += 1
            if(len(line) > 1):
                self.Instructions.append(parser.Instruction(line, line_num, instr_num))
                instr_num += 1

    def Break_Into_Blocks(self):
        idx = 0
        block_idx = 0
        while(idx < len(self.Instructions)):
            if(self.Instructions[idx].instruction_type == "header"):
                block_name = self.Instructions[idx].args.target
                block = ib.Instruction_Block(block_name, idx, block_idx)
                idx = block.Get_Block(self.Instructions)
                self.blocks.append(block)
                block_idx += 1
            else:
                idx += 1

        return

    