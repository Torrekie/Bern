# One natural-iteration-delayed midflight capture

**Assessment:** this is a bounded observer adjustment worth comparing if root elects to proceed. Returning to the existing main RunLoop once between trigger observation and CG capture gives the ordinary rendering/commit path another opportunity. It is not a synchronization fence, a demonstrated CF-pump root cause, or a product/animation fix. No implementation or execution is made here.

## Current evidence checked

`work/native-pq-hero-coordinator-ci-40103369574/runtime13/report.json` has immediate trigger sample10 (zero-based),p0.287220936/root rect(112.5062,87.1886); its capture brackets retain that same native progress/rect. The CG interval is5.314ms. Runtime14 sample7 hasp0.692075796/root rect(248.5375,176.2567), also unchanged in the native brackets; CG interval16.990ms. Thus the scalar brackets themselves do not explain which frame WindowServer returned. Root's separate visual observation reports an earlier rendered position on13 and the source position on14; this note does not remeasure those PNGs or assign cause.

The old next native samples are13:p0.532129451 at+49.481ms and14:p0.883897872 at+72.115ms from their respective triggers. These intervals include the old immediate-capture work and **cannot predict** the delayed candidate's next progress/cadence.

## Single proposed scheduling change

1. At the first existing live sample satisfying0.2<actual progress<0.8, arm a scalar record only: sample index, uptime, full current scalar state and pinned flight identity. Do not call CG capture or add any other waiting/scheduling work in that iteration.
2. Return through the original loop's normal path. After exactly its next existing natural RunLoop iteration and original ownership/normal/live checks, use that next sample for the one midflight capture. Require the same pinned live flight, actual timer and parent; loss/replacement, deadline/sample exhaustion or inability to capture that next sample makes the gate incomplete. Do not seek another band or retry.
3. Record armed and captured sample indices/states/uptimes separately. Capture index must be the next recorded transition sample; preserve the actual capture-before/after uptime and native state brackets. If capture progress has advanced beyond0.8, report that value without rejecting it merely for leaving the **arming** band or presenting it as an in-band rendered frame. Mark capture complete only after its PNG is written.

There is still at most one midflight PNG and three total PNGs. No preliminary screenshot, extra RunLoop call, stable-buffer wait, flush/layout/display, frame/progress assignment, clock change or source/destination change is introduced. Before/settled five-identical-buffer requirements and all original bounds/native gates remain.

## Interpretation limit

A more visibly advanced PNG would support that this capture schedule gives a different observation opportunity. It would not prove which AppKit/CA/WindowServer step was responsible or align the native state with the rendered pixels. An unchanged/late PNG likewise would not prove an animation defect. Preserve original ICC and image bytes for root's inspection; do not infer rendered geometry from manager metadata or demand crossOS pixel equality at different times/progress. Sampling remains asynchronous and affects timing; the candidate does not claim to solve that boundary.
