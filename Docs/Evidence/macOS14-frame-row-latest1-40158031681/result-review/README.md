# latest1 CI40158031681 — independent failed-result review

**Cohort FAIL.** Actual control A succeeded; observer B reports success=false and `ledger_log_error_after_cleanup=Final latest ledger hash differs from validated snapshot`. PixelGate did not run. The local13 observer gate remains closed. This review changes no original/frozen source or runtime file.

The build receipt is successful for exact e48 Gallery macos_modern/min13 and frozen latest1 package hashes. Harness/head is c28f678f31442db40358a20b877e0e1f03fdb2fb. The runtime download receipt binds artifact12584897807 (frame-row-ledger-on14),149,517B, API digest sha256:872ba8629608e643d8c9d63d25439cdb1c2a36c50434258959c73d5752284002, verified before its ZIP was deleted. This reviewer checked the receipt and extracted files, not the deleted ZIP or a newly downloaded executable. GUI identities in build/capture receipts agree: control d44f051c…749126c; observer de21e46f…118e90a; unchanged shared CLI31a75c0a…4f379f5. Source/compiled-source/helper hashes are preserved in verification.json, without claiming fresh executable re-verification.

| Evidence | Bound report metadata | Final retained packet |
| --- | --- | --- |
| Observed / sequence |122 /121|140 /139|
| SHA|6d234cb284b241147991c97e2f723e4d9996ee4b5ade30cbc6f844e271341fd2|9a86dcab45274ee5a0c5f56cd1a72d2fd8ad2ad466dc43d21e1484c7e061fda0|
| Bytes|2286|2287|
| Last complete uptime|422.5477074583334|426.86076962500005|

Stable image sample begins at426.0580055416667. The final record completes about0.803s later and its SHA differs from the bound metadata. Internal v2 counters/PID/token remain consistent; they do not repair the final time/hash violation. No extracted standalone file matches the bound SHA, and the report has only its metadata, so the bound record's raw contents cannot be recovered or used to explain widths. No width fields from either the final record or the absent bound record were interpreted. The data does not prove which event caused the later observations; cleanup is not established as a unique cause.

Offline PNG checks have a narrower scope. Each current original PNG is byte-identical to its respective original from failed cohort40155522534: A ef6951d5…eccfb6b, B66e16368…b61919b. Both are920×668 RGBA/1× with equal embedded ICC (3300B, SHA3d40c076…eb5f55). Pillow compared decoded RGBA bytes without conversion/resizing: fixed historical Frame ROI[211,52,920,668) has0 changed pixels; whole window has5284, bbox[10,118,200,146). This is offline image equivalence only, not a run or replacement of PixelGate and not cohort acceptance.

The retained reports record both apps no longer running, termination0, accepted original-front restore requests and before/after front PID343. Both closed contexts remain English workflow/Light window, source-declared dark Frame, caption=true, Volume closed, media Paused0; own-window ID checks and stable image comparisons passed. These are report facts, not a new live process/kernel query. The application logs lack the writer error marker; B still fails the separate final hash check. Only first startup sessions commands were nonzero (status3); later commands were0.

Stop this history/latest1 ledger route as its prior time/hash stop condition requires. Keep the actual failure and its final packet, preserve the final hash/time gates, and do not reconstruct bound data, raise the cap, add filtering/delays/fences, try new parameters or run the13 observer. Any separate plain-control13 planning does not unlock this observer gate. Frame Caption/Size equivalence remains unconfirmed; these results do not supply a product patch or a layout root cause.

Only offline source-identity metadata, JSON/log reads, SHA comparisons and Pillow pixel/ICC checks ran. No UI, CI, compiler, new build download, original edits or sampling matrix.
