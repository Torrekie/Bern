# Actual hero snapshots: one binary on macOS 13 and 14

The remote ordinary-effects reference is complete. The same signed ARM64/min13 executable was run on both hosts. macOS14 also changes the live picture's colors when creating/drawing the hero snapshot; forcing the13 snapshot to equal its live body is therefore not an established upstream behavior. The two hosts still differ materially in these endpoints, so hero color equivalence has not passed and no product patch was applied.

## Identities and provenance

|Record|Location / result|
|---|---|
|[Build40080291082](https://github.com/Torrekie/Bern/actions/runs/40080291082)|Build job succeeded; first14 runtime job stopped **before executable launch**, because a raw `defaults read` key was absent. No runtime report/log/PNG was produced. Preserved separately in `build40080291082-and-runtime13/runtime14/` and the job log.|
|[Runtime40080838898](https://github.com/Torrekie/Bern/actions/runs/40080838898)|Succeeded using the retained build artifact, without rebuilding. Raw runtime reference is `runtime40080838898/runtime14/`.|
|Exact13 runtime|`build40080291082-and-runtime13/runtime13/`; success, same original packaged executable.|
|Build source|Harness `cc0eb1ead71e2912180a8f8b4a349849f3775b7e`, locked extracted product source `b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`; AppKit hero block is byte-identical to locked upstream.|
|Runtime-only harness|`1f4ff43e1d6311d94b6d45f2137e84b80ebec1c9`; changes optional raw preference logging and pins original tar/binary hashes; effective normal flags remain mandatory.|
|Executable SHA256|`f50acd4dee545befeaafa500532c76dd9cd094c46e68e700ce403ce32f8aead2`|
|Original tar SHA256|`1b1312eb01ebdbed5baec9b9fd69dd7d9ee066ef1e6a1cb7cda686c589ffe807`|

Build: Xcode26.3/Swift6.2.4/SDK26.2, Swift5 mode, optimized, two compiler jobs, ARM64/min13. The original gain-map and coordinator clock sources compile without either SDK14 diagnostic adaptation. The original signature, architecture/minimum-OS metadata, 22-member package manifest and transfer hashes were verified, including again after the13 run;14 verified the same pinned tar and binary independently. The portable source package remains in [the harness](../../../.github/scripts/hero-snapshot-probe/README.md).

Both runtimes mount actual BernImage views with distinct nonnil hero keys. Actual modifier/Probe/Anchor snapshots feed actual FlightView.draw at fixed progress0/1, with from==to. There is no coordinator flight/timer. No changes to source image pixels/ICC, cache, fitting, orientation, snapshot conversion, renderer scale or draw equations were introduced. This is endpoint evidence, not complete animation or lifecycle acceptance.

## Result

[Full offline analysis](analysis/README.md), [summary](analysis/summary.json) and [signed patch residuals](analysis/crosshost-result/comparison.json) retain all comparisons. One local Pillow/LittleCMS version reads the original PNG/ICC from both hosts; no image resize, registration or fitted compensation is performed.

New-SDK13 vs the [old-SDK13 baseline](../macOS13-hdr-candidate/native-pq-hero-baseline13/README.md): all12 phase/ROI pairs are identical in raw RGB and normalized sRGB, with matching ICC. This rules out a change in those13 pixels from this compiler/SDK switch only.

For each patch/channel, `Dhost = mean(hero) − mean(body)` in normalized encoded sRGB. These are **ten-patch mean residual statistics**, not whole-image pixel MAE or physical light:

|Phase/source|Mean absolute D13−D14 /255|Maximum absolute D13−D14 /255|
|---|---:|---:|
|0 named|5.210863|112.616329|
|0 custom|5.223884|112.618733|
|1 named|5.224399|113.048334|
|1 custom|5.236956|113.048334|

The largest item is the cool812 red channel. At phase0, named13 body/hero are approximately92.49/254.89;14 are118.65/168.43. Both hosts have a hero/body discrepancy, but its size/color is not equal. Display profiles, potential headroom and 1×/2× sampling differ, so these observations do not establish a unique OS or rendering cause.

14 hero vs its same-row `oracle-bottom` has fullRGB sRGB MAE15.036186/15.060961 at phase0 and15.032037/15.032037 at phase1, maximum97. Its hero pixels also vary slightly between phases (named MAE0.132020/max1, custom0.131447/max2);14 body/oracles each remain unchanged.13's six regions are each unchanged across phases.

Body equality must retain its precise scope.13 named/custom bodies match the same-row `oracle-top`.14 named matches `oracle-top`, while custom has fullRGB MAE0.280619/max2, patch-mean MAE0.001293/max0.007212. The two oracle rows themselves also have small pixel differences on each host. Earlier prose that expanded same-row13 equality to both rows has been corrected in the old archive; original numerical reports/PNGs are unchanged.

## Runtime, limits and next step

13 window1.611717s, frontmost1390→1390, actual headroom1/potential2;14 window2.498606s, frontmost306→306, actual/potential1. Both are nonkey/inactive, activation0, normal accessibility flags false before/after, live Metal0, coordinator flights0/timer absent, cache identities/provider/ICC/file/orientation/ratio/average unchanged. Each retained phase requires five consecutive equal raw WindowServer buffers. Both actual snapshot representations are NSCGImageSnapshotRep/16 bits, sized at the respective backing scale. No CGImage/TIFF recaching of NSImage was requested.

The parent independently rechecked package/runtime contracts and recalculated all four cross-host patch residuals; see `root-crosshost-check.json` and per-run checks. `source-alpha/report.json` independently decodes every original RGBA16 alpha sample; both atlases are65535 throughout, rather than relying on an8-bit alpha conversion.

The prepared optional selected-display-image patch remains unapplied: named PQ also fails, and that patch cannot yet account for the measured discrepancy. Next is a bounded13 diagnostic of ImageRenderer's public colorMode option, starting with an unchanged-default control and one extendedLinear candidate. The SDK exposes these facilities on13. No fixed RGB, atlas-fitted tone curve, new control, or global color/style replacement is proposed. A useful result must then be checked against this actual14 baseline and wider image/flight invariants.

High/HLG, alpha/orientation/fit variants, physical HDR, enter/leave, hide/restore, interpolation, retarget/reversal and full application acceptance remain unproven. The goal remains active; macOS11/Swift5.3, Objective-C and iOS remain deferred.

## Retention and cleanup

Raw13/14 PNGs and ICCs, reports, first failed prelaunch record, source/build/signature provenance and offline analysis remain. `build40080291082-and-runtime13/cleanup.json` lists the22 unpacked package files plus manifest and redundant tar removed after process exit/hash/signature verification:939623 logical bytes. Those historical package/transfer manifests describe the original package, not a claim that deleted members remain here; the current `FINAL-SHA256SUMS` covers all retained files. Earlier local SDK14 module cache/executable cleanup removed about57.4MB of logical files. These are not APFS physical-space claims. Work paths now point to this single archive through symlinks; no duplicate apps or downloads remain.
