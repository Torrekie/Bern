# AppKit-loop coordinator original pixel analysis — prepared only

No analysis or CI polling has run. `analyze.py` reuses the frozen delayed-observer analyzer and adds a read-only extraction/check of the new `execution_model`. It reads original reports/PNGs only and writes one fresh numeric JSON; it refuses an existing output. No PNG copying, rewriting, derived images, registration, fitting or resampling.

Per OS13/14: new before/source→settled/destination and old→new before/source plus settled/destination controls. All endpoint comparisons require integral measured screenshot-pixel ROIs, equal raster sizes and alpha255. Raw RGB and embedded-ICC→sRGB perceptual intent0/flags0 comparisons report MAE, maximum difference, exactness and profile hashes. No cross-host asynchronous mid equality is tested. The new six PNGs, old four endpoint PNGs and four reports are hashed when present.

Midflight reports only fixed12pt root-edge-inset opaque nonwhite bounds. The actual before source root-point→screenshot conversion establishes scale/origin; no logical flight frame is treated as a pixel ROI. White cells can be omitted from these content bounds. Full armed/capture states, indices, progress, uptimes and actual CG capture state/time brackets remain separate; they do not identify a rendered frame or prove synchronization/cause. Execution fields are preserved verbatim even if their separate contract check is not_performed. `sampler_invalidated_before_stop` is a source-path flag, not an independent Timer.isValid observation. Partial/failed acquisition, missing phases or failed ROI/timing/execution gates yield explicit not_performed components; no missing values are fabricated.

Only after root confirms data readiness, run once from the workspace:

```sh
python3 -B work/hero-coordinator-app-pixel-analysis/analyze.py \
  --new-root work/native-pq-hero-coordinator-app-ci-40110795231 \
  --old-root outputs/Bern/Docs/Evidence/macOS14-hero-coordinator-delay-40107406624/same-binary-13-14 \
  --output work/hero-coordinator-app-pixel-analysis/summary.json
```

The old archived PNGs remain in place. This script performs no acquisition, UI, compilation, CI or product/repository edit. It does not declare color/animation acceptance from collection success.
