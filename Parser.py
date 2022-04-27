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
    def __init__(self, string):
        self.string = string
        self.tokens = []
        self.args = None
        self.breakUpInput()
        self.parseTokens()

    #tokenizes the input string
    def breakUpInput(self):
        #special characters in llvm ir, will get their own tokens
        token_breaks = [' ','[', ']', '<', '>', ',',':',';','#','*','\"', '\n', '!']
        currtok = ""
        str_idx = 0
        while(str_idx < len(self.string)):
            c = self.string[str_idx]
            if(c in token_breaks):
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

    #calls the appropriate instruction parser based on type of instruction
    #These are grouped based on the llvm manual grouping
    #the indexing is based on the assumption the llvm ir won't have llvm instructions anwhere they are not expected
    def parseTokens(self):
        #branch and ret only for now
        if(self.tokens[0] in self.terminator_instructions):
            #done
            self.instruction_type = "terminator"
            self.ParseTerminatorInstr()
        #arithmatic
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
        #memory access instructions
        elif(self.tokens[0] in self.memory_instructions or self.tokens[1] in self.memory_instructions or self.tokens[2] in self.memory_instructions or self.tokens[3] in self.memory_instructions):
            self.instruction_type = "memory"
            self.ParseMemoryInstr()
        #convert data types (I dont think I will have these)
        elif(self.tokens[2] in self.conversion_instructions):
            self.instruction_type = "conversion"
            self.ParseConversionInstr()
        #other misc instructions (need index 3 for the call instruction)
        elif(self.tokens[2] in self.other_instructions or self.tokens[3] in self.other_instructions):
            self.instruction_type = "other"
            self.ParseOtherInstr()
        else:
            print("Error: instruction not recognized\n")
            return

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
        else:
            print("Error: instruction not implemented\n")

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
        token_idx = self.args.data_type.Get_Type(self.tokens, token_idx)
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
            while(idx != len(self.tokens)):
                print("going through rest of array")
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
                self.args.value = self.tokens[0]
            elif('alloca' in self.tokens):
                self.args.instr = 'alloca'
                self.args.value = self.tokens[0]
                self.args.value_type.Get_Type(self.tokens, 3)
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
            idx = self.args.value_type.Get_Type(self.tokens, idx)
            if(self.args.instr == 'store'):
                self.args.value = self.tokens[idx + 1]
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
            idx = self.args.op_type.Get_Type(self.tokens, idx + 1)
            self.args.op_value = self.tokens[idx + 1]
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
            idx = self.args.data_type.Get_Type(self.tokens, idx + 1)
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
            idx = self.args.data_type.Get_Type(self.tokens, idx)
            idx += 1    #puts us on the [ of phi block
            while(idx < len(self.tokens)):
                phi_b = Phi_Block(self.tokens[idx + 1], self.tokens[idx + 3])
                self.args.block_list.append(phi_b)
                idx += 6       #puts on [ of next block
        elif('call' in self.tokens):
            #<result> = [tail | musttail | notail ] call [fast-math flags] [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs] [ operand bundles ]
            # i think i can ignore [fast-math flags], [cconv], <fnty>, 
            print("***not finished implementing***")
            idx = 0
            self.args = Call_Args()
            self.instr = 'call'
            self.instr_type = "Function Call"
            if(self.tokens[1] == '='):
                self.args.result = self.tokens[0]
                idx = 2
            while(self.tokens[idx] != 'call'):
                self.args.tail_flags.append(self.tokens[idx])
                idx += 1
            if(self.tokens[idx] != 'call'):
                print("error, should be call")
            idx += 1  
        return


        







