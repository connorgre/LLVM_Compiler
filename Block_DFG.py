from typing import List

from matplotlib import lines

import DFG_Node as dfg_node
import Instruction_Block as ib
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout

class Block_DFG:
    def __init__(self, block:ib.Instruction_Block):
        self.block:ib.Instruction_Block = block
        self.block_num:int = block.block_order          #block number this dfg corresponds to
        self.outer_vars:List[dfg_node.DFG_Node] = []    #variables that are used which have been assigned outside this block
        self.inner_vars:List[dfg_node.DFG_Node] = []    #variables assigned in this block
        self.graph = nx.DiGraph()

    def Get_Inner_Vars(self, dfg):
        """
        Get the variables that are assigned within the block
        """
        for var in dfg.variables:
            if var.assignment[0] == self.block_num:
                self.inner_vars.append(var)

    def Get_Outer_Vars(self, dfg):
        """
        Get the variables assigned outside of the block
        Get_Inner_Vars() must be called first
        """
        for var in self.inner_vars:
            for dep in var.dependencies:
                if(dep[0] != self.block_num):
                    dep_var = dfg.Get_Node_Block_Offset(dep)
                    if(dep_var == None):
                        print("Error, dep_var == None")
                    self.outer_vars.append(dep_var)

    def Print_Vars(self):
        print("\n**Inner Nodes**")
        for var in self.inner_vars:
            print(var.name)
        print("\n**Outer Nodes**")
        for var in self.outer_vars:
            print(var.name)

    def Make_Graph(self, dfg, show_imm=False):
        """
        Makes a networkx graph from this block
        """
        block_vars = self.outer_vars.copy()
        block_vars.extend(self.inner_vars)
        imm_num = 0
        for var in block_vars:
            for pos in var.uses:
                to_var = dfg.Get_Node_Block_Offset(pos)
                if(to_var is not None):
                    #don't care to print assignement of variables outside block from variable outside block
                    if(var in self.outer_vars and to_var not in self.inner_vars):
                        continue
                    #use var.name[1:], because llvm variables start with %, which causes a bug
                    #in the graphviz library where it reads the % as a special character and 
                    #causes an error, so simple solution is to just ignore it for the graph
                    self.graph.add_edge(var.name[1:] + "_v",to_var.name[1:] + "_v")
            if(show_imm and var not in self.outer_vars):
                for imm in var.immediates:
                    #purpose of imm_num is to create a unique node for each immediate, makes more sense on the
                    #graph
                    self.graph.add_edge(imm + "_i" + str(imm_num),var.name[1:] + "_v")
                    imm_num += 1        

    def Show_Graph(self):
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
        color_array = []
        for node in self.graph.nodes:
            if("_s" in node):
                color_array.append((0,1,1))
            elif(("%" + node[:-2]) in [var.name for var in self.inner_vars]):
                color_array.append((0,1,0))
            elif("%" + node[:-2] in [var.name for var in self.outer_vars]):
                color_array.append((0,0,1))
            elif("@" + node[:-2] in [var.name for var in self.outer_vars]):
                color_array.append((1,0,1))
            elif("_i" in node):
                color_array.append((1,0,0))
            else:
                color_array.append((1, 1, 0))
        plt.title(self.block.name + ", " + str(self.block_num))

        no_uses = lines.Line2D([], [], color=(0,1,1), marker='o', markersize=10, label='no use (call, br, store)')
        def_in = lines.Line2D([], [], color=(0,1,0), marker='o', markersize=10, label='defined inside')
        def_out = lines.Line2D([], [], color=(0,0,1), marker='o', markersize=10, label='defined outside')
        def_glob = lines.Line2D([], [], color=(1,0,1), marker='o', markersize=10, label='defined globally')
        imm = lines.Line2D([], [], color=(1,0,0), marker='o', markersize=10, label='immediate')
        use_out = lines.Line2D([], [], color=(1,1,0), marker='o', markersize=10, label='used outside')

        plt.legend(handles=[no_uses, def_in, def_out, def_glob,imm, use_out], bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure)

        pos = graphviz_layout(self.graph, prog='dot')
        nx.draw(self.graph, pos, with_labels=True, font_size=6, node_color=color_array)
        plt.show()