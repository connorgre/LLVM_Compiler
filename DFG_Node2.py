import Parser as p
from typing import List
import warnings

class DFG_Type:
    """
    helper class to handle the type of dfg it is
    """
    special:bool
    ret:bool
    phi:bool
    def __init__(self):
        """
        init all to false
        """
        self.special = False
        self.ret = False

    def Get_Type_Str(self):
        retStr = None
        if self.special == False:
            retStr = "Normal"
        elif self.ret:
            retStr = "ret"
        elif self.phi:
            retStr = "phi"
        else:
            # if we aren't special we need one of the specified types
            assert(False) 
        return retStr

class DFG_Node:
    """
    Re-doing the dfg node
    """
    nodeType:DFG_Type
    name:str
    instruction:p.Instruction
    assignment:tuple(int,int)
    useNodes:"list[DFG_Node]"
    depNodes:"list[DFG_Node]"
    psuNodes:"list[DFG_Node]"       #psu = psuedo, not a true dependency but useful info
    immediates:"list[int]"
    stride:"list[int]"
    numIters:"list[int]"
    riscVString:str
    vsetivliString:str

    def __init__(self, instruction:p.Instruction=None):
        self.nodeType = DFG_Type()
        if (instruction != None):
            self.instruction = instruction
            self.name = instruction.args.result
            if instruction.args.instr == "ret":
                self.name = "$ret"
                self.nodeType.special = True
                self.nodeType.ret     = True
        else:
            self.instruction    = None
            self.name           = "DEFAULT"

        self.assignment     = (-1, -1)
        self.useNodes       = []
        self.depNodes       = []
        self.psuNodes       = []
        self.stride         = []
        self.numIters       = []
        self.riscVString    = ""
        self.vsetivliString = "" 

    def Print_Node(self, extended=False):
        print("Name: " + self.name)
        print("Assigned: " + "(" + str(self.assignment[0]) + "," + str(self.assignment[1]) + ")")
        print("Type: " + self.nodeType.GetTypeStr())
        print("Deps: " )
        for node in self.depNodes:
            print("\t" + node.name)
        print("Uses: ")
        for node in self.useNodes:
            print("\t" + node.name)

    def Verify_Node(self):
        psuDepList = self.Get_Psu(True, False)
        psuUseList = self.Get_Psu(False, True)
        depList    = self.Get_Deps(True)
        useList    = self.Get_Uses(True)
        for dep in depList:
            assert(depList.count(dep) == 1)
            assert(dep not in useList)
        for use in useList:
            assert(useList.count(use) == 1)
            assert(use not in depList)
        for psuDep in psuDepList:
            assert(depList.count(psuDep) == 1)
            assert(self.psuNodes.count(psuDep) == 1)
            assert(psuDep not in useList)
            assert(psuDep not in psuUseList)
        for psuUse in psuUseList:
            assert(useList.count(psuUse) == 1)
            assert(self.psuNodes.count(psuUse) == 1)
            assert(psuUse not in depList)
            assert(psuUse not in psuDepList)
        # this also verifies legal type state
        self.nodeType.Get_Type_Str()

    def Get_Deps(self, includePsu=False):
        """
        returns a COPY of the depList, default with psuedo Nodes removed
        """
        retList:"list[DFG_Node]" = self.depNodes.copy()
        if includePsu == False:
            for node in self.psuNodes:
                if node in retList.copy():
                    retList.remove(node)
        return retList

    def Get_Psu(self, depPsu, usePsu):
        assert(depPsu or usePsu)
        retList:"list[DFG_Node]" = self.psuNodes.copy()
        if depPsu == False:
            for node in self.depNodes:
                if node in retList.copy():
                    retList.remove(node)
        if usePsu == False:
            for node in self.useNodes:
                if node in retList.copy():
                    retList.remove(node)
        return retList
    
    def Get_Uses(self, includePsu=False):
        """
        returns a COPY of the useList, default with psuedo Nodes removed
        """
        retList:"list[DFG_Node]" = self.useNodes.copy()
        if includePsu == False:
            for node in self.psuNodes:
                if node in retList.copy():
                    retList.remove(node)
        return retList

    def Add_Dep(self, depNode:"DFG_Node", addSelfAsUse=True, asPsu=False, warn=True):
        assert(depNode not in self.depNodes)
        self.depNodes.append(depNode)
        if addSelfAsUse:
            depNode.useNodes.append(self)
        elif warn:
            warnings.warn("not adding self as use to dep... mistake ?")

        if asPsu:
            assert(depNode not in self.psuNodes)
            self.psuNodes.append(depNode)
        return
    
    def Add_Use(self, useNode:"DFG_Node", addSelfAsDep=True, asPsu=False, warn=True):
        assert(useNode not in self.depNodes)
        self.useNodes.append(useNode)
        if addSelfAsDep:
            useNode.depNodes.append(self)
        elif warn:
            warnings.warn("not adding self as dep to use ... mistake ?")

        if asPsu:
            assert(useNode not in self.psuNodes)
            self.psuNodes.append(useNode)
        return

    def Remove_Dep(self, depNode:"DFG_Node", removeFromDep=True, warn=True):
        assert(depNode in self.depNodes)
        assert(self.depNodes.count(depNode) == 1)
        self.depNodes.remove(depNode)
        if depNode in self.psuNodes:
            assert(self.psuNodes.count(depNode) == 1)
            self.psuNodes.remove(depNode)
        
        if removeFromDep:
            depNode.Remove_Use(self, False, False)
        elif warn:
            warnings.warn("not removing self from dep uses ... mistake ?")
        return

    def Remove_Use(self, useNode:"DFG_Node", removeFromUse=True, warn=True):
        assert(useNode in self.useNodes)
        assert(self.useNodes.count(useNode) == 1)
        self.useNodes.remove(useNode)
        if useNode in self.psuNodes:
            assert(self.psuNodes.count(useNode) == 1)
            self.psuNodes.remove(useNode)
        
        if removeFromUse:
            useNode.Remove_Dep(self, False, False)
        elif warn:
            warnings.warn("not removing self from use deps ... mistake ?")
        return

    def Remove_Node(self, node:"DFG_Node"):
        """
        automatically removes the node from the right list
        """
        assert(node not in self.useNodes or node not in self.depNodes)
        if node in self.depNodes:
            self.Remove_Dep(node)
        elif node in self.useNodes:
            self.Remove_Use(node)
        else:
            assert(False)
        # just being careful...
        assert(node not in self.useNodes)
        assert(node not in self.depNodes)
        assert(node not in self.psuNodes)
        assert(self not in node.useNodes)
        assert(self not in node.depNodes)
        assert(self not in node.psuNodes)

        return

    def Remove_Psu_Connections(self):
        """
        removes all psuedo connections, 
        """
        psuList = self.Get_Psu(True, True)
        for psu in psuList.copy():
            self.Remove_Node(psu)
        assert(len(self.psuNodes) == 0)
        return

    def Delete_Node(self, relink=True):
        """
        No matter what, removes all references to uses and from deps, if the
        relink arg is true, this will link every dep to every use

        Doesn't relink psuedo nodes, expected to call Remove_Psu_Connections
        before this.  Force correct behavior.
        """
        assert(len(self.psuNodes) == 0)
        deps = self.Get_Deps()
        uses = self.Get_Uses()
        for dep in deps:
            self.Remove_Dep(dep)
        for use in uses:
            self.Remove_Use(use)
        assert(len(self.depNodes) == 0)
        assert(len(self.useNodes) == 0)

        if relink:
            for dep in deps:
                for use in uses:
                    # don't want to double up on connections
                    if use in dep.useNodes:
                        assert(dep in use.depNodes)
                    else:
                        dep.Add_Use(use)
        else:
            warnings.warn("not relinking deps and uses ? Maybe this is ok idk")

        return

    def Check_Connected(self, node:"DFG_Node"):
        """
        Checks if two nodes are already linked
        """
        selfDeps = self.Get_Deps()
        selfUses = self.Get_Uses()

        nodeDeps = node.Get_Deps()
        nodeUses = node.Get_Uses()

        selfPsus = self.Get_Psu(True, True)
        nodePsus = node.Get_Psu(True, True)

        isConnected = False
        if node in selfDeps:
            assert(node not in selfUses)
            assert(selfDeps.count(node) == 1)
            assert(self not in nodeDeps)
            assert(nodeUses.count(self) == 1)
            isConnected = True

        elif node in selfUses:
            assert(node not in selfDeps)
            assert(selfUses.count(node) == 1)
            assert(self not in nodeUses)
            assert(nodeDeps.count(self) == 1)
            isConnected = True

        elif node in selfPsus:
            assert(self in nodePsus)
            warnings.warn("only psuedo connected. Not bad just odd that I'd check this")
            isConnected = True

        return isConnected

