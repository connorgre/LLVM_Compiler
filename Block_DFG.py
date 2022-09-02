from ast import Delete
from typing import List

from matplotlib import lines

import DFG_Node as dfgn
import Instruction_Block as ib
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import Special_Nodes as sdfgn

class Block_DFG:
    def __init__(self, block:ib.Instruction_Block):
        self.block:ib.Instruction_Block = block
        self.block_num:int = block.block_order          #block number this dfg corresponds to
        self.outer_vars:List[dfgn.DFG_Node] = []    #variables that are used which have been assigned outside this block
        self.inner_vars:List[dfgn.DFG_Node] = []    #variables assigned in this block
        self.graph = nx.DiGraph()

        self.num_iters = -1                             #number of iterations block will run for
        self.self_iters = -1
        self.vector_len = -1
        self.initial_val = -1
        self.stride = -1

        self.is_macc = False
        self.phi_node:sdfgn.Phi_Node = None
        self.exit_node:dfgn.DFG_Node = None

        self.createdNodes:List[dfgn.DFG_Node] = []

        self.block_node:sdfgn.Block_Node = sdfgn.Block_Node()
        self.block_node.name = "$block_" + self.block.name

        self.bne_node:sdfgn.Bne_Node = sdfgn.Bne_Node()

        # forcibly link these two together for now
        self.bne_node.dep_nodes.append(self.block_node)
        self.block_node.use_nodes.append(self.bne_node)

        self.createdNodes.append(self.bne_node)
        self.createdNodes.append(self.block_node)

    def Get_Inner_Vars(self, dfg):
        """
        Get the variables that are assigned within the block
        """
        for var in dfg.variables:
            if var.assignment[0] == self.block_num:
                if var not in self.inner_vars:
                    self.inner_vars.append(var)
                if(var.instruction.args.instr in ['br', 'ret']):
                    self.exit_node = var
                if(var.is_phi):
                    self.phi_node = var
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
                if var == self.exit_node:
                    continue
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

    def Make_Graph_2(self, dfg, show_imm=True):
        """
        Uses node pointer lists of the inner vars rather than the location 
        pointers
        """
        blockNodes = self.outer_vars.copy()
        blockNodes.extend(self.inner_vars.copy())
        blockNodes.extend(self.createdNodes.copy())
        self.graph = nx.DiGraph()
        imm_num = 0
        for node in blockNodes:
            for use in node.use_nodes:
                if(node in self.outer_vars and use not in self.inner_vars):
                    continue
                if(node in dfg.branch_variables):
                    suffix_1 = "_b"
                else:
                    suffix_1 = "_v"
                if(use in dfg.branch_variables):
                    suffix_2 = "_b"
                else:
                    suffix_2 = "_v"
                self.graph.add_edge(node.name[1:] + suffix_1 ,use.name[1:] + suffix_2)

            if node in self.outer_vars:
                #only do the dep list for inner nodes
                continue
            for dep in node.dep_nodes:
                if(dep in dfg.branch_variables):
                    suffix_1 = "_b"
                else:
                    suffix_1 = "_v"
                if(node in dfg.branch_variables):
                    suffix_2 = "_b"
                else:
                    suffix_2 = "_v"
                self.graph.add_edge(dep.name[1:] + suffix_1 ,node.name[1:] + suffix_2)
            if(show_imm):
                for imm in node.immediates:
                    self.graph.add_edge(str(imm) + "_i" + str(imm_num),node.name[1:] + "_v")
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
            elif("$" + node[:-2] in [var.name for var in self.createdNodes]):
                color_array.append((.25, 1, .5))
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
        plt.title(self.block.name + " : " + str(self.block_num) + " : " + str(self.self_iters) + " : " + str(self.stride))

        no_uses = lines.Line2D([], [], color=(0,1,1), marker='o', markersize=10, label='no use (call, br, store)')
        branch = lines.Line2D([],[], color = (.75,.25,.75), marker = 'o', markersize=10, label = "branch node")
        def_in = lines.Line2D([], [], color=(0,1,0), marker='o', markersize=10, label='defined inside')
        def_out = lines.Line2D([], [], color=(0,0,1), marker='o', markersize=10, label='defined outside')
        def_glob = lines.Line2D([], [], color=(1,.25,1), marker='o', markersize=10, label='defined globally')
        imm = lines.Line2D([], [], color=(1,0,0), marker='o', markersize=10, label='immediate')
        use_out = lines.Line2D([], [], color=(1,1,0), marker='o', markersize=10, label='used outside')
        
        plt.legend(handles=[no_uses, branch, def_in, def_out, def_glob,imm, use_out], bbox_to_anchor=(1, 1), bbox_transform=plt.gcf().transFigure)

        pos = graphviz_layout(self.graph, prog='dot')

        # this is here bc the layout has the node for
        # 12 on a line and it makes it hard to 
        # tell whats going on, so scoot it over a bit
        # no functional difference if this is taken out
        if "12_v" in pos:
            val = pos["12_v"]
            newx = 1.05 * val[0]
            newVal = (newx, val[1])
            pos["12_v"] = newVal

        nx.draw(self.graph, pos, with_labels=True, font_size=6, node_color=color_array)
        plt.show()


    # this function does make a few assumptions about teh
    # structure of loops, and the dataflow in assigning and 
    # incrementing the loop indices.  This should
    # work for simple loops where very little transformation is done
    # on the loop counter
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
        # only get self_iters if we're an entry block
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

        exit_node:dfgn.DFG_Node = exit_dfg_block.exit_node
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
                self.initial_val = initial_val

        nodePath:List[dfgn.DFG_Node] = []
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
        compareNode:dfgn.DFG_Node = dfg.Get_Node_By_Name(compareVar)

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

        self.Get_Vector_Len()

        #put it all together now
        self.self_iters = abs((int((loop_limit - initial_val)/increment_val)) // self.vector_len)

    def Get_Vector_Len(self):
        """
        Gets the length of the vectors used within the block
        """
        for var in self.inner_vars:
            if var.instruction == None:
                continue
            res_type = var.instruction.args.result_type
            if res_type == None:
                continue
            if res_type.is_vector == False:
                continue
            if int(self.vector_len) != -1 and int(res_type.width) != int(self.vector_len):
                print("Error, multiple vector lengths in the loop")
            self.vector_len = int(res_type.width)

    def Identify_Macc(self, dfg):
        """
        This identifies the mutliply accumulate function dataflow pattern
        Right now it requires the llvm to compile down to a fmuladd, but 
        if the clang compiler that gets used doesn't support that, then I 
        can add in support for a multiply then add instruction
        """
        self.Get_Vector_Len()

        #first, identify if fmuladd is in block
        fma_node:dfgn.DFG_Node = None
        foundMacc = False
        for node in self.inner_vars:
            if node.instruction == None:
                continue
            if node.instruction.args.instr == "fmuladd":
                self.is_macc = True
                fma_node = node
                foundMacc = True
        if foundMacc == False:
            return

        #now get the nodes of the operands
        mul1_var = fma_node.instruction.args.mul1
        mul2_var = fma_node.instruction.args.mul2
        add_var = fma_node.instruction.args.add
        res_var = fma_node.instruction.args.result

        mul1_node:dfgn.DFG_Node = dfg.Get_Node_By_Name(mul1_var)
        mul2_node:dfgn.DFG_Node = dfg.Get_Node_By_Name(mul2_var)
        add_node:dfgn.DFG_Node = dfg.Get_Node_By_Name(add_var)
        res_node:dfgn.DFG_Node = dfg.Get_Node_By_Name(res_var)
        
        if(res_node != fma_node):
            print("res node != fma node (very odd error to have)")

        res_store_node:dfgn.DFG_Node = None
        res_ptr_node:dfgn.DFG_Node = None
        (res_ptr_node, res_store_node) = dfg.Get_Store_Node(res_node)

        addPtrInfo = add_node.Get_Pointer_Info(dfg)
        mul1PtrInfo = mul1_node.Get_Pointer_Info(dfg)
        mul2PtrInfo = mul2_node.Get_Pointer_Info(dfg)

        if res_ptr_node.instruction.args.pointer != addPtrInfo[0].name:
            print("Error, not a macc (store != add node)")
            print("res_store: " + res_ptr_node.name)
            print("add_node: " + dfg.Get_Pointer_Node(add_node).name)

        macc = sdfgn.Macc_Node()

        macc.accPtr = addPtrInfo[0]
        macc.mul1Ptr = mul1PtrInfo[0]
        macc.mul2Ptr = mul2PtrInfo[0]

        (macc.accStride, macc.accStrideDepth) = addPtrInfo[1].Get_Full_Stride()
        macc.accIdxInitVal = addPtrInfo[1].Get_Initial_Val()

        (macc.mul1Stride, macc.mul1StrideDepth) = mul1PtrInfo[1].Get_Full_Stride()
        macc.mul1IdxInitVal = mul1PtrInfo[1].Get_Initial_Val()

        (macc.mul2Stride, macc.mul2StrideDepth) = mul2PtrInfo[1].Get_Full_Stride()
        macc.mul2IdxInitVal = mul2PtrInfo[1].Get_Initial_Val()

        macc.numLoopRuns = self.Get_Iter_List(dfg)

        # now make sure the macc is dependent on this loop
        macc.dep_nodes.append(self.block_node)
        self.block_node.use_nodes.append(macc)

        macc.use_nodes.append(self.bne_node)
        self.bne_node.dep_nodes.append(macc)

        macc.name = "$macc_" + macc.accPtr.name + "_" + macc.mul1Ptr.name + "_" + macc.mul2Ptr.name

        self.inner_vars.append(macc)
        self.createdNodes.append(macc)

        macc.Relink_Nodes(dfg, fma_node)
        self.UnLinkNode(fma_node, dfg)
        self.UnLinkNode(res_store_node, dfg)
        
        removedNode = True
        while (removedNode):
            removedNode = self.CleanupOldNodes(dfg)


    def Identify_Load_Loop(self, dfg):
        """
        Identifies the loops where we are loading data from memory into the 
        register file.  Basically, this is any loop with memset/memcpy in it, 
        which doesn't output to stream_out. This
        Should make doing the vsetivli and the vle32.v simpler.
        """
        call_node:dfgn.DFG_Node = None
        for node in self.inner_vars:
            if node.instruction != None:
                if node.instruction.args.instr == "call":
                    call_node = node
                    break
        if(call_node == None):
            return
        vleNode:sdfgn.VLE_Node = sdfgn.VLE_Node()
        self.createdNodes.append(vleNode)
        self.inner_vars.append(vleNode)

        res_name = call_node.instruction.args.result
        load_name = call_node.instruction.args.value
        load_len = call_node.instruction.args.length

        load_node:dfgn.DFG_Node = None
        res_node:dfgn.DFG_Node = None
        for node in call_node.dep_nodes:
            if node.name == load_name:
                load_node = node
            if node.name == res_name:
                res_node = node
        # res_node can't be done. Need to store this 
        # somewhere. load_node can be if were loading an 
        # immediate value
        assert(res_node != None)

        load_ptr_info = [None, None, None]
        res_ptr_info = res_node.Get_Pointer_Info(dfg)
        load_val = None
        if(load_node == None):
            try:
                load_val = int(load_name)
            except:
                print("Error, no load node, and it isn't an int")
        else:
            load_ptr_info = load_node.Get_Pointer_Info(dfg)
        vleNode.pointer_node = res_ptr_info[0]
        vleNode.load_node = load_ptr_info[0]
        vleNode.load_val = load_val
        
        if res_ptr_info[1] != None:
            (vleNode.ptr_stride, vleNode.ptr_stride_depth) = res_ptr_info[1].Get_Full_Stride()
            vleNode.init_ptr_off = res_ptr_info[1].Get_Initial_Val()
        else:
            vleNode.init_ptr_off = res_ptr_info[2]
        
        if load_ptr_info[1] != None:
            (vleNode.load_stride, vleNode.load_stride_depth) = load_ptr_info[1].Get_Full_Stride()
            vleNode.init_load_off = load_ptr_info[1].Get_Initial_Val()
        else:
            vleNode.init_load_off = load_ptr_info[2]
        
        vleNode.length = load_len

        if(vleNode.load_node == None):
            vleLoadName = str(load_val) + "i"
        else:
            vleLoadName = str(vleNode.load_node.name)
        vleNode.name = "$vle_" + vleNode.pointer_node.name + "_" + vleLoadName

        #vleNode.use_nodes = call_node.use_nodes
        #vleNode.psuedo_nodes = call_node.psuedo_nodes

        vleNode.dep_nodes.append(self.block_node)
        self.block_node.use_nodes.append(vleNode)

        vleNode.use_nodes.append(self.bne_node)
        self.bne_node.dep_nodes.append(vleNode)

        vleNode.pointer_node.use_nodes.append(vleNode)
        vleNode.dep_nodes.append(vleNode.pointer_node)
        if vleNode.load_node != None:
            vleNode.load_node.use_nodes.append(vleNode)
            vleNode.dep_nodes.append(vleNode.load_node)

        vleNode.Relink_Nodes(dfg, call_node)
        self.UnLinkNode(call_node, dfg)

        removedNode = True
        while (removedNode):
            removedNode = self.CleanupOldNodes(dfg)

    def Identify_Load_Loop_OLD_WONT_WORK(self, dfg):
        """
        Identifies the loops where we are loading data from memory into the 
        register file.  Basically, this is any loop with memset/memcpy in it, 
        which doesn't output to stream_out. This
        Should make doing the vsetivli and the vle32.v simpler.
        """
        #first identify if this block even has a memset/memcpy in it (call)
        call_node:dfgn.DFG_Node = None
        for node in self.inner_vars:
            if node.instruction != None:
                if node.instruction.args.instr == "call":
                    call_node = node
                    break
        if(call_node == None):
            return
        vleNode:sdfgn.VLE_Node = sdfgn.VLE_Node()
        self.createdNodes.append(vleNode)
        self.inner_vars.append(vleNode)

        res_name = call_node.instruction.args.result
        load_name = call_node.instruction.args.value
        load_len = call_node.instruction.args.length

        load_node:dfgn.DFG_Node = None
        res_node:dfgn.DFG_Node = None
        for node in call_node.dep_nodes:
            if node.name == load_name:
                load_node = node
            if node.name == res_name:
                res_node = node

        load_val = None
        load_offset = 0
        load_offset_node:dfgn.DFG_Node = None
        if(load_node == None):
            try:
                load_val = int(load_name)
            except:
                print("Error, no load node, and it isn't an int")
        else:
            load_node = dfg.Get_Pointer_Node(load_node)
            if(load_node.instruction.args.instr == "getelementptr"):
                load_offset = load_node.instruction.args.index_value[1]
                if(load_offset[0] in ["%", "@"]):
                    load_offset_node = dfg.Get_Node_By_Name(load_offset)
                load_node = dfg.Get_Pointer_Node(load_node)
        
        pointer_node = dfg.Get_Pointer_Node(res_node)
        pointer_offset = 0
        pointer_offset_node:dfgn.DFG_Node = None
        if(pointer_node.instruction.args.instr == "getelementptr"):
            pointer_offset = pointer_node.instruction.args.index_value[1]
            if(pointer_offset[0] in ["%", "@"]):
                pointer_offset_node = dfg.Get_Node_By_Name(pointer_offset)
            pointer_node = dfg.Get_Pointer_Node(pointer_node)
        
        vleNode.length = load_len
        vleNode.pointer_node = pointer_node
        vleNode.load_node = load_node
        vleNode.pointer_offset = pointer_offset
        vleNode.load_offset = load_offset
        vleNode.pointer_offset_node = pointer_offset_node
        vleNode.load_offset_node = load_offset_node
        vleNode.load_val = load_val

        if(load_val != None):
            vleLoadName = str(load_val)
        else:
            vleLoadName = str(load_node.name)
        vleNode.name = "$vle_" + pointer_node.name + "_" + vleLoadName
        vleNode.assignment = call_node.assignment
        vleNode.use_nodes = call_node.use_nodes
        vleNode.uses = call_node.uses
        vleNode.psuedo_uses = call_node.psuedo_uses
        vleNode.Fill_Immediates()
        vleNode.Get_Ptr_Offset_Info(dfg)

        vleNode.ReLinkOtherNodes(dfg, call_node)
        self.UnLinkNode(call_node, dfg)
        return

    def UnLinkNode(self, removeNode:dfgn.DFG_Node, dfg):
        """
        When removing a node, we want to remove all nodes that 
        only contribute to the node were doing.
        Ie if len(removeNode.dep.uses) == 1, then its only used for our node,
        so we delete it.  Do this recursively until while the node is only
        used in one one. Also remove it from our
        Variable Lists
        exceptions are the nodes that don't count towards the 'one use' rule
        """

        for dep in removeNode.dep_nodes.copy():
            if removeNode not in dep.use_nodes:
                print("Error, removeNode not in dep.use_nodes")
                print("\t" + removeNode.name + ", " + dep.name)
            
            depUseNodes = dep.use_nodes.copy()
            for psuedo in dep.psuedo_nodes:
                if psuedo in depUseNodes:
                    depUseNodes.remove(psuedo)
            
            if(len(depUseNodes) == 1):
                try:
                    dfg.block_dfgs[dep.block_num].UnLinkNode(dep, dfg)
                except:
                    print("Error with recursive unlink on: ")
                    print("\t" + dep.name)
                    print("\tblockNum: " + str(dep.block_num))
            else:
                # this is an an else block bc the recursive UnLink
                # will take care of this
                dep.use_nodes.remove(removeNode)
                removeNode.dep_nodes.remove(dep)
                if dep in removeNode.psuedo_nodes.copy():
                    dep.psuedo_nodes.remove(removeNode)
                    removeNode.psuedo_nodes.remove(dep)

        for use in removeNode.use_nodes.copy():
            if removeNode not in use.dep_nodes:
                print("Error!, removeNode should be in use.depNodes")
            else:
                use.dep_nodes.remove(removeNode)
                removeNode.use_nodes.remove(use)
                if use in removeNode.psuedo_nodes.copy():
                    use.psuedo_nodes.remove(removeNode)
                    removeNode.psuedo_nodes.remove(use)

        if(removeNode in self.inner_vars):
            self.inner_vars.remove(removeNode)
        if(removeNode in self.outer_vars):
            self.outer_vars.remove(removeNode)

    def CleanupOldNodes(self, dfg, removePhiBranch=False):
        """
        Removes all the nodes that have no uses and aren't
        'terminal' nodes, i.e. nodes that write data to
        memory.  Not super necessary, but will be useful to
        catch errors
        """
        self.Remove_Duplicate_NodeLists()
        exemptInstrs = ['store']
        nodeList = self.inner_vars.copy()
        nodeList.extend(self.outer_vars.copy())
        removedNode = False
        for node in nodeList:
            # any node with no instruction was explicitly 
            # created, so likely don't want to delete it
            if removePhiBranch == True:
                if node.is_macc or node.is_vle:
                    continue
            elif node.is_special == True:
                continue
            if node.instruction.args.instr in exemptInstrs:
                continue

            nodeUses = node.use_nodes.copy()
            for psuedo in node.psuedo_nodes:
                if psuedo in nodeUses:
                    nodeUses.remove(psuedo)

            if removePhiBranch == True:
                for use in node.use_nodes:
                    if use.is_phi:
                        nodeUses.remove(use)
            
            if len(nodeUses) == 0:
                for dep in node.dep_nodes.copy():
                    if node in dep.use_nodes:
                        removedNode = True
                        dep.use_nodes.remove(node)
                        node.dep_nodes.remove(dep)
                        if dep in node.psuedo_nodes:
                            dep.psuedo_nodes.remove(node)
                            node.psuedo_nodes.remove(dep)
                    else:
                        print("node should be in deps...")
                for psuedo in node.psuedo_nodes.copy():
                    if psuedo in node.dep_nodes:
                        psuedo.use_nodes.remove(node)
                        psuedo.psuedo_nodes.remove(node)
                        node.psuedo_nodes.remove(psuedo)
                        node.dep_nodes.remove(psuedo)
                    elif psuedo in node.use_nodes:
                        psuedo.dep_nodes.remove(node)
                        psuedo.psuedo_nodes.remove(node)
                        node.psuedo_nodes.remove(psuedo)
                        node.use_nodes.remove(psuedo)
                    else:
                        print("Error, psuedo not in normal nodes")
                        print("\t" + node.name)
                        print("\t" + psuedo.name)

                for use in node.use_nodes.copy():
                    try:
                        node.use_nodes.remove(use)
                        use.dep_nodes.remove(node)
                        if use in node.psuedo_nodes:
                            use.psuedo_nodes.remove(node)
                            node.psuedo_nodes.remove(use)
                    except:
                        print("Error removing nodes")
                if node in self.inner_vars.copy():
                    self.inner_vars.remove(node)
                if node in self.outer_vars.copy():
                    self.outer_vars.remove(node)
                if node in self.createdNodes.copy():
                    print("\t\tRemoving created node ? ")
                    self.createdNodes.remove(node)
        return removedNode
    
    def Get_Stride(self, dfg):
        """
        Gets the loop->loop change of the value assigned by phi
        """
        phiNode = self.phi_node
        if phiNode == None:
            return
        dep = phiNode.Get_Second_Val(dfg)
        stridePath:List[dfgn.DFG_Node] = []
        dfg.Get_Use_Path_Graph(phiNode, dep, stridePath)

        totalStride = 0

        for idx, node in enumerate(stridePath):
            if idx == 0:
                continue
            if stridePath[idx -1].name not in node.instruction.args.vars_used:
                print("Error, path not right")
                return
            if node.instruction.args.instr == "add":
                totalStride += int(node.immediates[0])
            elif node.instruction.args.instr == "mul":
                if totalStride == 0:
                    totalStride = 1
                totalStride *= int(node.immediates[0])
            elif node.instruction.args.instr == "shl":
                if totalStride == 0:
                    totalStride = 1
                totalStride *= (2 ** (int(node.immediates[0])))
        
        self.stride = totalStride
        phiNode.stride.append(totalStride)
        return

    def Fill_Loop_Depths(self):
        """
        It is useful for each node to know how nested it is
        """
        for node in self.inner_vars:
            node.loop_depth = self.block.loop_depth

    def Get_Iter_List(self, dfg):
        """
        gets a list of the number of iterations the loop runs for,
        usefull for macc
        """
        if self.block.loop_depth == 0:
            return [self.self_iters]

        iterList = dfg.block_dfgs[self.block_num - 1].Get_Iter_List(dfg)

        iterList.append(self.self_iters)
        return iterList

    def Fill_Block_Nums(self):
        """
        puts the block number into each node.
        """
        for node in self.inner_vars:
            node.block_num = self.block_num

    def Convert_Br_To_Bne(self, dfg):
        """
        Converts the br instruction to a bne instruction.
        This will get rid of the br and icmp instruction, 
        and replace it with a bne.
        """
        self.Fill_Block_Node_Info() #convenient spot to do this... may move later
        assert(self.exit_node != None)
        assert(self.exit_node.instruction.args.instr in ["br", "ret"])
        if self.exit_node.instruction.args.instr == "ret":
            self.bne_node.name = "$ret"
            self.bne_node.is_bne = False
            self.bne_node.is_ret = True
            return
        brNode = self.exit_node
        bneNode = self.bne_node
        bneNode.name = "$bne_" + self.block.name

        bneNode.num_iters = int(self.self_iters)
        bneNode.stride = int(self.stride)
        bneNode.init_val = int(self.initial_val)

        # find the icmp node right before this to get the
        # loop limit
        for dep in brNode.dep_nodes:
            if dep.instruction.args.instr == "icmp":
                assert(dep.instruction.args.comparison == "eq")
                assert(len(dep.immediates) == 1)
                bneNode.loop_limit = int(dep.immediates[0])
                bneNode.always_forward = False

        # now get the forward and backward targets.  I think
        # the current logic in the branch nodes
        # arent enough

        target1 = brNode.instruction.args.true_target[1:]
        target2 = brNode.instruction.args.false_target[1:]

        if bneNode.always_forward == True:
            assert(target1 == target2)
        else:
            assert(target1 != target2)

        for block in dfg.block_dfgs:
            block:Block_DFG
            if block.block.name in [target1, target2]:
                if block.block_num <= self.block_num:
                    assert(bneNode.back_target == None)
                    bneNode.back_target = block.block_node
                    bneNode.use_nodes.append(bneNode.back_target)
                    bneNode.back_target.dep_nodes.append(bneNode)
                else:
                    assert(bneNode.forward_target == None)
                    bneNode.forward_target = block.block_node
                    bneNode.use_nodes.append(bneNode.forward_target)
                    bneNode.forward_target.dep_nodes.append(bneNode)

        assert(bneNode.forward_target != None)
        if bneNode.always_forward == False:
            assert(bneNode.back_target != None)

        self.Remove_Branch(dfg)

    def Remove_Branch(self, dfg):
        """
        removes the branch instruction in this block, and the conditional 
        that it is depenedent on.  Doesn't remove the bne, just the
        original branch
        """

        self.Remove_Duplicate_NodeLists()
        branchNode = self.exit_node
        if branchNode.instruction.args.instr != "br":
            return

        for dep in branchNode.dep_nodes.copy():
            dep.use_nodes.remove(branchNode)
            branchNode.dep_nodes.remove(dep)
        for use in branchNode.use_nodes.copy():
            use.dep_nodes.remove(branchNode)
            branchNode.use_nodes.remove(use)
        for psuedo in branchNode.psuedo_nodes.copy():
                psuedo.psuedo_nodes.remove(branchNode)
                branchNode.psuedo_nodes.remove(psuedo)

        self.inner_vars.remove(branchNode)

    def Remove_Duplicate_NodeLists(self):
        """
        The code has some issues where the same thing
        can get inserted into each nodelist multiple 
        times.  Ensures each nodelist only contains
        one of each node, and that no nodelist contains
        itself
        """
        for node in self.inner_vars:
            node.Remove_Duplicates()
        for node in self.outer_vars:
            node.Remove_Duplicates()
        for node in self.createdNodes:
            node.Remove_Duplicates()

    def Fill_Block_Node_Info(self):
        self.block_node.vector_len = self.vector_len
        self.block_node.total_iters = self.num_iters
        self.block_node.num_iters = self.self_iters
        self.block_node.init_val = self.initial_val
        self.block_node.stride = self.stride