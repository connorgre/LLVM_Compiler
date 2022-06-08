from typing import List
import DFG_Node as dfg_node
import Instruction_Block as ib

class Block_DFG:
    def __init__(self, block:ib.Instruction_Block):
        self.block:ib.Instruction_Block = block
        self.block_num:int = block.block_order          #block number this dfg corresponds to
        self.outer_vars:List[dfg_node.DFG_Node] = []    #variables that are used which have been assigned outside this block
        self.inner_vars:List[dfg_node.DFG_Node] = []    #variables assigned in this block
    
    def Get_Inner_Vars(self, dfg):
        """
        Get the variables that are assigned within the block
        """
        for var in dfg.variables:
            if var.assignment[0] == self.block_num:
                self.inner_vars.append(var)

    def Get_Outer_Vars(self, dfg):
        """
        Get the variables assigned outside of the block
        Get_Inner_Vars() must be called first
        """
        for var in self.inner_vars:
            for dep in var.dependencies:
                if(dep[0] != self.block_num):
                    dep_var = dfg.Get_Node_Block_Offset(dep)
                    if(dep_var == None):
                        print("Error, dep_var == None")
                    self.outer_vars.append(dep_var)

    def Print_Vars(self):
        print("\n**Inner Nodes**")
        for var in self.inner_vars:
            print(var.name)
        print("\n**Outer Nodes**")
        for var in self.outer_vars:
            print(var.name)