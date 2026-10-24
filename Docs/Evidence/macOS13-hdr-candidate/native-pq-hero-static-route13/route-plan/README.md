# One bounded static endpoint comparison through the actual overlay

This is a conditional work-only plan, not an implementation or a cause assignment. Wait for the pending post-PNG layer/container observations. If they show a meaningful parent/backing-route distinction, compare only the manual static flight parent: existing FixtureRoot versus the **existing actual manager.overlay**, using fresh processes and the unchanged two source snapshots, NSImages, BernHeroFlightView.draw, fixed p0/p1, screen ROIs, normal/front/cache/stability/deadline gates. Do not add a layer, change contentsFormat, or combine another candidate.

## Source basis

Product `crates/bern-backend-swiftui/templates/BernAppKit.swift`:

- `BernWindowImageHeroes.forWindow`1943–1948 owns one manager per window. Its private overlay is1951. `prepareOverlay`1981–1989 inserts that actual overlay above `window.contentView.superview` (fallback contentView), with the parent's bounds and autoresizing; do not reconstruct or resize it in the fixture.
- `BernPictureHeroAnchor.snapshot`1848–1864 already converts its bounds into this overlay, builds the real ImageRenderer snapshot and wraps its actual CGImage in NSImage. Existing driver `fixtureSnapshot`123–127 already calls prepareOverlay before snapshotting: no second snapshot or new overlay is needed.
- Actual `Flight.init`1969–1974 creates the same BernHeroFlightView and uses overlay-space rectangles. Actual `enter`2011–2023 adds that view directly to overlay but also changes visibility, populates manager.flights and starts its120Hz timer. Those side effects are excluded from this static route comparison.
- Existing fixture driver292–294 instead creates the same flight manually and adds it to FixtureRoot. `flights` and `regions` retain the exact two views; existing ROI calculation309–318 calls each view's convert(bounds,to:root), which also works for a same-window sibling subtree.

## Single route change and coordinate gate

Expose only a fixture-local same-file manager helper that mounts an already-created manual view into its private **existing** overlay. It must verify the original window/overlay attachment and prepareOverlay result, without calling enter/leave/finish, editing entries/departed/flights/timer, invoking visibility, or changing anchor IDs/live bindings.

For each original desired bottom-row rectangle D in FixtureRoot coordinates (the existing xs/bottomY/320×180), compute **O = overlay.convert(D, from: root)**; set manualFlight.frame=O and add that flight to overlay. Keep the original p.image, corner, from/to identity and progress handling. Do not assign p.rect to this bottom pane: p.rect is the source anchor's top-row rectangle. Do not manually invert y or subtract title-bar heights; root and overlay may have different parent origins even though both are flipped.

Immediately verify same window, exact expected parent, bounds320×180, and conversion back **flight.convert(flight.bounds,to:root)==D** within floating-point tolerance, followed by equality of the existing window/screenshot ROI with the control. Record O, D, back-converted rectangle and route identity. A root-descendants walk no longer contains overlay flights, so independently inspect the retained two manual views and their subtree for the existing no-Metal requirement rather than silently treating the old root walk as complete. Preserve the two actual anchors under root and manager flight_count0/timer_exists=false throughout. Do not reorder the root siblings or mount duplicate copies.

Read only final scalar route/layer descriptors after both PNGs, before teardown. Retain no view/layer in JSON. Cleanup should remove only the two fixture-owned manual overlay subviews as part of the post-PNG teardown; never call manager.finish for these unregistered views or change a visibility callback. Preserve the original window close/cache/normal/front cleanup. If mount/conversion/state gates fail, retain failure evidence and stop; no fallback route or pixel offset adjustment.

## What this would and would not establish

A controlled PNG difference would show that parenting the same static native draw under the actual overlay changes its endpoint output; it would not prove a specific color conversion, backing format, clipping cause, or that live animation is corrected. Matching endpoints would likewise not validate moving/resizing/cross-fading, automatic entry/detachment, retargeting, timed retirement or hidden-content restoration. Do not assume either route has a layer before observation.

The smallest later **actual enter/leave** gate is one real same-key source→destination SwiftUI replacement at distinct rectangles in one owned window, using actual BernImage/BernPictureHero/Probe and their normal update/dismantle callbacks (Probe1784–1796, schedule1824–1839, detach1842–1845). Let actual leave retain the departure and the destination enter consume it inside the source's0.3s window (1997–2000/2033–2050); do not manually call enter or visibility. Require an observed registered flight/timer and overlay parent during the transition, a real frame/progress change, then actual tick/finish returning flight_count0/timer_exists=false, removing the temporary flight and restoring destination visibility (2059–2065/2067–2098). Require no stranded hidden source/destination after window cleanup. That is one lifecycle transition, not retarget/reversal/reduced-motion/abandonment coverage, and its intermediate pixels need a separate time-aware comparison rather than the static5-identical-buffer endpoint gate.

Prepared by current source inspection only. No code implementation, new API research, compilation, UI, CI, product/harness/archive/index modification or child agent.
