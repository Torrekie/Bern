# Private backing scalar summary — CI40095339192

Four existing processes passed the reviewed acquisition/schema gate offline. All four receipts and the current packaged binary match SHA256 `86130e8e33a7170156d893147ff34878cd58409c284a06001a49c20b1b9b9d3f`. The current archive, 28 package manifest members and source map also matched the root verification receipt. Build context is arm64/min13/SDK26.2; signature status is the hashed root receipt, without another signing command.

Normal flags were false, activation calls zero, cache dictionaries unchanged, and original front remained 1390 on13 / 309 on14. Window lifetimes off/on were 1.652236/1.663753 seconds on13 and 2.219975/1.777357 on14. Both captures in each process were non-key/inactive, own-PID/window identified, five equal buffers, no MTKView, no manager flight or timer. All eight PNG file hashes matched their reports. Float capture remained off in every process: zero provider-copy calls, retained-image peak, records and raw bytes. Backing-off had empty records and null root/overlay; backing-on had two flights with complete same-window chains and exact same-role 320×180 ROI association.

The following public getter values were sampled **after PNGs and final guards, before teardown**:

| View | contentsFormat on13 | contentsFormat on14 | wantsUpdateLayer | redraw policy raw |
| --- | --- | --- | --- | --- |
| flight-named | AutomaticAppKit | RGBA8 | false | 2 |
| flight-custom | AutomaticAppKit | RGBA8 | false | 2 |
| fixture root | AutomaticAppKit | RGBA8 | false | 2 |
| existing actual overlay | RGBA8 | RGBA8 | true | 1 |
| NSThemeFrame ancestor | RGBA8 | RGBA8 | true | 1 |

All observed views reported wantsLayer=false, canDrawSubviewsIntoLayer=false, placement raw=0, an existing layer and delegate_is_view=true; each delegate class matched its view class. Layers were `_NSViewBackingLayer` / scale2 on13 and `NSViewBackingLayer` / scale1 on14. Flights, root and overlay were flipped; NSThemeFrame was not. Flight chains were root→NSThemeFrame; root and overlay each had NSThemeFrame as their sole ancestor. Five unique views were represented by ten node invocations per on report. Repeated records agreed in these observations; the helper does not globally deduplicate getters. Full raw class strings, flags, geometry, delegates and process-local identity paths remain in `summary.json`.

The prior local-SDK13 report agrees on all compared nonclass scalar fields and ancestor geometry/order. Exact class strings differ in three fixture types' Swift module/private-symbol spellings (`HeroFloatCaptureProbe` versus `HeroFloatProbe`), including delegate_class; these differences are preserved explicitly rather than normalized away.

The four existing root control JSONs each record all12 raw and ICC-normalized ROI comparisons exact. This analysis checked their 12-row coverage/results and current-cohort report hashes, without recomputing pixels or claiming earlier baseline reports were revalidated here. Capture scale/headroom differed (13: 2x, current1/potential2;14: 1x, 1/1); snapshot descriptor ICC context is retained in the JSON.

These observations establish public scalar differences at the recorded time only. They do not prove actual pixel storage, pre-PNG state/persistence, the cause of the visible difference, crosshost visual equivalence, zero observer effect or actual coordinated-flight/lifecycle acceptance. No new color matrix, image processing, app execution, compilation, CI, repository edit or spawning occurred. `summary.json` records exact input paths and hashes; `SHA256SUMS` freezes these small private outputs.
