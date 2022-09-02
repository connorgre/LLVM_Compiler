from typing import List, Tuple
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as dfgn
import Block_DFG as b_dfg
import Special_Nodes as sdfgn
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import lines
from networkx.drawing.nx_agraph import graphviz_layout
import Data_Flow_Graph as DFG

class RiscV_dfg:
    """
    A dfg where the unnecessary info from the original
    dfg isn't contained
    """
    def __init__(self, dfg, doAsmPasses:bool = True):
        self.dfg:DFG.Data_Flow_Graph = dfg
        self.nodes:List[dfgn.DFG_Node] = []

        self.first_node:dfgn.DFG_Node = None
        self.last_node:dfgn.DFG_Node = None

        self.linked_to_first:List[dfgn.DFG_Node] = []

        self.graph = nx.DiGraph()

        self.numIntRegs = 32
        self.intRegs:List[str] = ["x" + str(i) for i in range(self.numIntRegs)]
        self.openRegs:List[bool] = [True for i in range(self.numIntRegs)]
        self.openRegs[0] = False

        self.memOffset:int = 4096

        self.Init_From_DFG()
        if doAsmPasses == True:
            self.Do_Asm_Passes()

    def Do_Asm_Passes(self):
        """
        gets the dfg in a state where the assembly
        can easily be generated
        """
        self.Remove_WorkNode_Links()
        self.Remove_Empty_Blocks()
        self.Remove_Pass_Through_Bne()
        self.Remove_Useless_Loops()
        self.Remove_All_Macc_Unrolls()
        self.Remove_Unused_Targets()
        self.Fill_Out_IterNames()
        self.Show_Graph()
        self.Add_Load_Pointers()
    
    def Init_From_DFG(self):
        for block in self.dfg.block_dfgs:
            nodes:List[dfgn.DFG_Node] = []
            nodes.extend(block.inner_vars.copy())
            nodes.extend(block.outer_vars.copy())
            nodes.extend(block.createdNodes.copy())

            for node in nodes:
                if node not in self.nodes:
                    # llvm has first block always called entry
                    # I always prepend $block_ to it
                    if node.name == "$block_entry":
                        self.first_node = node
                    if node.name == "$ret":
                        self.last_node = node
                    node.Remove_Duplicates()
                    # we don't need psuedo links anymore
                    node.psuedo_nodes.clear()
                    self.nodes.append(node)

        if self.first_node == None:
            print("error, no first node")
        if self.last_node == None:
            print("error, no last node")

        self.Connect_No_Dep_To_First_Node()

    def Connect_No_Dep_To_First_Node(self):
        """
        connects nodes that have no dependencies
        to the first node, as thats the root dependency
        """
        for node in self.nodes:
            if node == self.first_node:
                continue
            if len(node.dep_nodes) == 0:
                print("linking: " + node.name)
                self.first_node.use_nodes.append(node)
                node.dep_nodes.append(self.first_node)
                self.linked_to_first.append(node)

    def Make_Graph(self):
        self.graph = nx.DiGraph()
        for node in self.nodes:
            if node in self.linked_to_first:
                continue
            for use in node.use_nodes:
                if use in self.linked_to_first:
                    continue
                self.graph.add_edge(node.name[1:], use.name[1:])
            for dep in node.dep_nodes:
                if dep in self.linked_to_first:
                    continue
                self.graph.add_edge(dep.name[1:], node.name[1:])
    
    def Show_Graph(self):
        self.Make_Graph()

        color_array = []
        for node in self.graph.nodes:
            if "macc" in node:
                color_array.append((1,0,0))
            elif "vle" in node:
                color_array.append((0,1,0))
            elif "block" in node:
                color_array.append((0,0,1))
            elif "bne" in node:
                color_array.append((1,1,0))
            else:
                color_array.append((0,1,1))
        plt.title("RiscV gcn dfg")

        pos = graphviz_layout(self.graph, prog='dot')
        nx.draw(self.graph, pos, with_labels=True, font_size=6, node_color=color_array)
        plt.show()

    def Remove_WorkNode_Links(self):
        """
        probably a better name but, this removes the 
        block_node -> bne_node links if there is a 
        worknode (ie vle or macc) between the two nodes
        """
        for node in self.nodes:
            if node.is_block == False:
                continue
            removeBne = False
            for use in node.use_nodes:
                if use.is_macc or use.is_vle:
                    removeBne = True
            if removeBne:
                for use in node.use_nodes.copy():
                    if use.is_bne:
                        use.dep_nodes.remove(node)
                        node.use_nodes.remove(use)

    def Remove_Empty_Blocks(self):
        """
        removes blocks that do no work.
        basically, any block_nodes that are linked
        directly to a bne node.  This would mean
        that they don't actually do anything.  Keep
        the bne node for now tho.  Will have another
        function remove those later.
        """
        for node in self.nodes.copy():
            if node.is_block == False:
                continue
            #want to keep the first one
            if node == self.first_node:
                continue
            if len(node.use_nodes) > 1:
                print("For now, shouldn't have more than 1 use")
                continue
            if node.num_iters > 1:
                continue
            if node.use_nodes[0].is_bne:
                # to remove the block, we move all the 
                # dep.use pointers to our use pointer, then 
                # delete the links
                for dep in node.dep_nodes.copy():
                    dep.use_nodes.remove(node)
                    node.dep_nodes.remove(dep)
                    dep.use_nodes.append(node.use_nodes[0])
                    node.use_nodes[0].dep_nodes.append(dep)
                node.use_nodes[0].dep_nodes.remove(node)
                node.use_nodes.remove(node.use_nodes[0])
                assert(len(node.use_nodes) == 0)
                self.nodes.remove(node)

    def Remove_Pass_Through_Bne(self):
        """
        Removes bne nodes where it just passes through
        to the next bne node
        """
        removedNode = True
        while removedNode:
            removedNode = False
            for node in self.nodes.copy():
                if node.is_bne == False:
                    continue
                if len(node.use_nodes) > 1:
                    continue
                #if node.use_nodes[0].is_bne:
                if len(node.use_nodes) == 1:
                    # to remove the block, we move all the 
                    # dep.use pointers to our use pointer, then 
                    # delete the links
                    removedNode = True
                    for dep in node.dep_nodes.copy():
                        dep.use_nodes.remove(node)
                        node.dep_nodes.remove(dep)
                        dep.use_nodes.append(node.use_nodes[0])
                        node.use_nodes[0].dep_nodes.append(dep)
                    node.use_nodes[0].dep_nodes.remove(node)
                    node.use_nodes.remove(node.use_nodes[0])
                    assert(len(node.use_nodes) == 0)
                    self.nodes.remove(node)

    def Get_Execution_Order_List(self):
        """
        Gets a list of nodes in an order that could be
        serially executed
        """
        listNodes:List[dfgn.DFG_Node] = []
        nodeQueue:List[dfgn.DFG_Node] = []
        listNodes.append(self.first_node)
        nodeQueue.extend(self.first_node.use_nodes.copy())
        
        while len(nodeQueue) > 0:
            node = Pop_Availible_Node(nodeQueue, listNodes)
            if node == None:
                print("Error, didn't find good node")
                break
            listNodes.append(node)
            for aNode in node.use_nodes:
                if aNode not in listNodes and aNode not in nodeQueue:
                    nodeQueue.append(aNode)
        # These are likely just pointers, not actual nodes in the list
        for node in self.linked_to_first:
            listNodes.remove(node)
        return listNodes

    def Remove_Useless_Loops(self):
        """
        Removes a final loop/block-bne pair if it only
        has 1 repetition.  vector.body in gcn3.ll
        """
        removedLoop = True
        while removedLoop == True:
            removedLoop = False
            # first find a terminal loop
            endNode:sdfgn.Bne_Node = None
            isTerminal = False
            startNode:sdfgn.Block_Node = None
            for node in self.nodes:
                isTerminal = False
                endNode = None
                if node.is_block == False:
                    continue
                (isTerminal, endNode) = node.Is_Terminal_Loop()
                if isTerminal:
                    print("\t" + node.name + " is terminal")
                if isTerminal and node.num_iters == 1:
                    startNode = node
                    break
            if startNode == None:
                continue
            print("removing: " + startNode.name)
            removedLoop = True
            # unlink these nodes from each other
            startNode.dep_nodes.remove(endNode)
            endNode.use_nodes.remove(startNode)
            # possible that these are bad assertions to make
            # but the logic is much simpler if I assume they 
            # only had 1 other entry/exit point.  
            assert(len(endNode.use_nodes) == 1)
            assert(len(startNode.dep_nodes) == 1)

            for use in startNode.use_nodes.copy():
                startNode.dep_nodes[0].use_nodes.append(use)
                use.dep_nodes.append(startNode.dep_nodes[0])
                use.dep_nodes.remove(startNode)
                startNode.use_nodes.remove(use)
            for dep in startNode.dep_nodes.copy():
                startNode.dep_nodes.remove(dep)
                dep.use_nodes.remove(startNode)
            self.nodes.remove(startNode)

            for dep in endNode.dep_nodes.copy():
                endNode.use_nodes[0].dep_nodes.append(dep)
                dep.use_nodes.append(endNode.use_nodes[0])
                dep.use_nodes.remove(endNode)
                endNode.dep_nodes.remove(dep)
            for use in endNode.use_nodes.copy():
                endNode.use_nodes.remove(use)
                use.dep_nodes.remove(endNode)
            self.nodes.remove(endNode)

    def Remove_Macc_Unroll_Nodes(self, maccNode:sdfgn.Macc_Node):
        """
        Since the macc must be unrolled, this will remove the
        node that the vsetlvi handles, and the node that gets 
        unrolled
        """
        maccNodeBlock = maccNode.Get_Block_Node_1()
        maccNodeBne = maccNode.Get_Bne_Node_1()

        outerBlock:dfgn.DFG_Node = maccNodeBlock.Get_Block_Node_1()
        outerBne:dfgn.DFG_Node = maccNodeBne.Get_Bne_Node_1()
        # for now, assume macc gets its own loop, can fix the 
        # more complicated logic if this isn't true later
        assert(len(maccNodeBlock.use_nodes) == 1)
        assert(len(outerBlock.use_nodes) == 1)
        assert(len(maccNodeBne.dep_nodes) == 1)
        assert(len(outerBne.dep_nodes) == 1)
            
        self.nodes.remove(maccNodeBlock)
        self.nodes.remove(outerBlock)
        self.nodes.remove(maccNodeBne)
        self.nodes.remove(outerBne)

        maccNodeBlock.use_nodes.remove(maccNode)
        maccNodeBne.dep_nodes.remove(maccNode)
        maccNode.dep_nodes.remove(maccNodeBlock)
        maccNode.use_nodes.remove(maccNodeBne)

        for dep in outerBlock.dep_nodes.copy():
            if dep == outerBne:
                continue
            assert(dep != maccNode)
            maccNode.dep_nodes.append(dep)
            outerBlock.dep_nodes.remove(dep)

            dep.use_nodes.append(maccNode)
            dep.use_nodes.remove(outerBlock)

        for use in outerBne.use_nodes.copy():
            if use == outerBlock:
                continue
            assert(use != maccNode)
            maccNode.use_nodes.append(use)
            outerBne.use_nodes.remove(use)

            use.dep_nodes.append(maccNode)
            use.dep_nodes.remove(outerBne)

        outerBlock.Remove_All_Use_And_Dep()
        outerBne.Remove_All_Use_And_Dep()
        maccNodeBlock.Remove_All_Use_And_Dep()
        maccNodeBne.Remove_All_Use_And_Dep()

        assert(len(outerBlock.use_nodes) == 0)
        assert(len(outerBlock.dep_nodes) == 0)
        assert(len(outerBne.dep_nodes) == 0)
        assert(len(outerBne.use_nodes) == 0)
        assert(len(maccNodeBlock.use_nodes) == 0)
        assert(len(maccNodeBlock.dep_nodes) == 0)
        assert(len(maccNodeBne.use_nodes) == 0)
        assert(len(maccNodeBne.dep_nodes) == 0)

    def Get_Macc(self, excludeList:List[dfgn.DFG_Node] = []):
        """
        returns the first macc node it finds
        """
        retNode:dfgn.DFG_Node = None
        for node in self.nodes:
            if node in excludeList:
                continue
            if node.is_macc:
                retNode = node
                break
        return retNode

    def Remove_All_Macc_Unrolls(self):
        foundMaccs = []
        maccNode = self.Get_Macc(foundMaccs)
        while (maccNode != None):
            foundMaccs.append(maccNode)
            self.Remove_Macc_Unroll_Nodes(maccNode)
            maccNode = self.Get_Macc(foundMaccs)

    def Remove_Unused_Targets(self):
        """
        Removes blocks that don't get branched to
        """
        for node in self.nodes:
            if node.is_block:
                if len(node.dep_nodes) == 1:
                    print("removing: **" + node.name)
                    depNode = node.dep_nodes[0]
                    for use in node.use_nodes.copy():
                        use.dep_nodes.append(depNode)
                        depNode.use_nodes.append(use)
                    node.Remove_All_Use_And_Dep()
    
    def Get_And_Use_IntReg(self):
        """
        Currently no way to free a register, honestly just
        gunna hope programs aren't complicated enough to need
        it for now lol
        """
        assert(self.openRegs[0] == False)
        for idx, reg in enumerate(self.openRegs):
            if reg == True:
                self.openRegs[idx] = False
                return self.intRegs[idx]

    def Fill_Out_IterNames(self):
        for node in self.nodes:
            if node.is_block:
                regName = self.Get_And_Use_IntReg()
                node.Get_IterName(regName)

    def Add_Load_Pointers(self):
        for node in self.nodes:
            if node.is_vle:
                node.Add_Load_Pointer_Inc(self)

    def Get_ASM_String(self):
        """
        The function to finally put it all together
        Returns the ASM string
        """
        orderNodes = self.Get_Execution_Order_List()
        asmString = ""
        immInitStr = ""
        for node in orderNodes:
            instrStr = ""
            immStr = ""
            if (node.is_vle or node.is_macc):
                instrStr = (node.Get_vsetivli())
                (instrStr, immStr) = self.Replace_Immediates(instrStr)
                asmString += instrStr + "\n"
                immInitStr += immStr
            instrStr = (node.Get_RiscV_Instr())
            (instrStr, immStr) = self.Replace_Immediates(instrStr)
            asmString += instrStr + "\n"
            immInitStr += immStr
        asmString += "\nwfi\n"
        return immInitStr + asmString

    def Replace_Immediates(self, instrStr:str):
        """
        replaces the immediate value in the string, and returns
        the proper immediate string
        """
        immInitInstr = ""
        if "!" in instrStr:
            # the ! surround immediate values
            assert(instrStr.count("!") == 2)
            firstIdx = instrStr.find("!")
            secondIdx = instrStr.find("!", firstIdx + 1)
            immVal = int(instrStr[firstIdx+1:secondIdx])
            immReg = self.Get_And_Use_IntReg()
            immInitInstr = self.Get_Immediate_Init_Instr(immVal, immReg)
            firstHalf = instrStr[0:firstIdx-1]
            secondHalf = instrStr[secondIdx+1:]
            instrStr = firstHalf + immReg + secondHalf
        return (instrStr, immInitInstr)

    def Get_Immediate_Init_Instr(self, immVal:int, immReg:str):
        """
        returns the string initializing an immediate
        """
        return "addi " + immReg + ", x0, " + hex(immVal) + "\n"


def Pop_Availible_Node(popList:List[dfgn.DFG_Node], depList:List[dfgn.DFG_Node]):
    """
    pops a node from the popList only if all of its deps are found
    in the depList
    """
    popNode = None
    for node in popList:
        foundDeps = True
        for dep in node.dep_nodes:
            if dep not in depList:
                foundDeps = False
        # if we are a block then we only need 
        # one of our dependencies
        if node.is_block:
            for dep in node.dep_nodes:
                if dep in depList:
                    foundDeps = True
        if foundDeps == True:
            popList.remove(node)
            popNode = node
            break
    return popNode
