import warnings
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node2 as dfgn
import Block_DFG2 as b_dfg
import SDFG_Node2 as sdfgn
import networkx as nx
import matplotlib.pyplot as plt
from matplotlib import lines
from networkx.drawing.nx_agraph import graphviz_layout


"""
First DFG was kinda gross and hacky to get working, redoing it
"""

class DFG:
    """
    attempt 2
    """
    parsedFile:pf.Parsed_File
    nodes:"list[dfgn.DFG_Node]"
    globalNodes:"list[dfgn.DFG_Node]"
    phiNodes:"list[sdfgn.Phi_Node]"
    branchNodes:"list[dfgn.DFG_Node]"
    blockDFGs:"list[b_dfg.Block_DFG]"
    graph:"nx.DiGraph"

    def __init__(self, fileName, do_init=True):
        self.parsedFile     = pf.Parsed_File(fileName)
        self.blockDFGs      = []
        self.nodes          = []
        self.globalNodes     = []
        self.phiNodes       = []
        self.branchNodes    = []
        if (do_init):
            self.Init_DFG()

    def Init_DFG(self):
        self.Init_Block_DFG_List()
        self.Init_All_Variables()
        self.Link_Nodes()
        self.Create_Block_DFGs()
        return

    def Do_Static_Analysis(self):
        self.Init_Macc()
        self.Init_Vle()


        return

    def Init_Block_DFG_List(self):
        for b_idx in range(len(self.parsedFile.blocks)):
            block = self.parsedFile.Get_Order_Idx(b_idx)
            block_dfg = b_dfg.Block_DFG(self, block)
            self.blockDFGs.append(block_dfg)

    def Init_All_Variables(self):
        """
        Finds all the variables in the file
        """
        # first get the globals
        self.Init_Global_Variables()
        for bIdx in range(len(self.parsedFile.blocks)):
            block = self.parsedFile.Get_Order_Idx(bIdx)
            ordIdx = block.block_order
            blockDfg = self.blockDFGs[ordIdx]
            for instr in block.instructions:
                if instr.args == None:
                    continue
                if (instr.args.result != "DEFAULT" or instr.args.instr == "ret"):
                    # if the variable isn't in the list yet
                    if self.Get_Node_By_Name(instr.args.result) == None:
                        node = None
                        if (instr.args.instr == "phi"):
                            node = sdfgn.Phi_Node(blockDfg, instr)
                            self.phiNodes.append(node)
                        else:
                            node = dfgn.DFG_Node(blockDfg, instr)
                        assert(instr.block_offset != -1)
                        node.assignment = (ordIdx, instr.block_offset)
                        self.nodes.append(node)
                    else:
                        # will be a call (memset/memcpy) or store
                        assert(instr.args.instr in ["call", "store"])
                        nodeName:str = None
                        if instr.args.instr == "store":
                            nodeName = "$store_" + instr.args.result
                        else:
                            if instr.args.function == "@llvm.memcpy.p0i8.p0i8.i64":
                                nodeName = "$memcpy_" + instr.args.result
                            elif instr.args.function == "@llvm.memset.p0i8.i64":
                                nodeName = "$memset_" + instr.args.result
                            else:
                                assert(False)
                        if (self.Get_Node_By_Name(nodeName) != None):
                            warnings.warn("Error, node already has this name\
                                            MUST MODIFY CODE")
                        newNode = dfgn.DFG_Node(blockDfg, instr)
                        newNode.name = nodeName
                        newNode.assignment = (ordIdx, instr.block_offset)
                        self.nodes.append(newNode)
                elif (instr.args.instr == "br"):
                    node = dfgn.DFG_Node(blockDfg, instr)
                    node.name = "%" + block.name
                    node.assignment = (ordIdx, instr.block_offset)
                    self.branchNodes.append(node)
                    self.nodes.append(node)
        return

    def Get_Node_By_Name(self, name:str):
        """
        Gets a node by its name from nodes,
        returns None if the node doesn't exist
        """
        retNode = None
        for node in self.nodes:
            if node.name == name:
                assert(retNode == None)
                retNode = node
        return retNode

    def Init_Global_Variables(self):
        """
        Easier to just handle the global variables seperately
        """
        for instr in self.parsedFile.Instructions:
            if(instr.args == None):
                continue
            if(instr.args.result[0] == '@'):
                assert(self.Get_Node_By_Name(instr.args.result) == None)
                node = dfgn.DFG_Node(None, instr)
                node.assignment = (-1, instr.instr_num) # -1 to indicate that it is a global variable
                self.nodes.append(node)
                self.globalNodes.append(node)
        return

    def Link_Nodes(self):
        """
        Goes through all nodes and links them to each other, creating the dfg
        """
        searchedNodes:"list[dfgn.DFG_Node]" = []
        for node in self.nodes:
            assert(node not in searchedNodes)
            searchedNodes.append(node)
            if node.instruction.args == None:
                warnings.warn("don't think this should happen")
                continue
            for dep in node.instruction.args.vars_used:
                depNode = self.Get_Node_By_Name(dep)
                if depNode == None:
                    # MUST be an immediate
                    assert(dep.isnumeric())
                    node.immediates.append(int(dep))
                else:
                    if depNode != node:
                        if node.Check_Connected(depNode) == True:
                            assert(depNode.Get_Type() == "phi" or node.Get_Type() == "phi")
                            assert(depNode in searchedNodes)
                            node.Add_Dep(depNode)
                        else:
                            node.Add_Dep(depNode)
                            assert(node in depNode.Get_Uses())
                            assert(depNode in node.Get_Deps())
        self.Link_Branch_To_Phi()
        return

    def Link_Branch_To_Phi(self):
        """
        does what it says.
        """
        for brNode in self.branchNodes:
            for phiNode in self.phiNodes:
                if brNode.name in phiNode.instruction.args.pred_names:
                    brNode.Add_Use(phiNode)
                    assert(phiNode in brNode.Get_Uses())
                    assert(brNode in phiNode.Get_Deps())
            # at least 1 use, no more than 2
            assert(len(brNode.Get_Uses()) > 0 and len(brNode.Get_Uses()) <= 2)
        return

    def Create_Block_DFGs(self):
        """
        creates smaller dfgs of basic blocks (ie no looping)
        """
        for block in self.blockDFGs:
            block.Init_Block_1()

        for block in self.blockDFGs:
            block.Init_Block_2()

        for block in self.blockDFGs:
            block.Init_Block_3()

    def Make_Graph(self, showImm=True):
        """
        Makes a networkX graph
        """
        self.graph = nx.DiGraph()
        imm_num = 0
        for node in self.Get_All_Nodes():
            for use in node.Get_Uses():
                if node in self.branchNodes:
                    suffix1 = "_b"
                else:
                    suffix1 = "_v"
                if use in self.branchNodes:
                    suffix2 = "_b"
                else:
                    suffix2 = "_v"
                self.graph.add_edge(node.name[1:] + suffix1 ,use.name[1:] + suffix2)
            if (showImm):
                for imm in node.immediates:
                    self.graph.add_edge(str(imm) + "_i" + str(imm_num),node.name[1:] + "_v")
                    imm_num += 1

    def Show_Graph(self):
        color_array = []
        self.Make_Graph()

        for node in self.graph.nodes:
            if("_s" in node):
                color_array.append((0,1,1))
            elif(("_b" in node)):
                color_array.append((.75, .25, .75))
            elif("$" + node[:-2] in [var.name for var in self.nodes]):
                color_array.append((.25, 1, .5))
            elif(("%" + node[:-2]) in [var.name for var in self.nodes]):
                color_array.append((0,1,0))
            elif("@" + node[:-2] in [var.name for var in self.nodes]):
                color_array.append((1,.25,1))
            elif("_i" in node):
                color_array.append((1,0,0))
            else:
                color_array.append((1, 1, 0))
        plt.title("DFG")

        no_uses = lines.Line2D([], [], color=(0,1,1), marker='o', markersize=10, label='no use (call, br, store)')
        branch = lines.Line2D([],[], color = (.75,.25,.75), marker = 'o', markersize=10, label = "branch node")
        def_in = lines.Line2D([], [], color=(0,1,0), marker='o', markersize=10, label='defined inside')
        def_out = lines.Line2D([], [], color=(0,0,1), marker='o', markersize=10, label='defined outside')
        def_glob = lines.Line2D([], [], color=(1,.25,1), marker='o', markersize=10, label='defined globally')
        imm = lines.Line2D([], [], color=(1,0,0), marker='o', markersize=10, label='immediate')
        use_out = lines.Line2D([], [], color=(1,1,0), marker='o', markersize=10, label='used outside')

        plt.legend(handles=[no_uses, branch, def_in, def_out, def_glob,imm, use_out], bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure)

        pos = graphviz_layout(self.graph, prog='dot')

        nx.draw(self.graph, pos, with_labels=True, font_size=6, node_color=color_array)
        plt.show()

    def Remove_Node(self, node:dfgn.DFG_Node):
        """
        removes a node from all blocks and dfg lists.
        Doesn't remove the node from any dependency or use lists
        """
        assert(node in self.nodes)
        self.nodes.remove(node)
        if node in self.globalNodes:
            self.globalNodes.remove(node)
        if node in self.branchNodes:
            self.branchNodes.remove(node)
        if node in self.phiNodes:
            self.phiNodes.remove(node)
        for block in self.blockDFGs:
            nodeList = block.Get_All_Nodes()
            if node in nodeList:
                block.Remove_Node(node)
        return

    def Init_Macc(self):
        for block in self.blockDFGs:
            block.Create_Macc()

    def Init_Vle(self):
        for block in self.blockDFGs:
            block.Create_Vle()

    def Get_All_Nodes(self):
        """
        Gets all nodes
        """
        nodeList = []
        for block in self.blockDFGs:
            blockNodes = block.Get_All_Nodes()
            for node in blockNodes:
                if node not in nodeList:
                    nodeList.append(node)
        for node in self.globalNodes:
            if node not in nodeList:
                nodeList.append(node)
        return nodeList
