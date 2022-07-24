import Data_Flow_Graph as dfg_t
import Parse_File as pf

par_f = pf.Parsed_File('gcn3_strip.ll')
dfg = dfg_t.Data_Flow_Graph(par_f)

dfg.Identify_Maccs()
dfg.Identify_Load_Loops()
dfg.Cleanup_All_Old_Nodes()

for block in dfg.block_dfgs:
    block.Make_Graph_2(dfg, True)
    block.Show_Graph()