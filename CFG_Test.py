import Parse_File as pf
import Parser as p 

"""
Testing the block ordering for the Control Flow Graph
"""


par_f = pf.Parsed_File("gcn.ll")

err = "ordered index error"
for idx in range(len(par_f.blocks)):
    if(par_f.Get_Order_Idx(idx).block_order != idx):
        print(err)

#manually going through each block in order and 
#verifying that they are correct
 
block_names = [
    'entry',
    'for.cond1.preheader',
    'for.cond16.preheader',
    'for.cond20.preheader',
    'for.cond52.preheader',
    'for.cond56.preheader',
    'for.cond60.preheader',
    'vector.body335',
    'for.cond.cleanup62',
    'for.cond.cleanup58',
    'for.cond.cleanup54',
    'for.cond127.preheader',
    'for.cond131.preheader',
    'vector.body',
    'for.cond.cleanup133',
    'for.cond.cleanup129',
    'for.cond.cleanup',
    'entry'
    ]

err = "\tError: ordered name wrong"
for idx in range(len(par_f.blocks)):
    if(par_f.Get_Order_Idx(idx).name != block_names[idx]):
        print(err)

loop_entries = [
    'for.cond1.preheader',
    'for.cond16.preheader',
    'for.cond20.preheader',
    'for.cond56.preheader',
    'for.cond60.preheader',
    'vector.body335',
    'for.cond131.preheader',
    'vector.body'
    ]

loop_exits = [
'for.cond20.preheader',
'vector.body335',
'for.cond.cleanup62',
'for.cond.cleanup58',
'for.cond.cleanup54',
'vector.body',
'for.cond.cleanup133',
'for.cond.cleanup129'
]

err = "\tError: "
prev_depth = 0
num_entry = 0
num_exit = 0
was_prev_exit = False
for idx in range(len(par_f.blocks)):
    block = par_f.Get_Order_Idx(idx)
    if(idx == 0 and block.loop_depth != 0):
        print(err + "first block not depth 0")
    if(was_prev_exit):
        if(block.loop_depth != prev_depth - 1):
            print(err + "exit depth wrong")
    if(was_prev_exit == False and block.is_loop_entry == False):
        if(prev_depth != block.loop_depth):
            print(err + "depth != prev depth on no change")
    was_prev_exit = False
    if(block.is_loop_entry):
        num_entry += 1
        if(block.name not in loop_entries):
            print(err + "mislabled entry")
        if(prev_depth + 1 != block.loop_depth):
            print(err + "entry depth wrong")
    if(block.is_loop_exit):
        num_exit += 1
        if(block.name not in loop_exits):
            print(err + "mislabled exit")
        was_prev_exit = True
    prev_depth = block.loop_depth
if(num_entry != len(loop_entries)):
    print(err + "wrong num of loop entries")
if(num_exit != len(loop_exits)):
    print(err + "wrong number of loop exits")
