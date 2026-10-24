# Actual Standard PQ hero: macOS 13 static endpoints

The unmodified product image-hero path visibly differs from its live Standard image in this fixture. Both the named-PQ and strict custom-cICP sources reproduce the difference. This is a measured within-host discrepancy, not yet a macOS 13 regression relative to macOS 14: the corresponding macOS 14 reference is the next gate. No product patch has been applied.

## What actually ran

The image/cache slice is identical to product `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`; extraction was locked to HEAD `b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`. Actual Motion/reduce-motion, `BernPictureHero`, Probe/Anchor, `snapshot(in:)`, FlightView and manager sources are retained. The complete AppKit hero block is also byte-identical to locked upstream `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee` (SHA256 `8e1e90a00ff2f386a38ed8c4977af27a505571051560d50406e9e54b69ed186c`, terminal-newline convention recorded in provenance).

Two real `BernImage` views use unique, nonnil hero keys. The actual SwiftUI modifier and Probe produce two attached Anchors; each actual snapshot is passed to the actual private FlightView as both source and destination. The lower row renders fixed progress 0 and 1, with the ordinary body and native named-PQ oracle visible simultaneously. There is no coordinator flight: its timer remains absent and flight count is zero. This checks snapshot/draw endpoints, **not** transition matching, interpolation, lifecycle, retargeting or visibility restoration.

The two existing atlas files are reused without regeneration: `color-probe13/source-named-pq.png` SHA256 `3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b` and `source-ffb-icc.png` SHA256 `fa3fdc43d91518c145c08b01ba6181ec063c68158e57d312a1ff942571c2a12e`. Both are 640×360, fully opaque RGBA, orientation up. The frame is 320×180pt, fill, corner 0, original rendering, explicit Standard. This does not cover HLG, alpha, other orientations or fit modes.

## Measured result

Two original WindowServer PNGs retain their ICC. Each phase required five consecutive equal raw buffers before capture. After ICC→sRGB conversion:

|Compared to same-phase native oracle|Full RGB MAE /255|Maximum channel difference|Different pixels /230400|
|---|---:|---:|---:|
|Actual body, named PQ|0|0|0|
|Actual body, custom cICP PQ|0|0|0|
|Actual snapshot→FlightView, named PQ|18.3777604167|164|159539|
|Actual snapshot→FlightView, custom cICP PQ|18.3857204861|164|159539|

Progress 0 and 1 give the same result, and each of the six image regions is unchanged between phases. The body matches its same-row `oracle-top` in raw RGB and normalized sRGB. The two oracle rows themselves differ slightly: normalized fullRGB MAE0.294106/max5; their patch-mean MAE is0.000755/max0.002747. Hero values in the table compare with its same-row `oracle-bottom`. Detailed color-patch/ramp measurements are in the companion offline analysis; their masks come from the existing source atlas, not inferred image boundaries.

Correction: the first version of this README incorrectly expanded same-row body equality to both oracle rows. The raw reports and offline numerical JSON always retained the cross-row difference and are unchanged; this correction narrows the prose to the measured result.

The actual snapshot returns `NSCGImageSnapshotRep`, 640×360, 16 bits per sample, public color-space label `NSCalibratedRGBColorSpace`. The driver does not request `cgImage(forProposedRect:)`, TIFF data, or a bitmap conversion from NSImage. The underlying ImageRenderer CGImage metadata is therefore unobserved; this public label alone does not specify its transfer function or prove a cause.

## Runtime and compilation boundaries

The owned nonkey window existed for 1.970354 seconds. Activation calls 0; frontmost PID 1390→1390. Both phases observed current headroom 1, potential headroom 2, zero MTKViews and no coordinator clock. Normal reduce-motion/reduce-transparency/increase-contrast flags were false before and after. Original and derived cache identity, providers, ICCs, files, dimensions, orientation, ratio and cached average values remain unchanged.

Local compiler: Swift 5.9.2 / SDK14.2, arm64, minimum macOS13, Swift5 language mode, optimized, two compiler jobs. Exact sources are preserved separately from the compiled fixture. Two explicit diagnostic adaptations are recorded: the previously reviewed compiler condition excludes the macOS15 gain-map decoder from the SDK14.2 build; an availability/compiler guard makes the **unused** coordinator timer fail immediately on13 if it is unexpectedly started. The actual snapshot and FlightView draw bodies are unchanged. Consequently this is not proof that the entire unmodified coordinator compiles with this old SDK or that an actual animation ran. A new-SDK build used on both hosts will remove this fixture-only clock restriction.

The first compile log is retained. Its errors were SDK14.2 availability for the unused timer and a driver dictionary expression exceeding Swift5.9 type-check limits; the latter was split into assignments. The existing product exhaustive-switch warning remains. The runtime log also retains the existing AppKit warning about adding the upstream overlay to NSThemeFrame; the fixture did not suppress or change it.

`cleanup.json` records deletion of this completed fixture's executable and module cache, after confirming its PID exited. About 57.4MB of logical files were removed; this is not an APFS physical-space claim. All raw images, reports, exact/adapted sources and logs remain. No product binaries, global defaults, user window history, privacy grants or unrelated caches were changed.

The archived `prepare.py` and `run.py` are the historical acquisition wrappers and retain their original scratch-directory layout assumptions; they are not portable replay entry points. Exact sources remain independently inspectable, and `build.sh` still builds them in this directory with the documented local-SDK adaptations. For the portable new-SDK cross-host package, use [the shared reference harness](../../../../.github/scripts/hero-snapshot-probe/README.md). The offline analyzer accepts an explicit report path and does not require replaying the UI. The work paths are symlinks to this single archive, not duplicate evidence copies.
