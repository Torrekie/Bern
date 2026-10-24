# Clean e48 Gallery on macOS 13: three fresh Film scenarios

Parent-owned local session 67853 exited 0 with `success=true`. This was the actual logger-free e48 source, built by [CI 40070407306](https://github.com/Torrekie/Bern/actions/runs/40070407306), not the earlier diagnostic 744/d146 executable. Build source e48fff46b3a92a28465ad74295bd273a9d69af7d is distinct from harness 25e18cbc7cd760c1c399042f1d7364c3d755a9dc. SDK 26.2 / Swift 6.2.4 / ARM64 / min13 / genuine SwiftUI-modern; existing 9dd Runtime/HDR fixes remain.

Exact original GUI SHA256: `d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c`.

Exact CLI SHA256: `31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5`.

The exact extracted app/CLI remain in the owned build directory for parent delivery. Analysis did not replace the existing f9 deliverable. The run copy used unique bundleID `dev.bern.gallery.filmclean.9697c3c5499d42df80b9bdfd0f43f986` with a valid local ad-hoc signature; full signed GUI hash became 62485469…, while all Mach-O section hashes and normalized signature-storage payload stayed identical. Complete before/after records are retained.

## Observed result

All three clean cases show Glen. Each final AX traversal is complete with six images; each Film PNG passed four equal raw-buffer comparisons. Normal accessibility flags were all false. The collector 3f434cf / SHA 79da4a84… was unchanged, with inactive13 / scenario=all / followup=none / trace unset. There were no activation requests, and no logger was expected or invented.

| Scenario | Clean 13 Glen center / width | Upstream 14 center / width | f9-port14 center / width |
|---|---|---|---|
| Immediate Inspector close → Film | 601.000  / 267.534781 | 566.000  / 268.799753 | 565.000  / 268.799753 |
| Wait until closed/static → Film | 601.000  / 267.534781 | 601.000  / 267.534787 | 601.000  / 267.534787 |
| Direct Film | 601.000  / 267.534781 | 601.000  / 267.534787 | 601.000  / 267.534787 |

For wait/direct, **all six measured AX image frames** differ from both 14 references by less than 0.00001 points. Immediate differs by 35/36 points in dominant center and is not a visual parity pass. The cited upstream run 40062194628 raw result records a 566-point immediate center.

In all three datasets, immediate starts at 900×652 then actually resizes to 920×668; wait/direct restore 920×668 before the resize call, which leaves the size unchanged. Inspector exit, window restoration, and first-process startup remain coupled; these samples do not assign a cause to the immediate difference. The clean run also has the startup-window readiness gate absent from older 14 collectors.

Clean 13 is an inactive 2x local capture with isolated identity; both references are active 14/1x. Equal AX geometry is not proof of equal active colors/materials. There was one sequence per condition. No physical gesture, native Binding setter trace or followup Last/resize capture was added. Earlier first Last/wide differences remain open.

## Retained records

- `runtime/`: all 219 original local run files, unchanged, including PNGs, CLI outputs, full report, logs, copied collector and cleanup receipt. Embedded preparation files intentionally describe their earlier preparation state.
- `original-runtime-SHA256SUMS`: complete pre-analysis raw inventory.
- `build/`: original environment, build metadata/log, artifact metadata, tar hash, exact-source/signature provenance and explicitly attributed parent confirmation of final CI success. ZIP digest was checked against GitHub before safe extraction. No final GitHub response was fabricated.
- `preparation/`: source scripts, source/hash/isolation records and prior startup-gate validation. The original startup contract is 15 seconds overall with 8 seconds per CLI call, not 15 seconds for every individual call.
- `comparison-inputs/f9-port14-40062837456/`: all 102 existing f9/14 reference files, unmodified, retained here with an original inventory. Upstream 14 remains in the separately frozen sibling `macOS14-film-timing` archive.
- `analyze.py` and `analysis.json`: offline, reproducible frame/window-history comparison using raw inputs and PNG metadata. They do not modify raw files or launch any application.
- `app-member-fingerprints.json` and `cleanup.json`: exact/isolated app member hashes and ownership-scoped cleanup. Only the isolated app/observer/cache may be removed; exact delivery app/CLI are retained. Logical bytes are not APFS physical-savings claims.
