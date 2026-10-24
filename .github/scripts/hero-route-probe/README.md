# Actual existing-overlay static-route comparison

This standalone diagnostic preserves the preceding hero-float/backing harness
unchanged. It uses their original newSDK ProductImage/Hero base, actual cache,
BernImage, Anchor.snapshot, NSImage and Flight.draw. It changes only the parent
of the two manual same-image static p0/p1 flights: FixtureRoot(default) versus
the actual manager overlay already prepared by fixtureSnapshot. It never calls
enter/leave/finish, changes manager maps/timer/visibility/bindings, creates a
layer, requests a contentsFormat, converts/relabels images or captures raw data.

Process-cached BERN_HERO_STATIC_ROUTE=root|overlay defaults root. This fixture
requires both BERN_HERO_LAYER_OBSERVE and BERN_HERO_FLOAT_CAPTURE selected off
before a window is created. That requirement is why it has its own directory;
the original float/backing workflows and their opt-in modes remain available.

Overlay mounting uses overlay.convert(originalDesiredRootRect,from:root), not
the source anchor rect or manual titlebar/y adjustments. Both retained flights
are checked after mount, before every original capture sample and after PNGs:
selected parent/same window/320x180 bounds, public roundtrip <=1e-6pt and their
entire subtrees contain no MTKView. Their original public ROI calculation is
unchanged. The root-only descendant check is still kept for original content.
After original orderOut, only fixture-owned overlay flights are removed before
original contentnil/close; unregistered views never call manager.finish.

The normal/cache/front/non-key/inactive/noManagerFlight/noTimer/stable5 and
7.9second window /15second process bounds remain. CI builds arm64/min13 once
with SDK26.2 and executes fresh root/overlay14 processes. CI success means
acquisition/schema only; separate rawRGB+ICC-normalized controls against old
root and between routes are required on both14 and13 using the same original
signed binary. No fixed overlay offset or expected pixel equality is asserted
during acquisition. Local SDK14.2 controls already found all12 ROIs exact for
old→root and root→overlay; that observation does not accept another host.

Static same-opaque-image endpoints do not validate live coordinator motion,
interpolation, retargeting, hiding/restoration, physical HDR or whole-app parity.
The before-static-route source/provenance and patch preserve the exact delta.
