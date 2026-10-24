# Actual BernImage body/cache diagnostic — prepared, not executed

This work-only fixture extracts the complete `enum BernImageFit` through `BernPictures` slice from product commit `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`. `ProductImage.exact.swift` is the unmodified slice; `source-provenance.json` records the full Runtime hash and extraction span. The real `BernImage.body`, `.task`, `BernPictures.load(fileURL)`, cache, Standard SwiftUI branch, Legacy software/Metal routes, and dismantle implementation remain present.

`ProductImage.swift` adds imports and one compiler condition around the macOS 15+/iOS 18+ gain-map decoder constants unavailable to SDK 14.2. Swift compiler <6 uses `decoded = nil`; that branch is unreachable on the required macOS 13 runtime. The exact delta is `sdk14-unreachable-gainmap.patch`. No other product-image code changes are allowed. The original product's redundant `@unknown default` warning under Swift 5.9.2 remains unmodified, so local typecheck/build uses normal warnings, not warnings-as-errors.

Only diagnostic dependencies are supplied: ObservableObject alias, `BernColor.fixed` shape, BernMotion values, and an identity BernPictureHero. Hero snapshots/transitions are excluded. This is not a full Showcase app, and HLG, gain maps, arbitrary alpha/EXIF and High color matching are outside its scope.

The planned own nonkey Aqua window contains two actual `BernImage(url:, fit:.fill, rendering:.original, width:320, height:180, dynamicRange:)` columns and a third bare native named-PQ SwiftUI image oracle. Both files are loaded through the actual cache before the window opens. The three phases are Standard → High → Standard. The public MTKView tree must be 0 → 2 → 0. The two observed High views are retained solely to verify detached `window == nil` and `wantsExtendedDynamicRangeContent == false` after dismantle; retention delays deallocation and is reported. No product renderer instrumentation is inserted.

The report records current/potential headroom and layer EDR state. High readiness requires the two public surfaces and their correct potential-capability request; it does not require current headroom >1 and does not accept High colors. Returning Standard requires current <=1.001, no live Metal views, and both held High views detached with EDR off. If the machine cannot settle, the bounded probe reports partial/failure rather than changing brightness or preferences.

Two real WindowServer PNGs per phase are collected without waiting for image equality. After collection, the four Standard captures must have identical canonical sRGB ROI hashes across phases for each column, and each product column must match the native oracle. High captures are retained only for lifecycle context. Original/derived CGImage identity, provider and ICC hashes, original file/layout/orientation/ratio, and cached average are compared across phases. No new image assets or formula tuning are introduced.

The app never activates or restores another app. It checks foreground/nonkey/inactive/onscreen state, records the entire public trajectory, closes its own window, and releases only its own Metal surfaces. Collection is bounded to 7.2 seconds; a 7.9 second process watchdog handles an unexpected stall. The pre-window file decode has its own 10 second bound. The watchdog failure marker is incomplete evidence, not a success report.

## Build only (root execution)

```sh
bash work/native-pq-product-body/build.sh
```

This produces `ProductBodyProbe`, `build.log` and a binary/source/environment `build-fingerprint.json`. It does not launch a window.

## One bounded run (root must coordinate desktop)

From the task workspace:

```sh
work/native-pq-product-body/ProductBodyProbe \
  outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/color-probe13/source-named-pq.png \
  outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/color-probe13/source-ffb-icc.png \
  work/native-pq-product-body/runtime13
```

Use a new output directory and preserve the executable hash/build fingerprint before removing executable/module cache. No runtime result is claimed by this preparation.
