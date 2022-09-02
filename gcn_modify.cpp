#define N 1024
#define D 16
#define NUM_SIMD_LANES 16
#define NUM_COL 4 
#define TK 32
#define TM 16

// only here to make the intellisense happy
typedef float FpOut;    // stream out
typedef float FpIn;     // stream in
typedef float FpMem;    // outside memory
typedef float FpReg;    // register file

FpOut stream_out [N];
FpIn stream_in [N*N]; 
FpMem hbm0 [N];
FpReg rf0 [NUM_SIMD_LANES*(TK+TM)]; 

int main(int argc, char const *argv[])
{    
    const int m_trip_count = (int) (N/NUM_SIMD_LANES);
    const int tm_trip_count = (int) (m_trip_count/TM);
    const int tk_trip_count = (int) (N/TK);
    const int trf_trip_count = TM;

    int hbm_idx; 
    int rf_idx1;
    int rf_idx2;
    int rf_idx3;
    int rf_idx4;
    int rf_idx5;
    int sin_idx;
    int sout_idx;

    for (int tm = 0; tm < tm_trip_count; tm++)
    {
        #pragma Fp_vle
        for (int trf = 0; trf < trf_trip_count; trf++)
        { 
            for (int lane0 = 0; lane0 < NUM_SIMD_LANES; lane0++)
            {
                rf_idx1 = TK*NUM_SIMD_LANES + trf*NUM_SIMD_LANES + lane0;
                rf0[rf_idx1] = 0.0;
            }
        }

        #pragma Fp_vle
        for (int tk = 0; tk < tk_trip_count; tk++)
        {   
            for (int k = 0; k < TK; k++)
            { 
                for (int lane1 = 0; lane1 < NUM_SIMD_LANES; lane1++)
                {
                    rf_idx2 = k*NUM_SIMD_LANES + lane1;
                    hbm_idx = tk*TK*NUM_SIMD_LANES + k*NUM_SIMD_LANES + lane1;
                    rf0[rf_idx2] = hbm0[hbm_idx];
                }
            }

            #pragma Fp_macc(16) rf0[512->768 x16] += stream_in[0->8192 x512]*rf0[0:512]
            for (int k2 = 0; k2 < TK; k2++)
            {
                for (int m=0; m < TM; m++)
                {
                    #pragma FP_vector
                    for(int lane2 = 0; lane2 < NUM_SIMD_LANES; lane2++)
                    {
                        rf_idx3 = NUM_SIMD_LANES*(TK+m) + lane2;
                        rf_idx4 = k2*NUM_SIMD_LANES + lane2;
                        sin_idx = tm*tk_trip_count*TM*TK*NUM_SIMD_LANES +
                                    tk*TM*TK*NUM_SIMD_LANES +
                                    m*TK*NUM_SIMD_LANES +
                                    k2*NUM_SIMD_LANES +
                                    lane2;
                        float mulRes = stream_in[sin_idx]*rf0[rf_idx4];
                        rf0[rf_idx3] += mulRes;
                    }
                }
            }
        }

        #pragma Fp_streamout
        for (int m2 = 0; m2 < TM; m2++)
        { 
            for (int lane3 = 0; lane3 < NUM_SIMD_LANES; lane3++)
            {
                rf_idx5 = NUM_SIMD_LANES*(TK+m2) + lane3;
                sout_idx = tm*TM*NUM_SIMD_LANES + m2*NUM_SIMD_LANES + lane3;
                stream_out[sout_idx] = rf0[rf_idx5];
            }
        }
    }
    return 0;
}