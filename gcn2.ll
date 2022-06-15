
%"class.std::ios_base::Init" = type { i8 }

@_ZStL8__ioinit = internal global %"class.std::ios_base::Init" zeroinitializer, align 1
@__dso_handle = external hidden global i8
@stream_out = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@hbm0 = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@llvm.global_ctors = appending global [1 x { i32, void ()*, i8* }] [{ i32, void ()*, i8* } { i32 65535, void ()* @_GLOBAL__sub_I_example.cpp, i8* null }]

declare dso_local void @_ZNSt8ios_base4InitC1Ev(%"class.std::ios_base::Init"* noundef nonnull align 1 dereferenceable(1)) unnamed_addr #0

declare dso_local void @_ZNSt8ios_base4InitD1Ev(%"class.std::ios_base::Init"* noundef nonnull align 1 dereferenceable(1)) unnamed_addr #1

declare dso_local i32 @__cxa_atexit(void (i8*)*, i8*, i8*) local_unnamed_addr #2

define dso_local noundef i32 @main(i32 noundef %argc, i8** nocapture noundef readnone %argv) local_unnamed_addr #3 {
entry:
  %rf0 = alloca [768 x float], align 16
  %rf0205 = bitcast [768 x float]* %rf0 to i8*
  %stream_in = alloca [1048576 x float], align 16
  call void @llvm.lifetime.start.p0i8(i64 3072, i8* nonnull %rf0205) #9
  %0 = bitcast [1048576 x float]* %stream_in to i8*
  call void @llvm.lifetime.start.p0i8(i64 4194304, i8* nonnull %0) #9
  %scevgep193 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 512
  %scevgep193194 = bitcast float* %scevgep193 to i8*
  br label %for.cond1.preheader

for.cond1.preheader:                              ; preds = %entry, %for.cond93.preheader
  %indvar = phi i64 [ 0, %entry ], [ %indvar.next, %for.cond93.preheader ]
  %1 = shl nuw nsw i64 %indvar, 8
  %scevgep243 = getelementptr [1024 x float], [1024 x float]* @stream_out, i64 0, i64 %1
  %scevgep243244 = bitcast float* %scevgep243 to i8*
  call void @llvm.memset.p0i8.i64(i8* noundef nonnull align 16 dereferenceable(1024) %scevgep193194, i8 0, i64 1024, i1 false), !tbaa !4
  %2 = shl nsw i64 %indvar, 18
  br label %for.cond18.preheader

for.cond.cleanup:                                 ; preds = %for.cond93.preheader
  call void @llvm.lifetime.end.p0i8(i64 4194304, i8* nonnull %0) #9
  call void @llvm.lifetime.end.p0i8(i64 3072, i8* nonnull %rf0205) #9
  ret i32 0

for.cond93.preheader:                             ; preds = %for.cond.cleanup45
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* noundef nonnull align 16 dereferenceable(1024) %scevgep243244, i8* noundef nonnull align 16 dereferenceable(1024) %scevgep193194, i64 1024, i1 false), !tbaa !4
  %indvar.next = add nuw nsw i64 %indvar, 1
  %exitcond250.not = icmp eq i64 %indvar.next, 4
  br i1 %exitcond250.not, label %for.cond.cleanup, label %for.cond1.preheader, !llvm.loop !8

for.cond18.preheader:                             ; preds = %for.cond1.preheader, %for.cond.cleanup45
  %indvar197 = phi i64 [ 0, %for.cond1.preheader ], [ %indvar.next198, %for.cond.cleanup45 ]
  %3 = shl nuw nsw i64 %indvar197, 9
  %scevgep206 = getelementptr [1024 x float], [1024 x float]* @hbm0, i64 0, i64 %3
  %scevgep206207 = bitcast float* %scevgep206 to i8*
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* noundef nonnull align 16 dereferenceable(2048) %rf0205, i8* noundef nonnull align 16 dereferenceable(2048) %scevgep206207, i64 2048, i1 false), !tbaa !4
  %4 = shl nsw i64 %indvar197, 13
  br label %for.cond47.preheader

for.cond47.preheader:                             ; preds = %for.cond18.preheader, %for.cond.cleanup49
  %indvars.iv221 = phi i64 [ 0, %for.cond18.preheader ], [ %indvars.iv.next222, %for.cond.cleanup49 ]
  %5 = shl i64 %indvars.iv221, 4
  %6 = add nuw nsw i64 %5, 512
  %7 = shl nsw i64 %indvars.iv221, 9
  br label %for.cond51.preheader

for.cond.cleanup45:                               ; preds = %for.cond.cleanup49
  %indvar.next198 = add nuw nsw i64 %indvar197, 1
  %exitcond230.not = icmp eq i64 %indvar.next198, 32
  br i1 %exitcond230.not, label %for.cond93.preheader, label %for.cond18.preheader, !llvm.loop !11

for.cond51.preheader:                             ; preds = %for.cond47.preheader, %for.cond.cleanup53
  %indvars.iv216 = phi i64 [ 0, %for.cond47.preheader ], [ %indvars.iv.next217, %for.cond.cleanup53 ]
  %8 = shl nsw i64 %indvars.iv216, 4
  br label %vector.body

vector.body:                                      ; preds = %vector.body, %for.cond51.preheader
  %index = phi i64 [ 0, %for.cond51.preheader ], [ %index.next, %vector.body ]
  %9 = add nuw nsw i64 %6, %index
  %10 = add nuw nsw i64 %index, %8
  %11 = add nuw nsw i64 %10, %2
  %12 = add nuw nsw i64 %11, %4
  %13 = add nuw nsw i64 %12, %7
  %14 = getelementptr inbounds [1048576 x float], [1048576 x float]* %stream_in, i64 0, i64 %13
  %15 = bitcast float* %14 to <16 x float>*
  %wide.load = load <16 x float>, <16 x float>* %15, align 4, !tbaa !4
  %16 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 %10
  %17 = bitcast float* %16 to <16 x float>*
  %wide.load251 = load <16 x float>, <16 x float>* %17, align 16, !tbaa !4
  %18 = getelementptr inbounds [768 x float], [768 x float]* %rf0, i64 0, i64 %9
  %19 = bitcast float* %18 to <16 x float>*
  %wide.load252 = load <16 x float>, <16 x float>* %19, align 16, !tbaa !4
  %20 = call <16 x float> @llvm.fmuladd.v16f32(<16 x float> %wide.load, <16 x float> %wide.load251, <16 x float> %wide.load252)
  %21 = bitcast float* %18 to <16 x float>*
  store <16 x float> %20, <16 x float>* %21, align 16, !tbaa !4
  %index.next = add nuw i64 %index, 16
  %22 = icmp eq i64 %index, 0
  br i1 %22, label %for.cond.cleanup53, label %vector.body, !llvm.loop !12

for.cond.cleanup49:                               ; preds = %for.cond.cleanup53
  %indvars.iv.next222 = add nuw nsw i64 %indvars.iv221, 1
  %exitcond227.not = icmp eq i64 %indvars.iv.next222, 16
  br i1 %exitcond227.not, label %for.cond.cleanup45, label %for.cond47.preheader, !llvm.loop !14

for.cond.cleanup53:                               ; preds = %vector.body
  %indvars.iv.next217 = add nuw nsw i64 %indvars.iv216, 1
  %exitcond220.not = icmp eq i64 %indvars.iv.next217, 32
  br i1 %exitcond220.not, label %for.cond.cleanup49, label %for.cond51.preheader, !llvm.loop !15
}

declare void @llvm.lifetime.start.p0i8(i64 immarg, i8* nocapture) #4

declare void @llvm.lifetime.end.p0i8(i64 immarg, i8* nocapture) #4

define internal void @_GLOBAL__sub_I_example.cpp() #5 section ".text.startup" {
entry:
  tail call void @_ZNSt8ios_base4InitC1Ev(%"class.std::ios_base::Init"* noundef nonnull align 1 dereferenceable(1) @_ZStL8__ioinit)
  %0 = tail call i32 @__cxa_atexit(void (i8*)* bitcast (void (%"class.std::ios_base::Init"*)* @_ZNSt8ios_base4InitD1Ev to void (i8*)*), i8* getelementptr inbounds (%"class.std::ios_base::Init", %"class.std::ios_base::Init"* @_ZStL8__ioinit, i64 0, i32 0), i8* nonnull @__dso_handle) #9
  ret void
}

declare void @llvm.memset.p0i8.i64(i8* nocapture writeonly, i8, i64, i1 immarg) #6

declare void @llvm.memcpy.p0i8.p0i8.i64(i8* noalias nocapture writeonly, i8* noalias nocapture readonly, i64, i1 immarg) #7

declare <16 x float> @llvm.fmuladd.v16f32(<16 x float>, <16 x float>, <16 x float>) #8

attributes #0 = { "frame-pointer"="none" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #1 = { nounwind "frame-pointer"="none" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #2 = { nofree nounwind }
attributes #3 = { mustprogress nofree norecurse nosync nounwind uwtable "frame-pointer"="none" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #4 = { argmemonly mustprogress nofree nosync nounwind willreturn }
attributes #5 = { uwtable "frame-pointer"="none" "min-legal-vector-width"="0" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "tune-cpu"="generic" }
attributes #6 = { argmemonly nofree nounwind willreturn writeonly }
attributes #7 = { argmemonly nofree nounwind willreturn }
attributes #8 = { nofree nosync nounwind readnone speculatable willreturn }
attributes #9 = { nounwind }