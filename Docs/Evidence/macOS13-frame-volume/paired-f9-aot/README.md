# Active macOS13 Frame/volume vs the locked A/B14 reference

Root's single AOT attempt (session28611) succeeded on macOS13.7.8, normal light, physical2× Color LCD:12.210336seconds, all three permissions true, own GalleryPID99204, frontmostPID1390 before/after. Source is delivered f9 Gallery, build39991406873/source`f9e08b1d55bed4b9d880b19934abe48281057bb3`, independently of later9dd Showcase. No product/main-collector change or UI rerun was used for this offline analysis.

**Interactions and major point geometry pass. Color/pixel equality does not.** The [existing A/B14 reference](../../macOS14-frame-volume/paired-40065164350/README.md) uses a virtual1× display. The original three C13 PNGs, complete raw reports and all CLI logs remain in `run-aot/`.

## Geometry and visible controls

Points are relative to the920×668 main outer frame; geometry is stable through closed/open/isolated-popup/dismissed stages.

| Measurement | A/B14 | C13 |
|---|---|---|
| Clip AXUnknown |251,167,629×354|exactly equal|
| Popup window |497,553,266×106|exactly equal|
| Slider AX frame |579,610,155×20|exactly equal|
| Volume AXButton |619,536,22×15|620.5,533,20×20|
| Visible Volume bezel bbox |[620,533,640,553)|[620.5,533,640.5,553)|
| Speaker ink bbox, meanRGB>130/160 |[621,536,638,548)|[622,536.5,639,549)|

The AX-frame difference does not establish a visible size difference: both circular bezels are20×20, shifted0.5point horizontally. Speaker ink edges differ at most1point under both thresholds. Popup title/Volume label ink edges differ at most0.5point. Its visible slider knob bboxes are[177,57,197,77) vs[176.5,57,196.5,77) in popup coordinates; red track differs0.5point at its right edge. Both knob-center samples are sRGB140,140,140. Popup alpha-mask bounds agree at thresholds0/127/254, with alpha MAE0.009097/255.

Other bottom-row differences remain: Caption bezel x251…358 vs251…356 (107 vs105points), Size bezel x370…608 vs368…608 (238 vs240), all y533…553. Caption text shifts1point left at RGB-distance-from-local-background>60. Size text shifts about3points left: [401,537,426,547) vs[398,537,422.5,547.5) at distance>40/60; its AA icon shifts about2.5points. Rest text edges differ at most0.5point at meanRGB thresholds95/130. `analysis/comparison.json` retains exact ROI definitions and threshold sweeps. These are visible-ink observations, not inferred view frames; no control/font compensation was applied.

## Color-managed pixels

C13 ICC SHA256 is`e2473ef48182e793b50bd21dd4d1d9b37d26b02b5a38508ded86d836ef9b64d4`;14 uses`3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`. Each original ICC is converted to sRGB with relative-colorimetric LittleCMS; only then C13's exact2×2 samples are area-averaged to points. No translation, fitted color correction or hidden ROI exclusion is applied.

| Full original capture | RGB MAE A14/C13, /255 | B14/C13, /255 |
|---|---:|---:|
| Frame closed920×668|4.600316|4.446010|
| Frame open920×668|4.704112|4.549806|
| Isolated popup266×106|4.237939|4.237939|

Closed detail ROI[211,52,920,668) MAE is2.763240; video ROI[251,167,880,521) is2.973325. Common fully opaque popup pixels have RGB MAE5.947916; its transparent outside area lowers the whole-image mean. Flat popup ROI[105,25,155,45) averages A14[103.428,103.416,103.412] vs C13[115.902,105.753,105.754]. This warm difference is measured without assigning a desktop/focus/material cause. Canvas gray50 and video gray patches102/191 agree after conversion, while saturated patches differ, e.g. magenta[176,0,186] vs[193,0,193]. A uniform color/position explanation is not assumed.

These native appearance, font/AA and video-color differences prevent a full visual/pixel-equivalence claim. Capture-time AXFocused/firstResponder was not collected; early CLI focused=true is not used to assign a focus cause. A14/B14's known sidebar gray/blue selection difference also remains in their reference.

## Runtime and provenance

The successful run retains21 own-active-PID mouseMoved heartbeats with native/CG/native window-number equality;15 exact raw-CGWindowID/owner round trips; six awake checks passing the unchanged>3.2second source loop; Ready→play/pause/seek→Paused0 with sourceVersion1. Each capture has5buffers/4equal comparisons. AXPress opens/closes the real popup. Its main+popup composite and isolated native popup agree at all76,844 fully opaque2× popup pixels. Final popup controls unmount and its CG window is absent. Bundled tides.mp4 SHA256`145a1b5e572bd3ce16207e2b341c0eecb04b4d1e765bf72f5fe3809a24f34957` matches A/B14. Individual awake-stage timestamps are not relabelled as the loop duration.

The interpreter attempt(session55767) exited255 with unresolved CryptoKit JIT symbols before collector top-level, permission queries, report or Gallery launch. `interpreter-attempt/` retains original log/failure/history. Root executed the AOT binary once, exit0. Frozen collector SHA256`77e4bb6849ea226cb4bcc4bacac7b08197e8f5a18f4aa991752d81cea44c4db8`; AOT binary SHA256`1d0e95f11c6f5174fdf65751a8b73be9ef898ec054b787715c3c8f33d954f1d1`. Its selected toolchain is local Swift5.9.2/SDK14.2, actual LC min13/sdk13, separate from Gallery Swift6.2.4/SDK26.2. Historical build metadata binary_executed=false refers to preparation time, not the subsequent runtime. The overstrict post-build SDK assertion was corrected against the existing binary without recompilation. The compile-only overlap with root's old Film baseline remains recorded.

`PREPARATION.md`, collector/baseline/patch, prepare/build scripts, all source/binary/toolchain fingerprints, section comparison, signature/load-command records and original reports are retained. `cleanup.json` and removed-file hashes record removal of the exited task-only app/CLI/AOT binary after hashing; original delivered Gallery/CLI are preserved. Full pre-cleanup/final manifests remain, and the work path is a symlink to this sole archive. Historical RUN scripts intentionally cannot execute after cleanup.

Run `python3 analyze.py` with NumPy/Pillow to regenerate `analysis/comparison.json` entirely offline against the relative14 reference. This covers these active light Frame/popover slices and process-targeted synthetic input, not physical input, dark/HDR, continuous playback/audio, arbitrary popup layouts or whole-project acceptance.
