# Private next-original-sample midflight driver

`Driver.swift.inc` is copied from the current published coordinator driver, then changed only for scalar arming and the one midflight capture schedule. Base SHA=`d8ed3e8d5716f65b00a6d14fd1007d89eaf30d5aca58446344263d59375a739b`. `delay-driver.patch` and `provenance.json` lock the difference; original repository/product/Hero files are untouched. This source preparation has not compiled or run.

At the first same-pinned-live-flight sample with0.2<progress<0.8, the driver writes the complete scalar arm to the report and takes no image. The next original loop performs its existing natural RunLoop and sample; only that adjacent sample may take the midflight image, requiring the same flight/timer/actual overlay parent. Progress there may exceed0.8. A lost manager/live flight, changed identity, missed next index or exhausted bound fails incomplete, without another arm/band search/retry. No RunLoop, flush, dispatch, layout/display, progress/visibility/clock control or capture call site is added. Before/settled five-buffer gates, one transition,3PNG/512sample/preload/window/outer bounds and CG capture brackets remain unchanged.

## Exact schema

Each `samples` row now also has `sample_index` (zero-based). Top-level `midflight_sampling` is initialized before sampling and contains `policy="first_band_arm_then_next_original_loop_sample"`, `armed`, `capture_sample`, `capture_attempted`, `next_sample_captured`. `armed` and `capture_sample` are null until available, then each contains **sample_index, state, uptime, progress, flight_identity**. The arm is stored immediately; the next sample/attempt flag is stored before CG capture, so failures preserve evidence. Capture-complete becomes true only after the PNG write.

The successful `in-flight` capture has these flat fields:

- `armed_sample_index`, `armed_sample_state`, `armed_sample_uptime`, `armed_progress`, `armed_flight_identity`.
- `capture_sample_index`, `capture_sample_state`, `capture_sample_uptime`, `capture_sample_progress`, `capture_sample_flight_identity`.
- `sampling_policy` as above; `trigger_state`/`trigger_progress` are explicit **armed** aliases, identified by `trigger_refers_to="armed_sample"`.
- Original capture-before/after uptime/state brackets, PNG/ICC/native/window/ROI fields and `consecutive_equal_buffers_required=false` remain.

Require `capture_sample_index=armed_sample_index+1` and both identities equal the original pinned flight. Only `armed_progress` is required in the band; do not impose that band on `capture_sample_progress` or the CG bracket state. Success `native_gates` replaces old `midband_captured` with **midband_armed** and **next_sample_captured**. Original movement/retirement gates remain. Partial failure may contain an arm and capture attempt without a PNG, or an arm with no next sample; it is never a successful capture.

This permits another ordinary commit opportunity; it is not a synchronization fence, a proven CF-pump explanation, or an animation/color fix. Native state is not the rendered frame, and different-time/progress13/14 PNGs are not required to match pixel-for-pixel. No zero-observer-effect claim or runtime acceptance is made.
