#instructions based on llvm formats as defined in 
#https://releases.llvm.org/2.7/docs/LangRef.html#i_fmul

from Instruction_Args import *
from Arg_Type import *


class Instruction:
    """
    holds a single instruction
    stores:
        original string
        tokenized string
        the Instruction_Args representation of the instruction
    """
    #for now, I am assuming these are the types supported on the CPU
    #may need to add more
    group_tokens = ["<",">" , "[","]" , "(",")"]
    scalar_types = ["void","i1","i8","i16","i32","i64","float","double"]
    type_tokens = group_tokens + scalar_types
    #all the possible llvm instructions, going to assume most will not be implemented
    #in the cpu, but doing this groups things better anyways, and will help with organization and error checking
    terminator_instructions = ["ret", "br", "switch", "indirectbr", "invoke", "unwind", "unreachable"]
    binary_instructions = ["add", "fadd", "sub", "fsub", "mul", "fmul", "udiv", "sdiv", "fdiv", "urem", "srem", "frem"]
    bitwise_instructions = ["shl", "lshr", "ashr", "and", "or", "xor"]
    vector_instructions = ["extractelement", "insertelement", "shufflevector"]
    aggregate_instructions = ["extractvalue", "insertvalue"]
    memory_instructions = ["alloca", "load", "store", "getelementptr"]
    conversion_instructions = ["trunc", "zext", "sext", "fptrunc", "fpext", "fptoui", "fptosi", "uitofp", "sitofp", "ptrtoint", "inttoptr", "bitcast"]
    other_instructions = ["icmp", "fcmp", "phi", "select", "call", "va_arg"]
    #takes as input the string of the instruction (1 line)
    def __init__(self, string, line_num=-1, instr_num = -1):
        self.string = string
        self.tokens = []
        self.args:Instruction_Args = None
        self.instruction_type = "DEFAULT"
        self.breakUpInput()
        self.parseTokens()
        self.line_num = line_num
        self.instr_num = instr_num
        self.block_offset = -1    #the line within the block (for ordering instructions)

    #tokenizes the input string
    def breakUpInput(self):
        #special characters in llvm ir, will get their own tokens
        token_breaks = [' ','[', ']', '<', '>', ',',':',';','#','*', '\n', '!','(',')']
        currtok = ""
        str_idx = 0
        in_quote = 0
        while(self.string[str_idx].isspace()):
            str_idx += 1
        while(str_idx < len(self.string)):
            c = self.string[str_idx]
            if(self.string[str_idx] == '"'):
                if(in_quote == 0):
                    in_quote = 1
                else:
                    in_quote = 0
            if(c in token_breaks and in_quote == 0):
                if(currtok != ''):
                    self.tokens.append(currtok)
                currtok = ""
                if(c == '\n'):
                    break
                if(c != ' '):
                    if(c != ''):
                        self.tokens.append(c)
            else:
                currtok += self.string[str_idx]
            str_idx += 1
        if(currtok != ''):
            self.tokens.append(currtok)
        while(len(self.tokens) < 4):
            self.tokens.append("")

    #calls the appropriate instruction parser based on type of instruction
    #These are grouped based on the llvm manual grouping
    #the indexing is based on the assumption the llvm ir won't have llvm instructions anwhere they are not expected
    def parseTokens(self):
        #branch and ret only for now
        if(self.tokens[0] in self.terminator_instructions):
            #done
            self.instruction_type = "terminator"
            self.ParseTerminatorInstr()
        elif("!" == self.tokens[0]):
            self.instruction_type = "metadata"
            self.args = MetaData_Args()
        elif(";" == self.tokens[0]):
            self.instruction_type = "comment"
            self.args = Instruction_Args()
            self.args.instruction_type = "comment"
        elif("zeroinitializer" in self.tokens):
            self.instruction_type = "zeroinitializer"
            self.ParseZeroInitializer()
        elif("attributes" == self.tokens[0]):
            self.instruction_type = "attribute"
            self.args = Attribute_Args()
            self.args.attribute_num = int(self.tokens.index("#") + 1)
        #arithmatic
        elif(":" == self.tokens[1]):
            self.instruction_type = "header"
            self.ParseHeaderInstr()
        elif(self.tokens[2] in self.binary_instructions):
            #done
            self.instruction_type = "binary"
            self.ParseBinaryInstr()
        #arithmatic
        elif(self.tokens[2] in self.bitwise_instructions):
            #done
            self.instruction_type = "bitwise"
            self.ParseBitwiseInstr()
        #data operations on vector data
        elif(self.tokens[2] in self.vector_instructions):
            self.instruction_type = "vector"
            self.ParseVectorInstr()
        #data operations on aggregate data (array/vector)
        elif(self.tokens[2] in self.aggregate_instructions):
            self.instruction_type = "aggregate"
            self.ParseAggregateInstr()
        #convert data types (I dont think I will have these)
        elif(self.tokens[2] in self.conversion_instructions):
            self.instruction_type = "conversion"
            self.ParseConversionInstr()
        #other misc instructions (need index 3 for the call instruction)
        elif(self.tokens[2] in self.other_instructions or self.tokens[3] in self.other_instructions or "call" in self.tokens):
            self.instruction_type = "other"
            self.ParseOtherInstr()
        #memory access instructions
        elif(self.tokens[0] in self.memory_instructions or self.tokens[1] in self.memory_instructions or self.tokens[2] in self.memory_instructions or self.tokens[3] in self.memory_instructions):
            self.instruction_type = "memory"
            self.ParseMemoryInstr()
        elif("source_filename" == self.tokens[0]):
            self.instruction_type = "filename"
            self.args = Instruction_Args()
            self.args.instr = self.tokens[2]
        elif("datalayout" == self.tokens[1]):
            self.instruction_type = "datalayout"
            self.args = Instruction_Args()
            self.args.instr = self.tokens[3]
        elif("triple" == self.tokens[1]):
            self.instruction_type = "triple"
            self.args = Instruction_Args()
            self.args.instr = self.tokens[3]
        elif("define" == self.tokens[0]):
            self.instruction_type = "define"
            self.args = Instruction_Args()
        elif("declare" == self.tokens[0]):
            self.instruction_type = "declare"
            self.args = Instruction_Args()
        elif("}" == self.tokens[0]):
            self.instruction_type = "function end"
            self.args = Instruction_Args()
        else:
            print("Instr not recognized: " + self.string)
            return
        #calling this here because it is a method to every arg class
        #that fills it out for its own thing
        if(self.args != None):
            self.args.getVarsUsed()


    """
    Not going to comment explicitly all of how these were created.  I just followed the llvm 
    reference documentation for each instruction.  Call is not fully implemented **yet** because
    I am not sure how it will be implemented as assembly, becasue it is calling memset and memcpy,
    if need be, I will add parsing for these two explicitly but it is not high on the to-do list right now,
    and will be implemented when I do the translation to assembly
    """
    #for now, only implementing ret and br, I don't think
    #the cpu instructions will be complicated enough to require the others
    def ParseTerminatorInstr(self):
        #   ret void
        #   ret <type> <value>
        if(self.tokens[0] == 'ret'):
            self.args = Ret_Args()
            if(self.tokens[1] == 'void'):
                self.args.ret_type.type_str = "void"
                self.args.ret_val = "void"
            else:
                self.args.ret_type.Get_Type(self.tokens, 1)
                self.args.ret_val = self.tokens[2]
        #   br i1 <cond>, label <iftrue>, label <iffalse>
        #   br label <dest>
        elif(self.tokens[0] == 'br'):
                self.args = Branch_Args()
                if(self.tokens[1] == 'label'):
                    self.args.condition = "None"
                    self.args.true_target = self.tokens[2]
                    self.args.false_target = self.tokens[2]
                else:
                    #5 and 8 addresses are because commas are counted as a token
                    self.args.condition = self.tokens[2]
                    self.args.true_target = self.tokens[5]
                    self.args.false_target = self.tokens[8]
                if('llvm.loop' in self.tokens):
                    self.args.is_loop = True
                    idx = self.tokens.index('llvm.loop')
                    self.args.loop_info = self.tokens[idx + 2]
        else:
            print("Error: instruction not implemented")

    #for binary and bitwise instructions, cannot use constant value vector operands (vector registers are ok)
    #   <result> = <instr> <flags> <type> <op1> , <op2>
    def ParseBinaryInstr(self):
        self.args = R_2op_Args()
        self.args.result = self.tokens[0]
        self.args.instr = self.tokens[2]
        self.args.instr_type = "R_2op"
        token_idx = 3
        flag_end = self.scalar_types + self.group_tokens
        #parse through the 
        while(self.tokens[token_idx] not in flag_end):
            self.args.flags.append(self.tokens[token_idx])
            token_idx += 1
        #if it is a scalar instruction
        token_idx = self.args.result_type.Get_Type(self.tokens, token_idx)
        token_idx += 1
        self.args.op1 = self.tokens[token_idx]
        token_idx += 2      #there will be a comma that needs to be skipped
        self.args.op2 = self.tokens[token_idx]
        if(token_idx != len(self.tokens)-1):
            print("Error, token_idx should be at end (binary)") 
        return
    
    #   <result>  = <instr> <flags> <type> <op1>, <op2>
    def ParseBitwiseInstr(self):
        #all the instructions look the exact same as Binary,
        #so can just use this
        self.ParseBinaryInstr()
    
    def ParseVectorInstr(self):
        print("Error: Parse Vector Instrucionts not Implemented")
        return

    def ParseAggregateInstr(self):
        print("Error: Parse Aggregate Instructions not implemented")
        return

    #cannot use a constant value vector as result 
    #can use vector type if loading from register
    def ParseMemoryInstr(self):
        #getelementptr
        if('getelementptr' in self.tokens):
            self.args = GetElementPtr_Args()
            self.args.result = self.tokens[0]
            self.args.instr = "getelementptr"
            self.args.instr_type = "Memory"
            idx = self.tokens.index('getelementptr')
            idx += 1
            if(self.tokens[idx] == 'inbounds'):
                self.args.is_inbounds = True
                idx += 1
            idx = self.args.result_type.Get_Type(self.tokens, idx)
            idx += 2    #+2 bc there will be a comma
            idx = self.args.pointer_type.Get_Type(self.tokens,idx)
            idx += 1
            self.args.pointer = self.tokens[idx]
            idx += 1
            while(idx != len(self.tokens) and self.tokens[idx] != ""):
                #print("going through rest of array")
                idx += 1
                #don't need the return value becaus only i32, taking up only 1 space
                newarg = Arg_Type()
                newarg.Get_Type(self.tokens, idx)
                self.args.index_type.append(newarg)
                idx += 1
                self.args.index_value.append(self.tokens[idx])
                idx += 1
        else:
            self.args = Memory_Args()
            if('align' in self.tokens):
                idx = self.tokens.index('align')
                self.args.alignment = int(self.tokens[idx + 1])
            if('volatile' in self.tokens):
                self.args.volatile = True
            if('store' in self.tokens):
                self.args.instr = 'store'
            elif('load' in self.tokens):
                self.args.instr = 'load'
                self.args.result = self.tokens[0]
            elif('alloca' in self.tokens):
                self.args.instr = 'alloca'
                self.args.result = self.tokens[0]
                self.args.result_type.Get_Type(self.tokens, 3)
                idx = self.tokens.index(',')
                idx = Arg_Type().Get_Type(self.tokens, idx + 1)
                self.args.alloca_num_elements = self.tokens[idx + 1]
                return
            else:
                print("Error, instr not found (memory)")
            #scan forward until the first token
            idx = 0
            while(self.tokens[idx] not in self.type_tokens):
                idx += 1
            idx = self.args.result_type.Get_Type(self.tokens, idx)
            if(self.args.instr == 'store'):
                self.args.result = self.tokens[idx + 1]
            idx = self.tokens.index(',')
            idx += 1
            idx = self.args.pointer_type.Get_Type(self.tokens,idx)
            self.args.pointer = self.tokens[idx + 1]
            
    def ParseConversionInstr(self):
        self.instruction_type = "Conversion"
        if('bitcast' in self.tokens):
            self.args = Bitcast_Args()
            self.args.result = self.tokens[0]
            idx = self.tokens.index('bitcast')
            idx = self.args.op1_type.Get_Type(self.tokens, idx + 1)
            self.args.op1 = self.tokens[idx + 1]
            idx = self.tokens.index('to')
            self.args.result_type.Get_Type(self.tokens, idx + 1)
        else:
            print('Error, only bitcast conversion instruction implemented')
        return

    def ParseOtherInstr(self):
        self.instruction_type = 'Other'
        if('icmp' in self.tokens or 'fcmp' in self.tokens):
            self.args = Cmp_Args()
            self.args.result = self.tokens[0]
            self.args.instr_type = "Comparison"
            self.args.instr = self.tokens[2]
            idx = 3
            #this will put all the [fast-math flags]* in the flags
            while(self.tokens[idx+1] not in self.type_tokens):
                self.args.flags.append(self.tokens[idx])
                idx += 1
            self.args.comparison = self.tokens[idx]
            idx = self.args.result_type.Get_Type(self.tokens, idx + 1)
            self.args.op1 = self.tokens[idx + 1]
            self.args.op2 = self.tokens[idx + 2]
        elif('phi' in self.tokens):
            self.args = Phi_Args()
            self.args.result = self.tokens[0]
            self.args.instr = "phi"
            self.args.instr_type = "Phi"
            idx = 3
            #this will put all the [fast-math flags]* in the flags
            while(self.tokens[idx+1] not in self.type_tokens):
                self.args.flags.append(self.tokens[idx])
                idx += 1
            idx = self.args.result_type.Get_Type(self.tokens, idx)
            idx += 1    #puts us on the [ of phi block
            while(idx < len(self.tokens)):
                phi_b = Phi_Block(self.tokens[idx + 1], self.tokens[idx + 3])
                self.args.block_list.append(phi_b)
                idx += 6       #puts on [ of next block
        elif('call' in self.tokens):
            #<result> = [tail | musttail | notail ] call [fast-math flags] [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs] [ operand bundles ]
            # only implementing @llvm.memset.p0i8.i64 and @llvm.memcpy.p0i8.p0i8.i64
            # these are the only ones in the program that appear to have any effect
            if("@llvm.memcpy.p0i8.p0i8.i64" != self.tokens[2] and "@llvm.memset.p0i8.i64" != self.tokens[2]):
                print("only memset and memcpy call implemented")
                return
            if(self.tokens[2] == "@llvm.memcpy.p0i8.p0i8.i64"):
                self.ParseMemcpy()
            else:
                self.ParseMemset()
            idx = 0
            self.args.instr = 'call'
            self.args.instr_type = "Function Call"
            self.args.function = self.tokens[2]
            #assumes src and dest have same alignment/ dereferencable
            if("align" in self.tokens):
                idx = self.tokens.index("align")
                self.args.align = int(self.tokens[idx + 1])
            if("dereferenceable" in self.tokens):
                idx = self.tokens.index("dereferenceable")
                self.args.dereferenceable = int(self.tokens[idx + 2])
            if("nonnull" in self.tokens):
                self.args.non_null = True
            
        return

    #call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) <dest>, i8* nonnull align 16 dereferenceable(64) <source>, i64 <length>, i1 <volatile>)
    def ParseMemcpy(self):
        self.args = Call_Args()
        idx = 4 #puts it at i8*
        idx = self.args.result_type.Get_Type(self.tokens, idx)

        #go forward until we get to the dest variable
        #(so skip all the pointer referencing info)
        while(self.tokens[idx][0] != "@" and self.tokens[idx][0] != "%"):
            idx += 1
        self.args.result = self.tokens[idx]
        idx += 2
        idx = self.args.value_type.Get_Type(self.tokens, idx)
        while(self.tokens[idx][0] != "@" and self.tokens[idx][0] != "%"):
            idx += 1
        self.args.value = self.tokens[idx]
        idx += 3
        self.args.length = int(self.tokens[idx])
        idx += 3
        self.args.is_volatile = self.tokens[idx]


    #call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf0, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)
    def ParseMemset(self):
        self.args = MemsetArgs()
        if("getelementptr" in self.tokens):
            idx = self.tokens.index("getelementptr")
        else:
            print("memset parsing error, expected a getelementptr call")
            return
        #scan forward until the start of the getelement ptr args
        while(self.tokens[idx] != "("):
            idx += 1
        idx += 1
        idx = Arg_Type().Get_Type(self.tokens, idx)
        idx += 2
        idx = self.args.result_type.Get_Type(self.tokens, idx)
        idx += 1
        self.args.result = self.tokens[idx]
        idx += 6
        self.args.pointer_offset = int(self.tokens[idx])    #right now we are at 512 in the example above
        while(self.tokens[idx] != ',' and idx < len(self.tokens)):
            idx += 1
        idx += 1
        idx = self.args.value_type.Get_Type(self.tokens,idx)
        if(self.args.value_type.printType() != "i8"):
            print("error, memset should only use i8")
        idx += 1
        self.args.value = self.tokens[idx]
        idx += 3
        self.args.length = int(self.tokens[idx])
        idx += 3
        self.args.is_volatile = self.tokens[idx]




    def ParseZeroInitializer(self):
        self.instruction_type = "Zero Initializer"
        self.args = ZeroInitializer_Args()
        self.args.instr_type = "Zero Initializer"
        self.args.instr = "zeroinitializer"
        self.args.result = self.tokens[0]
        idx = 2
        while(self.tokens[idx] not in (self.type_tokens + ["global"])):
            self.args.flags.append(self.tokens[idx])
            idx += 1
        if(self.tokens[idx] == "global"):
            self.args.is_global = True
            idx += 1
        idx = self.args.type.Get_Type(self.tokens, idx)
        idx += 1
        if(self.tokens[idx] != "zeroinitializer"):
            print("Error, this should be zeroinitializer: " + self.tokens[idx])
        if("align" in self.tokens):
            idx = self.tokens.index("align")
            self.args.alignment = int(self.tokens[idx + 1])

        return
    
    def ParseHeaderInstr(self):
        self.args = Header_Args()
        self.args.target = self.tokens[0]
        self.args.instr_type = "Header"
        self.args.instr = "None"
        if("preds" in self.tokens):
            idx = self.tokens.index("preds")
            idx += 2
            self.args.predecessors.append(self.tokens[idx])
            while(idx+1 < len(self.tokens)):
                idx += 2
                self.args.predecessors.append(self.tokens[idx])

    def Print_Instruction(self):
        print("String: " + self.string)
        print("Tokens: " + " ".join(self.tokens))
        print("Args: ")
        self.args.printArgs()
        print("Linenum: " + str(self.line_num) + ", Instrnum: " + str(self.instr_num))
        print("Block linenum: " + str(self.block_offset))





