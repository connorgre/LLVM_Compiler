from operator import ne
import Parser as p
from typing import TYPE_CHECKING
import warnings
import DfgUtil as util

if TYPE_CHECKING:
    import Block_DFG2 as bdfg
    import SDFG_Node2 as sdfgn

class DFG_Type:
    """
    helper class to handle the type of dfg it is
    """
    special :bool
    ret     :bool
    phi     :bool
    block   :bool
    bne     :bool
    macc    :bool
    vle     :bool
    def __init__(self):
        """
        init all to false
        """
        self.special = False
        self.ret = False
        self.phi = False
        self.block = False
        self.bne = False
        self.macc = False
        self.vle = False

    def Get_Type_Str(self):
        retStr = None
        if self.special == False:
            retStr = "Normal"
        if self.ret:
            assert(retStr == None)
            retStr = "ret"
        if self.phi:
            assert(retStr == None)
            retStr = "phi"
        if self.block:
            assert(retStr == None)
            retStr = "block"
        if self.bne:
            assert(retStr == None)
            retStr = "bne"
        if self.macc:
            assert(retStr == None)
            retStr = "macc"
        if self.vle:
            assert(retStr == None)
            retStr = "vle"
        assert(retStr != None)

        return retStr

    def Is_Special(self):
        special = self.special
        if special:
            assert(self.ret or self.phi or self.block or self.bne or self.macc)
        return special

class Loop_Info:
    """
    helper class to hold stride information
    """
    stride        : "list[int]"     # stride of the pointer through each loop
    strideIters   : "list[int]"     # number of iters on this stride before moving up
    strideDepth   : "list[int] "    # depth of the stride/offsets
    vectorLen     : "list[int]"     # list of vector length
    initVal       : "int"
    def __init__(self):
        self.stride         = []
        self.strideIters    = []
        self.strideDepth    = []
        self.vectorLen      = []
        self.initVal        = None
    def getCopy(self):
        retInfo = Loop_Info()
        retInfo.stride      = self.stride.copy()
        retInfo.strideIters = self.strideIters.copy()
        retInfo.strideDepth = self.strideDepth.copy()
        retInfo.vectorLen   = self.vectorLen.copy()
        retInfo.initVal     = self.initVal
        return retInfo
    def Print(self):
        print("\tstride:      " + str(self.stride))
        print("\tstrideIters: " + str(self.strideIters))
        print("\tvectorLen:   " + str(self.vectorLen))
        print("\tstrideDepth  " + str(self.strideDepth))
        print("\tinitVal:     " + str(self.initVal))


    def Get_InnerMost_Loop_Change(self):
        return self.stride[0]

class DFG_Node:
    """
    Re-doing the dfg node
    """
    nodeType      : DFG_Type
    name          : str
    instruction   : p.Instruction
    assignment    : "tuple[int,int]"
    useNodes      : "list[DFG_Node]"
    depNodes      : "list[DFG_Node]"
    psuNodes      : "list[DFG_Node]"       #psu = psuedo, not a true dependency but useful info
    immediates    : "list[int]"
    stride        : "list[int]"
    numIters      : "list[int]"
    riscVString   : str
    vsetivliString: str
    loopInfo      : Loop_Info
    parentBlock   : "bdfg.Block_DFG"

    def __init__(self, block:"bdfg.Block_DFG", instruction:p.Instruction=None):
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

        self.parentBlock    = block
        self.assignment     = (-1, -1)
        self.useNodes       = []
        self.depNodes       = []
        self.psuNodes       = []
        self.stride         = []
        self.numIters       = []
        self.immediates     = []
        self.riscVString    = ""
        self.vsetivliString = ""
        self.loopInfo       = Loop_Info()

    def Print_Node(self, extended=False):
        print("Name: " + self.name)
        print("Assigned: " + "(" + str(self.assignment[0]) + "," + str(self.assignment[1]) + ")")
        print("Type: " + self.nodeType.Get_Type_Str())
        print("Deps: " )
        for node in self.depNodes:
            print("\t" + node.name)
        print("Uses: ")
        for node in self.useNodes:
            print("\t" + node.name)

    def Get_Type(self):
        return self.nodeType.Get_Type_Str()

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
        assert(self != depNode)
        self.depNodes.append(depNode)
        if addSelfAsUse:
            depNode.useNodes.append(self)
            if asPsu:
                assert(self not in depNode.psuNodes)
                depNode.psuNodes.append(self)
        elif warn:
            warnings.warn("not adding self as use to dep... mistake ?")

        if asPsu:
            assert(depNode not in self.psuNodes)
            self.psuNodes.append(depNode)
        return

    def Add_Use(self, useNode:"DFG_Node", addSelfAsDep=True, asPsu=False, warn=True):
        assert(useNode not in self.useNodes)
        assert(self != useNode)
        self.useNodes.append(useNode)
        if addSelfAsDep:
            useNode.depNodes.append(self)
            if asPsu:
                assert(self not in useNode.psuNodes)
                useNode.psuNodes.append(self)
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
        removes all psuedo connections, doesn't relink
        """
        psuList = self.Get_Psu(True, True)
        for psu in psuList.copy():
            self.Remove_Node(psu)
        assert(len(self.psuNodes) == 0)
        return

    def Delete_Node(self, relink=True, *, warn=True):
        """
        No matter what, removes all references to uses and from deps, if the
        relink arg is true, this will link every dep to every use

        This also calls dfg.Remove_Node(), which removes the node from the
        dfg and all blocks.  This function totally erases a node other than psu
        connections.

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

        self.Get_DFG().Remove_Node(self)

        if relink:
            for dep in deps:
                for use in uses:
                    # don't want to double up on connections
                    if use in dep.useNodes:
                        assert(dep in use.depNodes)
                    else:
                        dep.Add_Use(use)
        elif warn:
            warnings.warn("not relinking deps and uses ? Maybe this is ok idk")
        return

    def Make_Psu_Connect(self, psuNode:"DFG_Node"):
        """
        Adds an existing node to the psuedo node connections
        """
        assert(self != psuNode)
        uses = self.Get_Uses()
        deps = self.Get_Deps()
        psuUses = psuNode.Get_Uses()
        psuDeps = psuNode.Get_Deps()

        assert(psuNode in uses or psuNode in deps)
        assert(self in psuUses or self in psuDeps)
        assert(psuNode not in self.Get_Psu(True, True))
        assert(self not in psuNode.Get_Psu(True, True))

        if psuNode in deps:
            if psuNode in uses:
                warnings.warn("psuedo connection with potential side \
                               effects bc its linked to use and dep")
            assert(self not in psuDeps)
            self.psuNodes.append(psuNode)
            psuNode.psuNodes.append(self)
        else:
            if psuNode in uses:
                warnings.warn("psuedo connection with potential side \
                               effects bc its linked to use and dep")
            assert(self not in psuUses)
            self.psuNodes.append(psuNode)
            psuNode.psuNodes.append(self)
        return

    def Add_Connections_To_Node(self, newNode:"DFG_Node", doPsu=True):
        """
        Adds all the connections into and out of self to newNode.
        Doesn't delete the connections
        """
        assert(self != newNode)
        for node in self.Get_Deps(doPsu):
            if (newNode.Check_Connected(node, checkUse=False) == False):
                newNode.Add_Dep(node)
        for node in self.Get_Uses(doPsu):
            if (newNode.Check_Connected(node, checkDep=False) == False):
                newNode.Add_Use(node)
        if doPsu:
            for node in self.Get_Psu(True, True):
                newNode.Make_Psu_Connect(node)
        return

    def Check_Connected(self, node:"DFG_Node", checkDep=True, checkUse=True):
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
        if node in selfDeps and checkDep:
            assert(selfDeps.count(node) == 1)
            assert(nodeUses.count(self) == 1)
            isConnected = True

        elif node in selfUses and checkUse:
            assert(selfUses.count(node) == 1)
            assert(nodeDeps.count(self) == 1)
            isConnected = True

        elif node in selfPsus and (checkUse and checkDep):
            assert(self in nodePsus)
            warnings.warn("only psuedo connected. Not bad just odd that I'd check this")
            isConnected = True

        elif self == node:
            warnings.warn("could be ok, probably not expected though")
            isConnected = True

        return isConnected

    def Search_For_Node(self,
                        searchNode:"DFG_Node",              # node to look for
                        depSearch=False,                    # search depList (useList default)
                        visited:"list[DFG_Node]"=None,      # internal
                        nodeList:"list[DFG_Node]"=None,     # internal
                        *,
                        phiSearch=False,                    # only look for phi nodes
                        storeSearch=False,                  # only look for search nodes
                        pointerSearch=False,                # only look for pointer nodes
                        withinBlock=False,                  # don't search outside block
                        stayAboveDepth=-1,                  # don't search shallower loops
                        excludeNodes:"list[DFG_Node]"=[],   # list of nodes ot exclude (useful for phiSearch)
                        needTwoOfNode=False                 # so that we can search for ourself (if we're phi)
                        ):
        """
        Returns a list of nodes in the path from self to searchNode
        """
        # either both are None or neither are
        assert((nodeList == None and visited == None) or (nodeList != None and visited != None))
        if visited == None:
            visited  = []
            nodeList = []

        # don't search if
        #   already searched the node,
        #   just found node,
        #   already found node
        doSearch = True
        if self in visited:
            doSearch = False

        if self == searchNode:
            if needTwoOfNode:
                if self in nodeList:
                    doSearch = False
                    nodeList.append(self)
            else:
                assert(self not in visited)
                assert(self not in nodeList)
                doSearch = False
                nodeList.append(self)

        if phiSearch:
            assert(searchNode == None)
            if self.Get_Type() == "phi":
                assert(self not in visited)
                assert(self not in nodeList)
                doSearch = False
                nodeList.append(self)
        if storeSearch:
            assert(searchNode == None)
            if self.Get_Instr() == "store":
                assert(self not in visited)
                assert(self not in nodeList)
                doSearch = False
                nodeList.append(self)
        if pointerSearch:
            assert(searchNode == None)
            # have extra and here so we can start search from a
            # getelementptr node, also zeroinitializer is global pointer
            if (self.Get_Instr() == "alloca") or \
                    ((self.Get_Instr() == "getelementptr") and (len(nodeList) > 0)) or\
                    (self.Get_Instr() == "zeroinitializer"):
                assert(self not in visited)
                assert(self not in nodeList)
                doSearch = False
                nodeList.append(self)

        if searchNode in nodeList:
            doSearch = False
            if needTwoOfNode and nodeList.count(searchNode) < 2:
                doSearch = True

        if doSearch:
            searchList:"list[DFG_Node]"
            visited.append(self)
            nodeList.append(self)

            if depSearch:
                searchList = self.Get_Deps()
            else:
                searchList = self.Get_Uses()

            if withinBlock:
                for node in searchList.copy():
                    if node not in self.parentBlock.Get_Inner_Nodes():
                        searchList.remove(node)

            if stayAboveDepth != -1:
                # cull the nodes that are too shallow
                for node in searchList.copy():
                    if node.Get_Loop_Depth() < stayAboveDepth:
                        searchList.remove(node)

            for node in excludeNodes:
                if node in searchList:
                    searchList.remove(node)

            doPop = True
            for node in searchList:
                node.Search_For_Node(searchNode,
                                     depSearch,
                                     visited,
                                     nodeList,
                                     phiSearch=phiSearch,
                                     storeSearch=storeSearch,
                                     pointerSearch=pointerSearch,
                                     withinBlock=withinBlock,
                                     stayAboveDepth=stayAboveDepth,
                                     excludeNodes=excludeNodes,
                                     needTwoOfNode=needTwoOfNode
                                     )

                # conditions where we've found what we want
                if searchNode in nodeList:
                    # don't wanna pop if we just found it
                    doPop = False
                    if needTwoOfNode and nodeList.count(searchNode) < 2:
                        doPop = True
                if phiSearch:
                    # if the final node in the list is phi
                    if nodeList[-1].Get_Type() == "phi":
                        doPop = False
                if storeSearch:
                    # if the final node in the list is a store
                    if nodeList[-1].Get_Instr() == "store":
                        doPop = False
                if pointerSearch:
                    if nodeList[-1].Get_Instr() in ["alloca", "getelementptr", "zeroinitializer"]:
                        doPop = False
                if doPop == False:
                    break

            if doPop:
                popNode = nodeList.pop()
                assert(popNode == self)

        return nodeList

    def Get_Instr(self):
        retStr = ""
        if self.instruction != None:
            retStr = self.instruction.args.instr
        return retStr

    def Get_Pointer(self):
        """
        Gets the pointer that this node comes from refers to
        """
        nodeList = self.Search_For_Node(None, depSearch=True, pointerSearch=True)
        return nodeList[-1]

    def Get_Root_Pointer(self):
        """
        Gets the root pointer (ie if it stops on getelementptr, it continues)
        """
        ptrNode = None
        nextPtr = self.Get_Pointer()
        while ptrNode != nextPtr:
            ptrNode = nextPtr
            nextPtr = ptrNode.Get_Pointer()
            if nextPtr == None:
                warnings.warn("dont think this should be reachable")
                assert(False)
        return ptrNode

    def Get_Root_Pointer_Path(self):
        """
        Gets the path to the root pointer
        """
        pointerNode:DFG_Node = self.Get_Root_Pointer()
        path = pointerNode.Search_For_Node(self)
        assert(path[-1] == self and path[0] == pointerNode)
        assert(self.Get_Pointer() in path)
        return path

    def Get_Link_By_Name(self, name:str):
        nodeList = self.Get_Uses()
        nodeList.extend(self.Get_Deps())
        retNode:DFG_Node = None
        for node in nodeList:
            if node.name == name:
                assert(retNode == None)
                retNode = node
        if retNode == None:
            warnings.warn("couldn't find node")
        return retNode

    def Is_Arithmatic(self):
        """
        returns true if instruction is add, mul, or shl
        """
        return util.Is_Arithmatic_Instr(self.Get_Instr())

    def Is_Phi(self):
        return self.nodeType.phi

    def Get_Init_Val(self):
        """
        Gets the initial value of a node (ie loop iteration 0)
        """
        if self.loopInfo.initVal != None:
            return self.loopInfo.initVal

        assert(self.Is_Arithmatic() or self.Is_Phi())
        deps = self.Get_Deps()
        imms = self.immediates

        retVal = None
        if self.Is_Phi():
            phiVal = self.Get_Phi_Value_By_Number(0)
            assert(phiVal.isnumeric())
            retVal = int(phiVal)
        else:
            assert(len(deps) + len(imms) == 2)
            if self.instruction.args.op1[0] not in ["%", "@"]:
                warnings.warn("need to add logic for if op1 is the immediate op")
            vals:"list[int]" = []
            for dep in deps:
                vals.append(dep.Get_Init_Val())
            if len(vals) == 1:
                assert(len(imms) == 1)
                vals.append(imms[0])
            else:
                assert(len(imms) == 0)
            assert(len(vals) == 2)
            # turn warn 0 off bc init val is expected to have 0 in it
            retVal = util.Do_Op(self.Get_Instr(), vals[0], vals[1], warnForZero=False)
        return retVal

    def Get_Loop_Info(self):
        """
        returns (deep) copy of loopinfo
        """
        self.Fill_Loop_Info()
        loopInfoCopy = self.loopInfo.getCopy()
        return loopInfoCopy

    def Fill_Loop_Info(self):
        """
        Fills out the loop info member
        """
        self.loopInfo.initVal = self.Get_Init_Val()
        self.Get_LoopInfo_Stride_And_Depth()
        self.Get_Loop_Iters()
        self.Get_Loop_VectorLen()
        assert(self.loopInfo.initVal != None)
        assert(len(self.loopInfo.stride)      > 0)
        assert(len(self.loopInfo.strideIters) > 0)
        assert(len(self.loopInfo.strideDepth) > 0)
        return

    def Get_Loop_VectorLen(self):
        """
        gets/fills out the self.loopInfo.vectorLen member,
        vector len of each loop at each depth
        """
        # we need to make sure we have this information
        (strideList, depthList) = self.Get_LoopInfo_Stride_And_Depth()
        assert(len(strideList) == len(depthList))

        vectorLen:"list[int]" = []

        curBlock = self.parentBlock
        for depth in depthList:
            while curBlock.Get_Loop_Depth() != depth:
                curBlock = curBlock.Get_Block_Entry_Loop_Up()
            vectorLen.append(curBlock.Get_Vector_Len())

        if len(self.loopInfo.vectorLen) > 0:
            assert(self.loopInfo.vectorLen == vectorLen)
        else:
            self.loopInfo.vectorLen = vectorLen

        return self.loopInfo.vectorLen.copy()

    def Get_Loop_Iters(self):
        """
        Gets/Fills out the self.loopInfo.loopIters member, it is
        the total number of iterations we do of each stride at each
        depth
        """
        # we need to make sure we have this information
        (strideList, depthList) = self.Get_LoopInfo_Stride_And_Depth()
        assert(len(strideList) == len(depthList))

        strideIters:"list[int]" = []

        curBlock = self.parentBlock
        for depth in depthList:
            while curBlock.Get_Loop_Depth() != depth:
                curBlock = curBlock.Get_Block_Entry_Loop_Up()
            strideIters.append(curBlock.Get_Loop_Iters())
        if len(self.loopInfo.strideIters) > 0:
            assert(self.loopInfo.strideIters == strideIters)
        else:
            self.loopInfo.strideIters = strideIters

        return self.loopInfo.strideIters.copy()

    def Get_LoopInfo_Stride_And_Depth(self):
        """
        returns (stride, strideDepth) tuple
        Gets/Fills out the stride and strideDepth lists for the loopInfo member
        This function makes the assumption that the IR will do operation as far out
        of the loop as possible.  While it isn't a requirement in llvm, the clang compiler
        should almost definitely do that.  This will fail on multiple asserts if that is
        not the case...
        """
        innerChange = self.Get_Loop_Change()
        innerDepth  = self.Get_Loop_Depth()

        if len(self.loopInfo.stride) > 0:
            assert(len(self.loopInfo.stride) == len(self.loopInfo.strideDepth))
            if self.Is_Phi():
                assert(len(self.loopInfo.stride) == 1)
                assert(len(self.loopInfo.strideDepth) == 1)

        elif self.Is_Phi():
            self.loopInfo.stride.append(innerChange)
            self.loopInfo.strideDepth.append(innerDepth)
            assert(len(self.loopInfo.stride) == 1)
            assert(len(self.loopInfo.strideDepth) == 1)

        elif len(self.immediates) == 1:
            # assume assignment would be out of loop
            assert(len(self.Get_Deps()) == 1)
            assert(self.Get_Deps()[0].Is_Node_In_Same_Loop(self))

            self.loopInfo.stride.append(innerChange)
            self.loopInfo.strideDepth.append(innerDepth)
            assert(len(self.loopInfo.stride) == 1)
            assert(len(self.loopInfo.strideDepth) == 1)

        else:
            deps = self.Get_Deps()
            assert(len(deps) == 2)
            # requirement for constant loop changes at each level
            assert(self.Get_Instr() == "add")

            strideList1:"list[int]" = None
            strideList2:"list[int]" = None
            depthList1 :"list[int]" = None
            depthList2 :"list[int]" = None

            (strideList1, depthList1) = deps[0].Get_LoopInfo_Stride_And_Depth()
            (strideList2, depthList2) = deps[1].Get_LoopInfo_Stride_And_Depth()

            strideList1.extend(strideList2)
            depthList1.extend(depthList2)

            util.Sort_List_Index(strideList1, depthList1)

            self.loopInfo.stride      = strideList1
            self.loopInfo.strideDepth = depthList1

        return (self.loopInfo.stride.copy(), self.loopInfo.strideDepth.copy())

    def Get_Loop_Change(self):
        """
        returns the amound that this node changes per loop it's assigned in
        """
        # phi nodes implement this on their own
        assert(self.Is_Phi() == False)
        # This should only be needed on arithmatic instructions
        assert(self.Is_Arithmatic())

        vals:"list[int]" = []
        for node in self.Get_Deps():
            if self.Is_Node_In_Same_Loop(node):
                vals.append(node.Get_Loop_Change())
            else:
                assert(self.Get_Instr() == "add")
                vals.append(0)
        if len(vals) == 0:
            warnings.warn("no valid op found...")
        for imm in self.immediates:
            if self.instruction.args.op1[0] not in ["%", "@"] and self.Get_Instr() == "shl":
                warnings.warn("need to add logic for immediate as op1")
                assert(False)
            if self.Get_Instr() == "add":
                # adding an immediate doesn't change the stride
                vals.append(0)
            else:
                vals.append(imm)
        assert(len(vals) == 2)

        return util.Do_Op(self.Get_Instr(), vals[0], vals[1])

    def Is_Node_In_Same_Loop(self, node:"DFG_Node"):
        """
        returns true if the two nodes are in the same loop
        """
        selfBlockOrder = self.Get_Block_Order()
        nodeBlockOrder = node.Get_Block_Order()
        isSameLoop = False
        if selfBlockOrder != nodeBlockOrder:
            if self.parentBlock.Is_Loop_Entry():
                exitBlock = self.parentBlock.Get_Exit_Block()
                if exitBlock == node.parentBlock:
                    isSameLoop = True
            elif self.parentBlock.Is_Loop_Exit():
                entryBlock = self.parentBlock.Get_Entry_Block()
                if entryBlock == node.parentBlock:
                    isSameLoop = True
        else:
            isSameLoop = True
        return isSameLoop

    def Find_Phi(self):
        """
        Finds the phi node that most recently assigns to this one
        Searches from the node for every phi node, and returns
        the one that is closest to this one --
          the one closet to this one thats before in execution order
        """
        phiList:"list[DFG_Node]" = []
        while True:
            nodeList = self.Search_For_Node(None,
                                            True,
                                            phiSearch=True,
                                            excludeNodes=phiList)
            if len(nodeList) == 0:
                break
            else:
                assert(nodeList[-1].Is_Phi())
                phiList.append(nodeList[-1])
        assert(len(phiList) > 0)
        earlyNode:"sdfgn.Phi_Node" = phiList[0]
        if len(phiList) > 1:
            for node in phiList[1:]:
                earlyIdx = earlyNode.Get_Block_Order()
                nodeIdx = node.Get_Block_Order()
                assert(earlyIdx != nodeIdx)
                # higher number means executed more recently
                if nodeIdx > earlyIdx:
                    earlyNode = node
        return earlyNode

    def Get_Block_Order(self):
        assert(self.parentBlock != None)
        return self.parentBlock.Get_Execution_Order()

    def Get_Loop_Depth(self):
        retVal = None
        if self.parentBlock != None:
            retVal = self.parentBlock.Get_Loop_Depth()
        else:
            # assert that this is global
            assert(self.name[0] == "@")
            retVal = -1
        return retVal

    def Get_Block(self):
        return self.parentBlock

    def Recursive_Delete(self, noDelete:"list[DFG_Node]"=[]):
        """
        Delete node, then recursively deletes it's dependency nodes
        if this node is the only node that uses that node.
        Any nodes in noDelete aren't deleted
        """
        deps = self.Get_Deps()
        uses = self.Get_Uses()
        assert(len(uses) == 0)
        self.Remove_Psu_Connections()
        self.Delete_Node()

        for dep in deps:
            if (len(dep.Get_Uses()) == 0) and (dep not in noDelete):
                dep.Recursive_Delete(noDelete)
        return

    def Get_DFG(self):
        return self.Get_Block().Get_DFG()

    def Is_MemCpy_Or_MemSet(self):
        """
        is the instruction memcopy or memset
        """
        isMem = False
        instr = self.Get_Instr()
        if instr == "call":
            func = self.instruction.args.function
            if func in ["@llvm.memset.p0i8.i64", "@llvm.memcpy.p0i8.p0i8.i64"]:
                isMem = True
        return isMem


