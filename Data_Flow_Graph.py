from typing import List, Tuple
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node as dfg_node
import Block_DFG as b_dfg



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
        self.variables : List[dfg_node.DFG_Node] = []        #holds all variables (includes global)
        self.global_variables : List[dfg_node.DFG_Node] = [] #holds only global variables
        self.branch_variables : List[dfg_node.DFG_Node] = [] #holds nodes created with branch instructions
        self.phi_variables : List[dfg_node.DFG_Node] = []    #holds all nodes created with phi
        self.par_file : pf.Parsed_File = parsed_file
        self.block_dfgs : List[b_dfg.Block_DFG] = []         #list of dfgs for each block
        self.Get_All_Variables()
        self.Create_Branch_Nodes()
        self.Get_Uses()
        self.Get_Dependencies()
        self.Create_Other_Nodes()
        self.Get_Immediates()
        self.Get_All_Block_DFGs()
        
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
                        node = dfg_node.DFG_Node(instr)
                        if(instr.block_offset == -1):
                            print("Error, block offset == -1")
                        node.assignment = (ord_idx, instr.block_offset)
                        if(instr.args.instr == "phi"):
                            node.is_phi = True
                            self.phi_variables.append(node)
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
                    node = dfg_node.DFG_Node(instr)
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
                node = dfg_node.DFG_Node(instr)
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
                        print("Error, expected call br or store, got: " + instr.args.instr + ", " + str(instr.line_num))
                        continue
                    if(use_node == None):
                        use_node = dfg_node.DFG_Node(instr)
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


    def Get_Use_Path(self, start:dfg_node.DFG_Node, target:dfg_node.DFG_Node, node_list:List[dfg_node.DFG_Node], do_dep=False):
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

    def Do_Use_Path_DFG(self, start:dfg_node.DFG_Node, target:dfg_node.DFG_Node, node_list:List[dfg_node.DFG_Node], visited, do_dep):
        
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
            
