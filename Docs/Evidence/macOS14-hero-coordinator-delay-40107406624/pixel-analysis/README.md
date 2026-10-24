# Delayed-observer original pixel analysis

`analyze.py` reads the new delayed same-binary13/14 runtime directories and the old frozen coordinator archive. It writes one fresh numeric JSON, never copies or rewrites PNGs or creates derived images. ICC normalization uses original embedded profiles, perceptual intent0, sRGB, flags0, matching the prior two pixel-analysis scripts.

Per OS: compare new before/source against new settled/destination; compare old→new before/source and old→new settled/destination. Require same-sized integral **measured screenshot pixel** ROIs and alpha255; report raw/normalized MAE,max,exact and ICC hashes. Midflight uses only a fixed12pt inset of all root edges, anchored from the actual before source root-point→screenshot-pixel conversion. It excludes transparent/rounded corners; nonwhite bounds are content descriptions, not complete flight bounds or fitted registration. Never crop a native logical flight rect as if it were a pixel ROI.

The result preserves full armed/capture samples, separate indices/progress/uptimes, actual CG state/time brackets and native ROI. Only arm must be in0.2..0.8; different-time13/14 mid pixels are never tested for equality. Partial/missing captures, opacity/ROI failures or missing timing protocol produce explicit not_performed components. Acquisition and visible/color/animation acceptance are separate.

Run once on root's readiness notice, from the workspace:

```sh
python3 -B work/hero-coordinator-delay-pixel-analysis/analyze.py \
  --new-root work/native-pq-hero-coordinator-delay-ci-40107406624 \
  --old-root outputs/Bern/Docs/Evidence/macOS14-hero-coordinator-40103369574/same-binary-13-14 \
  --output work/hero-coordinator-delay-pixel-analysis/summary.json
```

Old PNGs remain in their archive. New six PNGs, related old four endpoint PNGs and four reports are hashed when present. No new acquisition, UI, compile, CI, registration, color fitting or resampling is part of this analysis.
