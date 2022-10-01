from typing import TYPE_CHECKING
import warnings

if TYPE_CHECKING:
    import DFG2 as _dfg
    import DFG_Node as dfgn

def Do_Immediate_Op(val:int, node:"dfgn.DFG_Node"):
    """
    Does an immediate operation
    """
    warnings.warn("should refactor code to remove this function")
    assert(len(node.immediates) > 0)
    if node.instruction.args.instr == "add":
        val += int(node.immediates[0])
    elif node.instruction.args.instr == "mul":
        val *= int(node.immediates[0])
    elif node.instruction.args.instr == "shl":
        val *= (2 ** (int(node.immediates[0])))
    else:
        warnings.warn("unsupported immediate op (just need to add it)")
    return val

def Is_Arithmatic_Instr(instr:str):
    return instr in ["add", "mul", "shl"]

def Do_Op(op:str, val1:int, val2:int, *, warnForZero=True):
    """
    does the specified operation
    """
    assert(Is_Arithmatic_Instr(op))
    retVal = 0
    if op == "add":
        retVal = val1 + val2
    elif op == "mul":
        if (val1 == 0 or val2 == 0) and (warnForZero):
            warnings.warn("multiplying by 0")
        retVal = val1 * val2
    elif op == "shl":
        if (val1 == 0 or val2 == 0) and (warnForZero):
            warnings.warn("shift by 0")
        retVal = val1 * (2 ** (val2))
    else:
        warnings.warn("unsupported arithmatic op")
    return retVal

def Sort_List_Index(list, indexList, *, dontVerifyList=False):
    for i in range(len(list)):
        for j in range(len(list)):
            if i == j:
                continue
            # this line makes sure that there are no collisions, which would mean
            # the specific computation could have been done out of the loop
            assert((indexList[i] != indexList[j]) or dontVerifyList)
            if indexList[i] > indexList[j]:
                temp = list[i]
                tempIdx = indexList[i]
                list[i] = list[j]
                indexList[i] = indexList[j]
                list[j] = temp
                indexList[j] = tempIdx
