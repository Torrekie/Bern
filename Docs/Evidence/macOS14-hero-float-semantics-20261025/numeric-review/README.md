# Independent raw binary16 numeric review

The reported constant-patch result is confirmed. This reader uses its own fixed ten interior coordinates and `struct<4H` / `struct<4e` at every original pixel; it does not import or execute root's geometry, analyzer or comparator helpers. The40 flat interiors across13/14 named/custom are each constant over the complete region, finite and alpha exactly1 (`0x3c00`). All20 comparison rows, original RGBA words/values and all80 signed RGBA deltas match `constant-patch-comparison.json` exactly.

Named:10/10 RGBA-bit-identical patches. Custom:5/10 identical; the changed patches and nonzero13-minus14 RGB deltas are:

| Patch | Nonzero stored numeric delta |
| --- | --- |
| white812 | R=-0.001953125, G=-0.001953125 |
| red812 | B=0.000244140625 |
| green812 | R=0.0009765625 |
| blue812 | G=-0.000244140625 |
| pastel812 | R=-0.001953125 |

Custom maximum absolute RGB delta is0.001953125; the unweighted mean of all30 absolute RGB channel deltas (10 patches×3 channels, including zeros) is0.000244140625. Named maximum and mean are0. These are stored premultiplied extended-sRGB binary16 values under the independently reviewed lane/direction binding; they are not ICC-converted display codes or nits.

The four exported raw records are hash/length/stride/known-format locked and independently reread. Coordinates map exactly from the frozen640×360 atlas to640×360 on13 and320×180 on14; each flat region has11648/2912 original pixels. Every field of all44 native-resolution patch/ramp region statistics and all four whole-active-buffer statistics matches, including full bit-histogram hashes. The summary retains bounded native whole/ramp aggregates only. It does not pair cross-host ramp columns, resample, align, translate, normalize, clamp or unpremultiply.

`semantic-binding.json` hashes the earlier independent geometry/lane reviews and geometry result. Their saved times precede binding; binding precedes both known-extraction start times; receipt approval/analyzer hashes match, both processes exit0 and the comparator timestamp follows them. The current `extract-known.py` validates binding, geometry and review hashes before spawning either analyzer and requires fresh outputs. This verifies saved artifact/hash/UTC consistency plus current source ordering; it is not an independent attestation of historical process execution. The extraction wrapper's own hash was not recorded by its old execution receipt and is fingerprinted by this review now.

`summary.json` retains all20 rows and exact deltas, four raw aggregate confirmations and25 unique input fingerprints. Source direction/lane proofs are consumed from the separate frozen review; this task does not choose orientation or lanes from numeric/color similarity. No new experiment, UI, compile, CI, raw copy or product/source edit occurred. This evidence does not establish a visible residual's cause, unique OS/renderer causation, full-image equality, HDR brightness equivalence or UI/full-flight acceptance.

Reproduce offline from the workspace root into a fresh output directory:

```sh
python3 work/hero-snapshot-float-numeric-review/review.py work/hero-snapshot-float-geometry-compact work/hero-snapshot-float-numeric-replay
```

The script AST passed, then this independent reader ran once. It refuses an existing summary and bounds output at128KiB. All source inputs remain unchanged; no raw bytes are copied into this review directory.
