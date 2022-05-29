import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as node

class Data_Flow_Graph:
    """
    The data flow graph for the file
    """
    def __init__(self):
        self.variables = []
        