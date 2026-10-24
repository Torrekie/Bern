# Private backing-observer CI draft

This directory prepares a manual CI workflow and wrapper from committed float-probe inputs at `a2d8e3323a742ea881e91c73f480ae32913542e4`. This agent has not installed repository files, published, dispatched CI, compiled or run the native application. Root independently produced the existing local13 reports used below.

## Files for root review

- `macos14-hero-backing-probe.yml` → `.github/workflows/macos14-hero-backing-probe.yml`.
- `run-backing-one.py` → `.github/scripts/hero-float-probe/run-backing-one.py`.
- Root must inline the reviewed backing helper into `Driver.swift.inc` and update the existing `source-provenance.json` file hashes, including the wrapper. The build rejects an absent/unregistered wrapper. The float package path, `HeroFloatProbe`, original source kind/provenance fields and three-source concatenation remain.
- `workflow.diff` and `wrapper.diff` compare against the pinned originals kept here. `BackingObservation.schema-source.swift.inc` records the exact helper schema used for the report gate; it is not an additional build input.

The workflow builds once with SDK26.2/min13, then launches independent off/on processes on14 using the same binary. Separate backing artifact, tar and concurrency names avoid mixing float cohorts. The wrapper keeps the six arguments and 15-second child wait/kill bound:

```sh
python3 run-backing-one.py BINARY NAMED_PNG CUSTOM_PNG OUTPUT_DIR off 13
python3 run-backing-one.py BINARY NAMED_PNG CUSTOM_PNG OUTPUT_DIR on 14
```

Both modes force `BERN_HERO_FLOAT_CAPTURE=off`; `BERN_HERO_LAYER_OBSERVE` receives the requested mode. No added preferences, permissions, focus, theme or layer actions occur in the wrapper. Normalization of the disposable CI runner remains inherited from the original workflow.

## Acquisition gates

The original normal/cache/front/identity/5-stable-buffer and deferred metadata-v2 gates remain. The draft additionally requires zero activation calls, exact before/after cache dictionaries and `0 < window_seconds < 7.9`. Both modes require successful float-off observations with no raw records/bytes, provider copies or retained-image peak.

Backing-off requires success with empty records and null root/overlay. Backing-on requires two distinct flight roles, same captured window, complete bounded ancestor chains, immediate fixture-root identity and scalar field types. Each flight's 320×180 rect must equal the same-role ROI in both captures. Layer presence, class, contentsFormat and delegate identity values are recorded without predetermined outcomes. Ancestors may be read multiple times across separate tree calls; there is no global deduplication guarantee. Public scalar hints do not establish pixel storage or cause.

CI success would mean acquisition gates passed. Offline same-binary controls and interpretation remain root's responsibility; this draft does not assert visual equivalence, zero observer effect, flight lifecycle parity or a systemic cause.

## Validation performed

`validate_draft.py` parsed YAML, the wrapper and four embedded Python blocks, and passed `bash -n` for both shell bodies. Shell bodies were not executed. `validate_local13_schema.py` applied the identical report gate to root's existing local13 off/on reports after exactly four literal path/expected-OS substitutions; both passed. This offline check reads existing JSON/receipts, counts PNG files and hashes the existing binary, without decoding PNG pixels or launching anything.

Results and input hashes are in `static-validation.json`, `local13-schema-validation.json` and `provenance.json`. No new dependency was installed. `SHA256SUMS` freezes this private preparation.
