# Actual picture-hero snapshot baseline

This retains exact source copies of the product image/hero chain at
`b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`, whose extracted product blocks
are identical to `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`.
The exact blocks, imports, source hashes, original successful13 driver and its
small expected-OS patch are retained. The pre-observer shared driver and hero
base are also retained, with the precise `observer.patch`. New SDK builds compile the original
gain-map availability branch; the old SDK14 diagnostic guard is absent.

Two actual `BernImage` views have distinct hero keys. Their real anchors and
real snapshot method feed manually mounted, unmodified `BernHeroFlightView`
instances at progress0 and1. Each instance uses the same opaque snapshot at
both endpoints. The coordinator must have no flight and no timer. This tests
static snapshot/draw endpoints, not an actual coordinated flight or lifecycle.
No image equality result is used to make collection succeed.

The compiled hero base now has one fixture-only observation call immediately
after the actual `renderer.cgImage` succeeds. It reads image scalar format
descriptors and retains only the CGColorSpace reference. After all retained
PNGs and the original window teardown, it classifies that space and exports
an ICC-profile hash. From the same single
profile copy it retains complete profile base64 only when at most64KiB;
larger profiles retain SHA/length and an explicit omission reason, without
truncation. No second profile copy is requested. It never reads that
image's pixel provider, converts/relabels/copies the image, recaches NSImage,
retains an image in the report, or requests a second renderer image. The
default renderer colorMode is left untouched. Exact product copies remain
unmodified; `product_source_adaptations` explicitly identifies the observation
hook in the compiled base. A metadata query/profile copy can allocate or
materialize internal metadata caches, and hashing/base64 take CPU time: this is not
a claim of zero observer effect. In one localSDK14/min13 control, all12 raw and ICC-normalized regions exactly
matched the original13 baseline. The two localSDK14 diagnostic compile guards
are retained with that control and are absent from this new-SDK package.
Profile export and classification happen after measured rendering/capture work.

The primary descriptor list is frozen immediately before the existing
window teardown, with its scope recorded as `before_existing_window_teardown`;
the full metadata values are serialized only after teardown.
The runtime gate requires the two actual measurement keys, without inferring
any default pixel format or color space. Teardown can itself call the real
snapshot method: all later records are separately retained in
`snapshot_cgimage_cleanup_observations`, whose count is not required to be0.
The original teardown order and all acquisition actions remain unchanged.

The manual workflow builds once on macOS15/Xcode26.3, Swift5 mode, ARM64/min13,
then runs that exact signed binary on14. The package includes all source,
the two SHA-locked atlas files, build environment, signature and manifest.
The disposable14 runner sets the three normal accessibility flags to false.
The driver itself changes no preferences, requests no permissions, never
activates, and requires its window to remain nonkey/inactive with the original
frontmost process. Capture is only through the actual WindowServer window ID.

After verifying/extracting the packaged tar, the same binary can run on13:

```sh
bash /absolute/path/to/probe/run-runtime13.sh /absolute/path/to/new-output
```

The output directory must not exist. Existing screen-capture permission and
normal accessibility flags are required; failure does not prompt or alter TCC.
The collection loop is bounded at7.2 seconds with a7.9-second window watchdog,
in addition to a maximum10-second source preload. Keep the raw PNGs and ICC;
cross-OS color/ROI comparisons remain a separate offline step.

The initial build40080291082 succeeded; its first14 job stopped before launching
the executable because an optional raw defaults lookup was treated as fatal.
The runtime-only workflow pins that same tar and signed binary by SHA256 and
does not rebuild. Missing raw keys remain in the log; actual NSWorkspace normal
flags are still mandatory before and after acquisition.
That fixed historical workflow/package and all prior13/14 evidence are
unchanged by this observer preparation; the shared default build is now the
explicitly instrumented fixture described above.
