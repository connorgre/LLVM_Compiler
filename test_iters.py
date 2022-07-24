import Data_Flow_Graph as dfg_t
import Parse_File as pf

par_f = pf.Parsed_File('gcn3_strip.ll')
dfg = dfg_t.Data_Flow_Graph(par_f)
dfg.Get_Total_Iters()

print("\t Name : self iters : total iters : vector len")
for block in dfg.block_dfgs:
    print("\t" + block.block.name + " : " + str(block.self_iters) + " : " + str(block.num_iters) + " : " + str(block.vector_len))

par_f.Show_Graph()