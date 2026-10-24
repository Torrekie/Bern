# One actual coordinator replacement under NSApplication.run

This independent fixture keeps the exact product Hero/Image/Style/dependencies,
scene/key/asset/action, original Hero clock and capture/save helpers. It replaces
only the manually pumped observer host with a normal application lifecycle:
one NSApplication.run, one launch delegate callback, one asynchronous preload,
and a default-mode selector Timer that executes one original sample body per
callback. No per-sample Task, manual RunLoop.run or finishLaunching is used.
The observer timer never calls Hero tick/finish or controls animation progress.

The first real live .2<p<.8 sample arms scalar only. The next adjacent observer
sample may take the only mid PNG if the same flight/timer/actual-overlay parent
is still live. Capture may exceed.8; loss or missed next sample is incomplete
without re-arm/retry. Before/settled retain five identical raw buffers, one real
conditional replacement, one flight identity, original retirement and3 PNGs.
The old policy string first_band_arm_then_next_original_loop_sample is retained
for schema continuity; execution_model identifies that the next sample is now
from the next default-mode observer callback, not a manual RunLoop call.

Normal terminal success/error invalidates sampling, calls stop and posts one
applicationDefined event only to the own application queue. That terminal wake
permits event-loop return and is not physical input or a render fence. Report
writing and window cleanup occur through the original defer after run returns.
The exact entry/launch/preload/callback/terminal/stop/wake/return counts/times,
mode, reentrancy and invalidation path are recorded. Callback count includes
preloading and need not equal the number of actual scene samples. The invalidation
flag records the executed source path, not an independent Timer.isValid getter.

Cache/normal/front/noMTK/own-window/nonkey/inactive/fixed-frame gates remain.
Preload3s, readiness1.5s, callback-entry collection7.2s, independent global
window watchdog7.9s,512 scene samples and outer15s remain. A callback entering
before7.2s may finish afterward. The unchanged watchdog can replace partial
reports with a minimal failure and _exit; complete partial state is retained
only through normal defer and successful report writing. Late preload completion
cannot create a window after terminal. Fresh output is mandatory.

CI builds once SDK26.2 Swift5mode arm64/min13; use the original signed binary
on14 and13 without rebuild/resign. This modified driver has no local compile or
typecheck. Product Hero exact bytes have no old snapshot/metadata/float/backing
hooks or SDK14 unused-clock/gainmap guards. Native success requires offline
original PNG/ICC review; it is not visual/color/synchronized animation parity.
Full generated-app, retarget/reversal, other input/alpha/High/HLG/geometry and
physical input acceptance remain separate.

CLI: binary namedAsset output; BERN_HERO_EXPECT_OS=13|14. Wrapper adds expectedOS
as its fourth argument and only unsets BERN_MOTION in its child environment.

Apple references: [stop](https://developer.apple.com/documentation/appkit/nsapplication/stop%28_%3A%29?language=objc),
[postEvent](https://developer.apple.com/documentation/appkit/nsapplication/postevent%28_%3Aatstart%3A%29?language=objc).
