import networkx as nx
import matplotlib.pyplot as plt
import Data_Flow_Graph as dfgm
import Parse_File as pf
from networkx.drawing.nx_agraph import write_dot, graphviz_layout
import sys

def main(blocknum=3):
    par = pf.Parsed_File('gcn2_strip.ll')
    dfg = dfgm.Data_Flow_Graph(par)

    block = dfg.block_dfgs[blocknum]

    block.Make_Graph(dfg, True)
    block.Show_Graph()


if __name__ == '__main__':
    if(len(sys.argv) == 1):
        blocknum = 3
    else:
        blocknum = int(sys.argv[1])

    main(blocknum)