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
        self.num_iters = -1                             #number of iterations block will run for
        self.self_iters = -1
        self.vector_len = -1
        self.exit_node:dfg_node.DFG_Node = None

    def Get_Inner_Vars(self, dfg):
        """
        Get the variables that are assigned within the block
        """
        for var in dfg.variables:
            if var.assignment[0] == self.block_num:
                self.inner_vars.append(var)
                if(var.instruction.args.instr in ['br', 'ret']):
                    self.exit_node = var
        self.Find_End_Nodes()

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

    #finds all the nodes that need to be completed before we can branch,
    #as in at the end of the dependency chains within the block
    def Find_End_Nodes(self):
        for var in self.inner_vars:
            end_node = True
            for use in var.uses:
                if(use[0] == self.block_num):
                    end_node = False
            if(end_node):
                var.uses.append(self.exit_node.assignment)
                var.psuedo_uses.append(self.exit_node.assignment)
                self.exit_node.dependencies.append(var.assignment)
                self.exit_node.psuedo_dependencies.append(var.assignment)

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
                    if(var in dfg.branch_variables):
                        suffix_1 = "_b"
                    else:
                        suffix_1 = "_v"
                    if(to_var in dfg.branch_variables):
                        suffix_2 = "_b"
                    else:
                        suffix_2 = "_v"
                    self.graph.add_edge(var.name[1:] + suffix_1 ,to_var.name[1:] + suffix_2)
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
            elif(("_b" in node)):
                color_array.append((.75, .25, .75))
            elif(("%" + node[:-2]) in [var.name for var in self.inner_vars]):
                color_array.append((0,1,0))
            elif("%" + node[:-2] in [var.name for var in self.outer_vars]):
                color_array.append((0,0,1))
            elif("@" + node[:-2] in [var.name for var in self.outer_vars]):
                color_array.append((1,.25,1))
            elif("_i" in node):
                color_array.append((1,0,0))
            else:
                color_array.append((1, 1, 0))
        plt.title(self.block.name + ", " + str(self.block_num))

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


    #this function does make a few assumptions about teh
    #structure of loops, and the dataflow in assigning and 
    #incrementing the loop indices.  This should
    #work for simple loops where very little transformation is done
    #on the loop counter
    def Get_Self_Iters(self, dfg):
        """
        Gets the number of iterations the block will run for.
            -   Self.self_iters = number of iterations required for the exit 
                condition of this loop
            -   Self.total_iters = number of iterations it will go for in total
        This requires the number of iterations a loop 
        will run for to be a constant. I believe this 
        is an assumption that can be made based on the gcn file. It would
        be much more complicated otherwise, and impossible if the value is 
        something read in from memory.
        """
        #only get self_iters if we're an entry block
        if(self.block.is_loop_entry == False):
            return
        if(self.block.exit_idx == -1):
            print("Error, entry block with no exit block")
            return
        exit_block:ib.Instruction_Block = dfg.par_file.blocks[self.block.exit_idx]
        if(exit_block.is_loop_exit == False):
            print("Error, what should be exit isn't...")
        exit_dfg_block:Block_DFG = dfg.block_dfgs[exit_block.block_order]
        if(exit_dfg_block.block_num != exit_block.block_order):
            print("Error, exit dfg blocknum != exit_block.order_idx")

        exit_node:dfg_node.DFG_Node = exit_dfg_block.exit_node
        entry_node = self.inner_vars[0]
        if(entry_node.instruction.args.instr != "phi"):
            print("Error, expected phi as first instruction in for loop")
        
        #get the initial value for the loop. it is 0 for 
        #gcn, but it can be any constant int
        prev_branch = None  #This is the node that branched into this one
        for var in entry_node.dependencies:
            if var[0] < self.block_num:
                prev_branch = dfg.Get_Node_Block_Offset(var)
        initial_val = -1
        for block in entry_node.instruction.args.block_list:
            if block.predecessor == prev_branch.name:
                initial_val = int(block.value)

        nodePath:List[dfg_node.DFG_Node] = []
        dfg.Get_Use_Path(entry_node, exit_node, nodePath)

        #get the variable used in the comparison, and the comparison limit
        compareVar = None
        compareImm = None
        for node in nodePath:
            if(node.instruction.args.instr == "icmp"):
                if(node.instruction.args.comparison != "eq"):
                    print("Error, expected equality comparison")
                compareVar = node.instruction.args.op1
                compareImm = node.instruction.args.op2
        loop_limit = int(compareImm)
        
        #find the value that we increment the loop by
        compareNode:dfg_node.DFG_Node = dfg.Get_Node_By_Name(compareVar)

        if compareNode == entry_node and \
            loop_limit == initial_val and \
            exit_node.instruction.args.false_target[1:] == self.block.name:
            #This is the special case where we are only looping once. 
            #for some reason llvm ir doesn't use the .next variable, but rather compares
            #the initial variable with its initial value.  This makes no sense for clang to do
            #but whatever
            self.self_iters = 1
            return

        compareNode_deps = []
        for blk_off in compareNode.dependencies:
            compareNode_deps.append(dfg.Get_Node_Block_Offset(blk_off))
        if(entry_node not in compareNode_deps):
            print("Expected simpler loop logic")
            print("\t*****Need to revisit Block_DFG.Get_Self_Iters()")
        if(len(compareNode.immediates) != 1):
            print("Expected compare node to have only 1 immediate on assignment")
        increment_val = int(compareNode.immediates[0])

        #put it all together now
        self.self_iters = int((loop_limit - initial_val)/increment_val)

    def Get_Vector_Len(self):
        """
        Gets the length of the vectors used within the block
        """
        for var in self.inner_vars:
            res_type = var.instruction.args.result_type
            if res_type == None:
                continue
            if res_type.is_vector == False:
                continue
            if int(self.vector_len) != -1 and int(res_type.width) != int(self.vector_len):
                print("Error, multiple vector lengths in the loop")
            self.vector_len = int(res_type.width)