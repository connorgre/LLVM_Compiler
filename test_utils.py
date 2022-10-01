
import DFG2 as _dfg
from enum import Enum
import sys
import os

# powershell doesn't like colors
canPrintColors = False

class COLOR(Enum):
    Black=30
    Red=31
    Green=32
    Yellow=33
    Blue=34
    Purple=35
    Cyan=36
    White=37

def PrintResult(result):
    if result:
        Print_With_Bars("Pass", "-", printTop=False, textColor=COLOR.Green)
    else:
        Print_With_Bars("Fail", "$", printTop=False, textColor=COLOR.Red)

def PrintC(color:COLOR):
    if canPrintColors:
        print('\033[;'+str(color.value)+'m', end="")

def Re_Init():
    """
    re-initialize the dfg with output piped to nothing
    """
    origOut = sys.stdout
    origErr = sys.stderr
    noPrint = open(os.devnull, 'w')
    sys.stdout = noPrint
    sys.stderr = noPrint
    dfg = _dfg.DFG("gcn3_strip.ll")
    sys.stdout = origOut
    sys.stderr = origErr
    noPrint.close()
    return dfg

def Print_With_Bars(printStr:str, lineChar:str="#", *, printBottom=True, printTop=True, textColor:COLOR=COLOR.White, barColor:COLOR=COLOR.White):
    lineStr = ""
    for _ in range(90):
        lineStr += lineChar
    if printTop:
        PrintC(barColor)
        print(lineStr)
    PrintC(textColor)
    print(printStr)
    if printBottom:
        PrintC(barColor)
        print(lineStr)
    PrintC(COLOR.White)