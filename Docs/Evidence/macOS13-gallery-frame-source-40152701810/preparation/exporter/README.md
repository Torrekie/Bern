# Exact e48 Gallery Frame source export candidate

Private preparation for one source-only CI run. This directory does not contain a generated Swift fixture or runtime result. Neither `prepare` nor `collect`, Cargo, a compiler, a product GUI/CLI, Git mutation, nor CI was executed locally. Only Python AST and fixed-revision Git-object text checks ran; see `validation.json`.

## Fixed scope and interface

- Source: `e48fff46b3a92a28465ad74295bd273a9d69af7d`, tree `9b028204744063ae5c23a336a4eb32dbb41b6d86`.
- Application: `examples/gallery/Bern.toml`, root `app`, target `macos_modern` (`swiftui-modern`, macOS 13 minimum, release). No source/target selection option.
- Script: `.github/scripts/frame-source-export.py prepare SOURCE EVIDENCE`, then externally run the real CLI below, then `... collect SOURCE EVIDENCE`. `EVIDENCE` may contain only a bounded regular `environment.txt` before preparation. Fresh collection refuses existing output evidence rather than overwriting a prior attempt.

```sh
BERN_DIAGNOSTIC_GENERATE_ONLY=1 cargo +1.99.0 run --locked --release -p bern-cli -- build --manifest examples/gallery/Bern.toml --target macos_modern --release
```

The external workflow captures the complete command log as `generate.full.log` and its numeric status as `generate.exit-code.txt`. The helper invokes only Git read commands. Cargo builds the Bern generator CLI; the inserted return prevents the Gallery product build plan from being constructed or run. This distinction is not a claim that Cargo itself performs no compilation.

## Source guard and sole intended mutation

Preparation requires the exact HEAD and clean tracked source. It reads the e48 objects and fingerprints all 631 tracked files under `crates/**` and `examples/gallery/**`, plus root `Cargo.toml` and `Cargo.lock` (7,430,108 original bytes; content is not copied). This includes local generator/compiler/backend source, backend templates, Gallery declarations/protocol/engine, and Gallery resources. Cargo.lock pins external dependency versions; this is not an export or proof of the entire external dependency/toolchain closure. Other workspace examples are not individually fingerprinted; the fixed HEAD and sole tracked CLI diff still constrain the disposable checkout.

The original CLI SHA is `63af68fa7f763b118ca34ed432b0f1b9fdfa2b3190582ebde747135303d0fa64`. Its unique `target.plan` line is original line 917, after generated files have been written. The only inserted block checks `BERN_DIAGNOSTIC_GENERATE_ONLY=1`, emits exactly:

```text
BERN_FRAME_GENERATE_ONLY: Gallery generated files written; skipped target.plan and product build
```

and returns `ExitCode::SUCCESS` immediately before the unchanged `target.plan` statement. The resulting CLI SHA is `0510fef557d01e2849f4445ab450166b474dadc0e552f0b7eece27da02ef3636`. Collection checks exact expected patched bytes, HEAD/tree, the complete 631-file list and post-run hashes, exactly one marker, exit 0, and absent Gallery executable directory, product dSYM and `bin` outputs. `Gallery.app` may legitimately contain generated Info.plist/resources; it is not itself treated as a compiled product.

Preparation records cached source metadata, then removes only the exact nonsymlink `SOURCE/target/bern/macos_modern` subtree. Rust compiler/dependency caches remain. This reset is part of the prepared CI script; it was not run locally.

## Export and failure evidence

After generation identity gates, collection bounds `Sources/BernGenerated.swift` to 1 MiB and requires its real Bern-generated header. It copies those bytes unchanged immediately, then copies the bounded regular `build.json` unchanged, before semantic Frame/Scene/build-metadata checks. A later token or metadata failure preserves these originals, records `after.json.success=false`, and exits nonzero.

The exact Frame marker is ``/// Generated from the `frame` component.``. The derived `Frame.component.swift` preserves original bytes from that line through the byte before the next component comment, including original line endings. `after.json` records the original one-based inclusive line range, zero-based half-open byte range, size and SHA. No `frame_page` name, guessed Swift replacement, old Showcase file size/count, or layout-page slice is used.

The guards are backed by exact e48 source: `AppView_` naming is in `crates/bern-target-api/src/names.rs`; component/Window declarations are in Swift generator `windows.rs`; component calls in `mod.rs`; Caption `BernSplitButton` and `SwiftUI.Slider(value:` in `controls.rs`; `SwiftUI.Menu` in `toolbar.rs`; root/route/control IDs in Gallery UI. Calls are checked by name plus opening parenthesis, without assuming an empty initializer signature. Static checks establish guard intent, not that actual generated output already passed. The real source-only run remains necessary.

`generate.log` keeps at most 128 KiB, including its omission notice; the full log is streamed for its SHA/marker count and excluded from the artifact by the paired workflow. `before.json` / `after.json` are capped at 256 KiB. `SHA256SUMS` binds retained direct evidence files (excluding full log and the manifest itself). Collection success requires all guards and final slice writes. A success result establishes source generation only, not a product build, visual equivalence, native measurement, or Frame acceptance.
