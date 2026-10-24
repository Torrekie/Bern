# Clean e48 native macOS 14 runtime: success, with immediate-position variance

[Run 40071892408](https://github.com/Torrekie/Bern/actions/runs/40071892408) completed successfully. It ran the existing clean e48 Gallery from build 40070407306 without rebuilding the app. Source is e48fff46b3a92a28465ad74295bd273a9d69af7d; workflow/build harness is 25e18cbc7cd760c1c399042f1d7364c3d755a9dc. The app used SDK 26.2/Swift 6.2.4/min13/ARM64; the external observer used Swift 5.10/SDK 14.5 on macOS 14.8.9.

The observed exact original GUI SHA256 is `d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c`; CLI is `31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5`. These match the existing build and delivered original. The local 13 run used an isolated re-signed copy with identical code sections/normalized signature payload, not byte-identical signed executable bytes. No local app was run during this analysis.

## Measured result

All three fresh processes show Glen. Final AX traversals are complete, each with six images. All Film captures pass four identical raw-buffer comparisons at 920×668 points; normal accessibility flags are all false. Execution was active 14/1x with scenario=all, followup=none and trace=false.

| Scenario | New clean 14 Glen center / width | Upstream 14 center / width | Old f9/14 center / width | Clean 13 center / width |
|---|---|---|---|---|
| Immediate close → Film | 677.000 /256.153006 | 566.000 /268.799753 | 565.000 /268.799753 | 601.000 /267.534781 |
| Wait/static close → Film | 601.000 /267.534787 | 601.000 /267.534787 | 601.000 /267.534787 | 601.000 /267.534781 |
| Direct Film | 601.000 /267.534787 | 601.000 /267.534787 | 601.000 /267.534787 | 601.000 /267.534781 |

Wait/direct reproduce the complete frames of all six images in both old 14 references exactly. Their maximum frame-component difference from inactive 13 is 0.00000977 points. Their PNG files still differ in bytes; no whole-image pixel/color equivalence is claimed.

Immediate is **not** a parity pass. Its Glen center differs by +111 points from upstream 14, +112 from old f9/14 and +76 from clean13. Madras is centered at 407, width 246.927924; the six cards retain 270-point spacing. Independent review confirms this is not a window-origin subtraction error. There is no internal target/nearest/snap trace in this run.

## Confounds and missing observations

The observer's copied source hash is 79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755, introduced by collector 3f434cf. It includes a startup-window readiness gate absent from the earlier upstream/f9 three-scenario observers. The current 13 run used that same source content, but with inactive 13 and an isolated bundle signature. App source, observer timing and execution conditions are not all controlled by the old comparisons; no cause is assigned.

Immediate in every dataset starts 900×652 and resizes to 920×668. Wait/direct restore 920×668 before their no-change resize request. The new 14 run additionally records hidden/restoring window states before visible readiness. Fresh PID does not mean erased window restoration history. Close-return to Film-select preparation was about 6.3 microseconds; actual CLI command boundaries were about 1.383 milliseconds apart. Neither metric proves a particular SwiftUI layout schedule.

The first three immediate AX walks were truncated; the first complete one began about 0.873 seconds after selection. It already showed detail width 709 and Film AXScrollArea 240 with the final 677/407 centers. There is no observed earlier width such as 484→709. AXScrollArea 240 remains an accessibility region, not a native clip-width measurement. Each sequence ran once, and active 14 versus inactive 13 cannot establish active color/material parity.

The result therefore confirms clean e48 executes on native 14 and preserves the measured wait/direct geometry. It does not prove all three native 14 paths are visually unchanged, explain immediate variance, close existing Last/wide boundaries, or validate physical gestures. A matched-observer comparison is a separate experiment; this archive contains no such new run.

## Files and cleanup

- `runtime/`: all 119 original downloaded files, unchanged, including raw result, PNG, command/application/observer logs, exact build environment and copied observer source.
- `original-runtime-SHA256SUMS`: pre-analysis inventory of those files.
- `provenance/`: terminal success response, poll timestamp/error output, GitHub artifact metadata and the exact harness workflow source. Artifact 12551189267 was downloaded once; the 704717-byte ZIP digest `36b12949706b464d16cf889b230eea8cf64e71968ee2b7b3f1043c23de2f72d8` matched the server before safe path/type extraction.
- `analysis.json` and `analyze.py`: offline comparisons against separately frozen upstream 14, old f9/14 and clean13 evidence. Raw inputs are never rewritten.
- `reference.json` and `cleanup.json`: source/harness/hash scope and deletion of only the redundant owned download ZIP/raw copy. The original app was neither downloaded nor modified here. No local UI, CI dispatch, preference/TCC change or product/main-document edit occurred.
