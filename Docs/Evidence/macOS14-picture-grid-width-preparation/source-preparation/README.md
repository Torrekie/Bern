# Picture grid width-action diagnostic (private preparation)

Only the existing `BernAdaptiveGrid.onGeometryChange` action is instrumented.
This is a source diagnostic proposal, not a layout fix or native acceptance.

## Exact input and patch API

- Source: `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`.
- Real output name: `Sources/BernStyle.swift`; backend `src/lib.rs:143,278`
  passes the template to `GeneratedFile::text`; target API `src/lib.rs:498`
  converts that text directly to bytes. Exact template: 205764 B,
  SHA256 `e1cad857ba8d4d6a5ad5155c3d7f30cc44a511b6de8988329aa45392c6cd1c6f`.
- The archived source export reports 20 files/20 changed, but does not retain
  a per-output list or actual Style file. Its selected template input matches
  this Git blob. The patch must check the actual generated Style hash remotely.
- Keep the frozen 21-point full Scene observer first. Its combined generated
  source must remain 106494 B / `f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2`.
- Then, before the original `target.plan`, run:

  `python3 patch.py OUTPUT_ROOT FRESH_EVIDENCE_DIR`

  Keep `GridWidthTrace.swift` beside `patch.py`. Evidence must be fresh and
  outside OUTPUT_ROOT. Hash/match mismatch or reapplication raises an error;
  there is no fallback. Only generated Style is changed; no template is edited.

## Observation contract

The original grid is at template lines 3053–3090; the action starts at 3079.
Two immutable entry captures and a `defer` precede its existing guard. The guard,
initial zero-width Transaction, and both State writes stay contiguous original
bytes and in their original order. The defer writes after those original actions,
including guard-return entries. It adds no View state, layout getter, timer,
Task, RunLoop, flush, frame change, width override, or alternate layout path.
The entry uptime getter and synchronous logging still perturb callback cost.

Each row records old stored width, measured width, finite/Double bits, the
original guard predicate, body-captured columns, minimum/gap/rowGap, entry and
post-action record uptime, and main-thread status. `columns_captured_from_body`
is not recomputed from measured width and does not describe a settled render.
The three exact generated callsites are layout_page lines 1280/1314/1376:
minimum/gap/rowGap = 120/16/16, 192/16/16, 140/12/12. These distinguish source
configurations here; they do not identify grid instances or remounts.

Use the existing `BERN_PICTURE_OBSERVER_OUTPUT_DIR`, an externally precreated
directory outside fresh collector OUTPUT. This helper never creates it.
It writes `picture-grid-width-PID.json`, schema
`bern_picture_grid_width_action_v1`, independently of the unchanged 21-point
packet. Maximum 64 rows / 64 KiB; first write refuses an existing packet and
later writes are atomic. No unmount write, retry, or alternate output path.
Missing directory/existing packet disables logging; cap or I/O failure stops it
and can leave a shorter successful prefix. `end_state` is always `not_observed`;
no success/complete/settled claim is emitted. Sequence is serialized log order,
not a promise about concurrent callback entry order. Nonfinite widths are null
plus their exact Double bits; signed zero remains distinguishable by bits.

## Next runtime gates and stop boundary

First require full observed14 original PNGs unchanged (Picture 125 / HDR 147)
and original 21-label coverage; otherwise stop before interpreting trace. Then
use the exact same binary on 13 and 14 once each, preserving the complete Scene,
normal/en/920×668 route and original collector timing. Require the expected
separate per-PID packet, finite/main-thread target rows for 120/16/16 and
192/16/16, and no cap. Retain any 140/12/12 lower-section rows too; its absence
does not itself fail the two target grids. Bind PID/route and uptime to capture
receipts; a last callback does not prove continuous interval coverage.
Absent/partial/I/O-unknown coverage is incomplete, not evidence of no callback.

This can expose a different width-action sequence or captured columns. Equal
0→719 histories do not establish a cause, settlement, card intrinsic/proposed
size, or equivalence of container layout. If this boundary does not distinguish
the remaining possibilities, stop this diagnostic; do not add padding, fixed
height, static children, or another fixture based on this trace.

## Validation performed

`static-proof.json` records exact in-memory patch/reversal and negative hash
guards; `BernStyle.width-trace.patch` is the precise diff (no full Style copy).
Foundation helper only: local Swift 5.9 / SDK14.2, arm64 min13, Swift5 mode,
strict concurrency complete, exit 0 with empty log. Used only root-authorized
`work/picture-local13-build/module-cache`; it was not cleared and is no longer
being written. SDK26 full Scene compile, CI, UI, pixels and product acceptance
were not run. Root owns future integration and runtime gates.
