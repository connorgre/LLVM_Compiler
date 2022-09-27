import DFG_Node2 as dfgn
import DFG2 as _dfg
import Block_DFG2 as bdfg
import SDFG_Node2 as sdfgn

def main():
    dfg = _dfg.DFG("gcn3_strip.ll")
    dfg.blockDFGs[5].Create_Macc()
    dfg.blockDFGs[5].Show_Graph()
    #for block in dfg.blockDFGs[5]:
    #    block.Show_Graph(dfg)
    #return

if __name__ == '__main__':
    main()