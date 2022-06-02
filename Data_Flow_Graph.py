from typing import List
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as dfg

class Data_Flow_Graph:
    """
    The data flow graph for the file
    """
    def __init__(self, parsed_file):
        self.variables : List[dfg.DFG_Node] = []        #holds all variables
        self.global_variables : List[dfg.DFG_Node] = [] #holds only global variables
        self.par_file : pf.Parsed_File = parsed_file
        
    def Get_All_Variables(self):
        """
        Finds all the variables in the file
        """
        #first get the global variables
        self.Get_Global_Variables()
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                if(instr.args.result != "DEFAULT"):
                    #if the variable is not in the list
                    if(self.Get_Var_Idx(instr.args.result) == -1):
                        node = dfg.DFG_Node(instr)
                        if(instr.block_offset == -1):
                            print("Error, block offset == -1")
                        node.assignment = (b_idx, instr.block_offset)
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
                    node = dfg.DFG_Node(instr)
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

    def Get_Uses(self, node:dfg.DFG_Node):
        """
        Get all the uses of a variable
        """
        var = node.name
        for v in self.variables:
            print("still need to implement")