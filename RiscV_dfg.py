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
    def __init__(self, dfg):
        self.dfg:DFG.Data_Flow_Graph = dfg
        self.nodes:List[dfgn.DFG_Node] = []
        self.graph = nx.DiGraph()
        
        self.Init_From_DFG()

    def Init_From_DFG(self):
        for block in self.dfg.block_dfgs:
            nodes:List[dfgn.DFG_Node] = []
            nodes.extend(block.inner_vars.copy())
            nodes.extend(block.outer_vars.copy())
            nodes.extend(block.createdNodes.copy())

            for node in nodes:
                if node not in self.nodes:
                    node.Remove_Duplicates()
                    self.nodes.append(node)

    def Make_Graph(self):
        self.graph = nx.DiGraph()
        for node in self.nodes:
            for use in node.use_nodes:
                self.graph.add_edge(node.name[1:], use.name[1:])
            for dep in node.dep_nodes:
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
            if len(node.use_nodes) > 1:
                print("For now, shouldn't have more than 1 use")
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