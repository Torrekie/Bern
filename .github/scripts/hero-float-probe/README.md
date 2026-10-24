# Actual original hero float capture (diagnostic)

This uses the actual BernImage/cache/hero snapshot and native Flight.draw chain,
not an identity hero. Product blocks originate at b08db54, with the extracted
image/hero blocks identical to9dd. The default ImageRenderer/colorMode/NSImage
construction, draw, static fixed progress0/1 and six native panes remain.
This is a static opaque/up atlas diagnostic, not flight/lifecycle/app parity.

The original v2 metadata observer still records scalar/CGColorSpace references;
ICC classification/export occurs after PNGs and original window teardown.
A separate process-cached BERN_HERO_FLOAT_CAPTURE=off|on defaults off. Off holds
no CGImage and does not read snapshot provider data. On retains only the two
actual primary renderer-return CGImages; freeze precedes original teardown,
and cleanup snapshots are counted without retaining images. No second renderer
image, NSImage.cgImage/TIFF, recache, redraw, color conversion or relabel occurs.

After all PNGs and original teardown, on copies each original provider exactly
once, requires known16-float/RGBA64/16Little/premultipliedLast layout and exact
rowbytes*height, writes complete raw.bin/SHA with a4MiB total limit, and releases
fixture image references. Unknown/nil/length errors fail report/process without
conversion fallback. Float row direction remains unverified. Formats/profiles
and >1 values do not by themselves identify a semantic patch or a unique cause.

Retaining images changes lifetime; delayed provider reads may do internal work.
LocalSDK14.2 min13 controls first reproduced the v2 baseline and off/on12 raw+
ICC-normalized ROIs exactly. This observation is not a zero-effect guarantee.
CI builds once with SDK26.2/min13, preserving original new-SDK image/hero source
without the two localSDK14 diagnostic guards, then collects fresh off/on14
processes. CI success means acquisition/schema gates passed; pixel controls
remain a separate offline check. The same exact signed binary must also run13.

Each window retains its original7.9s bound and stable5/normal/front/nonkey/cache/
noMTKView/noFlight/noTimer gates; run-one.py has a15s outer process bound covering
post-teardown export. Disposable14 preferences are set normal. The probe changes
no preferences or permissions and does not activate. Native WindowServer PNGs,
raw payloads and ICC are retained for offline inspection. No image-equality
collection gate or color curve is introduced.
