# Real-coordinator recipe: minimal observation acceptance

This is an offline plan only: no new fixture, source change, pixel read, build, UI or CI execution. Use only the original before/in-flight/settled PNGs and reports from the new binary. Native/execution/recipe gates must pass first; failure/partial stops acceptance and remains partial.

## Endpoint controls (same OS/control conditions, same phase)

1. New13 default before/source and settled/destination must reproduce the corresponding old13 app-loop40110795231 endpoints. If a new14 default is acquired, compare each endpoint to the corresponding old14 endpoint as a second observer/toolchain control; old/new14 may be different VMs, so record instance/display/profile/scale conditions and do not call identical OS a literal same-host measurement. Never demand before/source==settled/destination: the old cohort already had small native row-dependent differences.
2. New13 baked-pair before/source and settled/destination must each remain exact to new13 default, because only temporary snapshot display changes. Verify original PNG/profile hashes, measured equal-size integral screenshot ROIs, full opacity, unchanged logical320×180/root positions and capture scales before raw RGB comparison. Also report each ICC→sRGB perceptual-intent0 comparison; do not compare unconverted gray/RGB values across different embedded profiles.
3. Cross-host scale1/2 original images are not raw-pixel-equality controls. Keep point geometry and any established atlas-normalized endpoint statistics separate from the within-OS exact controls. Do not resize/register an endpoint to manufacture agreement. Preserve old→new/new-default→candidate input hashes and failures, not only summary means.

## One asynchronous mid PNG

- Confirm actual visible nonblank atlas content has moved; inspect complete original PNG with its ICC. Look for source/destination double drawing outside the actual visible flight, correct clipping/extent/orientation, and final destination visibly in place with no stranded temporary view. A passing scalar opacity/attached flag alone is insufficient. If overlap/white atlas cells/lag makes visibility ambiguous, record that limitation rather than inventing a crop or pass.
- Preserve armed and adjacent capture sample index/uptime/progress/pinned identity, actual root/overlay frames and CG capture-before/after state/uptime. They bracket the observer's state, not a synchronized WindowServer frame. In particular, neither logical frame nor its interpolation is a measured pixel rectangle.
- Use those states only to contextualize original-image review. Do not fit/register/translate content to logical frame, select a pixel ROI from whichever state produces best color agreement, or compare cross-OS/default-candidate whole mid images at unequal progress. No mid MAE claim substitutes for endpoint controls or complete color equivalence. Static recipe's mixed color residual remains unresolved even if this lifecycle experiment succeeds.

## Exact latency table (one monotonic clock, no inferred missing events)

| Row | Source field / valid interpretation |
|---|---|
| Trigger | report.transition_uptime / mapping.transition_uptime, immediately before the single model replacement |
| Each snapshot | ordinal, actual anchor scalar identity/rect and mapped from/to role; snapshot_started_uptime→renderer_returned_uptime includes preparation+ImageRenderer, not isolated GPU time |
| Each conversion | conversion_started_uptime→conversion_finished_uptime; first includes context creation, second shared-context work; default fields are null, not zero-duration conversion |
| Wrapper/return | renderer/convert completion→nsimage_wrapped_uptime includes intervening helper and NSImage work; snapshot_returning_uptime is recorded by defer before the real return, not a display completion |
| Actual flight start | mapping.flight_started_uptime, native Flight stored-property initialization after both snapshots; subtract trigger to expose pre-animation synchronous delay |
| First live observation | mapping.first_live_observation_uptime and matching first live sample; subtract trigger/start separately, retaining sampler cadence; this is not first tick, first visible frame or input latency |
| Mid / finish | retain arm/capture and CG brackets, last-live→first-empty timer/flight samples, terminal/stop/run-return times; observed retirement is bounded by samples, not an exact native finish timestamp |

Report signed intervals and the two individual conversion costs as well as their sum; do not hide a cold0.259s-like pause inside a low-cost animation-duration statistic. Preserve absolute uptimes and actual order. A native-success deadline does not establish an acceptable responsiveness budget, nor does a delayed first observation uniquely identify a cause.

## Departure0.3s semantics

AppKit leave() stores Departure.time **after** its source snapshot returns. That source conversion cost precedes the0.3s lifetime; it does not consume an already-started Departure TTL. enter() checks a removed Departure's age before calling the destination snapshot, so destination conversion cost follows the acceptance check. Do not require “sum of both conversions<0.3s” or use Flight.started as Departure creation time.

Use only an actually observed departed[key].time and its observation uptime when available; missing transient departed entries mean not observed, not zero duration/expired/not used. Current sampling does not log the exact remove/check event, and a nil source weak identity cannot alone prove the Departure route. A destination snapshot start can help bracket source/departure→enter work, but is not the exact TTL check time. Preserve unresolvable route/check timing explicitly; do not alter the native TTL or add a timer to make it measurable.

The result can establish native acquisition, reference/retirement behavior and recorded costs for this one Standard named transition. It cannot resolve the existing mixed color errors, production intent routing, High/other inputs, arbitrary retargets, physical HDR, or animation equality from three asynchronously captured images.
