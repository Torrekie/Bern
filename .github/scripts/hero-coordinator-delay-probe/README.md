# One actual coordinator replacement, next-sample observation

This independent fixture keeps the exact Hero/Image/Style/dependencies, scene,
original clock and wrapper from hero-coordinator-probe. Only the scalar observer
and single midflight capture schedule change. The old fixture stays available.
No product draw/renderer, layer, frame, progress, visibility or clock is changed.

At the first actual live sample with0.2<progress<0.8, record a scalar arm and take
no image. Return through the original loop. Its next existing RunLoop.run call
and sample must still observe the same flight, timer and actual-overlay parent;
then take the only midflight PNG. Capture index must equal armed index+1.
Capture progress may exceed0.8. Loss/replacement/deadline is incomplete, without
another band, capture attempt or extra RunLoop/dispatch/flush/layout/display.
This is one next outer-loop opportunity, not a synchronization/presentation fence.

Both nested midflight_sampling and flat in-flight records preserve armed and
capture sample index/state/uptime/progress/identity separately; trigger_state
and trigger_progress explicitly alias the arm. The ordinary defer-written partial report stores arm and attempt before CG
capture, and complete only after PNG save. The unchanged hard watchdog can
replace it with a minimal failure report and _exit, bypassing that defer. Read-only
source review precedes CI; this modified driver has no local compile/typecheck.

Before/settled five-buffer gates and exactly3 original PNGs, one same-key
conditional SwiftUI action, one flight identity, original timer/frame movement
and automatic removal remain. Cache/normal/front/noMTK/own-window/nonkey/inactive
checks and preload3s/initial1.5s/collection7.2s/hardwindow7.9s/512samples/outer15s
bounds remain;7.2s is the original outer-loop entry deadline, so a RunLoop call
can return past it before that iteration samples. Weak source deallocation is
observed, not required.

CI builds once SDK26.2, Swift5mode arm64/min13; run the original signed binary
on14 and13 without rebuilding/resigning. Original PNG/ICC/native states need
offline review. Native collection success is not image/color/animation parity,
and different-time/progress crosshost mid images are not pixel-equality tests.
No SDK14 unused-clock/gainmap guards or previous snapshot/float/backing hooks.

CLI: binary namedAsset output; BERN_HERO_EXPECT_OS=13|14. Wrapper adds expectedOS
as its fourth argument and unsets BERN_MOTION only for the child. No physical
input, retarget/reversal, other image/alpha/HLG/High/geometry or full-app acceptance.
