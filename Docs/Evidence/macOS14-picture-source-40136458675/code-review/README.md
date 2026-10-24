# Picture Scene source exporter — final static review

Reviewed the frozen repository files on 2026-10-25. No remaining blocking defect found within the requested source-export boundary.

| File | SHA-256 |
| --- | --- |
| `.github/scripts/picture-source-export.py` | `e4f7bc61dce0241c53858d8c0f28250f13fa6bcac3c4c13759985ebb3b80df2e` |
| `.github/workflows/macos14-picture-source.yml` | `cad33c10a896d3d405717550c5bec2a31230bf77eeaf0f40c4f7cf2756a254ed` |

- The disposable source checkout is locked to `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`; the original CLI SHA and unique insertion needle are checked. Generator/template/Showcase inputs are enumerated from that Git tree and checked before and after generation.
- In that exact CLI, the hook follows successful writes of generated files and precedes `target.plan` and `run_steps`. The inserted return therefore skips the target plan and Swift product/glue build. Cargo may compile the Rust host and the CLI still performs IR compilation/generation; this is within the stated scope.
- Collection requires command exit zero, exactly one marker, the sole intended tracked CLI mutation, unchanged recorded inputs, actual `BernApplication`/unique `layout_page` source, and `swiftui-modern`/macOS 13/release metadata. Original product executable and CLI output paths must remain absent.
- The earlier failure-masking defect is fixed: success becomes true only after the exported source is written; any caught collection failure explicitly resets success to false and returns nonzero. The workflow's always-collection/upload paths preserve failure evidence without making the failed generation step pass.
- Cache use is restore-only. The artifact contains one bounded generated Swift file, bounded log and metadata/provenance; the complete log and disposable target tree are not uploaded.

Limits: this was source inspection only, not CI execution or Rust/Swift compilation. The recorded `layout_page` range uses generated component-comment boundaries rather than an AST body; the complete generated file is preserved for later exact inspection. Runner/toolchain/cache availability and actual generation remain runtime gates.
