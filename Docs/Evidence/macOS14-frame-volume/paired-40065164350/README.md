# Gallery Frame A/B on macOS 14

[Run 40065164350](https://github.com/Torrekie/Bern/actions/runs/40065164350) succeeded using the same macOS 14.8.9 ARM64 runner, Apple Virtual 1× display, light appearance and normal motion/transparency/contrast. The observer did not rebuild or inject code into either app.

- **A:** original upstream `ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee`, locked Gallery build 39959549054.
- **B:** port `f9e08b1d55bed4b9d880b19934abe48281057bb3`, locked Gallery build 39991406873, running its macOS 14 native path.

## Result

The Frame detail region and video are pixel-identical in both closed/open captures. The isolated volume popover is **PNG-file-byte-identical**, including ICC, at 266×106 pixels. All recorded native Clip/Volume/slider geometry and popup bounds agree exactly.

| Original PNG pair | Whole-image changed pixels | Frame detail changed pixels | Note |
|---|---:|---:|---|
| `frame-closed-light.png` | 5,284 / 614,560 (0.859802%) | 0 | All differences in sidebar selected row |
| `frame-open-light.png` | 5,284 / 614,560 (0.859802%) | 0 | Real main + independent popover WindowServer composite |
| `volume-popover-light.png` | 0 / 28,196 | 0 | Full encoded PNG files identical |

The main-window difference is limited to `[10,108,200,136)` pixels: the sidebar Frame selected row is gray in A and blue in B. No alignment, recoloring or suppression was applied to the whole-image results. The 709×616 detail ROI is `[211,52,920,668)`; video ROI is `[251,167,880,521)`. Raw RGBA and ICC-to-sRGB comparisons identify the same changed-pixel set. All six PNGs retain the same original ICC SHA256 `3d40c076ef474f107eb2c08fa5cebe2546e836500f4029ded5db7de763eb5f55`.

The capture enforces each target app as frontmost. The early CLI window listing reports window focus before Frame selection; it does not observe capture-time firstResponder or `AXFocused`. Those fields were not collected, so the sidebar difference is retained without assigning its cause.

## Geometry and interactions

Coordinates below are points relative to the normalized 920×668 main outer frame.

| Element | x | y | width | height |
|---|---:|---:|---:|---:|
| Volume AXButton | 619 | 536 | 22 | 15 |
| Clip AXUnknown | 251 | 167 | 629 | 354 |
| Popup window | 497 | 553 | 266 | 106 |
| Volume AXSlider | 579 | 610 | 155 | 20 |

Both apps pass source identity/version, Ready → play/pause/seek → Paused at 0 ms, the >=3.2-second awake loop, genuine AXPress open/close, popup control mount/unmount, and four consecutive identical WindowServer buffer comparisons. A uses 16 exact raw-window-ID/owner round trips and B uses 15. Each open composite contains precisely its main and independent popup window; standalone popup capture uses only that popup. For each app, all 19,174 fully opaque pixels of the standalone popup exactly match the corresponding pixels in the main-plus-popup composite, independently confirming that the composite includes the popup. Both pass final visual dismissal (popup no longer drawn). The bundled `tides.mp4` bytes are identical.

Native AX identifiers for Clip and Volume are inherited as `main_window.find` in these upstream/14 view hierarchies. The bounded observer records requested CLI identity separately and selects the unique same-parent content Clip/Volume pair by real labels, role/actions and own-window scope. This neither fixes nor hides that native identifier mismatch. Native slider retains `frame.volume_level`. AX geometry is not proof of a Cocoa view class.

## Reproduction and limits

`a/` and `b/` contain all original PNGs, CLI outputs, runtime/build provenance and reports. `harness/` preserves the exact observer (SHA recorded in `provenance.json`) and workflow. Run `python3 compare.py` with NumPy/Pillow to regenerate `comparison.json` entirely offline. `SHA256SUMS` covers this evidence except itself.

This establishes the stated **macOS 14 light Frame/popover** preservation. It does not establish whole-main-window pixel identity, macOS 13 visual equivalence, physical mouse/keyboard delivery, continuous video playback/audio, dark appearance or HDR. No additional CI or local UI run was used for the offline analysis.
