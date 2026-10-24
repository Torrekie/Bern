# Picture observer package — static review

Reviewed 2026-10-25; no blocking source defect identified within this package. No compilation, UI or CI was performed by this reviewer.

| Repository file under `.github/scripts/picture-scene-observer/` | SHA-256 |
| --- | --- |
| `build.py` | `70f388f8a7346d2edb68a8e428c40350fb67025ab0bd86e35ab375b055d7d97d` |
| `patch.py` | `9de84f9da6b52602e1bdc9613c3e32b884b68335e8da789c3a161ae8c1f9f4cd` |
| `Observer.swift` | `14532e7960a7138ae3be48b26fe08ecb0f0d6b347e6cd7faa76be08eb01709da` |

- Python AST parsing passed for both drivers. Preparation pins exact 9dd source and original CLI, checks recorded inputs, removes only the diagnostic target output and adds one hook. `Command` already exists in that Rust CLI's imports. The hook runs after original generated-file writes, returns failure on a failed patch process, and otherwise continues into unchanged `target.plan` and `run_steps`.
- The patcher retains full-source/component SHA and unique complete-expression checks, adds only the 21 requested modifiers, and proves byte-for-byte recovery by removing its recorded insertions. The build driver appends the helper at file scope; no Scene/container/children/FormRows/font/padding replacement occurs. Collection requires the command/marker/instrumentation/generated-source/input/package/build/product gates; caught failures explicitly remain false and return nonzero.
- The store, NSView subclass, representable, modifier and View extension are consistently MainActor-isolated. No explicit background closure or non-Sendable value crosses an actor boundary here. The NSViewRepresentable creation/update methods operate within that isolation. This static assessment does not replace the actual SDK14/Swift5.9 helper typecheck or the later new-SDK full-app compilation.

Measurement limits, not reasons to add new probe behavior: observation is synchronous JSON serialization/file I/O on the main actor and can affect the app. Recorded uptime is the append time after assembling a changed callback observation, not a draw/capture timestamp. `end_state` is deliberately `not_observed`; quota/write failure stops collection without a new terminal record. Build success therefore proves package production, not complete runtime observations or absence of observer effects. Runtime must retain the independently specified complete-label/geometry and 125/147 card gates, and stop interpretation if instrumenting changes those dimensions.
