# Film Last observer: build-only package

This derives the prior seven-file build package with one narrow Swift source
candidate described in `README.md`: the observation-owner expression is moved
to an explicitly typed private main-actor helper. The core and Runtime remain
byte-exact. `source-SHA256SUMS` binds the derived four-file observer source
packet (SHA-256
`3e2ba0b9fe468bfc920c357942c7d0fdefd96857b9fb0725f9e99b0fadcfa250`),
not this build driver. No prior failed build is reclassified as successful.

Use a disposable checkout at exact source
`e48fff46b3a92a28465ad74295bd273a9d69af7d`. Publish this directory as
`.github/scripts/film-last-observer`; the sibling frozen
`.github/scripts/frame-source-export.py` must have SHA-256
`5b4a254565f437f819a308f8cf3c5b1990b937f76b9918ff5b935e91e1a2b017`.

```
python3 harness/.github/scripts/film-last-observer/build.py prepare source evidence
(cd source && cargo +1.99.0 run --locked --release -p bern-cli -- build --manifest examples/gallery/Bern.toml --target macos_modern --release) > evidence/build.full.log 2>&1
# Preserve the cargo exit status in evidence/build.exit-code.txt and propagate it.
python3 harness/.github/scripts/film-last-observer/build.py collect source evidence
```

The workflow owns exit-status handling and always runs collection after a
successful preparation. Before preparation, only `environment.txt` and
`harness-inputs.sha256` may exist in evidence. No driver environment or
generate-only hook is used. `BERN_DIAGNOSTIC_GENERATE_ONLY` must be absent.

Preparation uses the frozen source-export module only for exact-head, Git
input and metadata utilities. Its generate-only entry points are never called.
It binds all 631 original inputs, records cached generated-file metadata, then
removes only `target/bern/macos_modern`. The frozen observer patcher emits two
diffs; only the Style and Runtime templates are changed. CLI and generator
remain original. Collection checks those two changed templates and the other
629 input files again.

Actual generated Style must equal the patched template. Actual generated
Runtime must equal the patched template after the original fixed extension
table expansion. The derived original/patched Runtime sizes are 119529/132272
bytes (SHA-256 `626c4b7785cf46f9e6d86389d5c64b8221d5f5ead8f7518a67e407b38883ba95`
and `e38647f3b918e4d0c4c503eb8876889578a35b57efdb8feeaadafaac5a51f663`).
These are independently derived bytes, not a claim of historical actual
Runtime retention. Removing the core and reversing the inspect hook must
restore the derived original Runtime exactly. The bounded no-SVG branch is
enforced by exact actual Runtime equality; the supplementary source regex is
not a general SVG audit. Actual BernGenerated must remain 81110 bytes with
SHA-256 `f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653`.

Collection retains actual `BernRuntime.generated.swift`,
`BernGenerated.generated.swift`, `product-build.json`, and actual-file hashes
before later semantic gates. It requires Swift 6, Rust 1.99.0, selected and
embedded SDK 26.2, arm64, minimum macOS 13.0, release metadata and strict App
signature verification. This is a full normal product build; no product is
launched. The newly rebuilt CLI is neither packaged nor claimed to be the
previously delivered original CLI.

Success writes `observer-build.json` and
`gallery-film-last-observer.tar.gz` plus its SHA-256 file. The tar contains only
`Gallery.app` and the same provenance JSON. Consumers must require successful
collection, external JSON `success=true`, matching packaged JSON bytes, tar
digest and App member hashes. The workflow performs an additional read-only
binary verification after collection. CI/build success proves no native
behavior, pixel preservation, diagnostic coverage or adoption gate.

On failure, the external JSON remains false with the error; logs and available
actual generated sources remain evidence. A packaging attempt uses a fresh
partial path and removes only its own partial/final tar and checksum on error.
The full build log is hashed but only a bounded 128 KiB log is uploaded. No
retry, fallback, native capture or cleanup of another checkout is performed.

CI 40175193229 remains a failed full build (Swift 6.2.4 SILGen ErrorExpr,
signal 6). This source candidate has not been compiled. The build driver
changes only the derived source-manifest and Style pins; its gates and Runtime
pins remain unchanged.

This private preparation was checked by AST parsing and independent in-memory
text derivation only. Neither entry point, patcher, Git, compiler nor App was
executed locally.
