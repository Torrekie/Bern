# Observed full Picture Scene: independent geometry gate

Verdict: `selected_13_png_files_exact_layout_125_147_preserved`.

All **13 original PNG files** from observed run40138440830 were read and compared byte-for-byte with unobserved control40135147500. Every pair is exact; thirteen is the file count, and both runs used macOS14.8.9. Full file hashes/sizes and input provenance are in `review.json`. No original image was copied.

The frozen `measured.py` SHA256 `05b74fd7cbeefdccdd953699e10c7c7e20570887f70a9959bd8411be1f76aae9` ran once to fresh `layout-measurements.json`, at actual scale1. Its unchanged ICC→sRGB conversion, 15 fixed ROIs, thresholds and27 x800 runs all match control and historical B14, without resampling. Layout PNG SHA256 is `dfe053e307e033d0a4e583a88d34a4b60f428318f63e1954a500f14bb2016780`; ICC SHA256 is `3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`.

The original complete PNG was viewed offline. Both first and HDR card edges are fully visible and unclipped. Whole-file identity to the control/old B14, the unchanged measurements, and complete-edge visibility support the same half-open card bounds `[161,98,900,223)` and `[161,321,900,468)`: **125pt /147pt**. The x800 border runs98..<99/222..<223 and321..<322/467..<468 support that interpretation; scanline fill plateaus are not full bounding boxes. No public native-card frame was obtained.

Metadata binds normal preferences (all three accessibility optionsfalse), en/en_US,920×668 outer points and pixels, scale1, same page-selection route, same decoded image-input metadata, and active own normal-level windows through the unchanged collector. Observed light PID1926/window28 and dark PID2239/window32 match the original application logs. Both runs have80 commands and18 passed checks. Only each appearance's initial `sessions` returned3; the immediate retry succeeded and all other78 commands returned0. Source/export/package/asset-file provenance is independently handled by root; this review checks reported source and original collector bytes, not a new binary or resource hash.

Layout retains the original0.8-second pause and **has no five-buffer stability gate**. Equality applies to these selected screenshots and conditions; it does not establish universal observer noninterference, native proposed sizes, physical-input behavior, flight/animation equivalence, HDR luminance/EDR equivalence, or macOS13 acceptance. Observer events were not interpreted. No UI, compile, CI, or new image algorithm was executed.

Reproduction command is recorded in `review.json`; run it only with a fresh output filename because the frozen adapter rejects overwrites. Original raw inputs and old analysis/archives were not modified.
