# Bounded timing observer (source only)

Base: repo `.github/scripts/hero-coordinator-sdr-probe`. Only three derived files; assembly unchanged: AppKit/SwiftUI imports → ProductHero.swift → FlightSDR.swift.inc → Driver.swift.inc. Image/Style/Dependencies/exacts/assets/wrapper stay unchanged. The new prewindow scope guard accepts **default13/default14 only**; all original SDR code/gates remain. No compile/UI/CI was performed.

Baseline SHA256:

- Hero: `cf924d4fa27df6486b65b30be1a194ec7daf4016674b79bd4084e045eba8beea`
- FlightSDR: `5f79ae281bb743ee7af87dc737e66195b4bd85c5e50c84d0c5183f53766d8f65`
- Driver: `16d366612fdb55a4a2a1e39ce731cc7ad247fa71608a89f65a1c8d241230ec92`

Native additions: one stamp after original RunLoop.add(clock,.common); first tick copies existing now before unchanged guards; first applied copies existing now/p immediately after original view.progress assignment. Neither tick hook reads a clock. Driver records callback entry and brackets its existing WindowInfo/scalar calls. Existing observeFlight receives an entry stamp; its existing first-live stamp is copied after mapping, without another clock. First two live callbacks receive callback/sample IDs and the actual pinned flight/scalar state.

Storage is bounded: exactly three named native-event slots, at most two live rows and one pending callback dictionary with fixed call-site fields. No object/image references, timer/dispatch/query/flush/layout/IO or animation assignment is added. Repeated tick calls only check populated slots. Once two live rows exist, sampling hooks return before a new clock read or formatting; caller arguments are existing scalar IDs/values. There is no assumed callback-entry≥timer-added order.

Post-teardown `report.flight_timing_trace`:

- `kind="bounded_native_sampler_scalar_timing"`, `complete`, `success`, `error`, `native_events`, `timer_added_count`, `live_samples`, `pending_callback`, `frozen_before_teardown`, `limits`, `scope`.
- `native_events.timer_added`: key, flight_started_uptime, uptime (post-registration checkpoint, not exact registration/first-fire time).
- `native_events.first_tick`: key, flight_started_uptime, now_uptime (existing tick now, which may precede a guard skip).
- `native_events.first_applied`: key, flight_started_uptime, now_uptime, progress (existing now/p after the assignment, not presentation).
- Each live row: callback_id, sample_index, callback_entered_uptime, window_info_begin_uptime/end_uptime, scalars_begin_uptime/end_uptime, matching_begin_uptime, existing_first_live_observation_uptime, state_uptime, flight_identity, flight_started_uptime, progress.
- limits: native_event_slots3/live_samples2/pending_callbacks1. Missing events stay missing; partial callback fields are preserved rather than filled. The first-live stamp on row2 is the original row1/global stamp, so only row1's stamp is ordered within its matching interval. Each row's matching_begin is bounded by its own scalars interval. Timing coverage checks require the first two adjacent callback/sample IDs, same identity/start, finite monotonic per-row fields and the three actual events. They do not impose ordering between callback entry and timer-added.

Freeze precedes original cleanup. Original native/execution/arm-nextsample/3PNG/stability/limits and SDR finalization run unchanged. After teardown, timing finish appends complete/success; `complete` describes trace coverage, `success` also requires original acquisition. Missing timing never manufactures native success; failure propagates nonzero through the existing finalization flag, preserving any earlier SDR/native error. Timing cannot establish rendered-frame synchronization, cause, zero observer effect or responsiveness acceptance.

Static checks passed: canonical patch zero-fuzz replay; removing three native hooks restores exact Hero; removing two matching hooks restores the exact original SDR enum; original arm/nextsample and native-final gate blocks match; no object/query/display/IO construction in the timing enum. No schema simulation or runtime testing was performed. Apply `coordinator-timing.patch -p1` to the three exact baseline files; SHA256SUMS locks the derived sources and this note.
