import DFG_Node2 as dfgn
import DFG2 as _dfg
import Block_DFG2 as bdfg
import SDFG_Node2 as sdfgn
import warnings

def main():
    Print_With_Bars("Start of Testing")

    dfg = _dfg.DFG("gcn3_strip.ll")

    Print_With_Bars("End of Init (some warnings about stuff implementation details I plan on changing)")

    tests = [Test_Find_Phi, Test_Search_For_Self, Test_Loop_Change]
    testNames = ["find phi", "search for self", "loop change"]

    assert(len(tests) == len(testNames))

    for idx in range(len(tests)):
        try:
            tests[idx](dfg)
        except:
            failStr = "ERROR: Test - " + testNames[idx] + " - failed an assertion"
            Print_With_Bars(failStr, "$")
            # re-init to see if that stops the assertion
            dfg = _dfg.DFG("gcn3_strip.ll")
            tests[idx](dfg)

    #dfg.blockDFGs[5].Create_Macc()
    dfg.blockDFGs[5].Show_Graph()
    #for block in dfg.blockDFGs[5]:
    #    block.Show_Graph(dfg)

    Print_With_Bars("End of Testing")

    return

def Print_With_Bars(printStr:str, lineChar:str="#", *, printBottom=True, printTop=True):
    lineStr = ""
    for _ in range(80):
        lineStr += lineChar
    if printTop:
        print(lineStr)
    print(printStr)
    if printBottom:
        print(lineStr)

def Test_Find_Phi(dfg:"_dfg.DFG"):
    Print_With_Bars("Testing Find Phi", "-", printBottom=False)
    warnStr        = "phiNode wrong: (node, expected, actual) \n\t"
    testNodes      = ["%13", "%indvars.iv.next222", "%scevgep241242"]
    expectNodes    = ["%index", "%indvars.iv221", "%indvar"]

    result = True
    for i in range(len(testNodes)):
        phiNode = dfg.Get_Node_By_Name(testNodes[i]).Find_Phi()
        if phiNode.name != expectNodes[i]:
            warnings.warn(warnStr + testNodes[i] + ", " + expectNodes[i] + ", " + phiNode.name)
            result = False

    if result:
        Print_With_Bars("Pass", "-", printTop=False)
    else:
        Print_With_Bars("Fail", "$", printTop=False)
    return result

def Test_Search_For_Self(dfg:"_dfg.DFG"):
    Print_With_Bars("Testing Search For Self", "-", printBottom=False)
    warnStr = "Error, couldn't find self: (self, found) \n\t"
    testNodes = ["%indvar"]

    result = True
    for node in testNodes:
        phiNode = dfg.Get_Node_By_Name(node)
        nodeList = phiNode.Search_For_Node(phiNode, needTwoOfNode=True)

        if nodeList[0] != phiNode or nodeList[-1] != phiNode:
            warnings.warn(warnStr + phiNode.name + ", " + nodeList[-1].name)
            result = False

    if result:
        Print_With_Bars("Pass", "-", printTop=False)
    else:
        Print_With_Bars("Fail", "$", printTop=False)

    return result

def Test_Loop_Change(dfg:"_dfg.DFG"):
    Print_With_Bars("Testing Loop Change", "-", printBottom=False)
    warnStr = "Error, wrong value: (node, val, expVal) \n\t"
    testNodes = ["%indvar", "%index", "%9", "%13", "%6", "%7"]
    expectedValues = [1, 16, 16, 16, 16, 16]

    result = True
    for idx in range(len(testNodes)):
        node = dfg.Get_Node_By_Name(testNodes[idx])
        expVal = expectedValues[idx]
        val = node.Get_Loop_Change()
        if  val != expVal:
            warnings.warn(warnStr + node.name + ", " + str(val) + ", " + str(expVal))
            result = False

    if result:
        Print_With_Bars("Pass", "-", printTop=False)
    else:
        Print_With_Bars("Fail", "$", printTop=False)
    return result

def Test_StrideDepth(dfg:"_dfg.DFG"):
    assert(False)

if __name__ == '__main__':
    main()