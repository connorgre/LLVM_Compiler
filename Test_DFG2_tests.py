import DFG2 as _dfg
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
    warnStr = "Error, in Get_Macc() (probably should break in and debug)"
    dfg.blockDFGs[5].Create_Macc()

    result = False
    util.PrintResult(result)
    return