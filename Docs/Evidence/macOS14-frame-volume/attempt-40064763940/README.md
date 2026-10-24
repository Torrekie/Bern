# Frame observer attempt 40064763940

This is a failed capture-harness attempt, not a completed A/B visual reference. The locked upstream Gallery A ran on macOS 14.8.9 ARM64 / Apple Virtual 1×; Gallery B did not launch.

The real >=3.2-second awake loop completed. Four CLI/native AX snapshots retain Volume and Caption controls; the video remains Paused at 0 ms with the same bound source/version. The scoped selector identifies the same-parent Clip AXUnknown and Volume AXButton/AXPress, while recording their actual inherited `main_window.find` native identifiers. See `analysis.json` and `a/report.json`.

The first `frame-closed-light` WindowServer array capture returned nil. No PNG was produced, no Volume AXPress/open/dismiss occurred, and no pixel/color or A/B-equivalence result follows. The capture function passed NSNumber objects where the API family represents raw CGWindowID slots. The proposed next tooling correction uses a callback-free CFArray and independently verifies exact IDs/own PID through public window descriptions; that correction is not represented as passed here.

`harness/` preserves the observer that actually ran. `provenance.json` pins the run, artifact, source builds and observer SHA; `SHA256SUMS` covers this directory except itself. Raw numbered CLI output, runtime logs, build metadata and job failure excerpt are retained. No app executable, compiler cache or screenshot substitute is included.
