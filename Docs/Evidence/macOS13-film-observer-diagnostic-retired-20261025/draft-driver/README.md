# Film observer13: private source preparation

This is source only. No prepare/run mode, source function, helper, App, CLI,
compiler, native/UI, CI, Git, network or cleanup action was executed here.
Root owns the actual download, compiler receipt, private-copy preparation,
independent review and any later single native run.

## Inputs and interfaces

The source App is the exact successful build 40176620054: GUI 3770800 bytes /
`e2fbcea5fdc4cea6ebcfb00e1214e55badd78d82a31ebd248e18971e2f6c39a2`,
manifest `fdb3ff8ca2fc2235531289c98fd5724f1eae816babd9646c83bf74587d86243f`.
All ten App members and sizes must match that manifest before copying. The
CLI remains the separately delivered original `31a75c0a…379f5`. The old
gallery-build/delivery receipts describe that original delivery and prove
CLI provenance; their d44 GUI is not the observer input App.

```
python3 prepare-film-observer13.py --prepare --delivery-receipt-sha256 SHA --reference14 PATH --observer-build PATH --observer-build-sha256 fdb3ff8ca2fc2235531289c98fd5724f1eae816babd9646c83bf74587d86243f --diagnostic-destination ABS_FRESH_WORK/diagnostic/film-last-observation.json OBSERVER_APP ORIGINAL_CLI GALLERY_BUILD_JSON ABS_FRESH_WORK
python3 run-film-observer13.py --run --collector PATH --focus-guard PATH --collector-sha256 SHA --focus-guard-sha256 SHA --local-sources SOURCE_DIR --helper-build PATH --helper-build-sha256 SHA --locks PATH --locks-sha256 SHA OUTPUT
```

Use normal Python without assertion suppression. Prepare creates a fresh
`dev.bern.frame13.filmobserver.UUID` copy, verifies strict signatures, preserves
every Mach-O section and signature-storage-normalized byte, and permits only
the original CFID/signature member changes. Input App/CLI remain unchanged.
New locks schema is `bern_film_last_observer13_locks_v1`, kind
`film_last_observer13_capture`; the sole `film` row explicitly binds e2fb as
its source GUI. Original d44 locks cannot be reused.

Locks and isolation receipt add `observer_build_manifest`,
`observer_build_manifest_sha256`, `observer_source_app_sha256`, and
`diagnostic_destination`. The latter must be the exact absolute path shown
above, outside capture OUTPUT and watchdog. Prepare creates only its fresh
0700 parent; it does not create the diagnostic file. Runner requires that
parent to remain owned by the current UID, nonsymlink and 0700, and the file
to be absent before launch. These four bindings are retained in watchdog.

The canonical14 reference remains SHA `8921655d…fe8f50` and binds original
e48/d44/31a initial plus first Last. It is a data prerequisite and has no
strong cleanup proof. It does not establish observer behavior or OS equality.

## Helper and environment boundary

`source/FilmFirstLast.swift` is a three-replacement environment adapter of the
canonical c4 collector, source SHA
`8bdf078fd1b75c8e4dd8b5c20725a12462491c9e92108818fd0b6e86b812ad0b`.
Its replacement pairs and byte-exact inverse are in source/source-proof.json.
FocusGuard remains ab78. Runner locks the new source manifest `8b6ac6b1…c9240`;
old c4/fa2 helper receipts cannot be substituted. Root's actual helper receipt
must use kind `film_last_observer13_helpers_build_only`, names FilmFirstLast
and FocusGuard, actual source_before/after, paths/bytes/SHA values, target
arm64-apple-macosx13.0, actual min/SDK and successful command records. Binary
hashes are required caller inputs and are not predicted in this preparation.

Runner rejects inherited core/handoff environment and supplies only
`BERN_FILM_LAST_OBSERVER_DESTINATION` to its supervised collector. Collector
removes that key from its shared environment. CLI and cleanup Guard receive
the cleaned environment; only the unique App environment copy adds
`BERN_FILM_LAST_OBSERVATION_FILE`. No user-global environment is changed.
Collector arguments and report schema/kind remain original; watchdog kind is
new. No new sample, inspect, UI action, sleep, timer or layout path is added.

## Preserved execution and separate truths

The original 12 kernel/ownership/helper definitions are byte-identical. The
95s outer, 75s inner, 18s startup and defaults-delete 5s caps remain. Original
front kernel correlation, exact parent/PID/path/start identity, conditional
restore-before-stop, exact CLI child cleanup, private prefs and owned IPC
guards are preserved. A timeout/error keeps raw false; later manual cleanup
must be separate and cannot rewrite it.

The original action order remains initial PNG → AX → inspect; Last target
lookup inspect → activate → stable Last PNG → terminal AX → checked-controls
inspect. The last inspect is the expected one-shot core export opportunity.
There is no new inspect between Last action and its original PNG/AX.

Wrapper success covers only its unchanged capture/cleanup gates. It does not
parse, retry, repair or mark the diagnostic valid; watchdog explicitly records
`diagnostic_validation_performed=false`. Missing, early, wrong-request or
incomplete diagnostic stops the separate offline diagnostic route without a
rerun and cannot replace original capture/cleanup truth. The independent
analysis entry accepts report/watchdog/diagnostic/locks/build-manifest and a
fresh output; endpoint observer-effect controls precede interpretation. No
position tolerance, 14.5pt explanation, adoption or cross-OS pass is asserted.
