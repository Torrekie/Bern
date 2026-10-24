# Actual picture-hero snapshot baseline

This is the unchanged product image/hero chain at
`b08db54e01ac2ec54fb84e6f2a70041f1f4c3604`, whose extracted product blocks
are identical to `9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0`.
The exact blocks, imports, source hashes, original successful13 driver and its
small expected-OS patch are retained. New SDK builds compile the original
gain-map availability branch; the old SDK14 diagnostic guard is absent.

Two actual `BernImage` views have distinct hero keys. Their real anchors and
real snapshot method feed manually mounted, unmodified `BernHeroFlightView`
instances at progress0 and1. Each instance uses the same opaque snapshot at
both endpoints. The coordinator must have no flight and no timer. This tests
static snapshot/draw endpoints, not an actual coordinated flight or lifecycle.
No image equality result is used to make collection succeed.

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
