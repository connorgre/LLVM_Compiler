import Data_Flow_Graph as dfg_t
import Parse_File as pf

dfg = dfg_t.Data_Flow_Graph('gcn3_strip.ll')

dfg.Identify_Maccs()
