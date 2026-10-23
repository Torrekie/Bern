Archived original run: the following measurements came from the retained `main.swift` local13/SDK14.2 fixture. They are **not** runtime results from the later public `.github/scripts/window-background-probe.swift`. This was an inactive, manually-created window rather than a full Gallery App scene. `archive.json` preserves original source/report/PNG/SHA256SUMS hashes; the old work path is now a symlink.

# Five native background paths on actual macOS13

The one own nonkey Aqua window remained at the same800x520point content size/position, with the same embedded capture ICC. Each group supplied two consecutive identical canonical WindowServer buffers. It closed after2.446seconds; no activation/global key, preference, wallpaper or brightness changes occurred. Foreground was the instantaneous startup PID1390 before, during captures and after; earlier QQ PIDs were not reused.

Fixed40x40point ROI at content top-left(680,430),80x80pixels at2x. After ICC->sRGB, modal RGB values were:

| Path | RGB |
|---|---|
| NSView NSColor.windowBackgroundColor solid draw |236,236,236|
| SwiftUI Color(nsColor:windowBackgroundColor) |236,236,236|
| Canvas via same BernColor role + ordinary opaque BernDraw rect branch |236,236,236|
| Native NavigationSplitView transparent detail |240,236,237|
| Same detail with explicit same-role background |236,236,236|

NSColor and window.backgroundColor resolve under each view's effective Aqua appearance to236/255 neutral RGB, alpha1. All groups have a framework-provided NSThemeFrame NSVisualEffectView with windowBackground material12, withinWindow blending1, active state1, alpha1/isOpaque false. Native split groups additionally have sidebar/divider material7, behindWindow blending0, followsWindowActiveState0; those do not cover the detail ROI. Root views report allowsVibrancy false. Explicit paints cover the underlying window material; transparent detail leaves native background visible. The probe has no Bern tint or page overlay.

This local result distinguishes explicit semantic NSColor drawing from transparent native container/background composition. It does not assign the precise system tint mechanism, equate240/236/237 to the earlier Gallery238/237/239, or establish macOS14 parity. Standalone manual NSWindow/NSHostingView is not the whole SwiftUI App scene, and only inactive light appearance was tested. There was no user-setting change and no RGB compensation.

Source trace: only Gallery Frame uses surface.canvas, inside an explicit dark region; Patterns and Film leave whole-page background unfilled. Existing analysis calls the blank point800,640 canvas but does not instrument a role. Role mapping is NSColor.windowBackgroundColor without a13/14 branch. Theme sets scoped accent and application appearance, not global tint; no project NSVisualEffectView/backgroundColor assignment exists on this SwiftUI path. Conditional search/modal/hero overlays do not establish a background tint in these ordinary states. `source-chain.json` records source hashes and locations.

`main.swift` is a standalone Swift5 script suitable for target macOS13 and future exact-binary13/14 comparison. It uses minimal operative-equivalent role/rect drawing instead of importing the entire Bern runtime. Local Swift5.9.2/SDK14.2 typecheck, compile and actual WindowServer run passed. Executable and own module cache were removed after hashing. Original five PNGs/report/effect-view trees remain unedited. `analyze.py` uses Pillow/LittleCMS perceptual intent0 to normalize ICC and measures the fixed ROI; native raw-profile values are retained too.
