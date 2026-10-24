from pathlib import Path
import shutil, json, hashlib, difflib
R=Path.cwd(); B=R/'work/native-pq-hero-float-capture'; D=R/'work/native-pq-hero-backing-observer'
D.mkdir(exist_ok=False)
for name in ['Dependencies.swift','ProductImage.swift','ProductImage.exact.swift','ProductImage.v2.base.swift','ProductStyle.swift','ProductStyle.exact.swift','ProductHero.clock-adapted.swift','ProductHero.exact.swift','ProductHero.v2.base.swift','FloatCapture.swift.inc','sdk14-unreachable-gainmap.patch','local-sdk14-clock.patch','local-image-imports-and-sdk14.patch','fingerprint.py','build.sh']:
    shutil.copy2(B/name,D/name)
shutil.copytree(B/'assets',D/'assets')
base=(B/'Driver.swift.inc').read_text(); (D/'Driver.before-backing.swift.inc').write_text(base)
helper=r'''
// Fixture-only, process-cached, scalar observation after PNGs/final guards.
// No contents/presentation/provider reads, layout/display, or layer/view setters.
private enum FixtureBackingMode {
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_LAYER_OBSERVE"]
    static let selected: String? = {
        guard let value = requested else { return "off" }
        return ["off", "on"].contains(value) ? value : nil
    }()
}
extension BernWindowImageHeroes {
    // Read the overlay already prepared by fixtureSnapshot; never prepare it here.
    fileprivate var fixtureExistingOverlay: NSView { overlay }
}
@MainActor private enum FixtureBackingObservation {
    static func initial() -> [String: Any] {
        ["requested": FixtureBackingMode.requested.map { $0 as Any } ?? NSNull(),
         "selected": FixtureBackingMode.selected.map { $0 as Any } ?? NSNull(),
         "stage": "post_png_post_final_guards_pre_teardown", "success": false,
         "error": NSNull(), "records": [], "root": NSNull(), "overlay": NSNull()]
    }
    private static func node(_ view: NSView) -> [String: Any] {
        // Each optional layer getter is performed once, only in selected=on.
        let wantsLayer = view.wantsLayer
        let layer = view.layer
        var layerRecord: [String: Any] = ["present": layer != nil]
        if let layer = layer {
            let delegate = layer.delegate
            layerRecord["object_id"] = String(describing: ObjectIdentifier(layer))
            layerRecord["class"] = NSStringFromClass(type(of: layer))
            layerRecord["contents_format"] = layer.contentsFormat.rawValue
            layerRecord["contents_scale"] = layer.contentsScale
            layerRecord["delegate_class"] = delegate.map { NSStringFromClass(type(of: $0)) as Any } ?? NSNull()
            layerRecord["delegate_is_view"] = (delegate as AnyObject?) === view
        }
        return ["object_id": String(describing: ObjectIdentifier(view)),
                "class": NSStringFromClass(type(of: view)),
                "window_number": view.window.map { $0.windowNumber as Any } ?? NSNull(),
                "frame": fixtureRect(view.frame), "bounds": fixtureRect(view.bounds),
                "is_flipped": view.isFlipped, "wants_layer": wantsLayer,
                "wants_update_layer": view.wantsUpdateLayer,
                "can_draw_subviews_into_layer": view.canDrawSubviewsIntoLayer,
                "layer_contents_redraw_policy": view.layerContentsRedrawPolicy.rawValue,
                "layer_contents_placement": view.layerContentsPlacement.rawValue,
                "layer": layerRecord]
    }
    private static func tree(_ view: NSView) throws -> [String: Any] {
        let first = node(view)
        var ancestors: [[String: Any]] = []
        var parent = view.superview
        var seen = Set<ObjectIdentifier>([ObjectIdentifier(view)])
        while let current = parent {
            guard ancestors.count < 16, seen.insert(ObjectIdentifier(current)).inserted else {
                throw FixtureFailure(message: "Backing observer ancestor bound/cycle; incomplete metadata")
            }
            ancestors.append(node(current)); parent = current.superview
        }
        return ["view": first, "ancestors": ancestors, "ancestor_chain_complete": true]
    }
    static func finish(_ flights: [BernHeroFlightView], root: NSView,
                       manager: BernWindowImageHeroes, window: NSWindow) throws -> [String: Any] {
        var report = initial()
        guard let mode = FixtureBackingMode.selected else {
            throw FixtureFailure(message: "Invalid BERN_HERO_LAYER_OBSERVE")
        }
        // Off does not query a new view/layer/ancestor property.
        guard mode == "on" else { report["success"] = true; return report }
        let overlay = manager.fixtureExistingOverlay
        let expectedParent = window.contentView?.superview ?? window.contentView
        guard flights.count == 2, root.window === window, overlay.window === window,
              expectedParent != nil, overlay.superview === expectedParent,
              flights.allSatisfy({ $0.window === window && $0.superview === root &&
                  $0.bounds.size == CGSize(width: 320, height: 180) }) else {
            throw FixtureFailure(message: "Backing observer expected two root flights/root/existing actual overlay in same window")
        }
        var records: [[String: Any]] = []
        for (i, flight) in flights.enumerated() {
            var record = try tree(flight)
            record["role"] = i == 0 ? "flight-named" : "flight-custom"
            record["parent_is_fixture_root"] = true
            record["rect_in_fixture_root"] = fixtureRect(flight.convert(flight.bounds, to: root))
            records.append(record)
        }
        report["records"] = records; report["root"] = try tree(root)
        report["overlay"] = try tree(overlay)
        report["overlay_parent_is_window_content_superview_or_content"] = true
        report["expected_window_number"] = window.windowNumber
        report["success"] = true
        return report
    }
}
'''
(D/'BackingObservation.swift.inc').write_text(helper)
needle='        defer {\n            FixtureSnapshotFloatCapture.freezePrimary()'
assert base.count(needle)==1
base=base.replace(needle,'        report["backing_observation"] = FixtureBackingObservation.initial()\n'+needle)
needle='            guard FixtureFloatCaptureMode.selected != nil else {'
assert base.count(needle)==1
base=base.replace(needle,'            guard FixtureBackingMode.selected != nil else {\n                throw FixtureFailure(message: "Invalid BERN_HERO_LAYER_OBSERVE; off/on required before window creation")\n            }\n'+needle)
needle='            report["success"] = true; return 0'
assert base.count(needle)==1
base=base.replace(needle,'            report["backing_observation"] = try FixtureBackingObservation.finish(flights, root: r, manager: manager, window: w)\n'+needle)
needle='            report["error"] = String(describing: error)'
assert base.count(needle)==1
base=base.replace(needle,'            var backing = report["backing_observation"] as? [String: Any] ?? FixtureBackingObservation.initial()\n            if backing["success"] as? Bool != true { backing["error"] = String(describing: error) }\n            report["backing_observation"] = backing\n'+needle)
driver=helper+base
(D/'Driver.swift.inc').write_text(driver)
(D/'ProductHero.swift').write_text((D/'ProductHero.clock-adapted.swift').read_text()+'\n'+(D/'FloatCapture.swift.inc').read_text()+'\n'+driver)
patch=''.join(difflib.unified_diff((D/'Driver.before-backing.swift.inc').read_text().splitlines(True),driver.splitlines(True),fromfile='Driver.before-backing.swift.inc',tofile='Driver.swift.inc'))
(D/'backing-observer.patch').write_text(patch)
shutil.copy2(B/'source-provenance.json',D/'source-provenance.float-base.json')
# This local verifier only verifies frozen inputs; it never runs prepare/build/UI.
(D/'verify_sources.py').write_text((B/'verify_sources.py').read_text())
p={'kind':'post_png_scalar_backing_observer_local13','base_fixture':'Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-float13/fixture','base_driver_sha256':hashlib.sha256((B/'Driver.swift.inc').read_bytes()).hexdigest(),'backing_default':'off','float_mode_required_for_these_runs':'off','stage':'post_png_post_final_guards_pre_teardown','scope':'Static root-mounted endpoint flights plus already-prepared actual manager overlay and their ancestor scalars; no actual flight/lifecycle or zero-observer-effect claim.','unchanged':['Actual snapshot renderer, NSImage construction, Flight.draw, all existing PNG/final guards/teardown','Local SDK14.2 gainmap/unused-clock compiler guards','7.9second watchdog,15second wrapper, min13, Swift5'], 'generated_files':{}}
for f in sorted(D.rglob('*')):
    if f.is_file():
        raw=f.read_bytes(); p['generated_files'][str(f.relative_to(D))]={'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
(D/'source-provenance.json').write_text(json.dumps(p,indent=2,sort_keys=True)+'\n')
manifest=''.join(hashlib.sha256(f.read_bytes()).hexdigest()+'  '+str(f.relative_to(D))+'\n' for f in sorted(D.rglob('*')) if f.is_file())
(D/'SHA256SUMS').write_text(manifest)
print('Prepared',D,'files',len(p['generated_files'])+2)
