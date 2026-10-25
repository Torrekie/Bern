# Single-run toolbar driver review

No execution-blocking static finding for the root-supervised single run. The runner binds the launched PID to the existing FocusGuard identity, saves that identity, and uses the unchanged restore-before-stop cleanup. Missing owned identity refuses blind termination; capture or cleanup failure yields a nonzero driver exit.

The reviewed runner is SHA`7c7209196d197d7fb86d485dd8565edfa742db2dece6e9f832f11125e19a1a9f`. Its actual FocusGuard binary is byte-identical to the previously reviewed B4 helper; source and binary hashes are in review.json. Only AST/source and byte-hash inspection ran.

Ready20s and capture75s are separate phase bounds plus helper/final-wait time. File existence of ready.json/capture.done is a handoff signal, not a PID/window/geometry or image acceptance verdict. Root must validate actual ready/capture evidence separately. Finally cleanup covers ordinary process flow; this is not a new external watchdog. No UI/compile/helper/network/git/signing execution was performed by this reviewer.
