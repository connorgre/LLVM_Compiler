// x5 holds tm
// x6 holds tm_trip_count (fixed number)

// x7 holds the HBM address
// x28 offset for incrementing HBM address
// if the number of iterations is bigger than 2048 then use for loop otherwise, you can omit the for loop

// x29 holds tk
// x30 holds tk_trip_count

// x31 holds m
// x1 holds TM 

// starting address of HBM data is 0x1000
// assuming HBM memory is byte-addressable

            // LOOP_TM
            addi x5, x0, 0x000 // init to zero
            addi x6, x0, 0x004 // 4
            // LOOP_TK
            addi x30, x0, 0x020 // 32
            addi x29, x0, 0x000 // init to zero
            # //LOOP_M
            # addi x1, x0, 0x010 // 16
            # addi x31, x0, 0x000 // init to zero

            // configuring VLEN // based on RF access pattern (for example lets say you have an offset and then a for loop (like TRF) you can determine 3-bit VLEN 
            // then you know which index you should use for VRF
            # vsetivli zero, 8, e32, m2, 256

            // starting address of HBM
            lui x7, 0x00001 // x7 is now equal to 0x1000 which is 4096 in decimal
            addi x28, x0, 0x800 /// equal to 2 K

LOOP_TM:    vsetivli zero, 8, e32, m2, 256
            vle32.v v1, (x0) // vectorization for LOOP_TRF
LOOP_TK:    vsetivli zero, 8, e32, m2, 32
            vle32.v v0, (x7) // vectorization for LOOP_K
            add x7, x7, x28 // LOOP_K

            vsetivli zero, 8, e32, m2, 32 // LOOP_M
            vmacc.v v1, v0, vs // vs is stream_in 
            vmacc.v v2, v0, vs
            vmacc.v v3, v0, vs
            vmacc.v v4, v0, vs
            vmacc.v v5, v0, vs
            vmacc.v v6, v0, vs
            vmacc.v v7, v0, vs
            vmacc.v v8, v0, vs
            vmacc.v v9, v0, vs
            vmacc.v v10, v0, vs
            vmacc.v v11, v0, vs
            vmacc.v v12, v0, vs
            vmacc.v v13, v0, vs
            vmacc.v v14, v0, vs
            vmacc.v v15, v0, vs
            vmacc.v v16, v0, vs

            addi x29, x29, 0x001 // LOOP_TK
            bne x29, x30, LOOP_TK // LOOP_TK
            
            streamout.v v1 // LOOP_MSOUT
            
            addi x5, x5, 0x001 // LOOP_TM
            bne x5, x6, LOOP_TM // LOOP_TM
