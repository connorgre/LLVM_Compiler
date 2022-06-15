
; This file is functionally the same as gcn2.ll,
; as in it gets parsed the exact same
; The only difference is that this file has the instructions
; That the parser ignores deleted (metadata, memory tracking),
; Also, the blocks are ordered by execution order. This does
; get handled by the parser, but is easier to read this way

@stream_out = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
define dso_local noundef i32 @main(i32 noundef %argc, i8** nocapture noundef readnone %argv) local_unnamed_addr #3 {
;0
entry:
  %rf0 = alloca [768 x float], align 16
  %stream_in = alloca [1048576 x float], align 16
  %scevgep193 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 512
  %scevgep193194 = bitcast float* %scevgep193 to i8*
  br label %for.cond1.preheader
;1
for.cond1.preheader:                              ; preds = %entry, %for.cond93.preheader
  %indvar = phi i64 [ 0, %entry ], [ %indvar.next, %for.cond93.preheader ]
  %1 = shl nuw nsw i64 %indvar, 8
  %scevgep243 = getelementptr [1024 x float], [1024 x float]* @stream_out, i64 0, i64 %1
  %scevgep243244 = bitcast float* %scevgep243 to i8*
  call void @llvm.memset.p0i8.i64(i8* noundef nonnull align 16 dereferenceable(1024) %scevgep193194, i8 0, i64 1024, i1 false), !tbaa !4
  %2 = shl nsw i64 %indvar, 18
  br label %for.cond18.preheader
;2
for.cond18.preheader:                             ; preds = %for.cond1.preheader, %for.cond.cleanup45
  %indvar197 = phi i64 [ 0, %for.cond1.preheader ], [ %indvar.next198, %for.cond.cleanup45 ]
  %3 = shl nsw i64 %indvar197, 13
  br label %for.cond47.preheader

;3
for.cond47.preheader:                             ; preds = %for.cond18.preheader, %for.cond.cleanup49
  %indvars.iv221 = phi i64 [ 0, %for.cond18.preheader ], [ %indvars.iv.next222, %for.cond.cleanup49 ]
  %4 = shl i64 %indvars.iv221, 4
  %5 = add nuw nsw i64 %4, 512
  %6 = shl nsw i64 %indvars.iv221, 9
  br label %for.cond51.preheader
;4
for.cond51.preheader:                             ; preds = %for.cond47.preheader, %for.cond.cleanup53
  %indvars.iv216 = phi i64 [ 0, %for.cond47.preheader ], [ %indvars.iv.next217, %for.cond.cleanup53 ]
  %7 = shl nsw i64 %indvars.iv216, 4
  br label %vector.body
;5
vector.body:                                      ; preds = %vector.body, %for.cond51.preheader
  %index = phi i64 [ 0, %for.cond51.preheader ], [ %index.next, %vector.body ]
  %8 = add nuw nsw i64 %5, %index
  %9 = add nuw nsw i64 %index, %7
  %10 = add nuw nsw i64 %9, %2
  %11 = add nuw nsw i64 %10, %3
  %12 = add nuw nsw i64 %11, %6
  %13 = getelementptr inbounds [1048576 x float], [1048576 x float]* %stream_in, i64 0, i64 %12
  %14 = bitcast float* %13 to <16 x float>*
  %wide.load = load <16 x float>, <16 x float>* %14, align 4, !tbaa !4
  %15 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 %9
  %16 = bitcast float* %15 to <16 x float>*
  %wide.load251 = load <16 x float>, <16 x float>* %16, align 16, !tbaa !4
  %17 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 %8
  %18 = bitcast float* %17 to <16 x float>*
  %wide.load252 = load <16 x float>, <16 x float>* %18, align 16, !tbaa !4
  %19 = call <16 x float> @llvm.fmuladd.v16f32(<16 x float> %wide.load, <16 x float> %wide.load251, <16 x float> %wide.load252)
  %20 = bitcast float* %17 to <16 x float>*
  store <16 x float> %19, <16 x float>* %20, align 16, !tbaa !4
  %index.next = add nuw i64 %index, 16
  %21 = icmp eq i64 %index, 0
  br i1 %21, label %for.cond.cleanup53, label %vector.body, !llvm.loop !12
;6
for.cond.cleanup53:                               ; preds = %vector.body
  %indvars.iv.next217 = add nuw nsw i64 %indvars.iv216, 1
  %exitcond220.not = icmp eq i64 %indvars.iv.next217, 32
  br i1 %exitcond220.not, label %for.cond.cleanup49, label %for.cond51.preheader, !llvm.loop !15
;7
for.cond.cleanup49:                               ; preds = %for.cond.cleanup53
  %indvars.iv.next222 = add nuw nsw i64 %indvars.iv221, 1
  %exitcond227.not = icmp eq i64 %indvars.iv.next222, 16
  br i1 %exitcond227.not, label %for.cond.cleanup45, label %for.cond47.preheader, !llvm.loop !14
;8
for.cond.cleanup45:                               ; preds = %for.cond.cleanup49
  %indvar.next198 = add nuw nsw i64 %indvar197, 1
  %exitcond230.not = icmp eq i64 %indvar.next198, 32
  br i1 %exitcond230.not, label %for.cond93.preheader, label %for.cond18.preheader, !llvm.loop !11
;9
for.cond93.preheader:                             ; preds = %for.cond.cleanup45
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* noundef nonnull align 16 dereferenceable(1024) %scevgep243244, i8* noundef nonnull align 16 dereferenceable(1024) %scevgep193194, i64 1024, i1 false), !tbaa !4
  %indvar.next = add nuw nsw i64 %indvar, 1
  %exitcond250.not = icmp eq i64 %indvar.next, 4
  br i1 %exitcond250.not, label %for.cond.cleanup, label %for.cond1.preheader, !llvm.loop !8
;10
for.cond.cleanup:                                 ; preds = %for.cond93.preheader
  ret i32 0
}