#include <iostream>
#include <fstream>
// #include <chrono>

// size of matrices
// A[NxN]*Y[NxD]

#define N 1024
#define D 16
#define NUM_SIMD_LANES 16
#define NUM_COL 4 // numbber of columns for cgra
#define TK 32
#define TM 16

float stream_out [N*NUM_COL];


int main(int argc, char const *argv[]) {
  //send_data(inbound);
  //send_data(stream_in);
  
  float rf0 [NUM_SIMD_LANES*(TK+TM)]; //register files (first column)
  float rf1 [NUM_SIMD_LANES*(TK+TM)]; //register files (second column)
  float rf2 [NUM_SIMD_LANES*(TK+TM)]; //register files (third column)
  float rf3 [NUM_SIMD_LANES*(TK+TM)]; //register files (fourth column)

  // float* rf0 = new float[NUM_SIMD_LANES*(TK+TM)]; //register files (first column)
  // float* rf1 = new float[NUM_SIMD_LANES*(TK+TM)]; //register files (second column)
  // float* rf2 = new float[NUM_SIMD_LANES*(TK+TM)]; //register files (third column)
  // float* rf3 = new float[NUM_SIMD_LANES*(TK+TM)]; //register files (fourth column)

  // rf is encoded in this way: (vectorized in this way)
  // add = 0: entry 0 of RF for PE0
  // add = 1: entry 0 of RF for PE1
  // add = 2: entry 0 of RF for PE2
  // add = 3: entry 0 of RF for PE3
  // ...
  // add = 4: entry 1 of RF for PE0

  float stream_in [N*N]; //stream_in and stream_out are both like to RFs exceot that they dont have address (depth)
  
  float hbm0 [N];
  float hbm1 [N];
  float hbm2 [N];
  float hbm3 [N];

  // float* stream_in = new float[NUM_SIMD_LANES]; //stream_in and stream_out are both like to RFs exceot that they dont have address (depth)
  // float* stream_out = new float[N*NUM_COL];
  // float* hbm0 = new float[N];
  // float* hbm1 = new float[N];
  // float* hbm2 = new float[N];
  // float* hbm3 = new float[N];

  // intitialize memory
  // for (int i = 0; i < N; i++) {
  //   hbm0[i] = 1.0;
  //   hbm1[i] = 1.0;
  //   hbm2[i] = 1.0;
  //   hbm3[i] = 1.0;
  // }

  // induction variable: row_A => m, col_A or row_Y => k; col_Y => n
  int m_trip_count = (int) (N/NUM_SIMD_LANES);
  // int m2_trip_count = TM*NUM_SIMD_LANES;
  int tm_trip_count = (int) (m_trip_count/TM);
  int tk_trip_count = (int) (N/TK);
  int trf_trip_count = TM*NUM_SIMD_LANES;
  int hbm_idx; // hbm_index
  int rf_idx1, rf_idx2, rf_idx3, rf_idx4, rf_idx5, sin_idx, sout_idx;
  int tk=0;

  #pragma clang loop unroll(disable)
  for (int tm = 0; tm < tm_trip_count; tm++){
    // re-initializing the accumulation part of RF (after TK) to 0.0
    // #pragma clang loop vectorize_width(16)
    #pragma clang loop unroll(disable)
    for (int trf = 0; trf < trf_trip_count; trf++){
      rf_idx1 = TK*NUM_SIMD_LANES + trf;
      rf0[rf_idx1] = 0.0;
      rf1[rf_idx1] = 0.0;
      rf2[rf_idx1] = 0.0;
      rf3[rf_idx1] = 0.0;
    }
    // #pragma clang loop unroll(disable)
    for (int tk = 0; tk < tk_trip_count; tk++) { //tk is tiling // another way is to have tk = tk + NUM_SIMD_LANES but my HW doesnt support
      // filling up register files
      // #pragma clang loop vectorize(enable)
      // #pragma clang loop unroll(disable)
      for (int k = 0; k < TK; k++){
        // #pragma clang loop vectorize_width(16)
        #pragma clang loop unroll(disable)
        for (int lane1 = 0; lane1 < NUM_SIMD_LANES; lane1++){
          rf_idx2 = k*NUM_SIMD_LANES + lane1;
          hbm_idx = tk*TK*NUM_SIMD_LANES + k*NUM_SIMD_LANES + lane1;
          rf0[rf_idx2] = hbm0[hbm_idx];
          rf1[rf_idx2] = hbm1[hbm_idx];
          rf2[rf_idx2] = hbm2[hbm_idx];
          rf3[rf_idx2] = hbm3[hbm_idx];
        }
      }
      // do the processing
      for (int m=0; m < TM; m++){
        // #pragma clang loop vectorize_width(32)
        for (int k2 = 0; k2 < TK; k2++){
          // #pragma clang loop vectorize_width(16)
          #pragma clang loop unroll(disable)
          for(int lane2 = 0; lane2 < NUM_SIMD_LANES; lane2++){
            rf_idx3 = NUM_SIMD_LANES*(TK+m) + lane2;
            rf_idx4 = k2*NUM_SIMD_LANES + lane2;
            sin_idx = tm*tk_trip_count*TM*TK*NUM_SIMD_LANES+ tk*TM*TK*NUM_SIMD_LANES + m*TK*NUM_SIMD_LANES + k2*NUM_SIMD_LANES + lane2;
            rf0[rf_idx3] += stream_in[sin_idx]*rf0[rf_idx4];
            rf1[rf_idx3] += stream_in[sin_idx]*rf1[rf_idx4];
            rf2[rf_idx3] += stream_in[sin_idx]*rf2[rf_idx4];
            rf3[rf_idx3] += stream_in[sin_idx]*rf3[rf_idx4];
          }
        }
      }
    }
    // accumulate result from different rfs
    // #pragma clang loop vectorize_width(16)
    // #pragma clang loop unroll(disable)
    for (int m2 = 0; m2 < TM; m2++) {
      // #pragma clang loop vectorize_width(16)
      #pragma clang loop unroll(disable)
      for (int lane3 = 0; lane3 < NUM_SIMD_LANES; lane3++){
        rf_idx5 = NUM_SIMD_LANES*(TK+m2) + lane3;
        sout_idx = tm*TM*NUM_SIMD_LANES*NUM_COL + m2*NUM_SIMD_LANES*NUM_COL + lane3;
        stream_out[sout_idx] = rf0[rf_idx5];
        stream_out[sout_idx + NUM_SIMD_LANES] =  rf1[rf_idx5];
        stream_out[sout_idx + NUM_SIMD_LANES*2] = rf2[rf_idx5];
        stream_out[sout_idx + NUM_SIMD_LANES*3] = rf3[rf_idx5];
      }
    }
  }
  return 0;
}