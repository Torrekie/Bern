# Upstream Film initial-position timing —40062194628

Locked upstream ffb application from build39959549054, harness2aa4e63, macOS14.8.9 arm64. Normal motion/transparency/contrast flags are all false; existing AX and Screen Recording access true. Three fresh PIDs/sessions, outer920×668, nine stable PNGs. App and CLI hashes match the preceding failed run; only the observer IPC path changed.

| Scenario | Largest card | Glen center x / width, window points | First complete AXImage set |
| --- | --- | --- | --- |
| Immediate close→Film | Glen |566.0 /268.79975 |+0.566s |
| Wait closed stable→Film | Glen |601.0 /267.53479 |+0.225s |
| Direct Film | Glen |601.0 /267.53479 |+0.704s |

Wait/direct PNGs are byte-identical. Inspector exit animation therefore is not a necessary cause of Glen identity. Immediate and the other scenarios have a35pt settled offset difference, but this is not a causal attribution: immediate initially starts900×652 then actually resizes, whereas wait/direct initially restore920×668 and their resize is a no-op. Each scenario ran once in fixed order. Detail center is565.5pt. In wait/direct, Madras center331 is234.5pt left of it, matching the expected centering margin(709−240)/2; this correlation does not prove the underlying target/layout order.

All returned detail split widths are709 and Film AXScrollArea widths240. The latter is an accessibility rect and must not be equated with a measured NSClipView bounds. Early walks are truncated, including inspector snapshots; the capture does not show a484→709 transition. Each AX walk has real start/end timestamps and can exceed its soft budget while a synchronous API call finishes. No internal position/target/nearest values were read, so source initial3→runtime4 is still not directly established.

The next useful sample is a single direct-entry standalone14 SwiftUI fixture retaining original snap/position layout and build SDK, tracing target writes, viewport/item/margin changes and release timing. Further Inspector-only repetitions cannot explain the direct case. No product correction is justified from these external frames alone.

Original downloaded files are unchanged; analysis.json adds compact geometry/provenance. The reported artifact ZIP digest is GitHub metadata, not a reconstructed extracted-file ZIP hash.

The concrete next trace design is documented in `../../Implementation/macOS13-Film-Initial-Position.md`; no new probe or product implementation was added.
