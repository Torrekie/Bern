# macOS13 toolbar editor-role candidate

Independent, actual SwiftUI App/Window Scene copied from the earlier `work/toolbar-scene-fixture/ToolbarProbe.swift` (origin SHA recorded in validation.json). Only the role varies: implicit automatic, `.toolbarRole(.editor)` on the NavigationSplitView, or on its detail. The original Showcase-like sidebar List + ranged width + sidebar search and automatic Button toolbar remain. Fixed Buttons title; no title/page transition was added.

Swift5.9.2, SDK14.2, arm64 macOS13 deployment; measured macOS13.7.8. SDK14.2 declares editor available from macOS13; browser and navigationStack are unavailable on macOS.

All three groups, each with three identical native geometry samples:

| Metric | All groups (points) |
| --- | --- |
| Actual sidebar | 140 |
| Toggle item x / width / top | 153.5 / 39.5 / 12 |
| Toggle graphics x / width / center | 163.5 / 19.5 / 173.25 |
| Visible Buttons title x / width / top | 199 / 60.5 / 16 |
| Native toolbarStyle | 0 |

Editor produced no movement and retained both NSWindow title and visible title field. This negative result is limited to this fixed-title, hidden Scene composition; it is not a real-window visual or page-transition equivalence result.

All nine samples were invisible and nonkey after orderOut + prohibited policy, with the original foreground PID unchanged. No own activation, NSToolbar/delegate/item mutation, main Bern app, or user preference-domain inspection/edit occurred. Each group had its own fresh bundle/domain, ran for 1.40–2.55 seconds (12-second deadline), and its exact owned preference/saved-state paths were removed after exit. Cleanup removed all owned bundles, executable and module cache. Source, runner, build/launch logs, raw mode JSON and report remain. The runner needs recompilation before reuse; do not run without the same bounded permission scope.

The new role test did not exercise Gallery, or Buttons→Text/Controls title changes. No broader exclusion of toolbarRole is claimed.
