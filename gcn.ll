; ModuleID = 'gcn.cpp'
source_filename = "gcn.cpp"
target datalayout = "e-m:e-p270:32:32-p271:32:32-p272:64:64-i64:64-f80:128-n8:16:32:64-S128"
target triple = "x86_64-unknown-linux-gnu"

%"class.std::ios_base::Init" = type { i8 }

@_ZStL8__ioinit = internal global %"class.std::ios_base::Init" zeroinitializer, align 1
@__dso_handle = external hidden global i8
@stream_out = dso_local local_unnamed_addr global [4096 x float] zeroinitializer, align 16
@rf0 = dso_local local_unnamed_addr global [768 x float] zeroinitializer, align 16
@rf1 = dso_local local_unnamed_addr global [768 x float] zeroinitializer, align 16
@rf2 = dso_local local_unnamed_addr global [768 x float] zeroinitializer, align 16
@rf3 = dso_local local_unnamed_addr global [768 x float] zeroinitializer, align 16
@stream_in = dso_local local_unnamed_addr global [1048576 x float] zeroinitializer, align 16
@hbm0 = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@hbm1 = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@hbm2 = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@hbm3 = dso_local local_unnamed_addr global [1024 x float] zeroinitializer, align 16
@llvm.global_ctors = appending global [1 x { i32, void ()*, i8* }] [{ i32, void ()*, i8* } { i32 65535, void ()* @_GLOBAL__sub_I_gcn.cpp, i8* null }]

declare dso_local void @_ZNSt8ios_base4InitC1Ev(%"class.std::ios_base::Init"*) unnamed_addr #0

; Function Attrs: nounwind
declare dso_local void @_ZNSt8ios_base4InitD1Ev(%"class.std::ios_base::Init"*) unnamed_addr #1

; Function Attrs: nofree nounwind
declare dso_local i32 @__cxa_atexit(void (i8*)*, i8*, i8*) local_unnamed_addr #2

; Function Attrs: nofree norecurse nounwind uwtable
define dso_local i32 @main(i32 %argc, i8** nocapture readnone %argv) local_unnamed_addr #3 {
entry:
  br label %for.cond1.preheader

for.cond1.preheader:                              ; preds = %for.cond.cleanup129, %entry
  %indvar310 = phi i64 [ 0, %entry ], [ %indvar.next311, %for.cond.cleanup129 ]
  call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf0, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)
  call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf1, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)
  call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf2, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)
  call void @llvm.memset.p0i8.i64(i8* nonnull align 16 dereferenceable(1024) bitcast (float* getelementptr inbounds ([768 x float], [768 x float]* @rf3, i64 0, i64 512) to i8*), i8 0, i64 1024, i1 false)
  %0 = shl nsw i64 %indvar310, 18
  br label %for.cond16.preheader

for.cond.cleanup:                                 ; preds = %for.cond.cleanup129
  ret i32 0

for.cond127.preheader:                            ; preds = %for.cond.cleanup54
  %1 = shl nsw i64 %indvar310, 10
  br label %for.cond131.preheader

for.cond16.preheader:                             ; preds = %for.cond.cleanup54, %for.cond1.preheader
  %indvar266 = phi i64 [ 0, %for.cond1.preheader ], [ %indvar.next267, %for.cond.cleanup54 ]
  %2 = shl nuw nsw i64 %indvar266, 9
  br label %for.cond20.preheader

for.cond52.preheader:                             ; preds = %for.cond20.preheader
  %3 = shl nsw i64 %indvar266, 13
  br label %for.cond56.preheader

for.cond20.preheader:                             ; preds = %for.cond20.preheader, %for.cond16.preheader
  %indvar = phi i64 [ 0, %for.cond16.preheader ], [ %indvar.next, %for.cond20.preheader ]
  %4 = shl nuw nsw i64 %indvar, 4
  %scevgep278 = getelementptr [768 x float], [768 x float]* @rf3, i64 0, i64 %4
  %scevgep278279 = bitcast float* %scevgep278 to i8*
  %5 = add nuw nsw i64 %2, %4
  %scevgep280 = getelementptr [1024 x float], [1024 x float]* @hbm3, i64 0, i64 %5
  %scevgep280281 = bitcast float* %scevgep280 to i8*
  %scevgep274 = getelementptr [768 x float], [768 x float]* @rf2, i64 0, i64 %4
  %scevgep274275 = bitcast float* %scevgep274 to i8*
  %scevgep276 = getelementptr [1024 x float], [1024 x float]* @hbm2, i64 0, i64 %5
  %scevgep276277 = bitcast float* %scevgep276 to i8*
  %scevgep270 = getelementptr [768 x float], [768 x float]* @rf1, i64 0, i64 %4
  %scevgep270271 = bitcast float* %scevgep270 to i8*
  %scevgep272 = getelementptr [1024 x float], [1024 x float]* @hbm1, i64 0, i64 %5
  %scevgep272273 = bitcast float* %scevgep272 to i8*
  %scevgep = getelementptr [768 x float], [768 x float]* @rf0, i64 0, i64 %4
  %scevgep265 = bitcast float* %scevgep to i8*
  %scevgep268 = getelementptr [1024 x float], [1024 x float]* @hbm0, i64 0, i64 %5
  %scevgep268269 = bitcast float* %scevgep268 to i8*
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) %scevgep265, i8* nonnull align 16 dereferenceable(64) %scevgep268269, i64 64, i1 false)
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) %scevgep270271, i8* nonnull align 16 dereferenceable(64) %scevgep272273, i64 64, i1 false)
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) %scevgep274275, i8* nonnull align 16 dereferenceable(64) %scevgep276277, i64 64, i1 false)
  call void @llvm.memcpy.p0i8.p0i8.i64(i8* nonnull align 16 dereferenceable(64) %scevgep278279, i8* nonnull align 16 dereferenceable(64) %scevgep280281, i64 64, i1 false)
  %indvar.next = add nuw nsw i64 %indvar, 1
  %exitcond.not = icmp eq i64 %indvar.next, 32
  br i1 %exitcond.not, label %for.cond52.preheader, label %for.cond20.preheader

for.cond56.preheader:                             ; preds = %for.cond.cleanup58, %for.cond52.preheader
  %indvars.iv293 = phi i64 [ 0, %for.cond52.preheader ], [ %indvars.iv.next294, %for.cond.cleanup58 ]
  %6 = shl i64 %indvars.iv293, 4
  %7 = add nuw nsw i64 %6, 512
  %8 = shl nsw i64 %indvars.iv293, 9
  br label %for.cond60.preheader

for.cond.cleanup54:                               ; preds = %for.cond.cleanup58
  %indvar.next267 = add nuw nsw i64 %indvar266, 1
  %exitcond301.not = icmp eq i64 %indvar.next267, 32
  br i1 %exitcond301.not, label %for.cond127.preheader, label %for.cond16.preheader

for.cond60.preheader:                             ; preds = %for.cond.cleanup62, %for.cond56.preheader
  %indvars.iv289 = phi i64 [ 0, %for.cond56.preheader ], [ %indvars.iv.next290, %for.cond.cleanup62 ]
  %9 = shl nsw i64 %indvars.iv289, 4
  br label %vector.body335

vector.body335:                                   ; preds = %vector.body335, %for.cond60.preheader
  %index337 = phi i64 [ 0, %for.cond60.preheader ], [ %index.next338, %vector.body335 ]
  %10 = add nuw nsw i64 %7, %index337
  %11 = add nuw nsw i64 %index337, %9
  %12 = add nuw nsw i64 %11, %0
  %13 = add nuw nsw i64 %12, %3
  %14 = add nuw nsw i64 %13, %8
  %15 = getelementptr inbounds [1048576 x float], [1048576 x float]* @stream_in, i64 0, i64 %14
  %16 = bitcast float* %15 to <16 x float>*
  %wide.load341 = load <16 x float>, <16 x float>* %16, align 4, !tbaa !2
  %17 = getelementptr inbounds [768 x float], [768 x float]* @rf0, i64 0, i64 %11
  %18 = bitcast float* %17 to <16 x float>*
  %wide.load342 = load <16 x float>, <16 x float>* %18, align 16, !tbaa !2
  %19 = fmul <16 x float> %wide.load341, %wide.load342
  %20 = getelementptr inbounds [768 x float], [768 x float]* @rf0, i64 0, i64 %10
  %21 = bitcast float* %20 to <16 x float>*
  %wide.load343 = load <16 x float>, <16 x float>* %21, align 16, !tbaa !2
  %22 = fadd <16 x float> %wide.load343, %19
  %23 = bitcast float* %20 to <16 x float>*
  store <16 x float> %22, <16 x float>* %23, align 16, !tbaa !2
  %24 = getelementptr inbounds [768 x float], [768 x float]* @rf1, i64 0, i64 %11
  %25 = bitcast float* %24 to <16 x float>*
  %wide.load344 = load <16 x float>, <16 x float>* %25, align 16, !tbaa !2
  %26 = fmul <16 x float> %wide.load341, %wide.load344
  %27 = getelementptr inbounds [768 x float], [768 x float]* @rf1, i64 0, i64 %10
  %28 = bitcast float* %27 to <16 x float>*
  %wide.load345 = load <16 x float>, <16 x float>* %28, align 16, !tbaa !2
  %29 = fadd <16 x float> %wide.load345, %26
  %30 = bitcast float* %27 to <16 x float>*
  store <16 x float> %29, <16 x float>* %30, align 16, !tbaa !2
  %31 = getelementptr inbounds [768 x float], [768 x float]* @rf2, i64 0, i64 %11
  %32 = bitcast float* %31 to <16 x float>*
  %wide.load346 = load <16 x float>, <16 x float>* %32, align 16, !tbaa !2
  %33 = fmul <16 x float> %wide.load341, %wide.load346
  %34 = getelementptr inbounds [768 x float], [768 x float]* @rf2, i64 0, i64 %10
  %35 = bitcast float* %34 to <16 x float>*
  %wide.load347 = load <16 x float>, <16 x float>* %35, align 16, !tbaa !2
  %36 = fadd <16 x float> %wide.load347, %33
  %37 = bitcast float* %34 to <16 x float>*
  store <16 x float> %36, <16 x float>* %37, align 16, !tbaa !2
  %38 = getelementptr inbounds [768 x float], [768 x float]* @rf3, i64 0, i64 %11
  %39 = bitcast float* %38 to <16 x float>*
  %wide.load348 = load <16 x float>, <16 x float>* %39, align 16, !tbaa !2
  %40 = fmul <16 x float> %wide.load341, %wide.load348
  %41 = getelementptr inbounds [768 x float], [768 x float]* @rf3, i64 0, i64 %10
  %42 = bitcast float* %41 to <16 x float>*
  %wide.load349 = load <16 x float>, <16 x float>* %42, align 16, !tbaa !2
  %43 = fadd <16 x float> %wide.load349, %40
  %44 = bitcast float* %41 to <16 x float>*
  store <16 x float> %43, <16 x float>* %44, align 16, !tbaa !2
  %index.next338 = add i64 %index337, 16
  %45 = icmp eq i64 %index337, 0
  br i1 %45, label %for.cond.cleanup62, label %vector.body335, !llvm.loop !6

for.cond.cleanup58:                               ; preds = %for.cond.cleanup62
  %indvars.iv.next294 = add nuw nsw i64 %indvars.iv293, 1
  %exitcond298.not = icmp eq i64 %indvars.iv.next294, 16
  br i1 %exitcond298.not, label %for.cond.cleanup54, label %for.cond56.preheader

for.cond.cleanup62:                               ; preds = %vector.body335
  %indvars.iv.next290 = add nuw nsw i64 %indvars.iv289, 1
  %exitcond292.not = icmp eq i64 %indvars.iv.next290, 32
  br i1 %exitcond292.not, label %for.cond.cleanup58, label %for.cond60.preheader

for.cond131.preheader:                            ; preds = %for.cond.cleanup133, %for.cond127.preheader
  %indvar312 = phi i64 [ 0, %for.cond127.preheader ], [ %indvar.next313, %for.cond.cleanup133 ]
  %46 = shl i64 %indvar312, 4
  %47 = add nuw nsw i64 %46, 512
  %48 = shl nsw i64 %indvar312, 6
  %49 = add nuw nsw i64 %48, %1
  br label %vector.body

vector.body:                                      ; preds = %vector.body, %for.cond131.preheader
  %index = phi i64 [ 0, %for.cond131.preheader ], [ %index.next, %vector.body ]
  %50 = add nuw nsw i64 %47, %index
  %51 = add nuw nsw i64 %49, %index
  %52 = getelementptr inbounds [768 x float], [768 x float]* @rf0, i64 0, i64 %50
  %53 = bitcast float* %52 to <16 x i32>*
  %wide.load = load <16 x i32>, <16 x i32>* %53, align 16, !tbaa !2
  %54 = getelementptr inbounds [4096 x float], [4096 x float]* @stream_out, i64 0, i64 %51
  %55 = bitcast float* %54 to <16 x i32>*
  store <16 x i32> %wide.load, <16 x i32>* %55, align 16, !tbaa !2
  %56 = getelementptr inbounds [768 x float], [768 x float]* @rf1, i64 0, i64 %50
  %57 = bitcast float* %56 to <16 x i32>*
  %wide.load330 = load <16 x i32>, <16 x i32>* %57, align 16, !tbaa !2
  %58 = add nuw nsw i64 %51, 16
  %59 = getelementptr inbounds [4096 x float], [4096 x float]* @stream_out, i64 0, i64 %58
  %60 = bitcast float* %59 to <16 x i32>*
  store <16 x i32> %wide.load330, <16 x i32>* %60, align 16, !tbaa !2
  %61 = getelementptr inbounds [768 x float], [768 x float]* @rf2, i64 0, i64 %50
  %62 = bitcast float* %61 to <16 x i32>*
  %wide.load331 = load <16 x i32>, <16 x i32>* %62, align 16, !tbaa !2
  %63 = add nuw nsw i64 %51, 32
  %64 = getelementptr inbounds [4096 x float], [4096 x float]* @stream_out, i64 0, i64 %63
  %65 = bitcast float* %64 to <16 x i32>*
  store <16 x i32> %wide.load331, <16 x i32>* %65, align 16, !tbaa !2
  %66 = getelementptr inbounds [768 x float], [768 x float]* @rf3, i64 0, i64 %50
  %67 = bitcast float* %66 to <16 x i32>*
  %wide.load332 = load <16 x i32>, <16 x i32>* %67, align 16, !tbaa !2
  %68 = add nuw nsw i64 %51, 48
  %69 = getelementptr inbounds [4096 x float], [4096 x float]* @stream_out, i64 0, i64 %68
  %70 = bitcast float* %69 to <16 x i32>*
  store <16 x i32> %wide.load332, <16 x i32>* %70, align 16, !tbaa !2
  %index.next = add i64 %index, 16
  %71 = icmp eq i64 %index, 0
  br i1 %71, label %for.cond.cleanup133, label %vector.body, !llvm.loop !9

for.cond.cleanup129:                              ; preds = %for.cond.cleanup133
  %indvar.next311 = add nuw nsw i64 %indvar310, 1
  %exitcond329.not = icmp eq i64 %indvar.next311, 4
  br i1 %exitcond329.not, label %for.cond.cleanup, label %for.cond1.preheader, !llvm.loop !10

for.cond.cleanup133:                              ; preds = %vector.body
  %indvar.next313 = add nuw nsw i64 %indvar312, 1
  %exitcond326.not = icmp eq i64 %indvar.next313, 16
  br i1 %exitcond326.not, label %for.cond.cleanup129, label %for.cond131.preheader
}

; Function Attrs: uwtable
define internal void @_GLOBAL__sub_I_gcn.cpp() #4 section ".text.startup" {
entry: 
  tail call void @_ZNSt8ios_base4InitC1Ev(%"class.std::ios_base::Init"* nonnull @_ZStL8__ioinit)
  %0 = tail call i32 @__cxa_atexit(void (i8*)* bitcast (void (%"class.std::ios_base::Init"*)* @_ZNSt8ios_base4InitD1Ev to void (i8*)*), i8* getelementptr inbounds (%"class.std::ios_base::Init", %"class.std::ios_base::Init"* @_ZStL8__ioinit, i64 0, i32 0), i8* nonnull @__dso_handle) #7
  ret void
}

; Function Attrs: argmemonly nounwind willreturn writeonly
declare void @llvm.memset.p0i8.i64(i8* nocapture writeonly, i8, i64, i1 immarg) #5

; Function Attrs: argmemonly nounwind willreturn
declare void @llvm.memcpy.p0i8.p0i8.i64(i8* noalias nocapture writeonly, i8* noalias nocapture readonly, i64, i1 immarg) #6

attributes #0 = { "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #1 = { nounwind "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "no-infs-fp-math"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #2 = { nofree nounwind }
attributes #3 = { nofree norecurse nounwind uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #4 = { uwtable "correctly-rounded-divide-sqrt-fp-math"="false" "disable-tail-calls"="false" "frame-pointer"="none" "less-precise-fpmad"="false" "min-legal-vector-width"="0" "no-infs-fp-math"="false" "no-jump-tables"="false" "no-nans-fp-math"="false" "no-signed-zeros-fp-math"="false" "no-trapping-math"="true" "stack-protector-buffer-size"="8" "target-cpu"="x86-64" "target-features"="+cx8,+fxsr,+mmx,+sse,+sse2,+x87" "unsafe-fp-math"="false" "use-soft-float"="false" }
attributes #5 = { argmemonly nounwind willreturn writeonly }
attributes #6 = { argmemonly nounwind willreturn }
attributes #7 = { nounwind }

!llvm.module.flags = !{!0}
!llvm.ident = !{!1}

!0 = !{i32 1, !"wchar_size", i32 4}
!1 = !{!"clang version 11.1.0"}
!2 = !{!3, !3, i64 0}
!3 = !{!"float", !4, i64 0}
!4 = !{!"omnipotent char", !5, i64 0}
!5 = !{!"Simple C++ TBAA"}
!6 = distinct !{!6, !7, !8}
!7 = !{!"llvm.loop.unroll.disable"}
!8 = !{!"llvm.loop.isvectorized", i32 1}
!9 = distinct !{!9, !7, !8}
!10 = distinct !{!10, !7}