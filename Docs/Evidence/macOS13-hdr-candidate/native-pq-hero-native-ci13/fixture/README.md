# Fixed-input native Core Image snapshot experiment

Prepared only. No Swift compilation/typecheck, UI, CI, product/branch/release edit, or modification of the existing baseline/colorMode/cgmetadata fixtures or archives. Root is waiting for14 metadata before deciding whether to run this. There is no image-equality success gate or fitted color formula.

## Exact scope and default

The successful archived `native-pq-hero-baseline13` image/cache/Style/complete Hero and same-file Driver are reused and verified against its build fingerprint. The source is the b08db54 extraction, with9dd-equivalent image/hero slices. The known SDK14.2 gain-map compiler guard and unused-coordinator-clock failguard remain byte-identical. Body, root driver frames/actions, all capture/stable-buffer/normal/front/cache/noMetal/noTimer/deadline gates are unchanged.

One process-cached `BERN_HERO_SNAPSHOT_BACKEND` selects `default` or `nativeCI`. Unset/default follows the original ImageRenderer snapshot code; it does not create a CIContext or register selected-CI inputs. Unknown values fail before window creation and cannot silently use the renderer. The default source gains a mode guard/branch, so it still requires its own measured control before interpreting a conversion result.

`native-ci-snapshot.patch` adds an early selected branch and otherwise preserves the archived renderer block byte for byte. The selected branch uses the same original `NSImage(cgImage: pixels, size: bounds.size)` arguments and unchanged FlightView.draw. It does not alter the Picture, cached image, ICC, provider, EXIF, body rendering or underlying source bytes.

## Locked selected path

This is only the already verified **opaque/up640×360 source → fill320×180pt at2×, no transform/corner** color gate. Preparation registers the two existing SHA-locked atlas files against actual cached original-image identities. The helper registry stores only identity/label, not CGImage/NSImage. At the actual snapshot it reuses `picture.legacyStandardPQImage`; if absent, only the exact previously verified named-PQ input may use its original image. A custom input without the actual cached canonical image fails. The filename/profile-name is not used to identify new arbitrary HDR inputs.

The selected conversion is exactly:

```swift
let image = CIImage(cgImage: display, options: [.colorSpace: sourceSpace])
let pixels = context.createCGImage(image, from: fixed640x360Extent,
                                  format: .RGBAh, colorSpace: extendedSRGB)
```

CIContext is created lazily only inside this selected conversion. No filter, exposure, resampling, kernel, hand-written transfer function or tone mapper is added. System conversion behavior itself remains to be measured; it is not assumed to equal body or14. `.RGBAh` and the extendedSRGB argument are requested format/configuration, not an assertion that their pixels solve the discrepancy.

The inherited no-Metal gate counts MTKView instances only. It does not establish that CIContext internally avoids Metal/GPU work; this fixture does not make that claim.

Unsupported fit/orientation/size/scale/transformed rect/corner/non-image capture, missing registered input/colorSpace or failed conversion yields an explicit native-ci diagnostic failure and nil snapshot. There is no fallback to ImageRenderer. This is not a general fit/orientation/alpha/HLG/gain-map or product-renderer proposal.

## Observation policy

New metadata uses CGImage scalars only: width/height, bit depths, row bytes, bitmap/alpha values and the float-components bit. No new CopyICCData, color-space name, PQ/HDR flags or color classification is performed before drawing/PNG. The source colorSpace is referenced only for the actual explicit CIImage input. Output metadata retains no CGImage/NSImage/CGColorSpace; only scalar dictionaries. The diagnostic report is assembled after the original window teardown. Existing baseline ledger and NSImageRep observations are retained without change.

This deliberately avoids the newly observed eager-profile-observer disturbance. The13 ImageRenderer extendedSRGB/16-float metadata is prior evidence, not a new observation made by this helper.14 metadata remains outside this candidate and cannot be predicted from that source fact.

Independent source-only review found no definite Swift5.9 scope/type/public-API blocker. It confirmed default lazy-context behavior, no selected-path fallback, metadata retention boundaries and the fixed-input guards. Swift compilation and pixel reproduction remain unperformed.

## Build/run entry points (not executed)

`build.sh` verifies prepared-source hashes, records environment, uses baseline optimized Swift5/two jobs/arm64-min13 flags, preserves warnings and records executable/signature fingerprints. It does not launch. `run.py` verifies the same two asset hashes and built executable, launches one process into a new output path and retains the baseline15-second outer bound. No automatic process/mode matrix exists.

Only if root authorizes after the14 metadata gate:

```sh
bash work/native-pq-hero-native-ci/build.sh
BERN_HERO_SNAPSHOT_BACKEND=default python3 -B work/native-pq-hero-native-ci/run.py work/native-pq-hero-native-ci/runtime13-default-control
```

Do not proceed past control merely because the process exits0. Default must reproduce the six-ROI baseline. A later separately coordinated selected run would use `BERN_HERO_SNAPSHOT_BACKEND=nativeCI` and a fresh output path. Compare actual NSImage.draw endpoints with the measured14 reference and retain the same-host body/oracle values as context; matching body is not the imposed goal. No new14 dispatch, color matrix or product patch is requested here.
