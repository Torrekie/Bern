# Private static-route CI draft

Based on committed backing workflow/wrapper at `8b96b8c7f93dc324bd8281fa2f8356f962ee387d`. No repository edit, publication, dispatch, app run, compilation or spawning was performed by this preparation.

Root review/copy targets:

- `macos14-hero-route-probe.yml` → `.github/workflows/macos14-hero-route-probe.yml`.
- `run-route-one.py` → `.github/scripts/hero-route-probe/run-route-one.py`.

The route package is independent because its Driver requires backing and float observation off; installing it over the float package would invalidate existing workflows' on modes. Root supplies the frozen inline Driver/helper and complete source-provenance map in `hero-route-probe`. The workflow checks kind `actual_existing_overlay_static_route_fixture`, route default root, backing/float defaults off and required selection off. It locks Driver SHA `a6b483d48f468f3479d6ac36ba7b95464c037d3c792f7efe134edfc1ba9109ca` and the original newSDK `ProductImage.swift`/`ProductHero.base.swift` hashes. The source concatenation/build recipe and binary name `HeroFloatProbe` are retained.

One SDK26.2/min13 build supplies fresh14 root and overlay processes. Wrapper arguments remain `binary named custom out root|overlay 13|14`; backing and float envs are forced off, route env receives the selected mode, and child wait/kill remains 15 seconds. Artifact/tar/concurrency names are separate from earlier probes.

Normal/cache/front/identity, zero activation, original window bound, deferred metadata, five equal buffers and float-off zero-copy/retention/raw gates remain. Both route stages require two roles, same captured window, selected parent, no MTKView, finite 320×180 reported rects, roundtrip ≤1e-6 and corresponding ROI association. No overlay offset is fixed. The actual flight.bounds condition is an internal guard in the frozen Swift source; JSON has no independent bounds field. No image equality, format, cause, general visual equivalence or coordinated-flight/lifecycle acceptance is asserted.

Validation passed YAML/Python AST, four embedded Python blocks and `bash -n` for both shell bodies. Existing local13 root/overlay JSONs passed the report gate after the recorded path/expected-OS adaptations. The local binary had already been removed: only its receipt SHA was checked against the saved build fingerprint; the formal CI gate still hashes its actual packaged binary. No pixels were recomputed. Details and source/input hashes are in `validation.json` and `provenance.json`.

`changes.diff` is a comparison against the pinned backing inputs, showing reuse; it is not an instruction to replace the backing workflow or wrapper. Root should copy the two new target files and update only the independent route package's source map. `SHA256SUMS` freezes these private files; no binaries, module caches, PNGs, raw buffers or archive copies are included.
