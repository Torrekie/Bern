# Private actual-coordinator SDR experiment

This extends the frozen actual NSApplication.run coordinator fixture with one
private Standard named-PQ snapshot display candidate. It is not product code or
whole-UI acceptance. Original timer, spring, drawing, scene and native gates
remain. macOS 14 runs default only; macOS 13 runs default before baked-pair.

Assemble imports AppKit/SwiftUI, ProductHero.swift, FlightSDR.swift.inc and
Driver.swift.inc into CoordinatorSDR.assembled.swift. Keep the separate exact
Image/Style/Dependencies inputs. Use the new SDK26.2 compiler targeting arm64
macOS13; no static clock guard, fake timer or actor shim is added.

BERN_HERO_FLIGHT_SDR=default observes each actual snapshot with scalar/space
metadata and weak references, without creating CI objects or retaining the
original CGImage. baked-pair uses the fixed native recipe separately for each
actual snapshot and one shared context: CIImage(toneMapHDRtoSDR:true, no space
override), exact extent, RGBA8/sRGB/deferred:false. Actual tone mapping remains
unknown. Invalid/incomplete geometry/layout/conversion/mapping fails without a
successful original-image fallback. Reports retain both same-key ordinals,
actual Flight.from/to NSImage identities and synchronous setup timestamps.

The original acquisition freezes before original cleanup; post-teardown metadata
serialization clears helper-owned cache/context/space/weak references. This
does not establish global deallocation or zero observer overhead. The original
native/execution gate remains the prefix; appended checks verify new evidence.
Before/mid/settled PNGs still require visibility/color/timing review. Mid PNGs
at different progress are not cross-OS pixel-equality targets. Production intent
routing, High/HLG/other input geometry and general animation are unverified.
