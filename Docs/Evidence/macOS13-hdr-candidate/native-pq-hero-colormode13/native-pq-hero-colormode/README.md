# Actual hero snapshot: public colorMode diagnostic fixture

Prepared only. No Swift compilation/typecheck, UI, CI, product edit or baseline-archive edit has run here. This is a single-mode experiment input, not a product fix or four-mode matrix.

Static checks passed: all inherited inputs match the successful archived build fingerprint; removing only the documented configuration/report/invalid-mode guard and optional setter restores the full archived ProductHero.swift byte for byte. Python AST parsing and bash -n passed. No executable or module cache was created. `static-validation.json` records these checks; they do not establish Swift compilation or runtime behavior.

## Precise source boundary

The sources and same-file driver are copied from `outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-baseline13` and verified against its successful build fingerprint. Actual BernImage/body/cache, Style/modifier, complete real AppKit hero manager, snapshot and FlightView.draw are retained. The base extraction is pinned to b08db54; the image/hero slices equal 9dd. No selectedDisplayImage candidate is applied: both named/custom hero inputs remain the original Picture image.

`color-mode-snapshot.patch` adds only an optional assignment to public `renderer.colorMode`, after the existing renderer creation/scale and before its existing cgImage read. `color-mode-driver.patch` adds the process-cached environment choice, three report fields, and a prewindow invalid-config failure. It changes no body, fit, orientation, resizing, NSImage.draw, view, window, collection timing, stable-buffer, normal-profile, foreground, no-Metal/no-coordinator-timer, capture or cache gate.

`BERN_HERO_COLOR_MODE` is read once per process and supports `default`, `linear`, `extendedLinear`, `nonLinear`. Unset/default performs **no setter**; explicit nonLinear must not be assumed equal to an unset property before measuring. Unknown values fail before UI. The report records the raw requested value, selected mode, and whether an assignment was requested. These are configuration records, not a readback of the ImageRenderer's internal/default format or transfer function.

The SDK14.2 public arm64e SwiftUI interface exposes MainActor ImageRenderer.colorMode (ImageRenderer available from macOS13), and ColorRenderingMode has all three public cases. Its exact interface path/hash are recorded in provenance. No private API or color formula is used.

The old successful SDK14 adaptations remain byte-identical: compiler condition excludes only the unavailable macOS15 gain-map decode branch on the local Swift5 compiler; the unused coordinator timer has its documented availability/compiler failguard. The full coordinator remains present, but it must have flight_count0/timer_exists=false. This is static snapshot/draw endpoint evidence, not true animation or lifecycle acceptance. The optional setter adds source/branch work even in default mode, so default control must run before interpreting an extendedLinear comparison.

## Build and coordinated future runs

Source preparation is already complete. `build.sh` first checks the source hashes, records environment, then uses the baseline flags: optimized Swift5, two jobs, arm64/min13. Its fingerprint records source/executable/signature and compiler warnings remain in build.log. The build script does not launch the executable.

Root may build with:

```sh
bash work/native-pq-hero-colormode/build.sh
```

Only after the controlled UI slot is granted, use a new output path for each independently chosen run. First default control; extendedLinear is a separate later process:

```sh
BERN_HERO_COLOR_MODE=default python3 -B work/native-pq-hero-colormode/run.py work/native-pq-hero-colormode/runtime13-default-control
BERN_HERO_COLOR_MODE=extendedLinear python3 -B work/native-pq-hero-colormode/run.py work/native-pq-hero-colormode/runtime13-extendedLinear
```

The commands above are documented, not executed. Do not execute them as an automatic sequence. Add linear only if the first results support that next step. `run.py` launches exactly one process, validates the same two SHA-locked existing atlas files and compiled-binary fingerprint, and retains the original15-second wrapper bound. The original driver still requires actual13/existing screen permission/normal flags, never activates, uses one nonkey own window, collection7.2s/window watchdog7.9s, five equal raw buffers per progress0/1, no image-equality acceptance gate, and unchanged cache/frontmost checks. The runtime report and original ICC PNGs go to that unique output directory.

Default control must reproduce the archived six-ROI geometry and old colors before attributing any mode difference. Compare body and actual NSImage.draw endpoints on the same host and preserve raw/ICC-normalized values separately. Public representation metadata does not expose the renderer's original CGImage color metadata. No14 parity, gain-map/HLG/alpha/orientation expansion or color-mapper claim follows from this fixture.
