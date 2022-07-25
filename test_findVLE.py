

import Data_Flow_Graph as dfg_t
import Parse_File as pf

par_f = pf.Parsed_File('gcn3_strip.ll')
dfg = dfg_t.Data_Flow_Graph(par_f)

dfg.Identify_Load_Loops()

for idx in range(len(dfg.block_dfgs)):
    dfg.block_dfgs[idx].Make_Graph_2(dfg)
    dfg.block_dfgs[idx].Show_Graph()

#dfg.block_dfgs[2].Identify_Load_Loop(dfg)
dfg.block_dfgs[2].Make_Graph_2(dfg)
dfg.block_dfgs[2].Show_Graph()