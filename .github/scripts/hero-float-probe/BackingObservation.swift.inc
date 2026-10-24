
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
