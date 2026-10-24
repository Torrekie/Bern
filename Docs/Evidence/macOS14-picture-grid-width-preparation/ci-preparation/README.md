# Private full-Scene width trace CI preparation

Publish only these four staged files after root review:

- `.github/scripts/picture-grid-width/build.py`
- `.github/scripts/picture-grid-width/patch.py`
- `.github/scripts/picture-grid-width/GridWidthTrace.swift`
- `.github/workflows/macos14-picture-grid-width.yml`

The two width files reuse the frozen preparation bytes exactly. No old observer
file is copied into the new package or modified. `BASE` reads the existing
`picture-scene-observer/{patch.py,Observer.swift}`; package hashes lock all three
old package files, source-export helper, width patch/helper, and record new build.py.

The wrapper keeps `prepare SOURCE EVIDENCE`, `patch OUTPUT_ROOT`, and
`collect SOURCE EVIDENCE`. It retains the original environment-gated Rust hook
before the sole `target.plan`, then continues that original build plan. Prepare
requires exact Git9dd, clean tracked inputs, all 55 original inputs, matching
workflow paths (the workflow supplies absolute paths), and removes only the
generated macos_modern subtree.
The Rust/cache paths are retained. Original bounded log, one marker, return-code,
only-CLI tracked mutation, min13/release, and nonempty product checks remain.

Patch first runs the old 21 modifiers and appends the original Observer.swift:
106494 B / `f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2`.
Then the new patch checks generated Style's original `e1cad857…1c6f` and changes
it to 209558 B / `09d8f99a26a73498e7ef4d7d597eca646be751f32b4fe99f63482b944a81987f`.
Collect requires both exact results, unchanged 55-input cohort except the
intentional CLI hook, and matching package hashes. Failure stays nonzero; there
is no retry, fallback, extra build, alternative Scene, or separate fixture.
The new `width-instrumentation.json` is separate from original instrumentation.

Workflow: manual dispatch without inputs; macOS15/Xcode26.3/Rust1.99, jobs2,
restore-only old cache, min13, one build. Retains signed App+CLI as
`picture-grid-width-build` / `showcase-grid-width.tar.gz` (3 days), then macOS14
downloads that exact artifact without rebuilding. Capture uses the unmodified
full reference collector, original normal/en/920×668 route and Layout .8s wait.
It precreates external `evidence/observer`; the existing observer packet and
`picture-grid-width-PID.json` use that directory with separate schemas. Capture
artifact `picture-grid-width-on14` retains all 13 PNGs and both packets (3 days).
Always-upload/partial metadata does not turn failed build/capture into success.

CI green alone does not establish packet coverage or native layout acceptance.
The collector's current `3dcaaf99…0ac6` hash is recorded through the harness
receipt; the original workflow does not assert an independent expected hash
before capture. CLI minos is printed by vtool; only GUI minos has the inherited
hard check. Root must verify the retained collector and CLI receipt independently.
Root must first require selected14 PNGs retain Picture125/HDR147 and original
21-point coverage before interpreting width rows. The frozen width plan and
review define target configs120/192, optional retained140 lower-section rows,
cap/partial limitations and the same-binary13/14 follow-up. Equal width histories
do not identify a cause or establish settlement. No new pixel algorithm is added.

`build.patch` / `workflow.patch` are exact baseline diffs. `validation.json`
records AST, YAML, nine shell syntax checks and 55 archived inputs matched to
Git9dd. The local tiny fixture calls real prepare with explicit substitutions
at Git HEAD/status/diff and input_rows boundaries; it is not a real disposable
checkout validation. It checks path/env rejection, generated-only cleanup and
Rust sentinel preservation, then actually runs old patch+helper followed by
width patch on the retained generated text and Git9dd Style. Temporary sources,
patch outputs and read-only baseline symlinks were removed; no old files changed.
`check-preparation.py` reproduces this private check without cargo or Swift.

No repo/index, CI, UI, compiler, SDK/cache, product, or old archive was modified.
Root owns publication, dispatch and all subsequent native acceptance.
