from typing import List
import Parser as parser

class Instruction_Block:
    """
    blocks of instructions in the control flow
    """
    def __init__(self, name = "DEFUALT", start_instr = -1, block_num = -1):
        self.start_idx = start_instr
        self.end_idx = -1
        self.block_num = block_num
        self.start_line = -1
        self.end_line = -1
        self.instructions = []
        self.name = name
        self.target1 = "DEFAULT"
        self.target2 = "DEFAULT"
        self.entry_blocks = []
        self.is_llvm_loop = False
        self.is_loop_entry = False
        self.is_loop_exit = False
        self.loop_depth = 0
        self.block_order = -1
        
        self.exit_idx = -1          #if we are an entry block, index of the block we exit from
        self.entry_idx = -1         #if we are a closing block, index of the block we enter to
        self.target1_idx = -1       #block index of target1
        self.target2_idx = -1       #block index of target2

    def Get_Block(self, instructions: List[parser.Instruction]):
        idx = self.start_idx
        self.start_line = instructions[idx].line_num
        if(self.start_idx != instructions[idx].instr_num):
            print("Error, start idx != instructions index")
        if(instructions[idx].instruction_type != "header"):
            print("Error, Get_Block not called on header")
            return idx + 1
        pred_idx = 0
        while(pred_idx < len(instructions[idx].args.predecessors)):
            self.entry_blocks.append(instructions[idx].args.predecessors[pred_idx])
            pred_idx += 1
        while(instructions[idx].instruction_type != "terminator"):
            self.instructions.append(instructions[idx])
            idx += 1
            if(idx == len(instructions)):
                print("Error in block, idx = length")
                return idx
        self.instructions.append(instructions[idx])
        self.end_idx = idx
        self.end_line = instructions[idx].line_num
        if(self.end_idx != instructions[idx].instr_num):
            print("Error, end idx != instructions index")
        if(instructions[idx].args.instr == "br"):
            self.target1 = instructions[idx].args.true_target
            self.target2 = instructions[idx].args.false_target
            self.is_llvm_loop = instructions[idx].args.is_loop
        elif(instructions[idx].args.instr != "ret"):
            print("Error, final instruction in block not br or ret")
        self.Get_Block_Offsets()
        return idx + 1

    def Get_Block_Offsets(self):
        initial_instruction_num = self.instructions[0].instr_num
        prev_offset = -1
        for instr in self.instructions:
            instr.block_offset = instr.instr_num - initial_instruction_num
            if(instr.block_offset <= prev_offset):
                print("Error, block offset got smaller")
            prev_offset = instr.block_offset



    def Print_Block(self, print_instructions = False):
        print("Name: " + self.name + ", Order: " + str(self.block_order))
        print("Start: " + str(self.start_idx) + ", Line: " + str(self.start_line))
        print("End: " + str(self.end_idx) + ", Line: " + str(self.end_line))
        print("BlockNum: " + str(self.block_num))
        print("Predecessors: " + ' '.join(self.entry_blocks))
        print("Target1: " + self.target1 + ", Target2: " + self.target2)
        print("Loop Entry: " + str(self.is_loop_entry) + ", Loop Exit: " + str(self.is_loop_exit) + ", Loop Depth: " + str(self.loop_depth))
        if(print_instructions == True):
            print("Instructions: ")
            for instr in self.instructions:
                print("*************************************************")
                instr.Print_Instruction()

    def Print_Block_Short(self):
        print("\tName: " + self.name + ", Order: " + str(self.block_order))
        if(self.target1 != self.target2):
            print("\tSucessors: " + self.target1 + ", " + self.target2)
        else:
            print("\tSucessors: " + self.target1)
        print("\tLoop Entry: " + str(self.is_loop_entry) + ", Loop Exit: " + str(self.is_loop_exit) + ", Loop Depth: " + str(self.loop_depth))


