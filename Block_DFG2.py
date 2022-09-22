from matplotlib import lines

import DFG_Node2 as dfgn
import Instruction_Block as ib
import networkx as nx
import matplotlib.pyplot as plt
from networkx.drawing.nx_agraph import graphviz_layout
import SDFG_Node2 as sdfgn

class Block_DFG:
    block:ib.Instruction_Block
    blockNum:int
    outerNodes:"list[dfgn.DFG_Node]"
    innerNodes:"list[dfgn.DFG_Node]"
    graph:nx.DiGraph

    selfIters:int
    vectorLen:int

    phiInitVal:int
    phiStride:int

    phiNode:sdfgn.Phi_Node
    exitNode:dfgn.DFG_Node

    blockNode:sdfgn.Block_Node
    bneNode:sdfgn.Bne_Node

    createdNodes:"list[dfgn.DFG_Node]"

    def __init__(self, block:ib.Instruction_Block):
        self.block = block
        self.blockNum = block.block_order          #block number this dfg corresponds to
        self.outerNodes = []    #variables that are used which have been assigned outside this block
        self.innerNodes = []    #variables assigned in this block
        self.graph = nx.DiGraph()

        self.selfIters = -1
        self.vectorL = -1
        self.phiInitVal = -1
        self.phiStride = -1

        self.phiNode = None
        self.exitNode = None

        self.createdNodes = []

        self.blockNode = sdfgn.Block_Node()
        self.blockNode.name = "$block_" + self.block.name
        self.bneNode = sdfgn.Bne_Node()
        # link these together
        self.bneNode.Add_Use(self.blockNode)

        self.createdNodes.append(self.bne_node)
        self.createdNodes.append(self.block_node)

    def Get_Inner_Nodes(self, dfg):
        """
        Get Variables assigned within block
        """
        for node in dfg.nodes:
            node:dfgn.DFG_Node
            if node.assignment[0] == self.blockNum:
                assert(node not in self.innerNodes)
                self.innerNodes.append(node)
                if node.instruction.args.instr in ['br', 'ret']:
                    self.exitNode = node
                if node.nodeType.phi:
                    self.phiNode = node
        assert(self.exitNode != None)
        self.Find_End_Nodes()
    
    def Get_Outer_Nodes(self, dfg):
        for node in self.innerNodes:
            for dep in node.Get_Deps():
                if dep.assignment[0] != self.blockNum:
                    self.outerNodes.append(dep)

    def Find_End_Nodes(self):
        """
        Gets nodes that are at end of dep chain so that we can link them to the
        exit node, to ensure dfg completes all instructions before finishing
        """
        for node in self.innerNodes:
            endNode = True
            for use in node.Get_Uses():
                if use == self.exitNode:
                    continue
                if use.assignment[0] == self.blockNum:
                    endNode = False
            if endNode:
                # add this as psuedo dependency
                self.exitNode.Add_Dep(node, True, True)

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