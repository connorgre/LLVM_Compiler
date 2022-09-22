import RiscV_dfg as RDFG
import Data_Flow_Graph as DFG

dfg = DFG.Data_Flow_Graph('gcn3_strip.ll')

rdfg = RDFG.RiscV_dfg(dfg, False)

rdfg.Show_Graph()
rdfg.Remove_WorkNode_Links()
rdfg.Remove_Empty_Blocks()
rdfg.Remove_Pass_Through_Bne()
rdfg.Remove_Useless_Loops()
rdfg.Remove_All_Macc_Unrolls()
rdfg.Remove_Unused_Targets()
rdfg.Fill_Out_IterNames()
rdfg.Show_Graph()
rdfg.Add_Load_Pointers()

# nodeList = rdfg.Get_Execution_Order_List()
# for node in nodeList:
#     print(node.name)
#     if node.is_block or node.is_bne:
#         print("\t" + str(node.num_iters))

# print("*****************************")
# for node in nodeList:
#     if(node.is_vle or node.is_macc):
#         node.Print_Node()
#         print("/////////////////////")

# print("*****************************")
# for node in nodeList:
#     if(node.is_vle):
#         print(node.name)
#         print("\t" + node.Get_vsetivli())
#         print("\t" + node.Get_RiscV_Instr())
#         print("/////////////////////")

# print("*****************************")
# for node in nodeList:
#     print()
#     #print("========================================================")
#     if (node.is_vle or node.is_macc):
#         print(node.Get_vsetivli())
#     print(node.Get_RiscV_Instr())

# print("\n\n")
print("EVERYTHING ABOVE HERE IS DEBUG MESSAGES I STILL")
print("HAVE TO TRACK DOWN!!")
print("#######################################################")
print(rdfg.Get_ASM_String())

rdfg.Show_Graph()
