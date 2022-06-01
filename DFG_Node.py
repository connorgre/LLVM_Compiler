import Parser as p 

class DFG_Node:
    """
    Node for the Data Flow Graph
    Holds one instruction, and related dfg metadata relating to it
    """
    def __init__(self, instruction=None):
        self.instruction = instruction              #instruction where variable is assigned
        self.name = instruction.args.result         #just to pull through the name to make access easier
        self.assignment = (-1, -1)                  #tuple with (block, instr) -- the block and offset into the block the var is assigned
        self.uses = []                              #list of (block, instr) -- locations var is used 
        self.is_loop_control = False                #true if this is a register related to loop control (ie loop index)
        self.is_phi = False