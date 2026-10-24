# Completed content-stable background comparison, actual13 and14

The pair uses one exact SDK26.5/Swift6.3.3 cross-built ARM64/min13 executable from build40063367959: SHA2566a2045be05cd9fd77c99bc03c2bd2f59806b2f5de58e63417dd2df0352b5e261, source6cf5cf53178f3028f9788755c4708a6f0f32821862e3c53d79fa804e68bbb2b4, harnessa39d29faeab8ad7fd15f04a2db219d755c5ef48d. The14 runtime is run40063500033 with independently verified normal profile flags. Root ran this same executable locally on13; the analysis agent started no window.

Both actual runs completed all five backgrounds with fixed800×520 content bounds/contentLayoutRect and two equal canonical pixel buffers at each variant's same outer frame.13 took2.075642seconds with foreground35793;14 took2.303916seconds with foreground331. Both stayed inactive/nonkey, activation_calls0. Initial window-server onscreen information was unavailable at the first two installation snapshots; every before-shot snapshot was onscreen and passed all guards.

ICC-normalized fixed40×40point blank ROI results:

| Background |13 modal RGB|14 modal RGB|
|---|---|---|
| NSView semantic solid paint |236,236,236|236,236,236|
| SwiftUI Color |236,236,236|236,236,236|
| Canvas with operative-equivalent Bern role/draw |236,236,236|236,236,236|
| Native split transparent detail |240,236,237|234,234,234|
| Same split with explicit semantic role fill |236,236,236|236,236,236|

NSColor/window.backgroundColor semantic sRGB metadata is identical neutral236/255 on both OSes.13 NSView has tiny screenshot dither (mean≈235.934), while other explicit paints have mean exactly236. On14 the native split adds toolbar/titlebar exterior height:548→572points,y100→113, leaving content800×520.13 exterior stays548points.14 sidebar is210points,13 sidebar180;14 split titlebar52points,13 titlebar28. These native differences are recorded rather than repaired. Public native effect trees are retained; their enums alone do not uniquely identify a system tint/composition mechanism.

This is one inactive Aqua manually-created NSWindow/NSHostingView diagnostic, not the full Gallery SwiftUI App.13 uses physical2×ColorLCD and14 virtual1× with a different ICC/display/desktop context; compare these complete pipelines without assigning an OS-only cause. No RGB compensation, preference/brightness/wallpaper or product change was made. The revised contract correctly holds content geometry and per-variant stable outer frames; it does not claim the same exterior across every variant. Earlier first/diagnostic partial runs remain separate historical evidence.

Raw report/five PNGs and provenance are kept in each OS folder. Detailed cross-OS `validation.json` and `analyze.py` are in the14 content-stable folder, linked from13. Work runtime paths are symlinks to these archives. Package/executable hashes were retained before removing redundant transfer/rebuildable copies after the completed pair. Acceptance was not edited.
