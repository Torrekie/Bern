# Appearance source review

Input: `b72cb5dee3cf73b376a5e3d28b6e97f777eaf3d8`; delivered Gallery source: `e48fff46b3a92a28465ad74295bd273a9d69af7d`. The inspected product templates, Swift generator and Gallery sources have no diff between these revisions. This review performed no GUI, build, network or Git mutation, and changed only this review directory.

No root cause was established. The parent-owned clean launch successfully changed System to Light (activate 0.0864 s; subsequent ui.inspect 0.5170 s), with parent-observed Light rendering and AX 68. See `../clean-appearance-attempt/appearance-commands.json`, `clean-appearance-result.json`, and `clean-light-ui.json`. This child read those structured records; screenshot interpretation and AX count are parent observations. This successful clean path does not explain the prior AXClose / appearance timeout sequence. The read-only sample attempt timed out after 8 s and produced no stack, so it supplies neither a product failure nor a diagnosis.

## Source findings

- `crates/bern-backend-swiftui/src/swift/values.rs:312–350` emits @Published engine fields; `src/swift/windows.rs:89,135–149` observes the engine and passes appearance to ThemeChoice; `src/swift/mod.rs:132–145` emits EnvironmentObject / ObservedObject. No source-proven missing observation link was found.
- `templates/BernStyle.swift:990–1006` synchronously sets NSApplication.appearance from the SwiftUI change callback. This setter logic is inherited from origin/master. It is a possible stack-inspection site for synchronous AppKit / SwiftUI reentrancy, not a proven fault.
- `templates/BernCompatibility.swift:42–51,89–137` selects LegacyOnChange only below 14. Its stable ActionBox refreshes the current closure during body, tracks previous values, and owns no lock. No inevitable stale appearance capture was found.
- The branch uses Combine for macOS 13 and 14 (`BernCompatibility.swift:5–10`, `src/swift/mod.rs:131–145`, `values.rs:312–350`), unlike upstream Observation. Broader invalidation is a design difference, not evidence of lost updates or a 13-only defect.
- `templates/BernRuntime.swift:1540–1544` completes ui.activate after the action closure; engine dispatch at 1166–1180 remains asynchronous (`crates/bern-ffi/src/lib.rs:761–779`). ACK therefore does not establish engine application or native redraw.
- Runtime callbacks at 965–981 enqueue main.async, without main.sync. Rust `crates/bern-command/src/lib.rs:772–805` releases state / listener locks before calling listeners; `crates/bern-ffi/src/lib.rs:250–266` releases the pending lock before calling the session callback. No obvious lock cycle was found on this inspected path; this is not exhaustive proof of freedom from deadlock.
- `templates/BernAppKit.swift:911–936` has display-link invalidation waiting, but nothing inspected links it to the appearance action. Do not prioritize it without a matching runtime stack.

## Preserved uncertainty

In `../narrow-attempt`, native Close returned AX error -25204 while the model became Details false and the panel disappeared. Later Light activation returned success and the engine became Light, but AX became empty with the old dark backing; the following Dark request timed out. These facts neither identify AXClose as cause nor prove an appearance setter deadlock, a 13-only regression, or a fix by restart.

If this episode recurs during otherwise required acceptance, capture the identity-verified own PID thread stack at the first AX0 / UI command timeout. Select the next investigation from that stack. No source patch, speculative workaround, or broad retry matrix is justified by this review alone. No whole-stage acceptance claim is made.
