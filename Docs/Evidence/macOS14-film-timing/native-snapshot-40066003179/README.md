# Public native scroll geometry on actual macOS14

Run40066003179/build40065764593 uses diagnostic744e316, based on original f9 product plus the prior e4c event logger. The only new instrumentation reads the app-owned public AppKit tree after the original two-second event interval. It adds no View or geometry/scroll mutation. Compiler/source/runtime provenance remain attached.

The observed Film HostingScrollView and real NSClipView are709×207pt, document1638×207pt, clip bounds x564. Left/right contentInsets are234.5pt and automatic adjustment is false. The full app-native tree has111 views and is not truncated. AXScrollArea240pt therefore is not the clip viewport width. The enclosing tracked SwiftUI viewport is709pt; the late target3 frame atx0 explains nearest4 in that coordinate space. This settled native snapshot does not prove when the inset/scroll retarget happened.

The102event trace has dropped0 and retains the same first-entry callback trajectory. Film PNG before/after the trace is byte-identical to the earlier e4c diagnostic14 PNG; representative original bytes are reused by relative symlink after hashing. The new settled AX traversal was truncated, so it is not claimed as a new full AXImage measurement. First/Last, resizing, arbitrary anchor semantics and initial-target correction remain separate gates.
