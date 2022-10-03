import DFG2 as _dfg
import SDFG_Node2 as sdfgn
import DFG_Node2 as dfgn
import test_utils as util

def Test_Find_Phi(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Find Phi", "-", printBottom=False)
    warnStr        = "phiNode wrong: (node, expected, actual) \n\t"
    testNodes      = ["%13", "%indvars.iv.next222", "%scevgep241242"]
    expectNodes    = ["%index", "%indvars.iv221", "%indvar"]

    result = True
    for i in range(len(testNodes)):
        phiNode = dfg.Get_Node_By_Name(testNodes[i]).Find_Phi()
        if phiNode.name != expectNodes[i]:
            print(warnStr + testNodes[i] + ", " + expectNodes[i] + ", " + phiNode.name)
            result = False

    util.PrintResult(result)
    return result

def Test_Search_For_Self(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Search For Self", "-", printBottom=False)
    warnStr = "Error, couldn't find self: (self, found) \n\t"
    testNodes = ["%indvar"]

    result = True
    for node in testNodes:
        phiNode = dfg.Get_Node_By_Name(node)
        nodeList = phiNode.Search_For_Node(phiNode, needTwoOfNode=True)

        if nodeList[0] != phiNode or nodeList[-1] != phiNode:
            print(warnStr + phiNode.name + ", " + nodeList[-1].name)
            result = False

    util.PrintResult(result)
    return result

def Test_Loop_Change(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Loop Change", "-", printBottom=False)
    warnStr = "Error, wrong value: (node, val, expVal) \n\t"
    testNodes = ["%indvar", "%index", "%9", "%13", "%6", "%7"]
    expectedValues = [1, 16, 16, 16, 16, 16]

    result = True
    for idx in range(len(testNodes)):
        node = dfg.Get_Node_By_Name(testNodes[idx])
        expVal = expectedValues[idx]
        val = node.Get_Loop_Change()
        if  val != expVal:
            print(warnStr + node.name + ", " + str(val) + ", " + str(expVal))
            result = False

    util.PrintResult(result)

    return result

def Test_StrideDepth(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing StrideDepth", "-", printBottom=False)
    warnStr = "Error, wrong value: (node, val, expVal) \n\t"
    testNodes = ["%9",
                "%13",
                "%5",
                "%10",
                "%3"]
    expectedValues = [  ([16, 16], [5,4]),
                        ([16, 512, 16, 8192, 262144], [5, 4, 3, 2, 1]),
                        ([16],[3]),
                        ([16,16],[5,3]),
                        ([512],[2])]
    result = True
    for i in range(len(testNodes)):
        node = dfg.Get_Node_By_Name(testNodes[i])
        expVal = expectedValues[i]
        resVal = node.Get_LoopInfo_Stride_And_Depth()
        if expVal != resVal:
            print(warnStr + node.name + ", " + str(resVal) + ", " + str(expVal))
            result = False

    util.PrintResult(result)
    return result

def Test_Iters(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Iters", "-", printBottom=False)
    warnStr = "Error, wrong value (node, res, exp)\n\t"
    testNodes:"list[dfgn.DFG_Node]" = ["%13", "%10", "%9"]
    expVals = [[1,16,32,32,4], [1, 32], [1,16]]

    for nodeName, exp in zip(testNodes, expVals):
        node = dfg.Get_Node_By_Name(nodeName)
        val = node.Get_Loop_Iters()
        result = True
        if val != exp:
            print(warnStr + ", " + node.name + ", " + str(val) + ", " + str(exp))
            result = False

    util.PrintResult(result)
    return result

def Test_Macc(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Create_Macc", "-", printBottom=False)
    maccNode:sdfgn.Macc_Node = dfg.blockDFGs[5].Create_Macc()

    result = True
    addInfo = maccNode.Get_AddPtrInfo()
    addOffset = addInfo.Get_Offset_Info()
    addVerify =(    (addOffset.stride == [16,16])       and\
                    (addOffset.strideDepth == [5, 4])   and\
                    (addOffset.strideIters == [1,16])   and\
                    (addOffset.initVal == 512)          and\
                    (addInfo.Get_Ptr_Node().name == "%rf0"))

    mul1Info = maccNode.Get_Mul1PtrInfo()
    mul1Offset = mul1Info.Get_Offset_Info()
    mul1Verify =(   (mul1Offset.stride == [16, 512, 16, 8192, 262144]) and\
                    (mul1Offset.strideDepth == [5, 4, 3, 2, 1])        and\
                    (mul1Offset.strideIters == [1, 16, 32, 32, 4])     and\
                    (mul1Offset.initVal == 0)                          and\
                    (mul1Info.Get_Ptr_Node().name == "@stream_in"))

    mul2Info = maccNode.Get_Mul2PtrInfo()
    mul2Offset = mul2Info.Get_Offset_Info()
    mul2Verify =(   (mul2Offset.stride == [16,16])       and\
                    (mul2Offset.strideDepth == [5, 3])   and\
                    (mul2Offset.strideIters == [1,32])   and\
                    (mul2Offset.initVal == 0)          and\
                    (mul2Info.Get_Ptr_Node().name == "%rf0"))

    resInfo = maccNode.Get_ResPtrInfo()
    resOffset = resInfo.Get_Offset_Info()
    resVerify =(    (resOffset.stride == [16,16])       and\
                    (resOffset.strideDepth == [5, 4])   and\
                    (resOffset.strideIters == [1,16])   and\
                    (resOffset.initVal == 512)          and\
                    (resInfo.Get_Ptr_Node().name == "%rf0"))

    if addVerify == False:
        print("incorrect add pointer info")
    if mul1Verify == False:
        print("incorrect mul1 pointer info")
    if mul2Verify == False:
        print("incorrect mul2 pointer info")
    if resVerify == False:
        print("incorrect result pointer info")

    result = addVerify and mul1Verify and mul2Verify and resVerify
    util.PrintResult(result)
    return

def Test_Vle(dfg:"_dfg.DFG"):
    util.Print_With_Bars("Testing Create_Vle", "-", printBottom=False)

    """
    doesn't test the pointer names.  idk just don't feel like adding
    rn and confident something else will break if the names are getting
    messed up...
    """
    vleBlocks = [1,2,9]
    expValRet  = [  [[], [], [], []],
                    [[], [], [], []],
                    [[256], [4], [1], [1]]]
    expValLoad = [  0,
                    [[512], [32], [1], [2]],
                    [[], [], [], []]]
    expValLen  = [  1024,
                    2048,
                    1024]
    result = True
    for idx in range(len(vleBlocks)):
        block = vleBlocks[idx]
        vleNode = dfg.blockDFGs[block].Create_Vle()
        resPtrInfo = vleNode.Get_ResPtrInfo()
        valRet = resPtrInfo.Get_Packed()
        if valRet != expValRet[idx]:
            result = False
            print("Incorrect result pointer")

        loadPtrInfo = vleNode.Get_LoadPtrInfo()
        valLoad = None
        if loadPtrInfo != None:
            valLoad = loadPtrInfo.Get_Packed()
        else:
            valLoad = vleNode.Get_Load_Imm()
        if valLoad != expValLoad[idx]:
            result = False
            print("Incorrect load pointer info")

        if vleNode.loadLength != expValLen[idx]:
            result = False
            print("Incorrect length")

    util.PrintResult(result)

def Test_Full_Static_Analysis(dfg:_dfg.DFG):
    """
    test for manual inspection
    """
    util.Print_With_Bars("Testing Full Static Analysis", "-", printBottom=False)

    dfg = util.Re_Init()
    #dfg.Show_Graph()
    dfg.Do_Static_Analysis()

    dfg.Show_Graph()
    for block in dfg.blockDFGs:
        block.Show_Graph()

    util.PrintResult(True)

