# Independent BT.2408-6 Annex 5 CPU/linear-EDR prototype

This is an archived work-only prototype, not a product implementation. No product source was changed. It supports exactly the upstream neutral `hdr-pq.png` (SHA256 `96f80d2f1c06070dac29e3b7e2924a6aed8e54286bc73921f62cf75420a599ed`), not general HDR images.

## Explicit candidate, not a claimed Apple algorithm

Input is strict RGB full-range CICP9/16/0/1, opaque neutral16-bit PQ. ImageIO's decoded provider is **RGBA16 little-endian** on this machine, although PNG scanlines store big-endian samples; the decoder checks the actual CGImage bitmapInfo. `copy(colorSpace:namedPQ)` retains byte-identical provider pixels, and the original file/ICC is not written. PQ EOTF decodes the top halves to203.016424/812.055272 cd/m².

The scalar candidate is BT.2408-6 Annex5 with LB0/LW1000/Lmin0/Lmax203×Hd. **LW1000 is a candidate preset supported by the prior A14 neutral ramp, not a mastering value read from PNG.** 203 is the ISO default diffuse white from Apple's ISO HDR documentation, not ICC lumi100. No valid override metadata is invented. For this fixed <=812.056nit fixture, PQ->absolute nit->Annex5->Lout/203 produces linear BT.2020 components relative to UI/SDR white1. Hd>=1000/203 passes L/203 through, avoiding the singular knee. Out-of-mastering-range or arbitrary color behavior is not established by this test.

`ToneMap.swift` builds a u16 lookup table and a640×360 Float32RGBA CGImage. `Display.swift` uses system Core Image/MTKView with a CAMetalLayer tagged extendedLinearITUR2020, rgba16Float; there is no PQ output layer, no extra EOTF, and no invented CA HDR10 metadata. CI supplies native color-space handling to the display pipeline. The output's EDR1 is UI white, not a fixed physical screen nit value.

The formula and input validation were independently reviewed by compat_audit against the separate Python Annex5 implementation. This only validates the specified scalar algorithm, not a unique identity with Apple's private14 method.

## Measured result

- macOS13.7.8, arm64 Apple M1; Swift5.9.2/SDK14.2. See `environment.txt`.
- Four real WindowServer captures observe current headroom **1→2→1→2**, potential2 throughout. All404 screen events were real OS notifications; no manual notification was posted.
- Hd1 Standard, after ICC->sRGB, has top halves **228.9266/254.8215**. Against fixed A14 reference ROI `[435,409,627,432]`,188 interior columns×3 channels: **MAE0.104109/255, max0.456522/255**. There is no phase fit. C13 retains raw2xPNG; analysis averages each pair of physical samples into the corresponding1pt reference column.
- Standard stays byte-identical in its image area while the other pane requests High. High→Standard reproduces the initial mapped image.
- At real Hd2, GPU readback from the presented rgba16Float texture is **1.000000/1.996094**, in **linear BT.2020 relative-to-UI-white** units. The direct Double formula is1.000081/1.99663 approximately for the quantized source. Hd1 texture is0.783203/0.999023. The expected reference vectors for Hd1/1.5/2/3/4/5 are in `report.json`.
- The Hd2 **SDR** WindowServer PNG has about254.89/255 for its top halves. Those screenshot values are clipped/compressed display capture, not the linear texture values or measured physical light. They cannot prove physical14/13 High equivalence. The full High ramp differs from the14 virtual-SDR reference as expected for a different display headroom; that MAE must not be treated as an equal-condition comparison.
- The unique fixture window was active for **0.369s**, then immediately restored the startup frontmost QQ PID75891. All four captures were of its own inactive window. Total window duration6.18s. No brightness or TCC changes, no user app interactions.

## Coarse performance and memory

At640×360 and `-O`, decode+validation18.03ms. First four CPU maps take7.50/6.68/7.44/6.65ms. During real dynamic-headroom changes,57 maps have median18.64ms, max88.08ms. This includes full LUT calculation and float image creation, not just a pixel loop. It is a coarse single-run measurement under current system load, not a throughput benchmark.

One retained Float32RGBA image is3,686,400B; original decoded RGBA16 is1,843,200B; one LUT is about191KB. The sampled whole-process resident max is60,112,896B; after stopping both views it is24,543,232B. This is process resident memory, **not** a measured GPU/VRAM peak. Temporary arrays/Data may coexist; multiply this proof's storage only with clear source-size/ownership accounting.

The raw main-thread CPU recomputation per changing headroom is **not production-ready**: max88ms can visibly stall updates. A later implementation needs bounded latest-request ownership, off-main/coalesced conversion, cache/working-buffer reuse or a GPU implementation. This test does not choose that architecture or alter the runtime.

## Remaining boundary

This is strong neutral-SDR evidence for one public candidate plus proof of correct linear output units and dynamic current-headroom updates. It does not prove general Apple14 equivalence, arbitrary color/gamut mapping, metadata default/priority, HLG, EXIF orientation, alpha, wide images or physical panel brightness. A same-condition14High reference is still missing. `1000` must not silently become a universal inferred source peak.

Files: `ToneMap.swift`, `Display.swift`, `main.swift`, `report.json`, `summary.json`, four rawPNG, `analyze.py`, `metrics.json`, build/environment logs. Executable and module cache are removed after validation.

Reproduce from workspace root into separate scratch (the executable briefly activates only its own window and restores the current frontmost):

```sh
mkdir -p work/hdr-annex5-rerun
xcrun swiftc -O -parse-as-library -swift-version 5 -target arm64-apple-macos13.0 -framework ColorSync -module-cache-path work/hdr-annex5-rerun/module-cache outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/prototype/ToneMap.swift outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/prototype/Display.swift outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/prototype/main.swift -o work/hdr-annex5-rerun/probe
work/hdr-annex5-rerun/probe outputs/Bern/examples/showcase/images/hdr-pq.png work/hdr-annex5-rerun
python3 outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/prototype/analyze.py work/hdr-annex5-rerun
```

Use a different output directory when preserving this run. Official sources: [BT.2408-6 Annex5](https://www.itu.int/dms_pub/itu-r/opb/rep/R-REP-BT.2408-6-2023-PDF-E.pdf), [BT.2100 PQ](https://www.itu.int/dms_pubrec/itu-r/rec/bt/R-REC-BT.2100-2-201807-S!!PDF-E.pdf), [Apple ISO default203 and EDR1 white](https://developer.apple.com/videos/play/wwdc2023/10181/). Research limitations and independent ramp derivation are in the [research note](../../../Implementation/macOS13-HDR-Tone-Mapping.md) and [numeric/REPORT.md](../numeric/REPORT.md).
