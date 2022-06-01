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
        self.variables : List[dfg.DFG_Node] = []
        self.par_file :pf.Parsed_File = parsed_file
        
    def Get_All_Variables(self):
        """
        Finds all the variables in the file
        """
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            for instr in block.instructions:
                if(instr.args.result != "DEFAULT"):
                    if(instr.args.result not in self.variables):
                        node = dfg.DFG_Node(instr)
                        if(instr.block_offset == -1):
                            print("Error, block offset == -1")
                        node.assignment = (b_idx, instr.block_offset)
                        if(instr.args.instr == "phi"):
                            self.is_phi = True
                        self.variables.append(node)