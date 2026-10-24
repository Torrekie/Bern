# Observed Picture Scene on macOS 14 — event review

The supplied light-process packet passes the requested bounded schema/identity checks: 49 events, all 21 exact labels, sequence 0–48, finite positive strictly increasing uptimes 126.598273125–128.592203416667 (span 1.993930292s), 286,397 bytes < 512KiB and count < 256. Callbacks: 21 `viewDidMoveToWindow`, 20 `setFrameOrigin`, 8 `updateNSView`. Each label retains one probe identity. PID 1926/window 28 matches the Layout capture; all event windows are visible/key/main, 920×668 at AppKit screen origin (500,222), scale 1. The capture's CG origin (500,190) is consistent with the 1080pt display and opposite vertical convention. This is the light process only; the separate dark PID is outside this packet.

`event-review.json` retains input hashes, checks, all 21 first/last records, native graphics-ancestor geometry and shared scroll/document stages. Rect arrays are `[x,y,width,height]` points. These are actual callback observations, **not proposed sizes or a terminal/settled layout**.

| Label group | First → last resolved size | SwiftUI global y first → last | Last recorded native probe height |
| --- | --- | --- | --- |
| Form root | 779×616 → same | 52 → 52 | 616 |
| Images Grid | 719×105 → 719×109 | 108 → 108 | 105 |
| Contain / Cover / Fill columns | each 120×109 → same | 108 → 108 | 109 |
| Those images | each 120×90 → same | 108 → 108 | 90 |
| Their captions | 38×13 / 29×13 / 14×13 → same | 204 → 204 | 13 |
| Mark column / image / caption | 64×83 / 64×64 / 52×13 → same | 108 / 108 / 178 → same | 83 / 64 / 13 |
| HDR Grid | 719×127 → same | 331 → 335 | 127 |
| Gain-map / PQ columns | each 192×127 → same | 331 → 335 | 127 |
| HDR images | each 192×108 → same | 331 → 335 | 108 |
| HDR captions | 74×13 / 39×13 → same | 445 → 449 | 13 |

All 49 events share these ten outer measurement-environment values: dynamic type `large`, size category `large`, default minimum list row height **24**, control size `regular`, light scheme, standard contrast, left-to-right, display scale 1, locale `en`, font `inherited nil`. That font value describes the measurement modifier's environment; it does not measure the styled caption's resolved glyph font. Result metadata reports source 9dd, macOS 14.8.9, success true and all three normal accessibility flags false.

The nearest reported `SwiftUI._NSGraphicsView` ancestor is 739×125 for the Images group and 739×147 for HDR; the last window-base rectangles are respectively (161,445,739,125) and (161,200,739,147). These are observed ancestor bounds, not an API naming a native card. The six-entry ancestor chains are all explicitly truncated. Form-root has no enclosing scroll view. Other labels share the same HostingScrollView/NSClipView/document identities: initial seq1–20 clip bounds (0,0,779,668) and document size 0×0; seq21–48 clip bounds (0,−52,779,668), document frame (0,0,779,1251), document window-base rect (141,−635,779,1251). Intermediate zeros are preserved, not treated as valid terminal document dimensions.

One explicit size mismatch occurs at seq48: Images Grid's resolved/global height is 109 while its native probe height remains 105 (`probe_bounds_size_equals_resolved_size=false`). The late HDR update records change global y by +4 while native window-base probe rectangles remain at their preceding positions (e.g. Grid (171,210,719,127)). Earlier attachment-to-origin callbacks also shift native positions by −52 before global-frame updates. These records cannot establish synchronized SwiftUI/AppKit/WindowServer geometry or explain the difference. `end_state=not_observed` remains binding: no last-record-as-settled, proposed-size, native-card or root-cause claim is made.

The Layout PNG hash is `dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780`, matching the hash supplied by root. No pixel/ICC comparison, 13 comparison, compilation, UI or CI was performed here; root's independent control-image/card result is not recomputed by this event-only review.
