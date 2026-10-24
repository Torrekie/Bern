// Fixture only: one stock NSImageView displays the original named snapshot.
private enum FixtureNativeDisplayMode {
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_NATIVE_DISPLAY"]
    static let selected: String? = {
        let value = requested ?? "control"
        return ["control", "image-view"].contains(value) ? value : nil
    }()
}
@MainActor private enum FixtureNativeDisplay {
    private static weak var child: NSImageView?
    private static weak var flight: BernHeroFlightView?
    private static weak var expectedImage: NSImage?
    private static var imageSize = NSSize.zero
    private static var installed = false
    private static var records: [[String: Any]] = []
    private static var cleanupRecord: [String: Any] = ["attempted": false]
    private static var succeeded = false
    private static var failure: String?
    static var finalizationFailed = false
    static func report() -> [String: Any] {
        ["requested": FixtureNativeDisplayMode.requested.map { $0 as Any } ?? NSNull(),
         "selected": FixtureNativeDisplayMode.selected.map { $0 as Any } ?? NSNull(),
         "target": "flight-named", "static_route_required": "overlay",
         "success": succeeded, "error": failure.map { $0 as Any } ?? NSNull(),
         "records": records, "cleanup": cleanupRecord]
    }
    static func validateModes() throws {
        guard FixtureNativeDisplayMode.selected != nil, FixtureStaticRouteMode.selected == "overlay",
              FixtureBackingMode.selected == "off", FixtureFloatCaptureMode.selected == .off else {
            throw FixtureFailure(message: "Native display requires control/image-view, existing overlay, backing/float off before window creation")
        }
    }
    static func mount(_ f: BernHeroFlightView, picture: BernHeroPicture, index: Int,
                      sourceMetadata: [String: Any]?, manager: BernWindowImageHeroes,
                      window: NSWindow) throws {
        guard FixtureNativeDisplayMode.selected == "image-view" else { return }
        guard index == 0 else { return } // Custom flight remains its original draw path.
        let image = picture.image
        // This exact atlas was previously verified opaque; no new pixel/provider scan.
        guard !installed, let sourceMetadata,
              sourceMetadata["file_sha256"] as? String == "3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b",
              sourceMetadata["orientation"] as? String == "up",
              sourceMetadata["original_size"] as? [Int] == [640, 360],
              let ratio = sourceMetadata["ratio"] as? CGFloat, abs(ratio - 16.0 / 9.0) < 0.000000001,
              picture.corner == 0, f.corner == 0, f.from === image, f.to === image,
              image.size == NSSize(width: 320, height: 180),
              f.bounds == NSRect(x: 0, y: 0, width: 320, height: 180),
              f.window === window, f.superview === manager.fixtureExistingOverlay,
              !f.fixtureNativeDisplaySkipsDraw else {
            throw FixtureFailure(message: "Named native display identity/opaque-atlas/up/aspect/corner/geometry precondition failed")
        }
        let view = NSImageView(frame: f.bounds)
        view.imageScaling = .scaleAxesIndependently
        view.imageFrameStyle = .none; view.animates = false
        view.image = image
        child = view; flight = f; expectedImage = image; imageSize = image.size
        f.addSubview(view); f.fixtureNativeDisplaySkipsDraw = true; installed = true
        try check(stage: "mounted", flights: [f], manager: manager, window: window)
    }
    static func check(stage: String, flights: [BernHeroFlightView],
                      manager: BernWindowImageHeroes, window: NSWindow) throws {
        guard FixtureNativeDisplayMode.selected == "image-view" else { return }
        guard installed, let view = child, let f = flight, let image = expectedImage,
              flights.first === f, f.from === image, f.to === image, view.image === image,
              type(of: view) == NSImageView.self, f.fixtureNativeDisplaySkipsDraw,
              f.window === window, view.window === window,
              f.superview === manager.fixtureExistingOverlay, view.superview === f,
              view.frame == f.bounds, view.bounds == NSRect(origin: .zero, size: f.bounds.size),
              f.bounds.size == NSSize(width: 320, height: 180), image.size == imageSize,
              imageSize == NSSize(width: 320, height: 180), f.corner == 0,
              view.imageScaling == .scaleAxesIndependently, view.imageFrameStyle == .none, !view.animates,
              fixtureDescendants(f).filter({ $0 is MTKView }).isEmpty else {
            throw FixtureFailure(message: "Native display child/image/flight/parent/window/geometry/configuration/no-Metal check failed")
        }
        records.append(["stage": stage, "target": "flight-named",
            "child_class": NSStringFromClass(type(of: view)),
            "child_identity": String(describing: ObjectIdentifier(view)),
            "flight_identity": String(describing: ObjectIdentifier(f)),
            "image_identity": String(describing: ObjectIdentifier(image)),
            "child_frame": fixtureRect(view.frame), "child_bounds": fixtureRect(view.bounds),
            "flight_bounds": fixtureRect(f.bounds), "nsimage_size": [image.size.width, image.size.height],
            "window_number": window.windowNumber, "parent_is_original_flight": true,
            "flight_parent_is_existing_overlay": true, "same_from_to_image": true,
            "skip_original_draw": true, "image_scaling_raw": view.imageScaling.rawValue,
            "image_frame_style_raw": view.imageFrameStyle.rawValue,
            "animates": view.animates, "flight_subtree_metal_count": 0])
    }
    static func finish(flights: [BernHeroFlightView], manager: BernWindowImageHeroes,
                       window: NSWindow) throws {
        if FixtureNativeDisplayMode.selected == "image-view" {
            try check(stage: "post_final_guards", flights: flights, manager: manager, window: window)
        }
        succeeded = true
    }
    static func fail(_ error: Error) { succeeded = false; failure = String(describing: error) }
    static func cleanup() {
        guard FixtureNativeDisplayMode.selected == "image-view" else { return }
        guard installed else { return }
        cleanupRecord = ["attempted": true, "stage": "after_orderOut_before_original_flight_removal"]
        guard let view = child else {
            finalizationFailed = true; succeeded = false; failure = "Native child missing before cleanup"; return
        }
        view.image = nil; view.removeFromSuperview()
        cleanupRecord["child_image_assigned_nil"] = true
        cleanupRecord["child_image_is_nil"] = view.image == nil
        cleanupRecord["child_superview_is_nil"] = view.superview == nil
        cleanupRecord["scope"] = "Only fixture child detachment and helper weak refs; not all NSImage deallocation"
        if view.image != nil || view.superview != nil {
            finalizationFailed = true; succeeded = false; failure = "Native child cleanup incomplete"
        }
        child = nil; flight = nil; expectedImage = nil
        cleanupRecord["helper_weak_refs_cleared"] = true
    }
}
