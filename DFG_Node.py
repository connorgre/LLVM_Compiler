import Parser as p 

class DFG_Node:
    """
    Node for the Data Flow Graph
    Holds one instruction, and related dfg metadata relating to it
    """
    def __init__(self, instruction=None):
        self.instruction:p.Instruction = instruction              #instruction where variable is assigned
        self.name:str = instruction.args.result         #just to pull through the name to make access easier
        self.assignment = (-1, -1)                  #tuple with (block, instr) -- the block and offset into the block the var is assigned
        self.uses = []                              #list of (block, instr) -- locations var is used 
        self.psuedo_uses = []                       #uses generated as a result of 'fake' going into a branch instruction
        self.dependencies = []                      #list of the 1 level up dependencies of this variable
        self.psuedo_dependencies = []               #dependencies generated as a result of an 'end' node going into a branch node
        self.immediates = []                        #the immediates used in the assignment of this node
        self.is_loop_control = False                #true if this is a register related to loop control (ie loop index)
        self.is_phi = False
        self.is_global = False

    def Print_Node(self, extended=False):
        print("Name: " + self.name)
        print("Assigned: " + "(" + str(self.assignment[0]) + "," + str(self.assignment[1]) + ")")
        uses = ""
        for use in self.uses:
            uses += "(" + str(use[0]) + "," + str(use[1]) + ")" + "; "
        print("Uses: " + uses)
        if(extended):
            print("Loop Control: " + str(self.is_loop_control))
            print("Phi Assigned: " + str(self.is_phi))
            print("Global: " + str(self.is_global))