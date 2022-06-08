import Parser as p 
import Parse_File as pf
"""
Script to run various tests on the parser.
Tests:
    binary/bitwise
    load
    store
    getelementptr
    phi
    br
"""

print("---\t\tStarting Tests\t\t---")

err = "\tbinary/bitwise -- Error: "
par = p.Instruction("%29 = fadd <16 x float> %wide.load345, %26")
if(par.instruction_type != "binary"):
    print(err + "instruction type wrong")
if(par.args.result != "%29"):
    print(err + "result wrong ")
if(par.args.result_type.printType(False) != "<16 x float>"):
    print(err + "data type wrong")
if(par.args.op1 != "%wide.load345" or par.args.op2 != "%26"):
    print(err + "operands wrong")
if(par.args.instr != "fadd"):
    print(err + "instr wrong")

err = "\tload -- Error: "
par = p.Instruction("%wide.load345 = load <16 x float>, <16 x float>* %28, align 16, !tbaa !2")
if(par.instruction_type != "memory"):
    print(err + "instruction type wrong")
if(par.args.instr != "load"):
    print(err + "instr wrong")
if(par.args.result != "%wide.load345"):
    print(err + "result wrong")
if(par.args.result_type.printType(False) != "<16 x float>"):
    print(err + "result type wrong")
if(par.args.pointer_type.printType(False) != "<16 x float>*"):
    print(err + "pointer type wrong")
if(par.args.pointer != "%28"):
    print(err + "pointer wrong")

err = "\tstore -- Error: "
par = p.Instruction("store <16 x i32> %wide.load, <16 x i32>* %55, align 16, !tbaa !2")
if(par.instruction_type != "memory"):
    print(err + "instruction type wrong")
if(par.args.instr != "store"):
    print (err + "instr wrong")
if(par.args.result != "%wide.load"):
    print(err + "result wrong")
if(par.args.result_type.printType(False) != "<16 x i32>"):
    print(err + "result type wrong")
if(par.args.pointer != "%55"):
    print(err + "pointer wrong")
if(par.args.pointer_type.printType(False) != "<16 x i32>*"):
    print(err + "pointer type wrong")



err = "\tgetelementptr -- Error: "
par = p.Instruction("%27 = getelementptr inbounds [768 x float], [768 x float]* @rf1, i64 0, i64 %10")
if(par.instruction_type != "memory"):
    print(err + "instruction type wrong")
if(par.args.instr != "getelementptr"):
    print(err + "instr wrong")
if(par.args.result != "%27"):
    print(err + "result wrong")
if(par.args.result_type.printType(False) != "[768 x float]"):
    print(err + "result type wrong")
if(par.args.pointer_type.printType(False) != "[768 x float]*"):
    print(err + "pointer type wrong")
if(par.args.pointer != "@rf1"):
    print(err + "pointer wrong")
if(par.args.index_type[0].printType(False) != "i64"):
    print(err + "index[0] type wrong")
if(par.args.index_value[0] != "0"):
    print(err + "index[0] wrong")
if(par.args.index_value[1] != "%10"):
    print(err + "index[1] wrong")
if(par.args.index_type[1].printType(False) != "i64"):
    print(err + "index type[1] wrong")

err = "\tbr -- Error: "
par = p.Instruction("br i1 %45, label %for.cond.cleanup62, label %vector.body335, !llvm.loop !6")
if(par.instruction_type != "terminator"):
    print(err + "instruction type wrong")
if(par.args.instr != "br"):
    print(err + "instr wrong")
if(par.args.condition != "%45"):
    print(err + "condition wrong")
if(par.args.true_target != "%for.cond.cleanup62"):
    print(err + "true target")
if(par.args.false_target != "%vector.body335"):
    print(err + "false target")

err = "\tphi -- Error: "
par = p.Instruction("%index = phi i64 [ 0, %for.cond131.preheader ], [ %index.next, %vector.body ]")
if(par.instruction_type != "Other"):
    print(err + "instruciton type wrong")
if(par.args.instr != "phi"):
    print(err + "instr wrong")
if(par.args.result != "%index"):
    print(err + "result wrong")
if(par.args.result_type.printType(False) != "i64"):
    print(err + "result type wrong")
if(par.args.block_list[0].value != "0"):
    print(err + "block 1 val wrong")
if(par.args.block_list[0].predecessor != "%for.cond131.preheader"):
    print(err + "block 0 pred wrong")
if(par.args.block_list[1].value != "%index.next"):
    print(err + "block 1 value wrong")
if(par.args.block_list[1].predecessor != "%vector.body"):
    print(err + "block 1 pred wrong")
if(len(par.args.block_list) != 2):
    print(err + "block list length wrong")

err = "\tVars used Error: "
print("\n\t***Expect some unhandled instructions here:\t***")
par = pf.Parsed_File('gcn.ll')
print('\n\t***Now expect an error with: %"class.std::ios_base::Init"\t***')
#test to insure that all the variables used
#are in vars used
#this also serves as supplamentary test to the rest of the file
#as improperly formatted inputs will generate errors, and this runs through
#almost all the instructions
for instr in par.Instructions:
    if(instr.args == None):
        continue
    if(instr.instruction_type in ["datalayout", "triple", "define","declare"]):
        continue
    for tok in instr.tokens:
        if(tok == ";"):
            break
        if(len(tok) == 0):
            continue
        if(tok[0] == '%' or tok[0] == '@'):
            if(instr.args.instr == 'br'):
                if(tok == instr.args.true_target or tok == instr.args.false_target):
                    continue
            if(instr.args.instr == "phi"):
                did_break = False
                for block in instr.args.block_list:
                    if(tok == block.predecessor):
                        did_break = True
                if(did_break):
                    continue
            if(instr.args.instr == "call"):
                if(tok == instr.args.function):
                    continue
            if(tok not in instr.args.vars_used):
                print(err + "variable not in vars_used: " + tok)
                print("\tInstr: " + instr.string)
    for var in instr.args.vars_used:
        if(var[0] != "%" and var[0] != "@" and var.isdigit() == False):
            if(instr.args.instr == 'ret' and var == 'void'):
                continue
            print(err + "value not variable or number: " + var)
            print("\tInstr: " + instr.string)
print("\t***End of expected errors\t***")

print("---\t\tEnd of Tests\t\t---")
