# Exact f9 macOS13 followup baseline — prepared only

This copies the delivered `outputs/macOS13/Gallery.app` and `bin/gallery`, whose exact executable hashes identify build39991406873/source f9e08b1. No744 logger/candidate source or new build was substituted. The original app and CLI remain unchanged. Preparation did not launch either executable, download artifacts, or dispatch CI.

The isolated bundle identifier is `dev.bern.gallery.filmbaseline.925b37e2b4f944a3bf7be7394e02942d`. Local ad-hoc signing changes the full executable hash. All Mach-O section records/hashes and normalized signature-storage payload match the original; `provenance.json` retains the complete before/after records. The CLI is byte-identical. This is the same built code with a distinct local bundle/signature environment, not an assertion of byte-identical signed apps.

The parent may execute `RUN-BY-PARENT.sh` once. It uses exactly collector3f434cf (SHA79da4a84…), `inactive13/direct/last-resize`, the same startup-window readiness gate, normal-profile guards, real samePID onscreen alpha>=0.99 buffers, and AX/CLI followups as the candidate run. It never activates or restores focus, and changes no user preference, TCC setting, or `dev.bern.gallery` history. A new output directory is required; any partial result is preserved rather than reused.

There is no internal logger in f9. The wrapper explicitly unsets `BERN_SCROLL_TRACE_DIR`; it neither waits for nor invents a trace. It adds no external pause. The candidate had its two-second one-shot trace flush and after-trace capture before Last, so this baseline and candidate do not have identical elapsed timing. Comparison is limited to actual stable PNG/AX geometry and recorded timestamps, not inferred animation causes or a native binding setter.

After the initial capture, the existing collector performs Last → First → Last again → width1020 → restore920. These are external CLI bindings/resizes, not physical gestures. The observer executable and its module cache are removed on exit; a cleanup receipt is written. The signed isolated app/CLI are retained until the parent authorizes cleanup.

Validation here is static preparation/signature/hash/architecture/minOS and shell syntax only. The unmodified observer was previously typechecked by the parent with Swift5.9.2/SDK14.2 target13, warnings as errors. The startup gate has a15-second overall deadline and an8-second per-call cap; this does not promise full15-second tolerance for every individual cold call. No UI result exists yet.
