import RiscV_dfg as RDFG
import Data_Flow_Graph as DFG

dfg = DFG.Data_Flow_Graph('gcn3_strip.ll')
rdfg = RDFG.RiscV_dfg(dfg)

rdfg.Remove_WorkNode_Links()
rdfg.Show_Graph()
rdfg.Remove_Empty_Blocks()
rdfg.Show_Graph()
rdfg.Remove_Pass_Through_Bne()
rdfg.Show_Graph()