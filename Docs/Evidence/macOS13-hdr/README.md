# macOS 13 HDR adaptation — partial validation

Product files: `crates/bern-backend-swiftui/templates/BernRuntime.swift` and explicit ColorSync framework link in `src/lib.rs`. Full generated-app build is still the parent task's CI gate.

## Implemented and verified

- Strict ColorSync CICP tag detection, once during image decode. Exact RGB full-range BT.2020 PQ/HLG encoding only: tag type `cicp`, size 12, zero reserved bytes, code points `9/(16|18)/0/1`. The source CGImage and its ICC are unchanged. Canonical named input color spaces are used only when this complete encoding matches. Native CoreGraphics-recognized HDR retains its original color space.
- Existing image intent remains High. `BernImageDynamicRange.standard` is an internal renderer choice; there is no new IR/property option. macOS 14 and iOS/tvOS keep their native allowedDynamicRange paths.
- Standard output is materialized by Core Image into RGBA8 sRGB. On macOS 13.7.8, Standard current-headroom 1 and 2 both preserve the two neutral halves: approximately 228.93/254.89 after screenshot ICC-to-sRGB conversion. Forced no-Metal native NSImageView fallback is 229/255. The macOS 14 virtual-SDR reference is approximately 228.93/254.83; this comparison supports the Standard output only.
- EDR request follows potential capability; actual HDR rendering follows current headroom. Eight policy combinations pass. Real OS notifications were observed as current headroom rose 1→2, naturally fell 2→1 after Standard, and rose 1→2 after High again. The paused MTKView redrew and switched SDR→HDR on those real callbacks. `manual:false` distinguishes these events from the later explicit notification-handler check.
- Resize 192×108→208×117 point frames updates drawables from 384×216 to 416×234. Unmount leaves zero Metal/SDR image views and invokes the two Metal teardown callbacks.
- Fixture briefly activated its own unique window for initial capture, then restored original frontmost QQ PID 75891. All later captures were of its own inactive window. No TCC or user brightness changes.

## High is NOT equivalent

At captured High states, actual current headroom=2, potential=2. The WindowServer SDR PNG has both top halves at 255, whereas Standard retains grey/white. This is not a physical HDR luminance measurement and must not be compared directly with the macOS 14 virtual SDR screenshot as a physical HDR baseline.

A fixture-only GPU blit reads the submitted RGBA16Float texture: left=0.58056640625, right=0.72900390625, with CAMetalLayer colorspace ITU-R 2100 PQ. These are normalized **PQ-encoded** components, not extended-linear EDR units, nits, or 0.58×/0.73× UI white. The two values remain distinct before presentation. A separate extended-linear Core Image inspection yields approximately 2.03/8.12, in a different encoding/unit. It does not prove the High result correct.

macOS 14 introduced automatic ISO HDR adjustment to lower display headroom using ITU global tone mapping. The macOS 13 custom Metal surface currently retains HDR encoded pixels but has no equivalent adaptive tone mapper. Its nil EDR metadata can allow clipping above current headroom. No invented HDR10 mastering metadata, arbitrary 100/203 reference-white factor, custom tone curve, or forced all-Standard workaround has been added.

Public CICP proves encoding, not ISO source content headroom or a universal reference white. ICC luminance Y=100 is not sufficient evidence to normalize every PQ source. HLG detection is covered by the classification checks, but rendered HLG visual equivalence has not been measured. Actual second-screen migration and physical macOS14-vs13 HDR output remain untested.

Official sources:

- [WWDC24 10177](https://developer.apple.com/videos/play/wwdc2024/10177/): ISO HDR ITU global tone mapping since macOS14/iOS17, plus newer content-headroom APIs.
- [NSScreen current headroom](https://developer.apple.com/documentation/appkit/nsscreen/maximumextendeddynamicrangecolorcomponentvalue): current value may rise after EDR request; changes post didChangeScreenParametersNotification.
- [CAMetalLayer EDR metadata](https://developer.apple.com/documentation/quartzcore/cametallayer/edrmetadata): nil metadata does not apply EDR tone mapping.
- [ICC CICP encoding](https://color.org/groups/hdr/ICC.1_CICP_tag.pdf).

## Evidence and reproduction

`main.swift` is the standalone real NSWindow fixture with product helper bodies plus fixture-only counters, real/manual notification logs and 2-pixel GPU readback. `report.json` contains raw events, submitted pixels, frames and current/potential headroom; `metrics.json` contains explicit screenshot ROIs after ICC→sRGB conversion. PNGs are the fixture window's actual WindowServer buffers, captured after four identical consecutive buffers. `linear-probe.swift/txt` records the separate linear-color-space experiment.

The UI fixture preceded one final resource-release-only change: software fallback dismantle now calls `stop()` to clear its retained picture as well as image. The final product helper source, including that change, passed local Swift 5.9.2 / SDK14.2 typecheck targeting arm64 macOS13 (`typecheck-current.swift/log`). One redundant `@unknown default` warning is retained for a future enum case. Full-source Swift6 CI remains pending.

From the workspace root, build this fixture without Rust:

```sh
xcrun swiftc -swift-version 5 -target arm64-apple-macos13.0 -module-cache-path work/hdr-adaptation/module-cache -framework ColorSync work/hdr-adaptation/main.swift -o work/hdr-adaptation/probe
work/hdr-adaptation/probe outputs/Bern/examples/showcase/images/hdr-pq.png work/hdr-adaptation
python3 work/hdr-adaptation/analyze.py
```

The executable intentionally activates only its own window briefly and restores the frontmost app it observed at startup. Keep its output directory separate when preserving this evidence. Executables and module caches have been removed after validation.
