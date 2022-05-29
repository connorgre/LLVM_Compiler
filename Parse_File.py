from typing import List
import Parser as parser
import Instruction_Block as ib

class Parsed_File:
    """
    parses an llvm ir file, and breaks it into blocks, and orders those blocks by execution order
    """
    def __init__(self, filename):
        self.filename = filename
        self.Instructions: List[parser.Instruction] = []  #holds a list of all instructions
        self.blocks: List[ib.Instruction_Block] = []    #holds list of all the blocks
        self.block_names = []                           #used to find the name of a block based off its index (simplify successor calculations)
        self.block_order = []                           #holds the block indexes in the correct order
        self.Parse_File()
        self.Break_Into_Blocks()
        self.Identify_Loops()
        self.Order_Loops()
        self.Get_Loop_Depth()
        return

    def Parse_File(self):
        """
        parses each instruction of the file
        """
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
        """
        Gets each block of instructions and fills in some relevant information about the block
        """
        idx = 0
        block_idx = 0
        while(idx < len(self.Instructions)):
            if(self.Instructions[idx].instruction_type == "header"):
                block_name = self.Instructions[idx].args.target
                block = ib.Instruction_Block(block_name, idx, block_idx)
                idx = block.Get_Block(self.Instructions)
                self.blocks.append(block)
                self.block_names.append("%" + block_name)
                block_idx += 1
            else:
                idx += 1

        #fill in the target indexes
        for block in self.blocks:
            if(block.target1 in self.block_names):
                block.target1_idx = self.block_names.index(block.target1)
            if(block.target2 in self.block_names):
                block.target2_idx = self.block_names.index(block.target2)
        return
    
    def Identify_Loops(self):
        """
        DFS from each block, if it reaches itself in the search, it is the start of a loop
        this marks blocks as entry and exits of loops
        """
        visited = ["Not Visited" for i in range(len(self.block_names))]
        for block in self.blocks:
            block_idx = block.block_num
            if(visited[block_idx] == "Not Visited"):
                visited_stack = []
                visited_stack.append(block_idx)
                visited[block_idx] = "In Stack"
                self.doDFS(visited_stack, visited, block_idx)
        return
        
    def doDFS(self, stack, visited, idx):
        """
        Helper function for Identify Loops, does the DFS
        """
        adjacent = []
        adjacent.append(self.blocks[idx].target1_idx)
        if(self.blocks[idx].target1_idx != self.blocks[idx].target2_idx):
            adjacent.append(self.blocks[idx].target2_idx)
        
        for adj in adjacent:
            if(adj == -1):
                print("no edges from: " + self.blocks[idx].name)
            elif(visited[adj] == "In Stack"):
                self.blocks[adj].is_loop_entry = True
                self.blocks[adj].exit_idx = idx
                self.blocks[idx].is_loop_exit = True
                self.blocks[idx].entry_idx = adj
            elif(visited[adj] == "Not Visited"):
                stack.append(adj)
                visited[adj] = "In Stack"
                self.doDFS(stack, visited, adj)
        visited[idx] = "Done"
        stack.pop()

    def Order_Loops(self):
        """
        Orders the loops based on the above DFS search. Starts at the entry block, and 
        traverses through the list of blocks based on the successors in the branch statement
        """
        if(self.blocks[0].name != "entry"):
            print("Error, block 0 is not entry block")
        if(self.blocks[0].target1_idx != self.blocks[0].target2_idx):
            print("Error, entry block branches")
        self.block_order = [0 for i in range(len(self.blocks))]
        idx = self.blocks[0].target1_idx
        self.blocks[0].block_order = 0
        block_idx = 1
        num_entries = 1
        while(block_idx < len(self.blocks)):
            while(idx != -1):
                self.block_order[block_idx] = idx
                self.blocks[idx].block_order = block_idx
                if(self.blocks[idx].target1_idx not in self.block_order):
                    idx = self.blocks[idx].target1_idx
                else:
                    idx = self.blocks[idx].target2_idx
                block_idx += 1
            #this is for if there are mutliple 'entry' blocks
            #i think it shouldn't be an issue with no functions
            #in the code, but just in case, i am doing this
            if(block_idx < len(self.blocks)):
                entries_found = 0
                entry_idx = 0
                num_entries += 1
                while(entries_found < num_entries):
                    if(self.blocks[entry_idx].name == "entry"):
                        entries_found += 1
                    entry_idx += 1
                idx = entry_idx-1
        
    def Get_Loop_Depth(self):
        """
        Gets the loop depth (level of nested loops)
        program starts at 0, and the deepest nested loop will be a higher number
        """
        depth = 0
        for idx in self.block_order:
            if(self.blocks[idx].is_loop_entry):
                depth += 1
            self.blocks[idx].loop_depth = depth
            if(self.blocks[idx].is_loop_exit):
                depth -= 1
            if(depth < 0):
                print("Error, depth < 0")
        if(depth != 0):
            print("Error, final depth != 0")
        

    def Print_All_Blocks(self, in_order=True, short=True):
        if(in_order == False):
            for block in self.blocks:
                print("***********************************")
                if(short == True):
                    block.Print_Block_Short()
                else:
                    block.Print_Block
        else:
            for i in self.block_order:
                print("***********************************")
                if(short == True):
                    self.blocks[i].Print_Block_Short()
                else:
                    self.blocks[i].Print_Block()

    def Get_Order_Idx(self, idx):
        return self.blocks[self.block_order[idx]]

    def Print_Names(self):
        for idx in range(len(self.blocks)):
            print("'" + self.Get_Order_Idx(idx).name + "',")
    
    def Print_Entries(self):
        for idx in range(len(self.blocks)):
            if(self.Get_Order_Idx(idx).is_loop_entry):
                print("'" + self.Get_Order_Idx(idx).name + "',")

    def Print_Exits(self):
        for idx in range(len(self.blocks)):
            if(self.Get_Order_Idx(idx).is_loop_exit):
                print("'" + self.Get_Order_Idx(idx).name + "',")