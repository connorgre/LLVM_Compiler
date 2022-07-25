

from ast import If
from email.policy import default
from typing import List
import DFG_Node as dfgn

"""
The nodes that will become individual instructions, will be the result of compressing
multiple nodes

Their names will start with a $ (rather than % or @ for llvm nodes)
"""

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
        self.accIdxInitVal:int = None
        self.mul1IdxInitVal:int = None
        self.mul2IdxInitVal:int = None

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

    def Relink_Nodes(self, dfg, origCallNode):
        """
        Puts in the actual links for relevant nodes
        I.e. fills out dep and use nodes
        """
        dfg.ReLinkNodes(self.accPtr, origCallNode, self)
        dfg.ReLinkNodes(self.mul1Ptr, origCallNode, self)
        dfg.ReLinkNodes(self.mul2Ptr, origCallNode, self)

class Bne_Node(dfgn.DFG_Node):
    def __init__(self, instruction=None):
        super().__init__(instruction)

        self.is_special = True

        self.loop_limit = None
        self.loop_stride = None
        self.init_val = None
        self.num_iters = None
        self.back_target:Block_Node = None
        self.forward_target:Block_Node = None
        self.always_forward = True  #unconditionally branch forward
        self.is_bne = True
    
    def Print_Node(self, extended=False):
        super().Print_Node(extended)
        print("Loop limit: " + str(self.loop_limit))
        print("Loop Stride: " + str(self.loop_stride))
        print("loop iters: " + str(self.num_iters))
        print("Back target: " + str(self.back_target.name))
        print("Forward target: " + str(self.forward_target.name))

class Block_Node(dfgn.DFG_Node):
    """
    Used in the RISC-V dfg to represent entry points for blocks
    mostly just to make the branch target more clearly defined.
    """
    def __init__(self, instruction=None):
        super().__init__(instruction)
        self.total_iters = None
        self.self_iters = None
        self.init_val = None
        self.stride = None
        self.vector_len = None
        self.is_special = True
        self.is_block = True

    def Print_Node(self, extended=False):
        super().Print_Node(extended)
        print("\titers: " + str(self.self_iters) + " : " + str(self.total_iters))
        print("\tVector Len: " + str(self.vector_len))        
        print("\tinit: " + str(self.init_val))
        print("\tstride: " + str(self.stride))
