# Single Frame Row ledger candidate

Private preparation only. No repository edits, compiler, tests, product launch, UI, CI or Git mutation. Python AST and in-memory source transformation/inverse checks are the only local validation. Not yet runtime or visual acceptance.

`patch.py GENERATED_OUTPUT_ROOT FRESH_EVIDENCE_DIR` is an external **after-generation, before-target.plan** hook, following the existing picture observers. It does not edit the Rust generator or its product logic. It requires the real e48 Gallery BernGenerated.swift exactly 81,110B / `f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653` and BernStyle.swift exactly 210,785B / `3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89`.

The sole generated-source edit adds `diagnosticID: "gallery.frame.controls"` to the actual Frame BernRow (original line1274). BernRow gains an optional property defaulting nil. Only its private widths/arrange methods accept the diagnostic memory object; existing sizeThatFits calls use the nil default. Original three sizeThatFits call sites, one dimensions call site, one place call site, Item arithmetic, guards, branches, assignments, gap calculations, and x advance remain. Their relative order stays intact. Memory snapshots interleave after the original values become available; instrumentation still has allocation/timing cost, requiring the no-observer pixel gate before interpreting it.

Raw 0/nil/infinity query responses are copied without another query. Normalized least/ideal/most/grows/spacer are copied from the existing Item values, not recomputed. Dimensions height/guide are copied from the existing dimensions object; extent/offer/top use the actual original arrays. Spacer entries explicitly say the corresponding queries did not run. Each original place call is followed by a memory copy of its pre-advance x/spacer; y and place proposal are represented after the loop from the unchanged original bounds/top/proposal formula. Offered width is not necessarily extent, and returned row.size.width need not equal bounds.width: the original length is sum(extents)+sum(gaps). Compare any independently recomputed length/finalX with floating-point tolerance rather than rejecting valid original behavior. These are Layout requested arguments, not native view frames, intrinsic size, bezel, or ink. All actual ordinals and count are retained, without assuming builder4 equals Subviews4 or assigning control names to ordinals.

Complete record construction, arm filesystem inspection, JSON encoding and output happen only after the complete original place loop and its final x advance. Entry/completion uptime bracket those original operations; completion is sampled before encoding. No extra Layout measurement, forced layout, observable state or UI mutation is introduced. A complete record correlates the width queries, dimensions and placements from the same original place→arrange→widths invocation. It does not capture independent sizeThatFits-only calls or prove a final settled state.

## Collector protocol

With `BERN_FRAME_ROW_LEDGER_OUTPUT_DIR` unset, no ledger file or filesystem inspection occurs. Set it to an existing absolute nonsymlink output directory. Before the existing Frame selection, the external collector atomically creates `frame-row-ledger.arm.json` (regular, <=4096B):

```json
{"schema":"bern_frame_row_arm_v1","pid":12345,"stage":"frame-closed-light","token":"one-unique-run-token"}
```

The PID must match the Gallery process; token must be nonempty and at most128 UTF-8 bytes. The helper checks arm only after original place completes. Unarmed calls have memory snapshots discarded and do not consume the cap; absence of a later real place produces no sample rather than forcing layout. The first valid arm is cached for this process/stage. Do not reuse this one-stage process for another capture or switch states after arming. The existing closed/awake context and uptime association remain collector responsibilities.

Output is `frame-row-ledger-<pid>.json`, schema `bern_frame_row_ledger_v1`, bound to stage/token/PID. Finite CGFloat values are Double JSON numbers; nil is `{ "kind":"nil" }`; infinities/NaN have explicit kind plus Double bits. Raw nil for an unqueried spacer is accompanied by raw_queries_performed=false. Nothing is silently converted from infinity to a finite width.

At most64 complete placements and at most65,536 file bytes are retained. A512B reserve permits rewriting the successful prefix with `truncated:true` / reason on the next count/byte overflow; no cap is enlarged. Invalid/incomplete memory capture also stops with a truncation reason. Truncated or missing data cannot be acceptance evidence. Every snapshot says end_state=not_observed: a finite prefix never proves app lifetime or settled layout. First output refuses overwrite; later snapshots replace atomically. I/O/encoding failures stop and emit `BERN_FRAME_ROW_LEDGER_IO_ERROR` to stderr; the old successful prefix may remain, so collector must reject that error even if the file exists.

## Receipts and gates

Patch execution emits exactly two ordinary unified diff files (`BernStyle.row-ledger.patch`, `BernGenerated.row-ledger.patch`) plus patch-proof.json into a fresh directory outside generated output. Headers use a/Sources/NAME.swift and b/Sources/NAME.swift. The Style ends with the exact helper bytes. Receipt hashes cover originals/helper/candidates and written readback; reversing the edits recovers original full Style and Generated bytes. No patched product source fixture is retained by this preparation.

Future work must bind the exact compiled bytes and compare observer-on with the no-observer control using the existing macOS14 original-pixel gate before the macOS13 comparison. The same source/current closed context must support any ordinal mapping. Equal/different ledgers alone do not establish a unique cause or justify a2pt adjustment. This preparation stops at the frozen source candidate.
