# Native search input delivery: source audit

Explicit `strategy=unicodeEvent, delivery=background` has no AXValue/pasteboard fallback in the reviewed backend source. It posts Unicode CG keydown/up events to the target PID; only `.auto` can resolve through app/text heuristics. Background/default restore_focus=false requests no activation. Event creation failure throws.

Use the native MCP x/y coordinate click for the intended CG mouse path. A regular element_index click can invoke AXPress. Native MCP coordinates are global screen points; the Sky adapter has a separate screenshot-coordinate mapper. Coordinate click posts mouse down/up to PID and makes no explicit real-pointer warp. Actual cursor before/after remains a runtime fact; no move-only/restore-real-cursor tool is exposed. Desktop release unlocks and hides the virtual overlay, without restoring the real pointer or original foreground.

Overlay movement is an independent NSPanel animation gated by virtual cursor mode; off prevents rendering while bounded marks can still be recorded. Capture metadata should preserve actual mode/overlay state. Exclusive session baseline mismatch rejects mutation before posting.

MCP successful mutation output is a new AX/screenshot/session snapshot, not Core strategy/delivery result fields; on snapshot failure it can be only a summary. Keep the explicit request, raw result, focused search/text, registry state and first Library invalid_search as separate evidence. No source-level posting claim alone proves product state propagation.

The skill and installed binary embedded source path located the exact native checkout; hashes/line pointers are in audit.json. This is read-only source evidence, not a binary-to-source rebuild attestation or new runtime result. No UI, MCP state/mutation, settings, compilation, network or git action ran.
