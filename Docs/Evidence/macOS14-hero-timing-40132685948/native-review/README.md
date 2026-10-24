# Bounded timing: independent native review

Verdict: `strict13_and14_native_trace_pass`. Both hosts passed the unchanged complete native/execution/SDR prefix (five path/OS literals only), strict timing and trace-only invocations, all exit0. Trace-only explicitly reports coverage=true, structure_error=null and strict_gate_passed=false; neither report was changed. First-row identity/start/original-stamp fields exactly match SDR mapping.

Actual binary SHA`723896fc46a2a5e29a1c02293ebc138948f5bffdff10cbe0eec2cf0cdb1108b6` was read before/after gates while present. Read-only arm64/min13/SDK26.2/strict signature checks passed, as did20 manifest members,12 source entries, tar and assembly. The4fc git base and5 overlay files match their source identities, including the cc960 committed overlays. Root13 readiness/four exits/endpoint results and their input hashes were checked; no pixel computation was repeated.

Observed intervals in milliseconds:

| OS | started→timer added | started→first tick now | callback entry→first stamp | entry→scalars end | first scalars end→first tick now, unattributed |
|---|---:|---:|---:|---:|---:|
| 13 | 0.128542 | 9.159292 | 0.428958 | 0.447667 | 3.032958 |
| 14 | 0.435083 | 159.426667 | 0.641833 | 0.665958 | 140.834583 |

The last column has no callback-exit boundary: remaining callback work, automatic drawing and dispatch are not separated. Existing tick now is neither callback return nor assignment/display completion; second-row original stamp still belongs to the first observation. These one-run scalar values establish neither cause nor responsiveness/visual acceptance.

Only compact timing rows/statuses and42 original input fingerprints are retained here; no original source, full gate, report, samples or image was copied. No UI/native app, compilation, CI dispatch, signing mutation or pixel algorithm was run. Temporary preparation metadata was replaced by this final result and manifest.
