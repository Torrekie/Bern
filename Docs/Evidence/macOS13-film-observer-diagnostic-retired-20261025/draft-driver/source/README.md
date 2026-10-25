# Film13 observer environment adapter

This source-only package derives the canonical c4 FilmFirstLast collector by
exactly three replacements: remove the explicit destination handoff from its
shared environment; explicitly use that cleaned environment for its cleanup
Guard; add the core diagnostic key only in the unique owned App environment
copy. The CLI already uses the cleaned shared environment. No report fields,
argument API, UI action, query, sampling, sleep, stable PNG, AX walk, layout,
first-Last ordering or restore-before-stop sequence is added or reordered.
The full source inverses to c4 byte-for-byte. FocusGuard remains original ab78.

Interface remains `FilmFirstLast APP CLI OUTPUT`; old collector report kind
remains `film_first_last13_capture`. The new observer wrapper/locks distinguish
the actual observer App e2fb and manifest fdb3 from the old unobserved d44 App.
Only the reviewed wrapper may provide the fresh absolute handoff destination.
The product core b9 and all product bytes remain outside this helper package.

Root owns actual compilation and receipt generation. The compiler receipt kind
is `film_last_observer13_helpers_build_only`, with dynamic actual binary paths,
sizes and SHA-256 values under names FilmFirstLast and FocusGuard, source_before
and source_after, target arm64-apple-macosx13.0, actual minimum/SDK and successful
commands. No binary identity is predicted here. No source entry, helper, App,
compiler, UI, CI or Git command was executed during this source preparation.
