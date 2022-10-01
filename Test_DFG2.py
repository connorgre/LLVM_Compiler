import DFG_Node2 as dfgn
import DFG2 as _dfg
import Block_DFG2 as bdfg
import SDFG_Node2 as sdfgn
import test_utils as util
from Test_DFG2_tests import *



def main():
    util.Print_With_Bars("Start of Testing")
    dfg = _dfg.DFG("gcn3_strip.ll")
    util.Print_With_Bars("End of Init (some warnings about implementation details I plan on changing)")

    tests = [Test_Find_Phi, Test_Search_For_Self, Test_Loop_Change, Test_StrideDepth, Test_Iters, Test_Macc]
    testNames = ["find phi", "search for self", "loop change", "stride and depth", "loop iters", "create macc"]

    assert(len(tests) == len(testNames))

    for idx in range(len(tests)):
        dfg = util.Re_Init()
        result = True
        try:
            result = tests[idx](dfg)
        except:
            util.PrintC(util.COLOR.Red)
            failStr = "ERROR: Test - " + testNames[idx] + " - failed an assertion"
            util.Print_With_Bars(failStr, "$")
            util.PrintC(util.COLOR.White)
            # re-init to see if that stops the assertion
            dfg = _dfg.DFG("gcn3_strip.ll")
            result = tests[idx](dfg)

    #dfg.blockDFGs[5].Create_Macc()
    dfg.blockDFGs[5].Show_Graph()
    #for block in dfg.blockDFGs[5]:
    #    block.Show_Graph(dfg)

    util.Print_With_Bars("End of Testing")

    return







if __name__ == '__main__':
    main()