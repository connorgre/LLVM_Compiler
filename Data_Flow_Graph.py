from typing import List, Tuple
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as dfg_node
import Block_DFG as b_dfg

class Data_Flow_Graph:
    """
    The data flow graph for the file
    """
    def __init__(self, parsed_file):
        self.variables : List[dfg_node.DFG_Node] = []        #holds all variables (includes global)
        self.global_variables : List[dfg_node.DFG_Node] = [] #holds only global variables
        self.par_file : pf.Parsed_File = parsed_file
        self.block_dfgs : List[b_dfg.Block_DFG] = []         #list of dfgs for each block
        self.Get_All_Variables()
        self.Get_Uses()
        self.Get_Dependencies()
        self.Get_All_Block_DFGs()
        
    def Get_All_Variables(self):
        """
        Finds all the variables in the file
        """
        #first get the global variables
        self.Get_Global_Variables()
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            ord_idx = block.block_order
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                if(instr.args.result != "DEFAULT"):
                    #if the variable is not in the list
                    if(self.Get_Var_Idx(instr.args.result) == -1):
                        node = dfg_node.DFG_Node(instr)
                        if(instr.block_offset == -1):
                            print("Error, block offset == -1")
                        node.assignment = (ord_idx, instr.block_offset)
                        if(instr.args.instr == "phi"):
                            self.is_phi = True
                        self.variables.append(node)

    def Get_Global_Variables(self):
        """
        Easier to just handle the global variables seperately
        """
        for instr in self.par_file.Instructions:
            if(instr.args == None):
                continue
            if(instr.args.result[0] == '@'):
                #if this isnt in the variable list yet
                if(self.Get_Var_Idx(instr.args.result) == -1):
                    node = dfg_node.DFG_Node(instr)
                    node.assignment = (-1, instr.instr_num) #-1 to indicate that it is a global variable
                    node.is_global = True
                    self.variables.append(node)
                    self.global_variables.append(node)

    def Get_Var_Idx(self, name):
        """
        Gets index of variable by name
        returns -1 if a variable with that name is not in the list
        """
        for idx in range(len(self.variables)):
            if(self.variables[idx].name == name):
                return idx
        return -1

    def Get_Node_Block_Offset(self, pos:Tuple[int, int]):
        """
        returns the Node that was assigned at (block, block offset)
        """
        for node in self.variables:
            if node.assignment == pos:
                return node
        return None

    def Get_Instruction_Block_Offset(self, pos:Tuple[int, int]):
        """
        returns the instruction at ((ordered) block, offset)
        """
        #if it is assigned outside a block (ie global variable)
        if(pos[0] == -1):
            instr = self.par_file.Instructions[pos[1]]
            if(instr.args.result[0] != '@'):
                print("Error: block -1, but not global variable")
            return instr
        
        block = self.par_file.Get_Order_Idx(pos[0])
        return block.instructions[pos[1]]

    #this assumes all uses of a variable are within blocks
    #ie, no global assignments use other variables 
    def Get_Uses(self):
        """
        Get all the uses of the variables (discluding the assignment)
        If I had planned a bit better, this could maybe
        have been done in the same function as Get_All_Variables,
        but this works fine too and is simpler
        """
        for idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(idx)
            ord_idx = block.block_order
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                for var in instr.args.vars_used:
                    var_idx = self.Get_Var_Idx(var)
                    if(var_idx == -1):
                        if(var[0] in ["%", "@"]):
                            print("Error, variable: " + str(var) + ", not in list of variables")
                        continue
                    var_loc = (ord_idx, instr.block_offset)
                    if(self.variables[var_idx].assignment != var_loc):
                        self.variables[var_idx].uses.append(var_loc)
    
    def Get_Dependencies(self):
        """
        Similar to Get_Uses, but goes the other direction in the graph
        Could have also been done in dependencies, but I think splitting it up makes reading/debugging 
        easier
        """
        for var in self.variables:
            for use in var.uses:
                use_var = self.Get_Node_Block_Offset(use)
                if(use_var == None):
                    #call br and store don't have variable assignment, and thus don't 
                    if(self.Get_Instruction_Block_Offset(use).args.instr not in ["call", "br", "store"]):
                        print("Error, use_var shouldn't be None, " + str(var.name) + ", " + str(use))
                    continue
                use_var.dependencies.append(var.assignment)


    def Get_All_Block_DFGs(self):
        """
        Gets all the basic block DFGs
        """
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            block_dfg = b_dfg.Block_DFG(block)
            block_dfg.Get_Inner_Vars(self)
            block_dfg.Get_Outer_Vars(self)
            self.block_dfgs.append(block_dfg)