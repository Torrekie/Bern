
import QuartzCore
private enum FixtureFormatMode {
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_FORMAT_REQUEST"]
    static let selected: String? = {
        let value = requested ?? "control"
        return ["control", "rgba8"].contains(value) ? value : nil
    }()
}
@MainActor private enum FixtureFormatRequest {
    private final class Item {
        weak var layer: CALayer?
        var values: [String: Any]
        init(_ values: [String: Any]) { self.values = values }
    }
    private static var items: [Item] = []
    private static var error: String?
    private static var stages = 0
    private static var frozen = false
    private(set) static var finalizationFailed = false
    private static let order = ["after_png_progress-0", "after_png_progress-1", "post_final_guards"]
    static func initial() -> [String: Any] {
        ["requested": FixtureFormatMode.requested.map { $0 as Any } ?? NSNull(),
         "selected": FixtureFormatMode.selected.map { $0 as Any } ?? NSNull(),
         "success": false, "error": NSNull(), "records": []]
    }
    private static func fail(_ message: String) throws -> Never {
        error = message; throw FixtureFailure(message: message)
    }
    static func mounted(_ flight: BernHeroFlightView, key: String,
                        manager: BernWindowImageHeroes, window: NSWindow) throws {
        guard FixtureFormatMode.selected == "rgba8" else { return }
        guard !frozen, items.count < 2, !items.contains(where: { $0.values["key"] as? String == key }),
              flight.window === window, flight.superview === manager.fixtureExistingOverlay else {
            try fail("Format request requires two unique attached actual-overlay flights")
        }
        let item = Item(["key": key, "request_stage": "after_mount_before_next_original_display_loop",
                         "layer_present": false, "set_count": 0, "checks": []])
        items.append(item)
        guard let layer = flight.layer else { try fail("Format request found no existing flight layer") }
        item.layer = layer
        let before = layer.contentsFormat
        item.values["layer_present"] = true
        item.values["layer_class"] = NSStringFromClass(type(of: layer))
        item.values["layer_object_id"] = String(describing: ObjectIdentifier(layer))
        item.values["before"] = before.rawValue
        item.values["view_needs_display_before"] = flight.needsDisplay
        item.values["layer_needs_display_before"] = layer.needsDisplay()
        guard before != .RGBA8Uint else { try fail("Existing layer is already RGBA8; non-discriminating premise") }
        layer.contentsFormat = .RGBA8Uint
        item.values["set_count"] = 1
        let after = layer.contentsFormat
        item.values["immediate_after"] = after.rawValue
        guard after == .RGBA8Uint else { try fail("Format request was not immediately retained") }
    }
    static func check(_ flights: [BernHeroFlightView], stage: String) throws {
        guard FixtureFormatMode.selected == "rgba8" else { return }
        guard !frozen, stages < order.count, order[stages] == stage, items.count == 2, flights.count == 2 else {
            try fail("Format persistence check count/order mismatch")
        }
        for (i, item) in items.enumerated() {
            guard let expected = item.layer, let actual = flights[i].layer, actual === expected else {
                try fail("Existing requested flight layer disappeared or was replaced")
            }
            let value = actual.contentsFormat
            var checks = item.values["checks"] as? [[String: Any]] ?? []
            checks.append(["stage": stage, "same_layer_identity": true, "contents_format": value.rawValue])
            item.values["checks"] = checks
            guard value == .RGBA8Uint else { try fail("Requested format was overwritten; no reapply") }
        }
        stages += 1
    }
    static func freeze(acquisitionSucceeded: Bool, priorError: String?) -> [String: Any] {
        frozen = true
        var problem = error
        if !acquisitionSucceeded { problem = problem ?? priorError ?? "Acquisition incomplete" }
        if FixtureFormatMode.selected == nil { problem = problem ?? "Invalid format request mode" }
        if acquisitionSucceeded, FixtureFormatMode.selected == "rgba8", (items.count != 2 || stages != order.count) {
            problem = problem ?? "Incomplete request/persistence observations"
        }
        let records = items.map { $0.values }
        items.removeAll() // Discard weak references before original teardown; serialize scalars only.
        finalizationFailed = problem != nil
        var report = initial()
        report["success"] = problem == nil; report["error"] = problem.map { $0 as Any } ?? NSNull()
        report["records"] = records; report["completed_check_stages"] = stages
        report["freeze_stage"] = "before_existing_window_teardown"
        report["retained_layer_or_image_references"] = 0
        report["interpretation"] = "Existing-layer hint request/persistence only; not actual storage or a cause"
        return report
    }
}
