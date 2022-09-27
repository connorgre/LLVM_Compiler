import warnings
from matplotlib import lines
from numpy import result_type

import DFG_Node2 as dfgn
import Instruction_Block as ib
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import SDFG_Node2 as sdfgn
from typing import TYPE_CHECKING
import DfgUtil as util
import sys

if TYPE_CHECKING:
    import DFG2 as _dfg

class Block_DFG:
    block           :ib.Instruction_Block
    dfg             :"_dfg.DFG"
    blockNum        :int
    outerNodes      :"list[dfgn.DFG_Node]"
    innerNodes      :"list[dfgn.DFG_Node]"
    graph           :nx.DiGraph

    selfIters       :int
    vectorLen       :int

    phiInitVal      :int
    phiStride       :int

    phiNode         :sdfgn.Phi_Node
    brNode          :dfgn.DFG_Node

    blockNode       :sdfgn.Block_Node
    bneNode         :sdfgn.Bne_Node

    createdNodes    :"list[dfgn.DFG_Node]"

    brToBneDone     :bool

    isLoopEntry     :bool
    isLoopExit      :bool

    def __init__(self, dfg:"_dfg.DFG", block:ib.Instruction_Block):
        self.block        = block
        self.blockNum     = block.block_order          #block number this dfg corresponds to
        self.outerNodes   = []    #variables that are used which have been assigned outside this block
        self.innerNodes   = []    #variables assigned in this block
        self.graph        = nx.DiGraph()
        self.dfg          = dfg
        self.selfIters    = -1
        self.vectorLen    = -1
        self.phiInitVal   = -1
        self.phiStride    = -1
        self.phiNode      = None
        self.brNode       = None
        self.createdNodes = []
        self.isLoopEntry  = None
        self.isLoopExit   = None

        self.blockNode      = sdfgn.Block_Node()
        self.blockNode.name = "$block_" + self.block.name
        self.bneNode        = sdfgn.Bne_Node()
        self.bneNode.name   = "$bne_" + self.block.name

        # link these together
        self.bneNode.Add_Dep(self.blockNode)

        self.createdNodes.append(self.bneNode)
        self.createdNodes.append(self.blockNode)

        self.brToBneDone = False

    def Init_Block_1(self):
        """
        These don't require any other blocks to have
        called init
        """
        self.Init_Inner_Nodes()
        self.Init_Outer_Nodes()
        self.Fill_Vector_Len()
        self.Assign_Self_As_Parent()

    def Init_Block_2(self):
        """
        These rely on other blocks being created and initialized
        with Init_Block_1()
        """
        self.Transfer_Br_Info_To_Bne()
        self.Fill_Iter_Info()

    def Init_Block_3(self):
        """
        can't do these until Init2 has been done for every block
        """
        self.Remove_Br()

    def Init_Inner_Nodes(self):
        """
        Get Variables assigned within block
        """
        dfg = self.dfg
        for node in dfg.nodes:
            node:dfgn.DFG_Node
            if node.assignment[0] == self.blockNum:
                assert(node not in self.innerNodes)
                self.innerNodes.append(node)
                if node.Get_Instr() in ['br', 'ret']:
                    self.brNode = node
                    if node.Get_Instr() == "br":
                        assert(node in dfg.branchNodes)
                if node.nodeType.phi:
                    self.phiNode = node
                    assert(node in dfg.phiNodes)
                    self.blockNode.Add_Use(node)
        assert(self.brNode != None)
        self.Find_End_Nodes()

    def Init_Outer_Nodes(self):
        for node in self.innerNodes:
            for dep in node.Get_Deps():
                if dep.assignment[0] != self.blockNum:
                    self.outerNodes.append(dep)

    def Assign_Self_As_Parent(self):
        """
        realized later that this would be useful to do, easier to refactor like this instead
        of hunting every instance down...
        """
        warnings.warn("should move parent block assignment")
        for node in self.innerNodes:
            assert(node.parentBlock == None)
            node.parentBlock = self
        for node in self.createdNodes:
            assert(node.parentBlock == None)
            node.parentBlock = self

    def Find_End_Nodes(self):
        """
        Gets nodes that are at end of dep chain so that we can link them to the
        exit node, to ensure dfg completes all instructions before finishing
        """
        for node in self.innerNodes:
            if node == self.brNode:
                continue
            endNode = True
            for use in node.Get_Uses():
                if use.assignment[0] == self.blockNum:
                    endNode = False
            if endNode:
                # add this as psuedo dependency
                self.brNode.Add_Dep(node, True, True)

    def Remove_Node(self, node:dfgn.DFG_Node):
        removed = False
        if node in self.innerNodes:
            assert(self.innerNodes.count(node) == 1)
            self.innerNodes.remove(node)
            removed = True
        if node in self.outerNodes:
            assert(self.outerNodes.count(node) == 1)
            self.outerNodes.remove(node)
            if removed:
                warnings.warn("block dfg has node in multiple lists")
            removed = True
        if node in self.createdNodes:
            assert(self.createdNodes.count(node) == 1)
            self.createdNodes.remove(node)
            if removed:
                warnings.warn("block dfg has node in multiple lists")
            removed = True
        assert(removed)
        return

    def Print_Vars(self):
        print("Inner Nodes")
        for node in self.innerNodes:
            print("\t" + node.name)
        print("Outer Nodes")
        for node in self.outerNodes:
            print("\t" + node.name)
        print("Created Nodes")
        for node in self.createdNodes:
            print("\t" + node.name)

    def Make_Graph(self, showImm=True):
        """
        Uses node pointer lists of the inner vars rather than the location
        pointers
        """
        blockNodes = self.outerNodes.copy()
        blockNodes.extend(self.innerNodes.copy())
        blockNodes.extend(self.createdNodes.copy())
        self.graph = nx.DiGraph()
        imm_num = 0
        for node in blockNodes:
            for use in node.Get_Uses():
                if(node in self.outerNodes and use not in self.innerNodes):
                    continue
                if(node in self.dfg.branchNodes):
                    suffix_1 = "_b"
                else:
                    suffix_1 = "_v"
                if(use in self.dfg.branchNodes):
                    suffix_2 = "_b"
                else:
                    suffix_2 = "_v"
                self.graph.add_edge(node.name[1:] + suffix_1 ,use.name[1:] + suffix_2)

            if node in self.outerNodes:
                #only do the dep list for inner nodes
                continue
            for dep in node.Get_Deps():
                if(dep in self.dfg.branchNodes):
                    suffix_1 = "_b"
                else:
                    suffix_1 = "_v"
                if(node in self.dfg.branchNodes):
                    suffix_2 = "_b"
                else:
                    suffix_2 = "_v"
                self.graph.add_edge(dep.name[1:] + suffix_1 ,node.name[1:] + suffix_2)
            if(showImm):
                for imm in node.immediates:
                    self.graph.add_edge(str(imm) + "_i" + str(imm_num),node.name[1:] + "_v")
                    imm_num += 1

    def Show_Graph(self, showImm=True):
        """
        displays the networkx graph for this block
            immediates are red
            'fake' (call branch store) variables are light blue
            variables defined in the block are green
            (non global) variables defined outside the block are blue
            global variables defined outside the block are purple
            variables outside the block that depend on variables assigned in the block are yellow

            *** ANY NON-CYAN NODES SHOULD HAVE OUTWARD ARROWS, AND ANY CYAN NODES SHOULD NOT ***
        """
        dfg:"_dfg.DFG" = self.dfg
        self.Make_Graph(showImm)
        color_array = []
        for node in self.graph.nodes:
            if("_s" in node):
                color_array.append((0,1,1))
            elif(("_b" in node)):
                color_array.append((.75, .25, .75))
            elif("$" + node[:-2] in [var.name for var in self.createdNodes]):
                color_array.append((.25, 1, .5))
            elif(("%" + node[:-2]) in [var.name for var in self.innerNodes]):
                color_array.append((0,1,0))
            elif("%" + node[:-2] in [var.name for var in self.outerNodes]):
                color_array.append((0,0,1))
            elif("@" + node[:-2] in [var.name for var in self.outerNodes]):
                color_array.append((1,.25,1))
            elif("_i" in node):
                color_array.append((1,0,0))
            else:
                color_array.append((1, 1, 0))
        plt.title(self.block.name + " : " + str(self.blockNum) + " : " + str(self.selfIters) + " : " + str(self.phiStride))

        no_uses = lines.Line2D([], [], color=(0,1,1), marker='o', markersize=10, label='no use (call, br, store)')
        branch = lines.Line2D([],[], color = (.75,.25,.75), marker = 'o', markersize=10, label = "branch node")
        def_in = lines.Line2D([], [], color=(0,1,0), marker='o', markersize=10, label='defined inside')
        def_out = lines.Line2D([], [], color=(0,0,1), marker='o', markersize=10, label='defined outside')
        def_glob = lines.Line2D([], [], color=(1,.25,1), marker='o', markersize=10, label='defined globally')
        imm = lines.Line2D([], [], color=(1,0,0), marker='o', markersize=10, label='immediate')
        use_out = lines.Line2D([], [], color=(1,1,0), marker='o', markersize=10, label='used outside')

        plt.legend(handles=[no_uses, branch, def_in, def_out, def_glob,imm, use_out], bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure)

        pos = graphviz_layout(self.graph, prog='dot')

        # This just moves the position of the node on the
        # screen over to make the graph clearer
        if "22_v" in pos:
            val = pos["22_v"]
            newx = 1.1 * val[0]
            newVal = (newx, val[1])
            pos["22_v"] = newVal

        nx.draw(self.graph, pos, with_labels=True, font_size=6, node_color=color_array)
        plt.show()

    def Transfer_Br_Info_To_Bne(self):
        """
        Fills out the Bne information with everything it needs from the Br instruction
        Useful bc Bne node is it's own class, while br is regular node
        """
        assert(self.brNode != None)
        if self.brNode.Get_Instr() == "ret":
            return # nothing to be done
        assert(self.brNode.Get_Instr() == "br")

        brNode = self.brNode
        for dep in brNode.Get_Deps():
            if dep.Get_Instr() == "icmp":
                assert(dep.instruction.args.comparison == "eq")
                assert(len(dep.immediates) == 1)
                self.bneNode.alwaysForward = False

        target1 = brNode.instruction.args.true_target[1:]
        target2 = brNode.instruction.args.false_target[1:]

        if self.bneNode.alwaysForward == True:
            assert(target1 == target2)
        else:
            assert(target1 != target2)

        # get the blocks we are branching to
        for block in self.dfg.blockDFGs:
            if block.block.name in [target1, target2]:
                if block.blockNum <= self.blockNum:
                    assert(self.bneNode.backTarget == None)
                    self.bneNode.backTarget = block.blockNode
                    self.bneNode.Add_Use(block.blockNode)
                else:
                    assert(self.bneNode.forwardTarget == None)
                    self.bneNode.forwardTarget = block.blockNode
                    self.bneNode.Add_Use(block.blockNode)

        assert(len(self.bneNode.Get_Uses()) in [1,2])
        assert(self.bneNode.forwardTarget != None)
        if self.bneNode.alwaysForward == False:
            assert(self.bneNode.backTarget != None)

        self.brNode.Add_Connections_To_Node(self.bneNode)
        self.brToBneDone = True
        return

    def Init_Loop_Entry_Exit(self):
        self.isLoopEntry = self.block.is_loop_entry
        self.isLoopExit = self.block.is_loop_exit

    def Is_Loop_Entry(self):
        return self.isLoopEntry
    def Is_Loop_Exit(self):
        return self.isLoopExit

    def Fill_Vector_Len(self):
        """
        Gets the vector length of the loop
        """
        for node in self.innerNodes:
            if node.instruction != None:
                resType = node.instruction.args.result_type
                if resType != None:
                    if resType.is_vector:
                        # assert that we haven't found a vector instruction,
                        # or all vector instructions are the same size within the block
                        assert(self.vectorLen == -1 or
                                int(resType.width) == self.vectorLen)
                        self.vectorLen = resType.width
        # if we didn't find a vector, vectorLen == 1
        if self.vectorLen == -1:
            self.vectorLen = 1
        return

    def Fill_Iter_Info(self):
        """
        Gets the iteration info about the loop
            numIters
            iterNode
            initVal for iterNode
            stride for iterNode
        self.Fill_Vector_Len MUST be called before this
        """
        # only need to get this info if we are at the entry to a loop
        if self.block.is_loop_entry == False:
            self.blockNode.loopEntry = False
            return

        # get the block we exit from
        assert(self.block.exit_idx != -1)
        exitBlockPf = self.dfg.parsedFile.blocks[self.block.exit_idx]
        assert(exitBlockPf.is_loop_exit == True)
        exitBlock = self.dfg.blockDFGs[exitBlockPf.block_order]
        assert(exitBlock.blockNum == exitBlockPf.block_order)

        # exit of end of loop and entry to loop
        blockExitNode = exitBlock.brNode
        assert(self.phiNode == self.innerNodes[0])
        assert(self.phiNode.Get_Instr() == "phi")
        assert(blockExitNode.Get_Instr() == "br")
        assert(self.phiNode.Get_Type() == "phi")

        # Get initial value of the phi variable
        prevBranch:dfgn.DFG_Node = None
        assert(isinstance(self.phiNode, sdfgn.Phi_Node))
        for node in self.phiNode.Get_Phi_Branches():
            if node.assignment[0] < self.blockNum:
                assert(prevBranch == None)
                prevBranch = node
        assert(prevBranch != None)
        assert(prevBranch.Get_Instr() == "br")
        assert(prevBranch.name == self.phiNode.Get_Phi_Branch_By_Number(0))

        initVal = self.phiNode.Get_Phi_Value_By_Number(0)
        if initVal.isdigit() == False:
            assert(False, "initial value assumed to be constant digit")
        else:
            self.phiInitVal = int(initVal)
        if self.phiInitVal != 0:
            warnings.warn("Loop init val != 0")

        compareVar:dfgn.DFG_Node  = None
        compareImm:int            = None
        for node in blockExitNode.Get_Deps():
            if node.Get_Instr() == "icmp":
                assert(node.instruction.args.comparison == "eq")
                compareVar = node.instruction.args.op1
                compareImm = node.instruction.args.op2
        assert(compareVar != None)
        assert(compareImm != None)
        assert(compareVar != "DEFAULT")
        assert(compareImm != "DEFAULT")

        self.loopLimit   = int(compareImm)
        compareNode = self.dfg.Get_Node_By_Name(compareVar)


        # normal loop iter logic
        # Get path from phi to the node we do the compare with
        nodePath:"list[dfgn.DFG_Node]" = self.phiNode.Search_For_Node(compareNode)
        currVal = 0
        for node in nodePath[1:]:
            if node.Get_Instr() != "add":
                warnStr = "currently only support adding for loop iters\n"
                warnStr += "\tinstr: " + node.Get_Instr()
                warnings.warn(warnStr)
                assert(False)
            if len(node.immediates) == 0:
                warnings.warn("only support immediate loop increments")
                assert(False)
            currVal = util.Do_Immediate_Op(currVal, node)
        self.phiStride = currVal
        if self.phiStride == 0:
            # see below comment, clang compiles the ir for this section in an odd way
            assert(self.block.name == "vector.body")
            self.phiStride = 1


        assert(self.vectorLen != -1)
        self.selfIters = int(((self.loopLimit - self.phiInitVal)//self.phiStride) // self.vectorLen)

        if compareNode == self.phiNode and \
            self.loopLimit == self.phiInitVal and \
            blockExitNode.instruction.args.false_target[1:] == self.block.name:
            #This is the special case where we are only looping once.
            #for some reason llvm ir doesn't use the .next variable, but rather compares
            #the initial variable with its initial value.  This makes no sense for clang to do
            #but whatever.  Does this for vector body in gcn
            self.selfIters = 1
            if self.block.name != "vector.body":
                warnStr = "not necessarily an error,\n"
                warnStr += "but only expect this for vector.body block(in gcn)"
                warnings.warn(warnStr)

        self.phiNode.loopStride = self.phiStride

        self.blockNode.numIters     = self.selfIters
        self.blockNode.stride       = self.phiStride
        self.blockNode.vectorLen    = self.vectorLen
        self.blockNode.initVal      = self.phiInitVal
        self.blockNode.loopEntry    = True
        return

    def Remove_Br(self):
        """
        Removes the br instructions, as all necessary info has been given
        to the bne block.  Must be called AFTER Transfer_Br_Info_To_Bne
        """
        if self.brNode.Get_Instr() == "ret":
            return
        assert(self.brToBneDone)
        assert(self.brNode.Get_Instr() == "br")
        # remove the node from all lists
        self.brNode.Remove_Psu_Connections()
        self.brNode.Delete_Node(False)
        self.dfg.Remove_Node(self.brNode)

        assert(sys.getrefcount(self.brNode) == 2)

    def Get_All_Nodes(self):
        """
        returns a COPY of inner+outer+created nodes
        """
        nodeList:"list[dfgn.DFG_Node]"
        nodeList = self.innerNodes.copy()
        nodeList.extend(self.outerNodes.copy())
        nodeList.extend(self.createdNodes.copy())
        return nodeList

    def Get_Inner_Nodes(self):
        return self.innerNodes.copy()

    def Get_Outer_Nodes(self):
        return self.outerNodes.copy()

    def Get_Loop_Depth(self):
        return self.block.loop_depth

    def Create_Macc(self):
        """
        This identifies the mutliply accumulate function dataflow pattern
        Right now it requires the llvm to compile down to a fmuladd, but
        if the clang compiler that gets used doesn't support that, then I
        can add in support for a multiply then add instruction
        """
        #first, identify if fmuladd is in block
        fmdNode:dfgn.DFG_Node = None
        foundMacc = False
        for node in self.innerNodes:
            if node.instruction == None:
                continue
            if node.Get_Instr() == "fmuladd":
                assert(foundMacc == False)
                fmaNode = node
                foundMacc = True
        if foundMacc == False:
            return

        #now get the nodes of the operands
        mul1_var = fmaNode.instruction.args.mul1
        mul2_var = fmaNode.instruction.args.mul2
        add_var  = fmaNode.instruction.args.add
        res_var  = fmaNode.instruction.args.result

        mul1Node:dfgn.DFG_Node = self.dfg.Get_Node_By_Name(mul1_var)
        mul2Node:dfgn.DFG_Node = self.dfg.Get_Node_By_Name(mul2_var)
        addNode :dfgn.DFG_Node = self.dfg.Get_Node_By_Name(add_var)
        resNode :dfgn.DFG_Node = self.dfg.Get_Node_By_Name(res_var)

        assert(resNode == fmaNode)

        resStoreNode:dfgn.DFG_Node = None
        resPtrNode  :dfgn.DFG_Node = None
        storePath = resNode.Search_For_Node(None, storeSearch=True)
        assert(len(storePath) >= 2)
        if len(storePath) > 2:
            warnings.warn("in gcn, this should only ever be 2 nodes")
        resStoreNode = storePath[-1]
        resStorePtr_temp = resStoreNode.Get_Link_By_Name(resStoreNode.instruction.args.pointer)
        resPtrNode = resStorePtr_temp.Get_Root_Pointer()

        maccNode:sdfgn.Macc_Node = sdfgn.Macc_Node()
        warnings.warn("should move parent block assignment")
        maccNode.parentBlock = self

        self.createdNodes.append(maccNode)
        maccNode.addPtrInfo.Init_Ptr_Info(addNode)


        warnings.warn("not done")
        assert(False)




