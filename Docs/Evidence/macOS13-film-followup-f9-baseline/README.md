# macOS 13 f9 Film baseline and three-way comparison

One parent-owned local run (session 72575) exited successfully. It used the actual delivered f9 application from build 39991406873, a unique local bundle identifier/ad-hoc signature, and the unchanged collector 3f434cf. No diagnostic 744 build or candidate source was substituted. The original delivered application and CLI were not modified.

This is an **inactive macOS 13 geometry diagnosis**, not active visual acceptance. Both 13 runs used 2x display captures; the 14 reference was active at 1x. The baseline's sampled front application was Codex, while the candidate's was Simulator. All three accessibility profile flags were false. The baseline made no activation requests. Its own visible window had alpha 1; each capture passed four identical raw-buffer comparisons. Every settled stage contained six AX images and a complete AX traversal.

## Measured result

Dominant card centers below are in window-local points. The viewport's measured detail width was 709 → 809 → 709 points in all three runs.

| Stage | Old f9 on 13 | Candidate d146 on 13 | f9 on 14 |
|---|---|---|---|
| Initial | Madras, 565.500 | Glen, 601.000 | Glen, 601.000 |
| Last | Windowpane, 558.500 | Windowpane, 565.686 | Windowpane, 573.000 |
| First | Gingham, 565.500 | Gingham, 565.686 | Gingham, 565.000 |
| Last again | Windowpane, 565.500 | Windowpane, 565.686 | Windowpane, 565.000 |
| Width 1020 | Windowpane, 615.500 | Windowpane, 615.686 | Windowpane, 599.000 |
| Restore 920 | Windowpane, 565.500 | Windowpane, 565.686 | Windowpane, 565.000 |

The candidate's initial Glen frame differs from the 14 reference by at most 0.0000062 points. The approximately 16.5-point wide-window discrepancy already exists in old f9; the candidate adds only about 0.186 points in that stage and in First / Last again / restore. This supports a limited conclusion that the candidate did not introduce the large wide-window difference. It does **not** establish full followup parity or exact equality.

The first Last differs by 7.186 points between the two 13 runs. Their initial identities and elapsed sequence differ: the candidate includes its two-second diagnostic flush and after-trace capture, while f9 has no logger. The wrapper explicitly unset `BERN_SCROLL_TRACE_DIR` and added no external pause. No cause is assigned to this single-run difference. All six candidate/baseline PNG pairs differ in bytes; encoded-RGB statistics in `analysis.json` are diagnostic only, not a color/material equivalence claim.

## Files and limits

- `runtime/` preserves every raw report, command output, application/observer log, PNG and copied observer source from this one run. Its embedded preparation README intentionally describes the earlier preparation state; it is not the current conclusion.
- `original-runtime-SHA256SUMS` inventories all 104 original run files before analysis. Raw bytes were not corrected or rewritten.
- `preparation/` retains source, signing/section provenance, preparation scripts and the existing startup-gate validation. Local re-signing changes the GUI's full hash, while all section hashes and normalized signature-storage payload match the original. The CLI remains byte-identical.
- `artifact-member-fingerprints.json` records original and temporary app/CLI members before cleanup. `cleanup.json` records the exact removed owned copies and confirms no matching processes were active. It does not claim physical APFS savings.
- `analyze.py` regenerates `analysis.json` offline with Pillow and NumPy, using the preserved candidate and 14 sibling archives. It neither runs an application nor changes raw inputs.
- The startup readiness contract is a 15-second overall deadline plus an 8-second per-CLI-call cap; it is not a promise to tolerate every individual cold call for 15 seconds.

The logger-free Style proposal was separately applied by the parent as source commit e48fff46. This archive does not claim that the clean version has completed whole-application CI or runtime validation. Main Runtime/HDR fixes were not overwritten. See the [Film implementation record](../../Implementation/macOS13-Film-Initial-Position.md) for current status and remaining boundaries.
