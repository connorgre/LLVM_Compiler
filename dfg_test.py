import Data_Flow_Graph
import Parse_File as pf

par = pf.Parsed_File('gcn.ll')
dfg = Data_Flow_Graph.Data_Flow_Graph(par)
print()
for i in range(5):
    print("**\t\t--" + str(i) + "--\t\t**")
    dfg.variables[i].Print_Node()

err = "\tError: assigned not used: "
for node in dfg.variables:
    if(len(node.uses) < 1):
        print(err + node.name)

err  = "\tError: used location not actually used in instruction: "
err1 = "\tError: use not found: "
err2 = "\tError: block offset doesn't return same value for assignment: "
err3 = "\tError: node instruction != block instruction"
for idx, node in enumerate(dfg.variables):
    if node != dfg.Get_Node_Block_Offset(node.assignment):
        print(err2 + str(node.name))
    for use in node.uses:
        use_node = dfg.Get_Node_Block_Offset(use)
        use_instr = dfg.Get_Instruction_Block_Offset(use)
        if use_node == None:
            #instructions that dont actually assign to anything
            if use_instr.args.instr not in ["call", "br", "store"]:
                print(err1 + str(node.name) + ", " + str(use))
            if node.name not in use_instr.tokens:
                print(err + str(node.name) + ", " + str(node.assignment) +", " + str(use))
        else: 
            if node.name not in use_node.instruction.tokens:
                print(err + str(node.name) + ", " + str(use))
            if use_node.instruction != use_instr:
                print(err3 + str(node.name) + ", " + str(use))

print("\n\n\n")
dfg.block_dfgs[6].Print_Vars()
print("\nTesting Done\n")
