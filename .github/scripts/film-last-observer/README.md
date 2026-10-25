# Film Last observation: source preparation only

Exact e48 templates: Style3912ecd…cbd89 / Runtime255bac…9e16e. `patch.py TEMPLATE_DIR FRESH_OUTPUT_DIR` emits two unified diffs and proof; never edits templates. It rejects generated Runtime. Future generation expands FILE_KIND_EXTENSIONS and may append SVG: root must bind those real bytes separately. No CI/wrapper/collector path is supplied.

Only macOS13 with BERN_FILM_LAST_OBSERVATION_FILE enables recording. Five fixed slots: post-assignment request; first eligible schedule; first eligible settle; first actual setter request (its own inputs via nonescaping autoclosure); terminal. Counts cover eligible schedules/settles and writer invocations, not rejected guards. Private Style snapshot reads existing state only. One selected document.frame getter is hoisted after minimum, before maximum; original arithmetic/branch/getter count stays, not machine timing or zero effect.

No new view/task/timer/queue/setter/layout. Non-Published buffer uses weak owners/surfaces plus permanent IDs; expired/mismatched identities invalidate without rebinding. Only export sanitizes/encodes after existing Last PNG/AX at first post-request ui.inspect. One export phase may encode each slot and the complete file; this is not one JSON API call. Slots≤2048 encoded bytes, total≤16KiB; fixed field/key shapes bound retention (not allocator overhead). Missing slots, multiple requests, invalid fields/identity or caps => diagnostic_complete=false; nonfinite=>null+path/type.

Fresh absolute env file, existing parent, one atomic write; no directory/prefs/IPC changes. Existing file/serialization/IO error: fixed stderr, no retry/throw/response change. No results or validity override. Control pixels remain a future gate. Author ran AST/in-memory edits only. Root reports b9a7 core typecheck rc0: Swift5.9.2/requestedSDK14.2/-swift-version5/arm64-target13. This is not product/Swift6/runtime validation.

## Narrow Swift 6 source candidate

Build-only CI 40175193229 failed in Swift 6.2.4 / SDK 26.2 during SILGen of
`BernSnap.body`, with signal 6 and “Found an ErrorExpr but didn't emit an
error?”. The actual generated Runtime/Generated/Style matched the previously
pinned e386/f72c/fb2 bytes. The old `snapAllowed` and `snapGeneration` map
expressions emitted warnings; they remain byte-for-byte unchanged.

This derived packet changes only the new observation-owner expression. A
private `@MainActor` helper in BernSnap's existing macOS block guards enabled,
then unwraps positionItems, then returns an explicitly typed `@MainActor`
closure capturing only `[weak owner]`. The existing legacy ViewBuilder branch
passes the helper result. Disabled/nil inputs still return nil, and the weak
closure still returns `owner as AnyObject?`. No new view, Task, timer, getter,
arithmetic, schedule, native setter or core change is introduced. There is no
machine-timing equivalence claim.

The candidate Style is 214863 bytes / SHA-256
`179b406b1a7246e855ac7634bf225d1680016033fb1044035fb0137399c81e0e`.
The immutable core remains b9a7 and the Runtime template remains 1da1; only
Style gains the helper and replaces the owner expression. AST and in-memory
forward/reverse checks do not establish a compiler root cause, successful
Swift 6 compilation, native diagnostic coverage or preserved pixels. The
failed cohort remains failed; a new full build is still required.
