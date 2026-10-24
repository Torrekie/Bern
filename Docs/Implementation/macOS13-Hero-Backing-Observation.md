# Hero flight backing-format boundary — read-only audit

## Conclusion

`CALayer.contentsFormat = .RGBA16Float` is publicly available on macOS10.12+, so macOS13 has no API-availability blocker. It is a **desired storage-format hint for layer drawing**, not a promise of the actual NSView backing pixel format, a color-space conversion, or a tone-map/headroom selector. Apple explicitly says a layer-backed NSView may change this property for the device. A one-property candidate is meaningful only if the existing flight already has its own drawing layer and the requested value survives AppKit updates; neither condition is currently recorded. It cannot yet be called a fix or evidence that13 clipped before color conversion. [Apple contentsFormat](https://developer.apple.com/documentation/quartzcore/calayer/contentsformat)

## Exact path and ownership

- Product `crates/bern-backend-swiftui/templates/BernAppKit.swift:1921–1937`: `BernHeroFlightView` is an NSView; init only saves the two NSImages and calls super. `draw` clips rounded bounds, draws `from` with sourceOver/fraction1, then `to` with a clamped progress fraction. There is no contentsFormat, wantsLayer, custom layer, makeBackingLayer, updateLayer, or layer-delegate override.
- The actual manager constructs that same class at1972 and adds it under `BernHeroOverlay` at2017. Overlay/prepareOverlay at1915/1981 also do not explicitly enable layer backing. A false wantsLayer value alone does **not** prove absence of an inherited layer.
- The current float fixture's `Driver.swift.inc:264/292–294` keeps its two real static endpoint flight views in local `flights`, as direct children of FixtureRoot. FixtureRoot also overrides draw and does not explicitly enable layer backing. This is a different parent route from a live overlay flight; results stay limited to the existing static-endpoint scope.
- SDK14.2 `AppKit/NSView.h:244–262` says a layer-backed parent can provide descendant layers even when their wantsLayer flag is false, unless an ancestor draws subviews into its own layer. A draw-overriding NSView normally uses the drawRect path rather than updateLayer. The layer getter returns the associated optional backing layer; it does not expose a documented pixel-storage guarantee. [Apple NSView.layer](https://developer.apple.com/documentation/appkit/nsview/layer)

An AppKit-created layer stays AppKit-managed. Do not replace it, its delegate, or its hierarchy to make this hypothesis work. Apple's layer guide discourages changing view-managed layer properties directly; contentsFormat is not in its absolute forbidden geometry/filter list, but this is not assurance that AppKit will preserve the value. [Apple layer-management rules](https://developer.apple.com/library/archive/documentation/Cocoa/Conceptual/CoreAnimation_guide/CreatingBasicAnimations/CreatingBasicAnimations.html)

Local SDK14.2 evidence: `QuartzCore/CALayer.h:375–380` identifies the draw-layer storage hint and default RGBA8Uint, and says it does not directly change interpretation of layer.contents; lines928–931 expose RGBA8Uint/RGBA16Float on10.12. `layerWillDraw` at874–880 is a supported point for a layer delegate to configure contentsFormat, but the existing NSView owns that relationship: adding/swapping a delegate or draw callback would enlarge this experiment. The adjacent wantsExtendedDynamicRangeContent API at382–392 is macOS14-only, defaults false, and concerns display headroom; it must not be conflated with a float storage hint or added to this13 candidate.

## One next observation, before any candidate

Use the existing two local `flights` after the phase2 completion/cache/normal/front guards and **before** `report["success"]=true` (`Driver.swift.inc:344–353`). Both original PNGs are already saved, the views are still attached, and this scope still has the flight objects. Add a scalar-only dictionary per source key: attached/window identity; view class and wantsLayer/wantsUpdateLayer/canDrawSubviewsIntoLayer; optional layer presence/class/object identity, contentsFormat.rawValue, contentsScale and delegate class/identity-to-view; and the corresponding root/parent flags needed to identify ancestor flattening. Record the stage as post-PNG/pre-existing-teardown. Do not read contents, presentation layer, bitmap/provider, NSImage representations again, or force display/layout/flush; do not set wantsLayer or manufacture a layer. No image or layer reference should be stored in the report. Getter work is not assumed to have zero observer effect, even though it cannot retroactively change already-saved PNG bytes.

This answers whether the existing-layer premise is valid and what hint AppKit reports on each OS. It does **not** reveal actual storage or prove the value held during the preceding draw. If no own layer exists, stop the one-property candidate: enabling wantsLayer would introduce a separate compositing path. If the hint is already RGBA16Float, repeating the setter has no clear discriminating value. Only an existing, observed non-float drawing layer supports a later isolated request for RGBA16Float before the original first draw, followed by readback after the unchanged captures to check persistence. A changed PNG would show that this request affects the endpoint path; unchanged output or an overwritten hint would not locate the loss. No expected pass, clipping stage, tone-mapper identity, actual-flight acceptance, or physical-HDR inference follows from current evidence.

Prepared by source/header/primary-document inspection only. No code changes outside this work note, compilation, UI, CI, product/index/archive edit, or new broad API experiment.


## Container scope to record alongside layer hints

The current endpoint fixture places its two manually controlled flight views under
FixtureRoot, while a real coordinator inserts them under its BernHeroOverlay in
the window content-view parent. This source fact does not establish that either
route has a layer or that the container caused the retained color difference.
The next read-only observation must include both current flight/root ancestry
and the already-existing actual manager overlay ancestry. A later container
comparison would need explicit coordinate conversion, same native window ROIs
and a default control before any conclusion about the live overlay path.
The current endpoint results do not prove that a full application flight has the
same color defect. No container mutation or backing-format setter has run yet.
