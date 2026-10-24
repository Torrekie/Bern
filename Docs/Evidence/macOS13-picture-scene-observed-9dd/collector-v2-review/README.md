# Local13 collector v2 — independent source review

Verdict: `no_remaining_blocking_source_finding_after_null_front_fallback_fix`.

This binds Collector `aa722884b6692f65fe5d7b4a3953ae2f8358361b373e9bad64cebcdbbc1a60d8`, FocusGuard `dfe7417c19f0ae334226a3cdd4bc135a444f2aaa71fdb7f3e9f973bcd5f0170d`, wrapper `4ec5481369c66fcf4e2d13939d49815b95568b0c8d8b0446760877c4ffdfda4a`.

PID/bundle/executable matching now uses public Darwin `proc_pidinfo` start seconds/microseconds; nullable NSRunningApplication launchDate is diagnostic-only. The installed public headers support the136-byte BSD record and start fields at120/128. Python AST and exact source hashes were checked; no compiler, native helper, libproc runtime query, UI or CI was run by this review.

One inherited issue was reported and fixed before final source acceptance: direct fallback previously continued when `front_after` was null/missing. It now rejects unknown or own foreground, as does the app-child fallback. Exact start/path/parent checks remain before direct termination. The helper conditionally restores the original exact foreground instance before stopping the private app, preserving a user-selected different foreground. Bootstrap only adopts an exact collector child; unavailable identity fails closed. Valid kernel identity removes the repeated inspect caused by null launchDate.

CLI/capture/showcase function block11,858B remains byte-identical to v1. The original full-reference `showcaseSlices` prefix through Layout capture is3,004B and byte-identical to v1 and the original collector. Layout still has its original0.8-second pause, not5stable. Final normal-profile readback is after the loop and does not change page actions. Exact hashes and bounded conclusions are in `review.json`.

The external observer directory is a root-owned prerequisite: the wrapper checks an absolute path but does not create it; the product helper requires an existing directory. An I/O-on observation needs an actual own-PID packet with label coverage. A run lacking that packet must not be called an I/O-on observer comparison.

Remaining limits: process identity checks and kill are not one atomic handle operation; unknown/orphaned ownership may require parent intervention. The175-second wrapper limit bounds collector waiting, with additional cleanup time. Report I/O/hard termination can limit partial output. Source review does not verify runtime cleanup, actual front/cursor restoration, selected PNG equality, observer output, or synchronized/settled layout. Parent's later A2/B/B3 results require their own receipts; no runtime result is imported into this source verdict. v1 failed evidence and all runtime artifacts remain untouched.
