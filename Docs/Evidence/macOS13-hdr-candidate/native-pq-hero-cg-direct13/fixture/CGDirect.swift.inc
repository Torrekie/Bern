// Fixture only: the display adapter changes, never the retained snapshot.
private enum FixtureCGDirectMode: String {
    case original = "default", direct
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_CG_DIRECT"]
    static let selected = FixtureCGDirectMode(rawValue: requested ?? "default")
}
@MainActor private enum FixtureCGDirect {
    private static let key = "baseline-body-named"
    private static weak var namedFlight: BernHeroFlightView?
    private static var prepared = false, completed = false
    private static var error: String?
    private static var associations: [[String: Any]] = []
    private static var firstDraw: [Int: [String: Any]] = [:]
    private static var drawCounts: [Int: Int] = [:]
    private static var checkedPhases: [Int] = []
    private static var floatCompleted: Bool?
    private(set) static var finalizationFailed = false
    static func fail(_ problem: Error) {
        if error == nil { error = String(describing: problem) }
        finalizationFailed = true
    }
    static func validate() throws {
        guard FixtureCGDirectMode.selected != nil, FixtureFloatCaptureMode.selected == .on,
              FixtureBackingMode.selected == "off" else {
            throw FixtureFailure(message: "CG adapter requires default/direct, float on and backing off")
        }
    }
    static func prepare(_ flight: BernHeroFlightView, index: Int, picture: BernHeroPicture,
                        source: [String: Any]?) throws {
        guard index == 0 else { return }
        guard !prepared, source?["orientation"] as? String == "up",
              let ratio = source?["ratio"] as? CGFloat, abs(ratio - 16.0 / 9.0) < 0.000000001,
              picture.corner == 0, flight.corner == 0,
              flight.from === picture.image, flight.to === picture.image,
              picture.image.size == NSSize(width: 320, height: 180),
              flight.bounds == NSRect(x: 0, y: 0, width: 320, height: 180) else {
            throw FixtureFailure(message: "Named adapter requires opaque-atlas/up/same-aspect/corner0/320x180 identity scope")
        }
        try FixtureSnapshotFloatCapture.withOriginalSnapshot(key: key, nativeImage: picture.image) { _ in }
        flight.fixtureCGDirectKey = key; namedFlight = flight; prepared = true
    }
    // true means handled, including failure: never silently fall back after a bad binding/draw.
    static func drawIfHandled(_ flight: BernHeroFlightView) -> Bool {
        guard let marked = flight.fixtureCGDirectKey else { return false }
        do {
            guard error == nil, prepared, marked == key, namedFlight === flight,
                  flight.from === flight.to, flight.corner == 0, flight.isFlipped,
                  flight.bounds == NSRect(x: 0, y: 0, width: 320, height: 180),
                  flight.progress.isFinite, let mode = FixtureCGDirectMode.selected else {
                throw FixtureFailure(message: "Named adapter draw identity/geometry/state failed")
            }
            let alpha = min(1, max(0, flight.progress))
            guard alpha == 0 || alpha == 1 else {
                throw FixtureFailure(message: "Only fixed opaque endpoint alpha0/1 is in scope")
            }
            let phase = alpha == 0 ? 0 : 1
            var row: [String: Any] = ["phase": phase, "progress": flight.progress,
                "flight_identity": String(describing: ObjectIdentifier(flight)),
                "native_image_identity": String(describing: ObjectIdentifier(flight.from)),
                "bounds": fixtureRect(flight.bounds), "source_over_alphas": [1, alpha],
                "path": mode.rawValue, "context_observed": false]
            try FixtureSnapshotFloatCapture.withOriginalSnapshot(key: key, nativeImage: flight.from) { image in
                row["original_cgimage_identity"] = String(describing: ObjectIdentifier(image))
                guard mode == .direct else { return } // Original NSImage calls remain below the hook.
                guard let context = NSGraphicsContext.current?.cgContext else {
                    throw FixtureFailure(message: "Existing AppKit CGContext unavailable; no fallback")
                }
                context.saveGState()
                defer { context.restoreGState() }
                context.translateBy(x: 0, y: flight.bounds.height)
                context.scaleBy(x: 1, y: -1)
                context.setBlendMode(.normal); context.setAlpha(1)
                context.draw(image, in: flight.bounds)
                context.setBlendMode(.normal); context.setAlpha(alpha)
                context.draw(image, in: flight.bounds)
                row["context_observed"] = true
                row["cg_draw_calls_issued"] = 2
                row["blend_mode"] = "normal_source_over"
                row["local_y_flip"] = true
                row["state_restore"] = "paired_save_defer_restore_source_path"
            }
            drawCounts[phase, default: 0] += 1
            if firstDraw[phase] == nil { firstDraw[phase] = row }
            return mode == .direct
        } catch { fail(error); return true }
    }
    static func check(_ flights: [BernHeroFlightView], phase: Int? = nil) throws {
        if let error { throw FixtureFailure(message: error) }
        guard prepared, flights.count == 2, namedFlight === flights[0],
              flights[0].fixtureCGDirectKey == key, flights[1].fixtureCGDirectKey == nil else {
            throw FixtureFailure(message: "Named-only adapter binding missing or replaced")
        }
        for (index, flight) in flights.enumerated() {
            guard flight.from === flight.to else { throw FixtureFailure(message: "Endpoint images changed") }
            try FixtureSnapshotFloatCapture.withOriginalSnapshot(
                key: index == 0 ? key : "baseline-body-custom", nativeImage: flight.from) { _ in }
        }
        associations = try FixtureSnapshotFloatCapture.bindingRecords()
        if let phase {
            guard [0, 1].contains(phase), drawCounts[phase, default: 0] > 0 else {
                throw FixtureFailure(message: "No named adapter callback observed for captured endpoint")
            }
            if !checkedPhases.contains(phase) { checkedPhases.append(phase) }
        }
    }
    static func afterExport(_ capture: [String: Any]) {
        floatCompleted = capture["success"] as? Bool == true
        completed = true
        if error == nil && (!prepared || checkedPhases != [0, 1] || floatCompleted != true) {
            fail(FixtureFailure(message: "Adapter endpoint/post-teardown float completion gate failed"))
        }
    }
    static func report() -> [String: Any] {
        ["requested": FixtureCGDirectMode.requested.map { $0 as Any } ?? NSNull(),
         "selected": FixtureCGDirectMode.selected.map { $0.rawValue as Any } ?? NSNull(),
         "success": completed && error == nil, "error": error.map { $0 as Any } ?? NSNull(),
         "target": "flight-named", "prepared": prepared, "associations": associations,
         "draws": [0, 1].compactMap { firstDraw[$0] },
         "draw_callback_counts": ["0": drawCounts[0, default: 0], "1": drawCounts[1, default: 0]],
         "checked_phases": checkedPhases,
         "post_teardown_float_success": floatCompleted.map { $0 as Any } ?? NSNull(),
         "pixel_acceptance": "not performed; issued calls and binding gates are not visible-image proof"]
    }
}
