import networkx as nx
import matplotlib.pyplot as plt
import Data_Flow_Graph as dfgm
import Parse_File as pf
from networkx.drawing.nx_agraph import write_dot, graphviz_layout


par = pf.Parsed_File('gcn.ll')
dfg = dfgm.Data_Flow_Graph(par)

block = dfg.block_dfgs[3]

block.Make_Graph(dfg, True)
block.Show_Graph()