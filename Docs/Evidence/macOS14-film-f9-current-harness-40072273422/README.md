# Old f9 on macOS 14 with the current Film observer

[Run 40072273422](https://github.com/Torrekie/Bern/actions/runs/40072273422) completed successfully. It ran the existing f9 Gallery from build 39991406873, without rebuilding the app, using the same current observer as clean e48 run 40071892408. App source is f9e08b1d55bed4b9d880b19934abe48281057bb3; the original app-build harness is c1900f58bca6fd283bce2d4cf9769f1e6029ebb0. The runtime workflow harness is 25e18cbc7cd760c1c399042f1d7364c3d755a9dc, and copied observer source SHA256 is `79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755` (collector 3f434cf).

The recorded exact GUI SHA256 is `887173af876a3f802c68dfff7fef087f318cc6909a61ea4beff69dad536dfd7e`; CLI is `31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5`. This is the old f9 artifact, not clean e48. The app is ARM64/min13/SDK 26.2; the observer used Swift 5.10/SDK 14.5 on macOS 14.8.9. No app binary was downloaded or run locally by this analysis.

## Result and bounded conclusion

Three fresh processes were active 14/1x, normal accessibility flags all false, with scenario=all, followup=none and trace=false. Each final AX traversal is complete with six images; each Film capture passed four identical raw-buffer comparisons at 920×668 points.

| Scenario | Old f9, current observer | Old f9, old observer | Clean e48, current observer | Upstream, old observer |
|---|---|---|---|---|
| Immediate Glen center / width | 565.000  / 268.799753 | 565.000  / 268.799753 | 677.000  / 256.153006 | 566.000  / 268.799753 |
| Wait Glen center / width | 601.000  / 267.534787 | 601.000  / 267.534787 | 601.000  / 267.534787 | 601.000  / 267.534787 |
| Direct Glen center / width | 601.000  / 267.534787 | 601.000  / 267.534787 | 601.000  / 267.534787 | 601.000  / 267.534787 |

**Every complete AXImage frame in all three control cases is numerically identical to the old f9/old-observer run 40062837456.** Wait/direct are also identical to all six frames in clean e48/current-observer14. Immediate Madras remains 295  / width 240, versus 407  / width 246.927924 in clean e48.

The current observer's startup-window gate did not reproduce 677 in this f9 control. A deterministic explanation that merely replacing the observer must produce 677 is not supported. This does not exclude gate interactions or timing variability, prove a source regression, or identify the Film patch/another mechanism as the cause: app source/build and run differ, and each condition was sampled once. The 112-point current f9/e48 immediate difference remains open.

All external comparison PNG pairs differ in bytes, despite exact AX geometry in some pairs. Within this run, wait/direct Film PNGs are byte-identical. No active color/material parity, internal Binding setter trajectory, physical gesture or Last/resize followup is established.

## Window and timing facts

Immediate records 900×600 visible, then 900×652, followed by an actual Command resize to 920×668. Wait/direct restore hidden 920×616 to visible 920×668 before no-change resize. Final origins y158/106/54 match earlier 14 references. This is the same outer-window history pattern as clean e48; it does not expose internal layout timing or erase restoration history.

Close-return to selection preparation is about 2.96 microseconds for immediate, and 2.075028 seconds for wait. The first complete new f9 AX sample begins about 0.498 seconds after selection; clean e48's was about 0.873 seconds. Earlier walks were truncated. Once recorded, detail width is 709 and Film AXScrollArea 240; no earlier width transition was observed. The accessibility 240 region is not a native clip-width measurement.

## Preserved evidence and cleanup

- `runtime/`: all 117 original downloaded files, unchanged, including report, PNGs, command/application/observer logs, exact build environment and observer source.
- `original-runtime-SHA256SUMS`: full pre-analysis raw inventory.
- `provenance/`: final successful CI response, GitHub artifact metadata and exact current-harness workflow. Artifact 12551278015 was downloaded once. Its 679270-byte ZIP digest `bc63280807f06347aa8b2c371a8c7499d496f8ce77eca06e5a932dc418ce8c2f` matched the server before safe path/type extraction.
- `reference.json`, `analysis.json`, `analyze.py`: source/build/runtime-harness separation and reproducible offline comparisons with separately frozen evidence. Raw inputs are not rewritten.
- `cleanup.json`: only the redundant owned ZIP and duplicate raw copy were removed; the work raw path remains a symlink. No local app/CLI, compiler cache, UI/CI dispatch, product/main-document edit, preference/history/TCC mutation or unrelated-process change occurred. Logical byte counts are not APFS physical savings.
