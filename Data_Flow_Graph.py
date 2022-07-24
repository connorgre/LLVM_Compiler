from typing import List, Tuple
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as dfgn
import Block_DFG as b_dfg
import Special_Nodes as sdfgn


"""
The naming may be a bit weird, because I decided halfway through that 'node' is a better
descriptor than 'variable', so they are used somewhat interchangeably
"""
class Data_Flow_Graph:
    """
    The data flow graph for the file
    """
    def __init__(self, parsed_file):
        print('dfg creation*****')
        self.variables : List[dfgn.DFG_Node] = []        #holds all variables (includes global)
        self.global_variables : List[dfgn.DFG_Node] = [] #holds only global variables
        self.branch_variables : List[dfgn.DFG_Node] = [] #holds nodes created with branch instructions
        self.phi_variables : List[dfgn.DFG_Node] = []    #holds all nodes created with phi
        self.par_file : pf.Parsed_File = parsed_file
        self.block_dfgs : List[b_dfg.Block_DFG] = []         #list of dfgs for each block
        self.Get_All_Variables()
        self.Create_Branch_Nodes()
        self.Get_Uses()
        self.Get_Dependencies()
        self.Create_Other_Nodes()
        self.Get_Immediates()
        self.Get_All_Block_DFGs()
        self.Fill_All_Node_Lists()
        self.Get_Total_Iters()
        self.Get_All_Strides()
        self.Fill_All_Loop_Depths()
        self.Fill_All_Block_Nums()
        
    def Get_All_Variables(self):
        """
        Finds all the variables in the file
        """
        #first get the global variables
        self.Get_Global_Variables()
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            ord_idx = block.block_order
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                if(instr.args.result != "DEFAULT"):
                    #if the variable is not in the list
                    if(self.Get_Var_Idx(instr.args.result) == -1):
                        if (instr.args.instr == "phi"):
                            node = sdfgn.Phi_Node(instr)
                            self.phi_variables.append(node)
                        else:
                            node = dfgn.DFG_Node(instr)
                        if(instr.block_offset == -1):
                            print("Error, block offset == -1")
                        node.assignment = (ord_idx, instr.block_offset)

                        self.variables.append(node)

    def Get_Global_Variables(self):
        """
        Easier to just handle the global variables seperately
        """
        for instr in self.par_file.Instructions:
            if(instr.args == None):
                continue
            if(instr.args.result[0] == '@'):
                #if this isnt in the variable list yet
                if(self.Get_Var_Idx(instr.args.result) == -1):
                    node = dfgn.DFG_Node(instr)
                    node.assignment = (-1, instr.instr_num) #-1 to indicate that it is a global variable
                    node.is_global = True
                    self.variables.append(node)
                    self.global_variables.append(node)

    def Create_Branch_Nodes(self):
        """
        This could have been added to Get_All_Variables, but I 
        Think breaking the function up makes more sense, and easier to 
        debug
        """
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            ord_idx = block.block_order
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                if(instr.args.instr != "br"):
                    continue
                node = dfgn.DFG_Node(instr)
                node.name = "%" + block.name
                node.assignment = ((ord_idx, instr.block_offset))
                #loop to get all the phi blocks that this branch statement targets
                for var in self.phi_variables:
                    if node.name in var.instruction.args.pred_names:
                        node.uses.append(var.assignment)
                self.branch_variables.append(node)
                self.variables.append(node)
        
    def Create_Other_Nodes(self):
        """
        Creates nodes used in store, some calls.  These need to be handled specially, since they are the only instructions
        That use variables without writing to anything.  They still need to be tracked as dependencies for the instructions though
        so we create 'fake' nodes that have no uses, but do have dependencies
        """
        num_new = 0
        for var in self.variables:
            for use in var.uses:
                block = self.par_file.Get_Order_Idx(use[0])
                instr = block.instructions[use[1]]
                use_node = self.Get_Node_Block_Offset(use)
                if(use_node == None or len(use_node.uses) == 0):
                    if(instr.args.instr not in ['call', 'store']):
                        print("Error, expected call or store, got: " + instr.args.instr + ", " + str(instr.line_num))
                        continue
                    if(use_node == None):
                        use_node = dfgn.DFG_Node(instr)
                        #num_new ensures that we get unique names
                        use_node.name = "%" + instr.args.instr + "_" + str(num_new) + "_s"
                        num_new += 1
                        use_node.assignment = use
                        self.variables.append(use_node)
                    use_node.dependencies.append(var.assignment)
                    
    def Get_Var_Idx(self, name):
        """
        Gets index of variable by name
        returns -1 if a variable with that name is not in the list
        """
        for idx in range(len(self.variables)):
            if(self.variables[idx].name == name):
                return idx
        return -1

    def Get_Node_By_Name(self, name):
        """
        Gets a node by its name
        """
        for node in self.variables:
            if node.name == name:
                return node
        return None
    
    def Get_Node_Block_Offset(self, pos:Tuple[int, int]):
        """
        returns the Node that was assigned at (block, block offset)
        """
        for node in self.variables:
            if node.assignment == pos:
                return node
        return None

    def Get_Instruction_Block_Offset(self, pos:Tuple[int, int]):
        """
        returns the instruction at ((ordered) block, offset)
        """
        #if it is assigned outside a block (ie global variable)
        if(pos[0] == -1):
            instr = self.par_file.Instructions[pos[1]]
            if(instr.args.result[0] != '@'):
                print("Error: block -1, but not global variable")
            return instr
        
        block = self.par_file.Get_Order_Idx(pos[0])
        return block.instructions[pos[1]]

    #this assumes all uses of a variable are within blocks
    #ie, no global assignments use other variables 
    def Get_Uses(self):
        """
        Get all the uses of the variables (discluding the assignment)
        If I had planned a bit better, this could maybe
        have been done in the same function as Get_All_Variables,
        but this works fine too and is simpler
        """
        for idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(idx)
            ord_idx = block.block_order
            for instr in block.instructions:
                if(instr.args == None):
                    continue
                for var in instr.args.vars_used:
                    var_idx = self.Get_Var_Idx(var)
                    if(var_idx == -1):
                        if(var[0] in ["%", "@"]):
                            print("Error, variable: " + str(var) + ", not in list of variables")
                        continue
                    var_loc = (ord_idx, instr.block_offset)
                    if(self.variables[var_idx].assignment != var_loc):
                        self.variables[var_idx].uses.append(var_loc)
    
    def Get_Dependencies(self):
        """
        Similar to Get_Uses, but goes the other direction in the graph
        Could have also been done in dependencies, but I think splitting it up makes reading/debugging 
        easier
        """
        for var in self.variables:
            for use in var.uses:
                use_var = self.Get_Node_Block_Offset(use)
                if(use_var == None):
                    if(self.Get_Instruction_Block_Offset(use).args.instr not in ["call", "br", "store"]):
                        print("Error, use_var shouldn't be None, " + str(var.name) + ", " + str(use))
                    continue
                use_var.dependencies.append(var.assignment)

    def Get_Immediates(self):
        """
        Gets immidiate values used in assignment of each variable
        This also error checks uses and dependencies
        """
        for var in self.variables:
            for used in var.instruction.args.vars_used:
                if(used[0] in ['%', '@']):
                    used_node_idx = self.Get_Var_Idx(used)
                    if(used_node_idx == -1):
                        print("Error, " + used + ", not in variables")
                        continue
                    used_node = self.variables[used_node_idx]
                    if((used_node.assignment not in var.dependencies) and (used != var.name)):
                        print("Error, " + used + ", should be in dependencies")                       
                elif(used.isnumeric() == False):
                    print("Error, " + used + ", should be a number \
                        (may cause error if its a float, just fix this error check if thats the case)")
                    print("\tVar: " + var.name + ", line: " + str(var.instruction.line_num))
                else:
                    var.immediates.append(used)

    def Get_All_Block_DFGs(self):
        """
        Gets all the basic block DFGs
        """
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            block_dfg = b_dfg.Block_DFG(block)
            block_dfg.Get_Inner_Vars(self)
            block_dfg.Get_Outer_Vars(self)
            block_dfg.Get_Vector_Len()
            self.block_dfgs.append(block_dfg)
        
        for block in self.block_dfgs:
            block.Get_Self_Iters(self)

    def Get_Use_Path(self, start:dfgn.DFG_Node, target:dfgn.DFG_Node, node_list:List[dfgn.DFG_Node], do_dep=False):
        """
        Wrapper to call Do_Use_Path_DFG, just adds the visited array

        Populates a list of the nodes on (a) path from start to target.
        There could theoretically be more paths ig, but this is mostly meant
        for loop counting.

        do_dep is true if you are searching using the dependency list 
        (backwards search)
        """
        visited = []
        self.Do_Use_Path_DFG(start, target, node_list, visited, do_dep)

    def Do_Use_Path_DFG(self, start:dfgn.DFG_Node, target:dfgn.DFG_Node, node_list:List[dfgn.DFG_Node], visited, do_dep):
        #called by Get_Use_Path
        if(start in visited):
            return False
        visited.append(start)
        node_list.append(start)
        if(start == target):
            return True
        if(do_dep == False):
            nodes = start.uses
            exclude = start.psuedo_uses
        else:
            nodes = start.dependencies
            exclude = start.psuedo_dependencies
        for use in nodes:
            if(use in exclude):
                continue
            node = self.Get_Node_Block_Offset(use)
            ret_val = self.Do_Use_Path_DFG(node, target, node_list, visited, do_dep)
            if(ret_val == True):
                return True
        node_list.pop()
        return False

    def Get_Use_Path_Graph(self, start:dfgn.DFG_Node, target:dfgn.DFG_Node, nodeList:List[dfgn.DFG_Node], visited = None, do_dep=False, findPhi=False, depth=5):
        """
        Same functionality as the above Get_Use_Path, but this uses the node pointers
        to traverse the graph, which is better than using the block references
        findPhi is true if we don't know for sure the target were searching for, but just want the first phi that assigns to this node.  If it is true, set target to false
        depth counts down to 0 to prevent the search from getting too long, initialize at a larger number to search deeper
        """
        if (depth == 0):
            return False

        if visited == None:
            visited = []

        if(start in visited):
            return False

        visited.append(start)
        nodeList.append(start)

        if(start == target):
            return True
        if((findPhi == True) and (start.is_phi == True)):
            return True

        if(do_dep == False):
            nodes = start.use_nodes
        else:
            nodes = start.dep_nodes
        exclude = start.psuedo_nodes

        for node in nodes:
            ret_val = self.Get_Use_Path_Graph(node, target, nodeList, visited, do_dep, findPhi, depth=depth-1)
            if(ret_val == True):
                return True
        nodeList.pop()
        return False

    def Get_Total_Iters(self):
        """
        Gets the total number of iterations that a for loop will do. Must have had 
        Get_Self_Iters() done on every block in the cfg (this gets done normall on __init__ tho)
        """
        prev_iters = 1
        for block in self.block_dfgs:
            if block.self_iters == -1:
                block.self_iters = 1
            
            #if we are a block that isn't a loop exit, then multiply the previous blocks iterations
            #by the number of iterations we do ourself.  If we are a self loop, then we also need to 
            #do the multiplication, even though we are technically also an exit block
            if block.block.is_loop_exit == False:
                block.num_iters = block.self_iters * prev_iters
                prev_iters = block.num_iters
            elif (block.block.is_loop_exit == True and block.block.is_loop_entry == True):
                block.num_iters = block.self_iters * prev_iters
                #dont update prev iters in this case
            else:
                entry_idx = block.block.entry_idx
                entry_order_idx = self.par_file.blocks[entry_idx].block_order
                entry_block = self.block_dfgs[entry_order_idx]
                block.num_iters = entry_block.num_iters
                prev_iters = block.num_iters
            
    def Identify_Maccs(self):
        for block in self.block_dfgs:
            block.Identify_Macc(self)

    def Fill_All_Loop_Depths(self):
        for block in self.block_dfgs:
            block.Fill_Loop_Depths()

    def Get_Pointer_Node(self, data_node:dfgn.DFG_Node, max_search_depth=5):
        """
        Gets the node where the pointer to this element was created.
        Assumes a data flow of 
            getElementPtr (or alloca) -> (optionally) bitcast -> load
        """
        ret_node:dfgn.DFG_Node = None
        for node in data_node.dep_nodes:
            if(ret_node != None):
                break
            if(node.instruction.args.instr in ["getelementptr", "alloca", "zeroinitializer"]):
                ret_node = node
            elif(len(node.dependencies) > 1):
                #if any node we find on the path has more than one dependency, then 
                #we have searched too far
                print("searched too far (definitely shouldn't happen in gcn")
                return None
            else:
                ret_node = self.Get_Pointer_Node(node, max_search_depth-1)

        return ret_node

    def Get_Store_Node(self, data_node:dfgn.DFG_Node, max_search_depth=5):
        """
        Finds the node where the address that we are storing the data in gets created.
        As in we assume data_node gets stored (could have some bitcasts), then from the 
        store instruction we find the getelementptr where we create the 
        """
        ret_node:dfgn.DFG_Node = None
        store_node:dfgn.DFG_Node = None
        for node in data_node.use_nodes:
            if(node.instruction.args.instr == "store"):
                if(store_node == None):
                    store_node = node
                else:
                    print("Error already have a store node")
        if store_node == None:
            print("Didnt find store node.  May be bc a bitcast or something")
        
        store_var_name = store_node.instruction.args.pointer
        store_pointer_node = self.Get_Node_By_Name(store_var_name)
        ret_node = self.Get_Pointer_Node(store_pointer_node, max_search_depth)

        return (ret_node, store_node)

    def Fill_All_Node_Lists(self):
        for var in self.variables:
            var.Fill_Pointer_Lists(self)

    def Identify_Load_Loops(self):
        for block in self.block_dfgs:
            block.Identify_Load_Loop(self)
        for block in self.block_dfgs:
            block.CleanupOldNodes(self)
        return

    def Get_All_Strides(self):
        for block in self.block_dfgs:
            block.Get_Stride(self)

    def Fill_All_Block_Nums(self):
        for block in self.block_dfgs:
            block.Fill_Block_Nums()

    def ReLinkNodes(self, source:dfgn.DFG_Node, dest:dfgn.DFG_Node, newDest:dfgn.DFG_Node, doBackWardSearch=False):

        """
        Changes the link from source->firstOnPath to source->newDest

        Used for converting several llvm instructions to 1 compiled 
        Instruction.  As in conversion of memcpy to vle32.v


        ***********************************************************
        ****    AFTER DOING THIS, node.uses IS NOT VALID, ONLY ****
        ****    THE node.use_nodes IS A FULLY VALID UPDATED DFG ***
        ****    ANY FUNCTIONS THAT USE THIS AFTER THIS FUNCTION ***
        ****    IS CALLED MAY BE INVALID                       ****
        ***********************************************************
        """
        
        if source == None:
            return
        nodes:List[dfgn.DFG_Node] = []
        self.Get_Use_Path(source, dest, nodes, doBackWardSearch)
        
        for idx in reversed(range(len(nodes)-1)):
            node = nodes[idx]
            nodeUses = node.use_nodes.copy()

            for ps in node.psuedo_nodes:
                if ps in nodeUses:
                    nodeUses.remove(ps)
            
            # So if this node has already been unlinked, just
            # break.  This can happen bc the search algorithm
            # doesn't use the correct links... should change 
            # that...
            if node not in nodes[idx + 1].dep_nodes:
                break

            nodes[idx+1].dep_nodes.remove(node)
            node.use_nodes.remove(nodes[idx + 1])
            for ps in node.psuedo_nodes:
                ps.psuedo_nodes.remove(node)
                node.psuedo_nodes.remove(ps)
                if node in ps.dep_nodes:
                    ps.dep_nodes.remove(node)
                    node.use_nodes.remove(ps)
                else:
                    ps.use_nodes.remove(node)
                    node.dep_nodes.remove(ps)
    
            if len(nodeUses) > 1:
                break

        source.use_nodes.append(newDest)
        newDest.dep_nodes.append(source)

        return

    def Cleanup_All_Old_Nodes(self):
        """
        potentially slow, as its worst case n^3 in the number
        of nodes, but likely will finish much quicker, and don't
        expect large dfgs
        """
        removedNode = True
        while(removedNode):
            removedNode = False
            for block in self.block_dfgs:
                thisRemove = block.CleanupOldNodes(self)
                removedNode = (thisRemove or removedNode)