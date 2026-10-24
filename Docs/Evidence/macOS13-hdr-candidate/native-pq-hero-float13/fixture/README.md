# Original snapshot float capture — source-only isolated fixture

Base: committed shared v2 fixture at `34dbeff0c4a9ab07828e8459ea990efba2f9fbf2`; its driver and hero base are byte-identical to `1a77dd3165ea420e64d422ae62a49dadf9aa31f5`. `prepare.py` preserves those immutable copies and applies only the explicit diagnostic diff plus the already archived SDK14.2 gain-map and unused-clock guards. Product source provenance remains the shared fixture's original scope; this is not a product change.

`BERN_HERO_FLOAT_CAPTURE` is process-cached: unset means `off`; only `off` and `on` are valid. An invalid value fails before window creation. Off keeps no snapshot CGImage references and performs no new snapshot provider read. On holds the two actual original renderer-return CGImages, freezes primary observations before the original window teardown, and disables retention for cleanup observations. After the original PNG acquisition and teardown it copies each original provider once, validates the exact known layout/length, writes complete raw bytes, then releases this fixture's image references. It does not claim object deallocation or zero observer effect.

The strict accepted layout is 16-bit float / RGBA64, bitmap info4353, premultiplied-last alpha1, 16Little byte order4096, pixel-format0, rowbytes at least width×8, and provider length exactly rowbytes×height. Both outputs together must fit4MiB. Unknown layout, absent provider, unexpected length, duplicate/missing key, or quota failure is explicit, without conversion or fallback. Export failure changes the report's success to false and makes the process exit nonzero even when acquisition had already returned success.

The existing v2 CGImage metadata/ICC serialization still occurs after original teardown. Its “no retained image/provider read” statement concerns the metadata observer; opt-in raw capture intentionally changes image lifetime and accesses the original provider. No second renderer access, NSImage recache/cgImage/TIFF readback, CI/CGContext conversion, colorMode setter, fit, panes, window, phase, draw, cache, timer, or Metal behavior is added. The original7.9s window deadline and15s outer process limit remain. This static two-endpoint experiment does not validate actual hero-flight lifecycle or physical HDR output.

## Entry points (not executed during preparation)

From the workspace root, root first builds once:

```sh
bash work/native-pq-hero-float-capture/build.sh
```

Then root runs the off control in one fresh output directory:

```sh
BERN_HERO_FLOAT_CAPTURE=off python3 -B work/native-pq-hero-float-capture/run.py work/native-pq-hero-float-capture/runtime13-off-control
```

Only after that control passes, root may run one on acquisition:

```sh
BERN_HERO_FLOAT_CAPTURE=on python3 -B work/native-pq-hero-float-capture/run.py work/native-pq-hero-float-capture/runtime13-on
```

There is no automatic matrix or retry. Build uses Swift5 mode, `-O -j2`, arm64/min13 and this directory's own module cache. `fingerprint.py` records source/binary/toolchain/signature information after root's build. The run wrapper verifies that binary fingerprint and both existing atlas hashes before its single child launch. Source generation and hash/static checks are the only preparation actions performed here.

## Report contract

`snapshot_float_capture` contains `requested` (raw environment string or null), `selected` (`off`/`on`, or null if invalid), actual `primary_observation_count`, actual `cleanup_observation_count`, `success`, nullable `error`, and `records`. Successful acquisition requires exactly two unique primary keys (`baseline-body-named`, `baseline-body-custom`); cleanup count is recorded rather than constrained to zero. Successful off has no records, no retained images, and zero provider-copy calls. Successful on has two records in named/custom order. A failed export may retain already-written records as partial evidence; overall report and exit remain failure.

Each record contains `key`, `file` (relative to the directory containing report.json), `byte_count`, `sha256`, `width`, `height`, `bits_per_component`, `bits_per_pixel`, `bytes_per_row`, `bitmap_info_raw`, `alpha_info_raw`, `byte_order_raw`, `pixel_format_raw`, `float_components`, and `export_stage=after_existing_window_teardown`, plus retention/read timing. Files are `snapshot-named.bin` and `snapshot-custom.bin`. Existing `snapshot_cgimage_observations` records supply the original color-space/ICC evidence; the raw dump does not relabel or reconstruct it. Raw row direction is explicitly `unverified`; an analyzer must preserve both orientation candidates until independently established.

`source-provenance.json` and `SHA256SUMS` freeze generated sources, scripts, exact copies, assets and patches. `static-validation.json` is a separate receipt for source-only validation, intentionally outside that source manifest to avoid self-reference. No Swift compile, runtime/UI/CI, publication, index, product, shared-harness, or historical archive edit is part of this preparation.
