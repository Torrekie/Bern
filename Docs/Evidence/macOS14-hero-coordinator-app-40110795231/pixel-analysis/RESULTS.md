# Normal-AppKit-loop coordinator: original pixel analysis

One authorized offline execution completed with exit0. All14 inputs were reverified by byte count and SHA256: six new original PNGs, four old endpoint PNGs and four reports. No PNG was copied or rewritten; no derived image, registration, fitting, resampling, UI, compilation or CI run was added. `summary.json` retains full numerical values, original input/profile hashes, timing states and execution fields. `PREPARED-SHA256SUMS` validates the three source-only preparation files; the unchanged README/provenance describe that historical preparation state. `execution.json`, this file and the final manifest describe the completed execution.

The new input is `work/native-pq-hero-coordinator-app-ci-40110795231/runtime13|14`; old control is the frozen `macOS14-hero-coordinator-delay-40107406624/same-binary-13-14/runtime13|14` archive. ICC normalization used each embedded profile, perceptual intent0 to sRGB, flags0. All endpoint ROIs were equal-size measured integral screenshot-pixel rectangles and entirely opaque.

| Same-host new before/source→settled/destination | raw MAE / max | sRGB MAE / max |
|---|---:|---:|
| macOS13,640×360 pixels |0.3447728587962963 /2 |0.29410590277777776 /5 |
| macOS14,320×180 pixels |0.27116898148148144 /2 |0.27116898148148144 /2 |

Each of the four same-host old→new endpoint controls (before/source and settled/destination on each OS) is exact in both raw RGB and normalized sRGB: MAE0,max0. Embedded ICC hashes also match within every comparison. No cross-host pixel equality is required.

Within the fixed12pt all-opaque root inset, normalized nonwhite content bounds in root points were:

- macOS13: `[96,76.5,416,256.5]`; measured scale2 and screenshot inset `[24,80,2024,912]`.
- macOS14: `[233,166,554,347]`; measured scale1 and screenshot inset `[12,40,1012,456]`.

These bounds describe nonwhite content and may omit white cells; they are not exact flight bounds. The macOS14 content in this capture is outside the original source rectangle. There is no fitted registration, crop based on a logical flight frame, or cross-host different-progress mid comparison.

Arm/capture remain separate adjacent observer samples of the same pinned identity:

| OS | armed sample / progress | capture sample / progress | CG capture uptime bracket |
|---|---|---|---|
|13 |8 /0.23794066346417264 |9 /0.36223425401025877 |260098.3054161667…260098.310032375 |
|14 |7 /0.6466071089564183 |8 /0.6938772476658079 |65.64710079166667…65.66520120833334 |

Both new native acquisition reports are successful, and the script's execution-contract check performed successfully. Each reports one launch/run entry/run return/terminal/stop/wake, default-mode sampling, maximum callback depth1, no reentrant or post-terminal sampler callback, and terminal-only own-queue applicationDefined wake. Reported sampler callback counts are57 on13 and49 on14. The invalidate-before-stop Boolean is the source-path flag, not an independent Timer.isValid observation.

The actual native state, progress and capture time brackets are retained in JSON. They do not establish which state WindowServer rendered, synchronized capture, a root cause, zero observer effect, physical HDR behavior or complete color/animation acceptance. Original-image visibility review remains root's separate step.
