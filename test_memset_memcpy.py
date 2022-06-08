import Parse_File as pf
import Parser as p

"""
Tests for memset and memcpy
"""

print("\t-- Starting Tests --")

par = p.Instruction("call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf3, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)")

err = "-- Memset Error: "
if(par.args.function != "@llvm.memset.p0i8.i64"):
    print(err + "function wrong")
if(par.args.result != "@rf3"):
    print(err + "result")
if(par.args.result_type.printType() != "[768 x float]*"):
    print(err + "result type")
if(par.args.value != "0"):
    print(err + "value")
if(par.args.value_type.printType() != "i8"):
    print(err + "value type")
if(par.args.dereferenceable != 1024):
    print(err + "dereferencable")
if(par.args.length != 1024):
    print(err + "length")
if(par.args.non_null != True):
    print(err + "nonull")
if(par.args.is_volatile != "false"):
    print(err + "volatile")
if(par.args.pointer_offset != 512):
    print(err + "pointer offset")

par = p.Instruction("call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) %scevgep265, i8* nonnull align 16 dereferenceable(64) %scevgep268269, i64 64, i1 false)")

err = "-- Memcpy Error: "
if(par.args.function != "@llvm.memcpy.p0i8.p0i8.i64"):
    print(err + "function wrong")
if(par.args.result != "%scevgep265"):
    print(err + "result")
if(par.args.result_type.printType() != "i8*"):
    print(err + "result type")
if(par.args.value != "%scevgep268269"):
    print(err + "value")
if(par.args.value_type.printType() != "i8*"):
    print(err + "value type")
if(par.args.dereferenceable != 64):
    print(err + "dereferencable")
if(par.args.length != 64):
    print(err + "length")
if(par.args.non_null != True):
    print(err + "nonull")
if(par.args.is_volatile != "false"):
    print(err + "volatile")

print("\t-- Ending Tests --")