from typing import Dict
import DFG_Node2 as dfgn
import warnings

class Phi_Node(dfgn.DFG_Node):
    """
    utilities for phi nodes
    """
    initVal:int
    stride:int
    initEntry:str
    valDict:dict
    def __init__(self, instruction=None):
        super.__init__(instruction)
        self.nodeType.special = True
        self.nodeType.phi     = True
        self.initVal          = None
        self.initEntry        = None
        self.stride           = []
        self.valDict          = {}

        self.Fill_Phi_Info()
        return

    def Fill_Phi_Info(self):
        self.init_val   = self.instruction.args.block_list[0].value
        self.init_entry = self.instruction.args.block_list[0].predecessor

        for phiBlock in self.instruction.args.block_list:
            self.val_dict[phiBlock.predecessor] = phiBlock.value
        
    def Get_Second_Val(self, dfg):
        ret_names = []
        for phiBlock in self.instruction.args.block_list:
            if phiBlock.predecessor != self.init_entry:
                ret_names.append(self.val_dict[phiBlock.predecessor])
        if (len(ret_names) != 1):
            print("Error, phi block has too many (or few) entry points")
        
        return dfg.Get_Node_By_Name(ret_names[0])

class Block_Node(dfgn.DFG_Node):
    """
    Node indicating entry to block (bne target).  Ends up taking on the role of 
    phi and block in riscV dfg
    """
    numIters:int
    initVal:int
    stride:int
    vectorLen:int

    iterName:str
    def __init__(self, instruction=None):
        self.nodeType.special = True
        self.nodeType.block   = True
        self.numIters         = None
        self.initVal          = None
        self.stride           = None
        self.vectorLen        = None
        self.iterName         = None
        return

    def Get_IterName(self, iterName:str = None):
        if iterName == None:
            self.iterName = "!" + self.name + "!"
        else:
            self.iterName = iterName
    
    def Is_Terminal_Loop(self):
        warnings.warn("Not implemented")
        return

class Bne_Node(dfgn.DFG_Node):
    """
    Node for bne info
    """
    loopLimit:int
    loopStride:int
    initVal:int
    backTarget:dfgn.DFG_Node
    forwardTarget:dfgn.DFG_Node
    alwaysForward:bool

    def __init__(self, instruction=None):
        self.nodeType.special = True
        self.nodeType.bne     = True
        self.loopLimit        = None
        self.loopStride       = None
        self.backTarget       = None
        self.forwardTarget    = None
        self.alwaysForward    = None
        return