
// Fixture-only route switch; no layer-format/contents/pixel observation.
private enum FixtureStaticRouteMode {
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_STATIC_ROUTE"]
    static let selected: String? = {
        let value = requested ?? "root"
        return ["root", "overlay"].contains(value) ? value : nil
    }()
}
@MainActor private enum FixtureStaticRoute {
    private static func parent(root: NSView, manager: BernWindowImageHeroes,
                               window: NSWindow) throws -> NSView {
        guard root.window === window, let mode = FixtureStaticRouteMode.selected else {
            throw FixtureFailure(message: "Static route requires valid mode and attached root")
        }
        if mode == "root" { return root }
        // Existing overlay: do not prepare/reconstruct it or change its geometry.
        let overlay = manager.fixtureExistingOverlay
        let expected = window.contentView?.superview ?? window.contentView
        guard expected != nil, overlay.window === window, overlay.superview === expected else {
            throw FixtureFailure(message: "Static route actual existing overlay is not attached")
        }
        return overlay
    }
    static func mount(_ flight: BernHeroFlightView, desired: CGRect, root: NSView,
                      manager: BernWindowImageHeroes, window: NSWindow) throws {
        let target = try parent(root: root, manager: manager, window: window)
        flight.frame = target === root ? desired : target.convert(desired, from: root)
        target.addSubview(flight)
    }
    static func check(_ flights: [BernHeroFlightView], desired: [CGRect], root: NSView,
                      manager: BernWindowImageHeroes, window: NSWindow) throws -> [[String: Any]] {
        let target = try parent(root: root, manager: manager, window: window)
        guard flights.count == 2, desired.count == 2 else {
            throw FixtureFailure(message: "Static route requires exactly two manual flights")
        }
        var records: [[String: Any]] = []
        for (i, flight) in flights.enumerated() {
            let back = flight.convert(flight.bounds, to: root), want = desired[i]
            let error = max(max(abs(back.minX - want.minX), abs(back.minY - want.minY)),
                            max(abs(back.width - want.width), abs(back.height - want.height)))
            // Root descendants do not cover overlay siblings; inspect each retained subtree.
            let metal = fixtureDescendants(flight).filter { $0 is MTKView }.count
            guard flight.window === window, flight.superview === target,
                  flight.bounds.size == CGSize(width: 320, height: 180),
                  want.size == CGSize(width: 320, height: 180), error <= 0.000001, metal == 0 else {
                throw FixtureFailure(message: "Static route parent/window/bounds/ROI/no-Metal gate failed")
            }
            records.append(["role": i == 0 ? "flight-named" : "flight-custom",
                            "desired_root_rect": fixtureRect(want),
                            "frame_in_selected_parent": fixtureRect(flight.frame),
                            "back_converted_root_rect": fixtureRect(back),
                            "roundtrip_max_error_points": error,
                            "window_number": window.windowNumber,
                            "parent_is_selected_route": true,
                            "flight_subtree_metal_count": metal])
        }
        return records
    }
}
