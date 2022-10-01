from typing import TYPE_CHECKING
import DFG_Node2 as dfgn
import warnings
import DfgUtil as util

if TYPE_CHECKING:
    import DFG2 as _dfg
    import Block_DFG2 as bdfg

class Pointer_Info():
    """
    class to hold information about pointer Nodes
    """
    offsetInfo : "dfgn.Loop_Info"
    ptrNode    : "dfgn.DFG_Node" # node for the pointer
    initInfo   : "bool"
    def __init__(self):
        self.offsetInfo = dfgn.Loop_Info()
        self.ptrNode    = None
        self.initInfo   = False
        return

    def Init_Ptr_Info(self, pointerUse:"dfgn.DFG_Node"):
        self.initInfo = True
        pointerPath   = pointerUse.Get_Root_Pointer_Path()
        self.ptrNode  = pointerPath[0]

        getElementPtrNode:"dfgn.DFG_Node" = None
        ptrOffsetNode    :"dfgn.DFG_Node" = None
        for node in pointerPath:
            if node.Get_Instr() == "getelementptr":
                assert(getElementPtrNode == None)
                getElementPtrNode = node
        if getElementPtrNode != None:
            if len(getElementPtrNode.instruction.args.index_value) != 2:
                warnings.warn("only expect 2 level getelementptr in gcn")
            offsetStr = getElementPtrNode.instruction.args.index_value[-1]
            if offsetStr[0] in ["%", "@"]:
                ptrOffsetNode = getElementPtrNode.Get_Link_By_Name(offsetStr)
                ptrOffsetNode.Fill_Loop_Info()
                self.offsetInfo = ptrOffsetNode.loopInfo.getCopy()
            else:
                assert(offsetStr.isnumeric())
                assert(self.offsetInfo.strideIters == [])
                assert(self.offsetInfo.stride      == [])
                assert(self.offsetInfo.strideDepth == [])
                self.offsetInfo.initVal = int(offsetStr)

    def Get_Offset_Stride(self):
        assert(self.initInfo)
        return self.offsetInfo.stride.copy()
    def Get_Offset_StrideIters(self):
        assert(self.initInfo)
        return self.offsetInfo.strideIters.copy()
    def Get_Offset_StrideDepth(self):
        assert(self.initInfo)
        return self.offsetInfo.strideDepth.copy()
    def Get_Offset_InitVal(self):
        assert(self.initInfo)
        return self.offsetInfo.initVal
    def Get_Ptr_Node(self):
        return self.ptrNode

class Phi_Node(dfgn.DFG_Node):
    """
    utilities for phi nodes
    """
    stride      :int
    valDict     :dict
    loopStride  :int
    def __init__(self, block:"bdfg.Block_DFG", instruction=None):
        super().__init__(block, instruction)
        self.nodeType.special = True
        self.nodeType.phi     = True

        self.loopStride       = None
        self.stride           = []
        self.valDict          = {}

        self.Fill_Phi_Info()
        return

    def Get_Phi_Stride(self):
        if self.loopStride == None:
            self.Get_Loop_Change()
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

    def Get_Loop_Change(self):
        """
        phiNode gets its stride info handled specially
        """
        # normal loop iter logic
        # Get path from phi to the node we do the compare with
        nodePath = self.Search_For_Node(self, needTwoOfNode=True)
        assert(nodePath[0] == self and nodePath[-1] == self and len(nodePath) > 2)
        currVal = self.Get_Init_Val()
        prevNode = self
        for node in nodePath[1:-1]:
            assert(node.Is_Arithmatic())
            # phi loop stride MUST be constant for this compiler
            assert(len(node.immediates) == 1)
            if node.instruction.args.op1 != prevNode.name:
                warnings.warn("I assume the immediate val is always op2 for now, \
                                need to implement extra logic otherwise")
                assert(False)
            currVal = util.Do_Op(node.Get_Instr(), currVal, node.immediates[0])
            prevNode = node

        if self.loopStride != None:
            assert(self.loopStride == currVal)
        if len(self.loopInfo.stride) != 0:
            assert(len(self.loopInfo.stride) == 1)
            assert(self.loopInfo.stride[0] == currVal)

        self.loopStride = currVal
        return currVal

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
    def __init__(self, block:"bdfg.Block_DFG", instruction=None):
        super().__init__(block, instruction)
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

    def __init__(self, block:"bdfg.Block_DFG", instruction=None):
        super().__init__(block, instruction)
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

    def __init__(self, block:"bdfg.Block_DFG"):
        super().__init__(block)
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

    def __init__(self, block:"bdfg.Block_DFG"):
        super().__init__(block)
        self.nodeType.special   = True
        self.nodeType.macc      = True

        self.resPtrInfo  = Pointer_Info()
        self.addPtrInfo  = Pointer_Info()
        self.mul1PtrInfo = Pointer_Info()
        self.mul2PtrInfo = Pointer_Info()
        return

    def Get_Res_Ptr(self):
        return self.resPtrInfo.Get_Ptr_Node()
    def Get_Add_Ptr(self):
        return self.addPtrInfo.Get_Ptr_Node()
    def Get_Mul1_Ptr(self):
        return self.mul1PtrInfo.Get_Ptr_Node()
    def Get_Mul2_Ptr(self):
        return self.mul2PtrInfo.Get_Ptr_Node()