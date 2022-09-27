from typing import TYPE_CHECKING
import DFG_Node2 as dfgn
import warnings

if TYPE_CHECKING:
    import DFG2 as _dfg

class Pointer_Info():
    """
    class to hold information about pointer Nodes
    """
    loopInfo      : "dfgn.Loop_Info"
    ptrNode       : "dfgn.DFG_Node" # node for the pointer
    ptrOffsetNode : "dfgn.DFG_Node" # if the load value is from a pointer
    ptrInitOffset : "int"           # list of the loop-loop offsets

    def __init__(self):
        self.loopInfo       = dfgn.Loop_Info()
        self.ptrNode        = None
        self.ptrInitOffset  = None
        self.ptrOffsetNode  = None
        return

    def Init_Ptr_Info(self, pointerUse:"dfgn.DFG_Node"):
        pointerPath   = pointerUse.Get_Root_Pointer_Path()
        self.ptrNode  = pointerPath[0]

        getElementPtrNode = None
        for node in pointerPath:
            if node.Get_Instr() == "getelementptr":
                assert(getElementPtrNode == None)
                getElementPtrNode = node
        if getElementPtrNode != None:
            if len(getElementPtrNode.instruction.args.index_value) != 2:
                warnings.warn("only expect 2 level getelementptr in gcn")
            offsetStr = getElementPtrNode.instruction.args.index_value[-1]
            if offsetStr[0] in ["%", "@"]:
                self.ptrOffsetNode = getElementPtrNode.Get_Link_By_Name(offsetStr)
                self.ptrInitOffset = self.ptrOffsetNode.Get_Init_Val()
            else:
                assert(offsetStr.isnumeric())
                self.ptrInitOffset = int(offsetStr)

class Phi_Node(dfgn.DFG_Node):
    """
    utilities for phi nodes
    """
    stride      :int
    valDict     :dict
    loopStride  :int
    def __init__(self, instruction=None):
        super().__init__(instruction)
        self.nodeType.special = True
        self.nodeType.phi     = True

        self.loopStride       = None
        self.stride           = []
        self.valDict          = {}

        self.Fill_Phi_Info()
        return

    def Get_Phi_Stride(self):
        assert(self.loopStride != None)
        return self.loopStride

    def Get_Phi_Branches(self):
        """
        Returns the nodes that branched to this one
        """
        deps = self.Get_Deps()
        for dep in deps.copy():
            try:
                self.valDict[dep.name]
            except KeyError:
                deps.remove(dep)
        return deps

    def Get_Phi_Branch_By_Number(self, branchNum):
        """
        Returns the NAME of the node that branched to here

        0-indexed by execution order
          0 for first entry
          1 for second
        """
        branchName:str = self.instruction.args.block_list[branchNum].predecessor
        return branchName
    def Get_Phi_Value_By_Number(self, branchNum):
        """
        Returns the NAME of the value

        0-indexed by execution order
          0 for first entry
          1 for second
        """
        branchName:str = self.Get_Phi_Branch_By_Number(branchNum)
        value:str = self.valDict[branchName]
        return value

    def Get_Phi_Value_By_Name(self, branchName):
        """
        Returns the NAME of the value that branched to here
        """
        value:str = self.valDict[branchName]
        return value

    def Fill_Phi_Info(self):
        for phiBlock in self.instruction.args.block_list:
            self.valDict[phiBlock.predecessor] = phiBlock.value

    def Get_Second_Val(self, dfg):
        ret_names = []
        for phiBlock in self.instruction.args.block_list:
            if phiBlock.predecessor != self.init_entry:
                ret_names.append(self.valDict[phiBlock.predecessor])
        assert(len(ret_names) != 1)
        return dfg.Get_Node_By_Name(ret_names[0])

class Block_Node(dfgn.DFG_Node):
    """
    Node indicating entry to block (bne target).  Ends up taking on the role of
    phi and block in riscV dfg
    """
    numIters    :int
    initVal     :int
    stride      :int
    vectorLen   :int
    loopEntry   :bool

    iterName:str
    def __init__(self, instruction=None):
        super().__init__(instruction)
        self.nodeType.special = True
        self.nodeType.block   = True
        self.numIters         = None
        self.initVal          = None
        self.stride           = None
        self.vectorLen        = None
        self.iterName         = None
        self.loopEntry        = None
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
        super().__init__(instruction)
        self.nodeType.special = True
        self.nodeType.bne     = True
        self.alwaysForward    = True

        self.loopLimit        = None
        self.loopStride       = None
        self.backTarget       = None
        self.forwardTarget    = None
        return

class VLE_Node(dfgn.DFG_Node):
    """
    holds info about vle node.  created from memset and memcpy
    """
    resPtrInfo  :Pointer_Info
    loadPtrInfo :Pointer_Info
    loadLength  :int
    loadValue   :int

    def __init__(self):
        super().__init__()
        self.nodeType.special   = True
        self.nodeType.vle       = True

        self.resPtrInfo         = Pointer_Info()
        self.loadPtrInfo        = Pointer_Info()
        self.loadLength         = None
        self.loadValue          = None

    def Is_Imm_Load(self):
        if self.loadValue != None:
            assert(self.loadPtrInfo.ptrNode == None)
            return True
        else:
            return False

class Macc_Node(dfgn.DFG_Node):
    """
    macc info
    """
    resPtrInfo  :Pointer_Info
    addPtrInfo  :Pointer_Info
    mul1PtrInfo :Pointer_Info
    mul2PtrInfo :Pointer_Info

    def __init__(self):
        super().__init__()
        self.nodeType.special   = True
        self.nodeType.macc      = True

        self.resPtrInfo  = Pointer_Info()
        self.addPtrInfo  = Pointer_Info()
        self.mul1PtrInfo = Pointer_Info()
        self.mul2PtrInfo = Pointer_Info()
        return