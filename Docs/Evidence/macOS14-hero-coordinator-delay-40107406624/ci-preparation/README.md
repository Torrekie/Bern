# Private next-sample coordinator CI preparation

This frozen private preparation is based on committed coordinator workflow `fe7f30d21494a290f363572c6556a138804fb1ba`. Its report gate follows frozen Driver SHA256 `b9d6b699af43128b0658ecb9e81df8ef346e6f9b3be253c07cca80968bcd8ec6` (384 lines). No repository/index change, UI, typecheck, compilation or CI execution occurred. No delayed runtime report was available, so schema execution is untested.

New identities are `.github/workflows/macos14-hero-coordinator-delay-probe.yml`, independent `.github/scripts/hero-coordinator-delay-probe`, binary `HeroCoordinatorDelayProbe`, tar `hero-coordinator-delay-probe.tar.gz`, artifacts `macos14-hero-coordinator-delay-probe-build` / `macos14-hero-coordinator-delay-evidence`, and separate workflow/concurrency names. The old package/workflow remain untouched. SDK26.2/min13/arm64 build recipe and original product/source/asset hashes stay unchanged; kind becomes `actual_coordinator_next_sample_fixture`.

`run-one.py` is byte-identical to the committed wrapper: four args, child-only unset BERN_MOTION, expected OS environment and15-second wait/kill. It introduces no new mode or action.

The initial explicit pending Driver token has been replaced with the frozen hash in the workflow and provenance; no unresolved placeholder remains. The new source kind is checked, `local_compile_attempted` must be false, and old `local_static_preflight` must be absent. No old typecheck success is attributed to the new Driver.

First in-band sample arms only; exactly the next existing natural RunLoop/sample supplies the one mid capture. The gate cross-checks zero-based adjacent indices against the actual samples array, full states/uptimes/progress/identity, top-level `midflight_sampling` records and flat in-flight fields. It requires `midband_armed` and `next_sample_captured`, same pinned live flight/timer/actual-overlay parent, and the original retirement/settling gates. Only armed progress is band-limited; capture may exceed.8. Loss is incomplete without retry, re-arming, added wait or forced flush.

`trigger_state` and `trigger_progress` are explicitly armed aliases, marked `trigger_refers_to=armed_sample`; they do not describe the later capture sample. Offline consumers must use `capture_sample_state/progress/uptime` plus the actual shot bracket states rather than treating the old trigger alias as capture state. No bracket/pixel synchronization is assumed.

Original endpoint/native/cache/front/normal/no-MTK/bounds and before/settled-five-stable gates remain. There is still one mid PNG and three total; no mid stable-buffer condition or image equality requirement was introduced. Native/schema success is not pixel, synchrony or animation acceptance.

`validate.py` passed YAML, wrapper/Python AST, four embedded Python AST blocks, both shell `bash -n` checks, frozen source/map hashes and wrapper byte identity. These checks did not execute workflow bodies or native code. `workflow.diff` compares with the old workflow; root should copy the new target rather than replace the old one. `provenance.json`, `static-review.json` and `SHA256SUMS` record this preparation. No binary, source archive, PNG, raw buffer or module cache was copied.
