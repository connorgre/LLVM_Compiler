from Arg_Type import *
import Parser as p
#instructions of type <result> = <instr> <flags> <type> <arg1>, <arg2>
class Instruction_Args:
    def __init__(self):
        self.instr = "DEFAULT"
        self.instr_type = "DEFAULT"
        self.flags = []
        self.result = "DEFAULT"
    def printArgs(self):
        print("\tInstruction: " + self.instr + ", type: " + self.instr_type)
        print("\tFlags: " + ' '.join(self.flags))

#<result> = [tail | musttail | notail ] call [fast-math flags] [cconv] [ret attrs] [addrspace(<num>)] <ty>|<fnty> <fnptrval>(<function args>) [fn attrs] [ operand bundles ]

class Call_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.result = "DEFAULT"
        self.result_type = Arg_Type()
        self.tail_flags = []
        self.math_flags = []
        self.cconv = "DEFAULT"
        self.ret_attrs = []
        self.addrspace = "DEFAULT"
        self.ty = None
        self.fnty = None
        self.fnptrval = None
        self.fn_attrs = []
        self.operand_bundles = []

class Bitcast_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.instr_type = 'BitCast'
        self.instr = 'bitcast'
        self.result = 'DEFAULT'
        self.result_type = Arg_Type()
        self.op1_type = Arg_Type()
        self.op1 = 'DEFAULT'
    def printArgs(self):
        super().printArgs()
        print("\tResult: " + self.result)
        print("\tOperand: " + self.op1)
        print("\tFrom: " + self.op1_type.printType() + ", to " + self.result_type.printType())

class R_2op_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.result = "DEFAULT"
        self.result_type = Arg_Type()
        self.op1 = "DEFAULT"
        self.op2 = "DEFAULT"
    def printArgs(self):
        super().printArgs()
        print("\tResult: " + self.result)
        print("\top1: " + self.op1 + ", op2: " + self.op2)
        print("\tData Type: " + self.result_type.printType())

class Cmp_Args(R_2op_Args):
    def __init__(self):
        R_2op_Args.__init__(self)
        self.comparison = "DEFAULT"
    def printArgs(self):
        super().printArgs()
        print("\tComparison Type: " + self.comparison)

class Phi_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.result = "DEFAULT"
        self.result_type = Arg_Type()
        self.block_list = []
    def printArgs(self):
        super().printArgs()
        print("\tResult: " + self.result)
        print("\tData Type: " + self.result_type.printType())
        for i in self.block_list:
            print("\t" + i.printPhiBlock())
class Phi_Block():
    def __init__(self, value=None, predecessor=None):
        self.value = value
        self.predecessor = predecessor
    def printPhiBlock(self, do_print=False):
        print_str = "[" + self.value + ", " + self.predecessor + "]"
        if(do_print):
            print(print_str)
        return print_str

class Ret_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.instr = "ret"
        self.instr_type = "Return"
        self.ret_val = "DEFAULT"
        self.ret_type = Arg_Type()
    def printArgs(self):
        super().printArgs()
        print("\tReturn value: " + self.ret_val)
        print("\tReturn type: " + self.ret_type.printType())

#for unconditional branch, condition == 'None', and use 'true_target'
class Branch_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.instr = 'br'
        self.instr_type = "Branch"
        self.condition = "DEFAULT"
        self.true_target = "DEFAULT"
        self.false_target = "DEFAULT"
        self.is_loop = False
        self.loop_info = "DEFUALT"
    def printArgs(self):
        super().printArgs()
        print("\tCondition: " + self.condition)
        print("\tTrue target: " + self.true_target)
        print("\tFalse target: " + self.false_target)
        print("Is Loop: " + str(self.is_loop) + ", Loop Info: " + self.loop_info)

#instructions are named for loads/stores
#but alloca does not use pointer or pointer_type
class Memory_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.instr_type = "Memory"
        self.result = "DEFUALT"
        self.result_type = Arg_Type()
        self.pointer = "DEFUALT"
        self.pointer_type = Arg_Type()
        self.alloca_num_elements = "DEFAULT"
        self.alignment = 0
        self.volatile = False
    def printArgs(self):
        super().printArgs()
        print("\tValue: " + self.result + ", type: " + self.result_type.printType())
        print("\tPointer: " + self.pointer + ", type: " + self.pointer_type.printType())
        print("\tAlignment: " + str(self.alignment))
        print("\tVolatile: " + str(self.volatile))
        print("\talloca numelements: " + str(self.alloca_num_elements))

#will not be implementing the inrange attribute
#will not be 
class GetElementPtr_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.result = "DEFAULT"
        self.result_type = Arg_Type()
        self.pointer_type = Arg_Type()
        self.pointer = "DEFAULT"
        self.is_inbounds = False
        self.index_type = []
        self.index_value = []
    def printArgs(self):
        super().printArgs()
        print("\tResult: " + self.result + ", Type: " + self.result_type.printType())
        print("\tPointer: " + self.pointer + ", Type: " + self.pointer_type.printType())
        print("Is inbounds: " + str(self.is_inbounds))
        type_print = ""
        for i in range(len(self.index_type)):
            type_print += self.index_type[i].printType() + ' '
        print("Index Types: " + type_print)
        print("Index Vals:  " + ' '.join(self.index_value)) 

class ZeroInitializer_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.result = "DEFAULT"
        self.type = Arg_Type()
        self.is_global = False
        self.alignment = 0
    def printArgs(self):
        super().printArgs()
        print("\tResult: " + self.result + ", Type: " + self.type.printType())
        print("\tAlignment: " + str(self.alignment))
        print("\tIs Global: " + str(self.is_global))

class Header_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.target = "DEFAULT"
        self.predecessors = []

    def printArgs(self):
        super().printArgs()
        print("\tTarget: " + self.target)
        print("\tPredecessors: " + ', '.join(self.predecessors))

class Attribute_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.attribute_num = -1
    def printArgs(self):
        super().printArgs()
        print("\tAttribute Num: " + str(self.attribute_num))

class MetaData_Args(Instruction_Args):
    def __init__(self):
        Instruction_Args.__init__(self)
        self.metadata_num = -1
    def printArgs(self):
        super().printArgs()
        print("Metadata num: " + str(self.metadata_num))