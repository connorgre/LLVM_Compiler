import warnings
import Instruction_Block as ib
import Parser as p
import Parse_File as pf
import DFG_Node2 as dfgn
import Block_DFG as b_dfg
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
    globalVars:"list[dfgn.DFG_Node]"
    phiNodes:"list[sdfgn.Phi_Node]"
    branchNodes:"list[dfgn.DFG_Node]"
    
    def __init__(self, fileName, do_init=True):
        self.parsedFile = pf.ParsedFile(fileName)
        if (do_init):
            self.Init_DFG()

    def Init_DFG(self):
        self.Get_All_Variables()
        return

    def Get_All_Variables(self):
        """
        Finds all the variables in the file
        """
        # first get the globals
        self.Get_Global_Variables()
        numNew = 0
        for bIdx in range(len(self.parsedFile.blocks)):
            block = self.parsedFile.Get_Order_Idx(bIdx)
            ordIdx = block.block_order
            for instr in block.instructions:
                if instr.args == None:
                    continue
                if (instr.args.result != "DEFUALT" or instr.args.instr == "ret"):
                    # if the variable isn't in the list yet
                    if self.Get_Node_By_Name(instr.args.result) != None:
                        if (instr.args.instr == "phi"):
                            node = sdfgn.Phi_Node(instr)
                            self.phiNodes.append(node)
                        else:
                            node = dfgn.DFG_Node(instr)
                        assert(instr.block_offset != -1)
                    node.assignment = (ordIdx, instr.block_offset)
                    self.nodes.append(node)
                elif (instr.args.instr in ["call", "store"]):
                    newNode = dfgn.DFG_Node(instr)
                    newNode.name = "$" + instr.args.instr + "_" + str(numNew)
                    newNode.assignment = (ordIdx, instr.block_offset)
                    numNew += 1
                    self.nodes.append(newNode)
                    warnings.warn("take prints out, j wanna make sure it works")
                    print(newNode.name)
                elif (instr.args.instr == "br"):
                    node = dfgn.DFG_Node(instr)
                    node.name = "%" + block.name
                    node.assignment = ((ordIdx, instr.block_offset))
                    self.branchNodes.append(node)
                    self.nodes.append(node)
        return

    def Get_Node_By_Name(self, name:str):
        retNode = None
        for node in self.nodes:
            if node.name == name:
                assert(retNode == None)
                retNode = node
        return retNode

    def Get_Global_Variables(self):
        """
        Easier to just handle the global variables seperately
        """
        for instr in self.par_file.Instructions:
            if(instr.args == None):
                continue
            if(instr.args.result[0] == '@'):
                # if this isnt in the variable list yet
                if(self.Get_Var_Idx(instr.args.result) == -1):
                    node = dfgn.DFG_Node(instr)
                    node.assignment = (-1, instr.instr_num) # -1 to indicate that it is a global variable
                    self.variables.append(node)
                    self.global_variables.append(node)
        return

    def Link_Nodes(self):
        """
        Goes through all nodes and links them to each other, creating the dfg
        """
        for node in self.nodes:
            if node.instruction.args == None:
                warnings.warn("don't think this should happen")
                continue
            for use in node.instruction.args.vars_used:
                useNode = self.Get_Node_By_Name(use)
                if useNode == None:
                    # it is either an immediate, or a store/call
                    assert(use.isnumeric())
                    node.immediates.append(int(use))
                else:
                    assert(useNode != node)
                    assert(node.Check_Connected(useNode) == False)
                    node.Add_Use(useNode)
                    assert(useNode in node.Get_Uses())
                    assert(node in useNode.Get_Deps())
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
        for b_idx in range(len(self.par_file.blocks)):
            block = self.par_file.Get_Order_Idx(b_idx)
            block_dfg = b_dfg.Block_DFG(block)
            block_dfg.Get_Inner_Vars(self)
            block_dfg.Get_Outer_Vars(self)
            block_dfg.Get_Vector_Len()
            self.block_dfgs.append(block_dfg)
        
        for block in self.block_dfgs:
            block.Get_Self_Iters(self)