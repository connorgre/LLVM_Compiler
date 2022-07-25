from typing import List
from regex import D
import Parser as p 

def Do_Immediate_Op(val, node):
    """
    Does an immediate operation
    """
    if len(node.immediates) == 0:
        print("Node has no immediates")
        return val
    if node.instruction.args.instr == "add":
        val += int(node.immediates[0])
    elif node.instruction.args.instr == "mul":
        val *= int(node.immediates[0])
    elif node.instruction.args.instr == "shl":
        val *= (2 ** (int(node.immediates[0])))
    else:
        print("unsupported immediate op (just need to add it)")
    return val

class DFG_Node:
    """
    Node for the Data Flow Graph
    Holds one instruction, and related dfg metadata relating to it
    """
    def __init__(self, instruction=None):
        self.is_special = False
        self.is_ret = False
        if(instruction != None):
            self.instruction:p.Instruction = instruction              #instruction where variable is assigned
            self.name:str = instruction.args.result         #just to pull through the name to make access easier
            if instruction.args.instr == "ret":
                self.name = "$ret"
                # simplifies logic bc really we don't want
                # to do anything with ret
                self.is_special = True
                self.is_ret = True
        else:
            self.instruction:p.Instruction = None
            self.name:str = "DEFAULT"

        self.assignment = (-1, -1)                  #tuple with (block, instr) -- the block and offset into the block the var is assigned
        self.uses = []                              #list of (block, instr) -- locations var is used 
        self.psuedo_uses = []                       #uses generated as a result of 'fake' going into a branch instruction
        self.dependencies = []                      #list of the 1 level up dependencies of this variable
        self.psuedo_dependencies = []               #dependencies generated as a result of an 'end' node going into a branch node
        self.immediates = []                        #the immediates used in the assignment of this node
        self.is_loop_control = False                #true if this is a register related to loop control (ie loop index)
        
        self.loop_depth = None

        self.block_num = None

        self.is_phi = False
        self.is_global = False
        self.is_vle = False
        self.is_macc = False
        self.is_bne = False
        self.is_block = False

        # loop-loop change of this node
        self.stride:List[int] = []

        #idk why but for the rest of these I left the node dependency and use lists
        #as the location in the blocks, rather than just as pointers to the nodes themselves.
        self.use_nodes:List[DFG_Node] = []
        self.dep_nodes:List[DFG_Node] = []
        self.psuedo_nodes:List[DFG_Node] = []
        
    def Print_Node(self, extended=False):
        print("Name: " + self.name)
        print("Assigned: " + "(" + str(self.assignment[0]) + "," + str(self.assignment[1]) + ")")
        print("Deps: " )
        for node in self.dep_nodes:
            print("\t" + node.name)
        print("Uses: ")
        for node in self.use_nodes:
            print("\t" + node.name)
        
        if(extended):
            print("Psuedo: ")
            for node in self.psuedo_nodes:
                print("\t" + node.name)
            print("Loop Control: " + str(self.is_loop_control))
            print("Phi Assigned: " + str(self.is_phi))
            print("Global: " + str(self.is_global))

    def Fill_Pointer_Lists(self, dfg):
        for use in self.uses:
            self.use_nodes.append(dfg.Get_Node_Block_Offset(use))
        for dep in self.dependencies:
            self.dep_nodes.append(dfg.Get_Node_Block_Offset(dep))
        for loc in self.psuedo_dependencies:
            self.psuedo_nodes.append(dfg.Get_Node_Block_Offset(loc))
        for loc in self.psuedo_uses:
            self.psuedo_nodes.append(dfg.Get_Node_Block_Offset(loc))

    def Get_Loop_Change(self, dfg):
        """
        Gets the loop to loop change of a node
        won't get run on all nodes tho
        """
        # first find the 'root' phi node for this
        
        print("Getting loop change: " + self.name)
        depth = 1
        stride = None
        nodeList:List[DFG_Node] = []
        # 20 should be a high enough upper bound...
        while (depth < 20 and len(nodeList) == 0):
            nodeList.clear()
            dfg.Get_Use_Path_Graph(self, None, nodeList, depth=depth, do_dep=True, findPhi=True)
            depth +=1
        if depth == 20:
            print("need to increase Get_Loop_Change depth")
        
        print([node.name for node in nodeList])

        if len(nodeList) == 0:
            print("Error, no phi node found")
            return
        # set nodeList to execution order now
        nodeList.reverse()

        stride = nodeList[0].stride[0]
        if stride == None or stride < 1:
            print("stride error for : " + nodeList[0].stride[0])
            return

        for node in nodeList[1:]:
            stride = Do_Immediate_Op(stride, node)

        self.stride.append(stride)
        print("Stride= " + str(stride))
        return
        
    def Get_Pointer_Info(self, dfg):
        """
        This function asserts that the node were acting on
        loads from a pointer with GetElementPtr, and returns
        the pointer we load from and the offset of that pointer
        """

        getElemPtr:DFG_Node = dfg.Get_Pointer_Node(self)
        offset = None
        offsetNode = None
        ptrNode = None
        if getElemPtr.instruction.args.instr == "alloca":
            ptrNode = dfg.Get_Node_By_Name(getElemPtr.instruction.args.result)
            offset = 0
            offsetNode = None
        elif getElemPtr.instruction.args.instr == "getelementptr":
            ptrNode = dfg.Get_Node_By_Name(getElemPtr.instruction.args.pointer)

            offset = getElemPtr.instruction.args.index_value[1]
            offsetNode = None
            if(offset[0] in ["%", "@"]):
                offsetNode = dfg.Get_Node_By_Name(offset)
                offset = None
            else:
                offset = int(offset)
        else:
            print("Error, wrong node type: " + getElemPtr.instruction.args.instr)
            assert(False)

        return [ptrNode, offsetNode, offset]
        
    def Get_Full_Stride(self):
        """
        Similar to get Loop-Loop Change, except that this
        gets the stride for ever loop, not the shallowest one,
        so it returns a list of ints, not just one
        """

        if self.is_phi == True:
            retStride = self.stride.copy()
            return (retStride, [self.loop_depth])

        if self.instruction.args.instr_type != "R_2op":
            print("Error, this shoudl be an R_2op instr")
            return None

        # these lists will hold the stride we take
        stride = 0
        strideList1 = []
        strideList2 = []

        # these are used to order the stride
        blockDepth1 = []
        blockDepth2 = []

        if len(self.immediates) > 0:
            assert(len(self.immediates) == 1)
            assert(len(self.dep_nodes) == 1)

            opVal = 0
            if self.instruction.args.instr == "add":
                opVal = 0
            else:
                opVal = 1

            (strideList1, blockDepth1) = self.dep_nodes[0].Get_Full_Stride()
            if self.dep_nodes[0].is_phi:
                stride = Do_Immediate_Op(opVal, self)
                strideList1[0] *= stride

            assert(strideList1[0] > 0)
        else:
            assert(len(self.immediates) == 0)
            assert(len(self.dep_nodes) == 2)

            (strideList1, blockDepth1) = self.dep_nodes[0].Get_Full_Stride()
            (strideList2, blockDepth2) = self.dep_nodes[1].Get_Full_Stride()
            strideList1.extend(strideList2)
            blockDepth1.extend(blockDepth2)
        
        Sort_List_Index(strideList1, blockDepth1)
        return (strideList1, blockDepth1)

    def Get_Initial_Val(self):
        """
        Gets the initial value of the node
        """
        if self.is_phi == True:
            return int(self.init_val)

        if self.instruction.args.instr_type != "R_2op":
            print("Error, this shoudl be an R_2op instr")
            return None

        val = 0
        if len(self.immediates) > 0:
            assert(len(self.immediates) == 1)
            assert(len(self.dep_nodes) == 1)

            val = self.dep_nodes[0].Get_Initial_Val()

            val = Do_Immediate_Op(val, self)

        else:
            assert(len(self.immediates) == 0)
            assert(len(self.dep_nodes) == 2)

            val = self.dep_nodes[0].Get_Initial_Val()
            val2 = self.dep_nodes[1].Get_Initial_Val()
            
            val = self.Do_Node_Op(val, val2)

        return val

    def Do_Node_Op(self, op1, op2):
        """
        Does the operation specified in the node, after
        the values have been decided 
        """
        res = 0
        if self.instruction.args.instr == "add":
            res = op1 + op2
        elif self.instruction.args.instr == "mul":
            res = op1 * op2
        elif self.instruction.args.instr == "shl":
            res = op1 * (2 ** op2)
        else:
            print("Error, unsupported operation (just need to add it")
        return res

    def Remove_Duplicates(self):
        oldList = self.use_nodes.copy()
        self.use_nodes.clear()
        for node in oldList:
            if node == self:
                continue
            if node not in self.use_nodes:
                self.use_nodes.append(node)

        oldList = self.dep_nodes.copy()
        self.dep_nodes.clear()
        for node in oldList:
            if node == self:
                continue
            if node not in self.dep_nodes:
                self.dep_nodes.append(node)
        
        oldList = self.psuedo_nodes.copy()
        self.psuedo_nodes.clear()
        for node in oldList:
            if node == self:
                continue
            if node not in self.psuedo_nodes:
                self.psuedo_nodes.append(node)

def Sort_List_Index(list, indexList):
    for i in range(len(list)):
        for j in range(len(list)):
            if indexList[i] > indexList[j]:
                temp = list[i]
                tempIdx = indexList[i]
                list[i] = list[j]
                indexList[i] = indexList[j]
                list[j] = temp
                indexList[j] = tempIdx