

from math import log2
from typing import List
import DFG_Node as dfgn

"""
The nodes that will become individual instructions, will be the result of compressing
multiple nodes

Their names will start with a $ (rather than % or @ for llvm nodes)
"""

VecRegLen = 1024    # length of the vector register in 4B words
MaxDivision = 8     # Max divisions of vector
def GetRegFileDiv(offset):
    # returns the how much we need to divide reg file into (for offset)
    if offset == 0:
        return 1

    minAlign = VecRegLen // MaxDivision
    count = MaxDivision
    while ((offset & minAlign == 0) and (count > 0)):
        count >>= 1
        minAlign <<= 1

    return count

def GetStartVec(offset):
    # Gets the vector to do instruction from
    if (offset == 0):
        return 0
    start = offset
    while (start & 1 == 0):
        start >>= 1
    # assert that we don't have a higher index than number of divisions
    assert(start < GetRegFileDiv(offset))
    return start

class VLE_Node(dfgn.DFG_Node):
    def __init__(self):
        super().__init__()
        self.is_vle = True
        self.is_special = True

        self.pointer_node:dfgn.DFG_Node         = None  # the node where the pointer gets assigned
        self.load_node:dfgn.DFG_Node            = None  # the node where the pointer to the data we copy is assigned
        self.load_val:int                       = None  # if we are memsetting with an immediate
        self.length = 0

        self.init_ptr_off  = None   # initial value of the pointer offset
        self.init_load_off = None   # initial value of the load offset
        self.ptr_stride    = []   # stride of the pointer offset between calls
        self.load_stride   = []   # stride of the load offset between calls

        self.ptr_stride_depth = []
        self.load_stride_depth = []

        self.load_ptr_reg:str = None

    def Print_Node(self, extended=False):
        defaultStr = "None"
        super().Print_Node(extended)

        print("\tPointer: " + self.pointer_node.name)
        print("\tptr Stride: " + ', '.join([str(x) for x in self.ptr_stride]))
        print("\tptr Stride Depth: " + ' '.join([str(x) for x in self.ptr_stride_depth]))
        print("\tptr init Val: " + str(self.init_ptr_off))

        if(self.load_node != None):
            print("\tLoad: " + self.load_node.name)
            print("\tload Stride: " + ', '.join([str(x) for x in self.load_stride]))
            print("\tload Stride Depth: " + ' '.join([str(x) for x in self.load_stride_depth]))
            print("\tload init Val: " + str(self.init_load_off))
        else:
            print("\tLoad: " + str(self.load_val))
        print("\tLength: " + str(self.length))

    def Relink_Nodes(self, dfg, origCallNode:dfgn.DFG_Node):
        """
        This will move the uses of the node that uses this around
        And will
        """
        dfg.ReLinkNodes(self.pointer_node, origCallNode, self)
        dfg.ReLinkNodes(self.load_node, origCallNode, self)
        return

    def Get_vsetivli(self):
        """
        Returns a string of the vsetivli instruction for this node.
        For now, assumes rf0 points to the base of the register file
        """
        # this assert is bc we only load 16 floats at a time minimum,
        # and bc the length is given as bytes, not floats (4B)
        assert (self.length % 64 == 0)
        retStr = "vsetivli zero, "
        ptrOff = self.init_ptr_off
        if self.pointer_node.name == "@stream_out":
            ptrOff = self.init_load_off
        numIters = str((self.length // 64)) + ", "
        bitLen = "e32, "
        div = "m" + str(GetRegFileDiv(ptrOff))
        retStr += numIters + bitLen + div
        self.vsetivliString = retStr
        return retStr

    def Get_RiscV_Instr(self):
        """
        returns the RiscV instruction string
        """
        if (self.riscVString != None):
            return self.riscVString
        if "@stream_out" == self.pointer_node.name:
            self.riscVString = self.Get_StreamOut_Str()
            return self.riscVString
        self.riscVString = ""
        retStr = "vle32.v "
        vecOffset = "v" + str(GetStartVec(self.init_ptr_off)) + ", "
        loadPtr = ""
        if (self.load_val != None):
            if (self.load_val == 0):
                loadPtr = "(x0)"
            else:
                print("Error, only loading 0 imm supported")
                loadPtr = "ERROR"
        else:
            assert(self.load_node != None)
            loadPtr = "(" + self.load_ptr_reg + ")"
        loadPtrStr = None
        if self.load_ptr_reg != None:
            loadPtrStr = "addi " + self.load_ptr_reg + ", " + self.load_ptr_reg + ", "
            # * 4 bc the stride is in sizeof(float), while it needs to be byte indexed
            assert(len(self.load_stride) == 1)
            loadPtrStr += " !" + str(self.load_stride[0] * 4) + "!"
        self.riscVString += retStr + vecOffset + loadPtr
        if loadPtrStr != None:
            self.riscVString += "\n" + loadPtrStr
        return self.riscVString

    def Add_Load_Pointer_Inc(self, rdfg):
        """
        adds the instructions to initialize and increment the
        register for the offset of the load pointer
        """
        if self.load_node == None:
            return
        if self.pointer_node.name == "@stream_out":
            return

        # for now assert we only have 1 type of offset
        self.Print_Node()
        assert(len(self.load_stride) == 1)
        stride:int = self.load_stride[0]
        blockNode:Block_Node = self.Get_Block_Node_1(True)

        blockNode2:Block_Node = blockNode.Get_Block_Node_1(True)
        addNode = dfgn.DFG_Node()
        addNode.name = self.name + "__loadOffPtr"
        addNodeReg = rdfg.Get_And_Use_IntReg()

        # not sure what memory offset to give anything else...
        assert(self.load_node.name == "@hbm0")

        addNodeInstr = "addi " + addNodeReg + ", " + hex(self.init_load_off + rdfg.memOffset)
        addNode.riscVString = addNodeInstr

        # make sure that this gets initialized in the previous block
        addNode.dep_nodes.append(blockNode2)
        blockNode2.use_nodes.append(addNode)

        addNode.use_nodes.append(blockNode)
        blockNode.dep_nodes.append(addNode)

        self.dep_nodes.append(addNode)
        addNode.use_nodes.append(self)

        rdfg.nodes.append(addNode)

        self.load_ptr_reg = addNodeReg

    def Get_StreamOut_Str(self):
        """
        returns streamout version of the vle
        """
        retStr = "streamout.v, "
        vecOffset = "v" + str(GetStartVec(self.init_load_off))
        return retStr + vecOffset


class Phi_Node(dfgn.DFG_Node):
    def __init__(self, instruction = None):
        super().__init__(instruction)
        self.is_phi = True
        self.is_special = True

        self.init_val = None
        self.init_entry = None
        self.stride = []

        self.val_dict = {}

        self.Fill_Phi_Info()


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

class Macc_Node(dfgn.DFG_Node):
    def __init__(self):
        super().__init__()

        self.is_macc = True
        self.is_special = True

        # pointers we load from
        self.accPtr:dfgn.DFG_Node = None
        self.mul1Ptr:dfgn.DFG_Node = None
        self.mul2Ptr:dfgn.DFG_Node = None

        # stride, ordered by the depth of the loop during the stride
        self.accStride:List[int] = []
        self.mul1Stride:List[int] = []
        self.mul2Stride:List[int] = []

        # corresponding depth for the strides
        self.accStrideDepth:List[int] = []
        self.mul1StrideDepth:List[int] = []
        self.mul2StrideDepth:List[int] = []

        # initial values for the pointers
        self.accIdxInitVal :int = None
        self.mul1IdxInitVal:int = None
        self.mul2IdxInitVal:int = None

        # the number of iterations we do at each block
        self.accPtrIters  = []
        self.mul1PtrIters = []
        self.mul2PtrIters = []

        # the number of times we do each loop for
        self.numLoopRuns = []

    def Print_Node(self, extended=False):
        super().Print_Node(extended)

        if self.accPtr != None:
            print("\taccPtr: " + self.accPtr.name)
        print("\taccStride: " + ', '.join([str(x) for x in self.accStride]))
        print("\taccStrideDepth: " + ' '.join([str(x) for x in self.accStrideDepth]))
        print("\taccPtr init Val: " + str(self.accIdxInitVal))
        print()

        if self.mul1Ptr != None:
            print("\tmul1Ptr: " + self.mul1Ptr.name)
        print("\tmul1Stride: " + ', '.join([str(x) for x in self.mul1Stride]))
        print("\tmul1StrideDepth: " + ' '.join([str(x) for x in self.mul1StrideDepth]))
        print("\tmul1Ptr init Val: " + str(self.mul1IdxInitVal))
        print()

        if self.mul2Ptr != None:
            print("\tmul2Ptr: " + self.mul2Ptr.name)
        print("\tmul2Stride: " + ', '.join([str(x) for x in self.mul2Stride]))
        print("\tmul2StrideDepth: " + ' '.join([str(x) for x in self.mul2StrideDepth]))
        print("\tmul2Ptr init Val: " + str(self.mul2IdxInitVal))
        print()

        print("\tnumLoopRuns: " + ' '.join([str(x) for x in self.numLoopRuns]))

    def Relink_Nodes(self, dfg, origCallNode):
        """
        Puts in the actual links for relevant nodes
        I.e. fills out dep and use nodes
        """
        dfg.ReLinkNodes(self.accPtr, origCallNode, self)
        dfg.ReLinkNodes(self.mul1Ptr, origCallNode, self)
        dfg.ReLinkNodes(self.mul2Ptr, origCallNode, self)

    def Get_vsetivli(self):
        #  FOR NOW, assume that the accumulate pointer is
        # stationary, ie it gets the v1 instead of x1

        # assert that we are multiplying from the register file
        assert(self.mul1Ptr.name == "%rf0" or self.mul2Ptr.name == "%rf0")
        # assert that we are accumulating to register file
        assert(self.accPtr.name == "%rf0")

        instrStr = "vsetivli zero, "
        vecNum = -1
        for i in self.numLoopRuns[::-1]:
            if i > 1:
                vecNum = i
                break
        vecIters = str(vecNum) + ", e32, "
        div = "m" + str(GetRegFileDiv(self.accIdxInitVal))

        self.vsetivliString = instrStr + vecIters + div
        return self.vsetivliString

    def Get_RiscV_Instr(self):

        retStr = ""
        instrStr = "vmacc.vx "
        accVec = "v" + str(GetStartVec(self.accIdxInitVal)) + ", "
        mul2Vec = ""

        if self.mul1Ptr.name == "@stream_in" or self.mul2Ptr.name == "@stream_in":
            mul2Vec = "vs"
        else:
            print("ERROR, EXPECTED STREAM_IN FOR VMACC")
            mul2Vec = "ERROR"

        if self.mul1Ptr.name == "@stream_in":
            # is this really necessary ?
            assert(self.mul2Stride[1] == 16)
            unRoll = self.numLoopRuns[self.mul2StrideDepth[1]]
            start = self.mul2IdxInitVal // 16

            for loop in range(start, unRoll):
                mul1Vec = "x" + str(loop) + ", "
                retStr += instrStr + accVec + mul1Vec + mul2Vec + "\n"
        else:
            print("Error, only implemented stream_in as mul1")
            print("Solution is simply to copy paste mul1 code...")

        self.riscVString = retStr
        return retStr

class Bne_Node(dfgn.DFG_Node):
    def __init__(self, instruction=None):
        super().__init__(instruction)

        self.is_special = True

        self.loop_limit = None
        self.loop_stride = None
        self.init_val = None
        self.num_iters = None
        self.back_target:dfgn.DFG_Node = None
        self.forward_target:dfgn.DFG_Node = None
        self.always_forward = True  #unconditionally branch forward
        self.is_bne = True


    def Print_Node(self, extended=False):
        super().Print_Node(extended)
        print("Loop limit: " + str(self.loop_limit))
        print("Loop Stride: " + str(self.loop_stride))
        print("loop iters: " + str(self.num_iters))
        print("Back target: " + str(self.back_target.name))
        print("Forward target: " + str(self.forward_target.name))

    def Get_RiscV_Instr(self):
        if self.always_forward == True:
            return ""
        assert(self.back_target.iterName != None)
        incName = str(self.back_target.iterName)
        retStr = "addi " + incName + ", " + incName + ", " + hex(1)
        retStr += "\n"
        retStr += "bne " + incName + ", " + "!" + str(self.loop_limit) + "!" + ", " + self.back_target.name
        self.riscVString = retStr
        return retStr

class Block_Node(dfgn.DFG_Node):
    """
    Used in the RISC-V dfg to represent entry points for blocks
    mostly just to make the branch target more clearly defined.
    """
    def __init__(self, instruction=None):
        super().__init__(instruction)
        self.total_iters = None
        self.num_iters = None
        self.init_val = None
        self.stride = None
        self.vector_len = None
        self.is_special = True
        self.is_block = True

        self.iterName = None

    def Print_Node(self, extended=False):
        super().Print_Node(extended)
        print("\titers: " + str(self.num_iters) + " : " + str(self.total_iters))
        print("\tVector Len: " + str(self.vector_len))
        print("\tinit: " + str(self.init_val))
        print("\tstride: " + str(self.stride))

    def Is_Terminal_Loop(self):
        """
        returns true, and the node we found ourself from
        if there are no more nested loops
        within this one.  For now, only safe to call within
        a RiscV_dfg after the block and bne nodes have been
        processed to remove useless ones
        """
        nodeList:List[dfgn.DFG_Node] = self.use_nodes.copy()
        searchedNodes:List[dfgn.DFG_Node] = []
        found_self = False
        bneNode = None
        while len(nodeList) > 0 and found_self == False:
            for node in nodeList.copy():
                nodeList.remove(node)
                searchedNodes.append(node)
                if node.is_block and node != self:
                    # don't try to find ourself through another block
                    continue
                for use in node.use_nodes:
                    if use == self:
                        assert(node.is_bne)
                        found_self = True
                        bneNode = node
                        break
                    if use not in searchedNodes and use not in nodeList:
                        nodeList.append(use)
        return (found_self, bneNode)

    def Get_RiscV_Instr(self):
        assert(self.iterName != None)
        retStr = "addi " + self.iterName + ", " + "x0, 0x000"
        retStr += "\n"
        retStr += self.name + ":"
        self.riscVString = retStr
        return retStr

    def Get_IterName(self, iterName:str = None):
        if iterName == None:
            self.iterName = "!" + self.name + "!"
        else:
            self.iterName = iterName
