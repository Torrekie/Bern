// Private Standard-only named-asset fixture: no product intent routing is added.
import CoreImage

private enum FixtureFlightSDRMode: String {
    case `default`, bakedPair = "baked-pair"
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_FLIGHT_SDR"]
    static let selected = FixtureFlightSDRMode(rawValue: requested ?? "default")
}

@MainActor private enum FixtureFlightSDR {
    @MainActor private final class Observation {
        weak var anchor: BernPictureHeroAnchor?
        weak var displayImage: NSImage?
        var inputSpace: CGColorSpace?
        var derived: CGImage?
        var values: [String: Any]
        init(_ anchor: BernPictureHeroAnchor, ordinal: Int) {
            self.anchor = anchor
            values = ["ordinal": ordinal, "key": anchor.key, "anchor_identity": fixtureID(anchor),
                      "snapshot_started_uptime": fixtureUptime(), "wrapped": false,
                      "renderer_returned_uptime": NSNull(), "conversion_started_uptime": NSNull(),
                      "conversion_finished_uptime": NSNull(), "nsimage_wrapped_uptime": NSNull()]
        }
    }
    private static var primary = true, cleanupCount = 0, conversions = 0, contextCreates = 0
    private static var observations: [Observation] = []
    private static var context: CIContext?
    private static var problem: String?
    private static var transitionTime: Double?
    private static var mapping: [String: Any] = [:]
    private(set) static var finalizationFailed = false

    static func begin(_ anchor: BernPictureHeroAnchor) -> Int? {
        guard primary else { cleanupCount += 1; return nil }
        observations.append(Observation(anchor, ordinal: observations.count + 1))
        if observations.count > 2 { problem = problem ?? "Extra primary snapshot; actual records are not deduplicated" }
        return observations.count - 1
    }
    static func end(_ token: Int?) {
        guard let token else { return }
        observations[token].values["snapshot_returning_uptime"] = fixtureUptime()
        if observations[token].values["wrapped"] as? Bool != true {
            problem = problem ?? "Actual snapshot did not return its NSImage wrapper"
            observations[token].values["error"] = problem
        }
    }
    private static func layout(_ image: CGImage) -> [String: Any] {
        ["width": image.width, "height": image.height, "bits_per_component": image.bitsPerComponent,
         "bits_per_pixel": image.bitsPerPixel, "bytes_per_row": image.bytesPerRow,
         "bitmap_info_raw": image.bitmapInfo.rawValue, "alpha_info_raw": image.alphaInfo.rawValue,
         "byte_order_raw": image.byteOrderInfo.rawValue, "pixel_format_raw": image.pixelFormatInfo.rawValue,
         "float_components": image.bitmapInfo.contains(.floatComponents)]
    }
    static func pixels(_ image: CGImage, token: Int?, anchor: BernPictureHeroAnchor,
                       rect: CGRect, returnedAt: Double) -> CGImage? {
        // Cleanup has already frozen acquisition and follows the original unconverted path.
        guard let token else { return image }
        let item = observations[token]
        item.values["renderer_returned_uptime"] = returnedAt
        item.values["rect_in_overlay"] = fixtureRect(rect)
        item.values["logical_size"] = [anchor.bounds.width, anchor.bounds.height]
        item.values["input_object_id"] = fixtureID(image)
        item.values["input_layout"] = layout(image)
        item.inputSpace = image.colorSpace // Reference only; ICC work is deferred until teardown.
        do {
            if let problem { throw FixtureFailure(message: problem) }
            guard anchor.key == fixtureHeroKey, anchor.bounds.size == CGSize(width: 320, height: 180),
                  anchor.corner == 0, anchor.picture?.orientation == .up,
                  case .fill = anchor.fit else { throw FixtureFailure(message: "Unexpected private Standard named snapshot geometry/input") }
            let width = image.width, height = image.height
            guard (width == 320 || width == 640), height == width * 9 / 16,
                  image.bitsPerComponent == 16, image.bitsPerPixel == 64,
                  image.bitmapInfo.rawValue == 4353, image.alphaInfo.rawValue == 1,
                  image.byteOrderInfo.rawValue == 4096, image.pixelFormatInfo.rawValue == 0,
                  image.bitmapInfo.contains(.floatComponents), image.bytesPerRow >= width * 8,
                  let space = item.inputSpace, space.model == .rgb, space.numberOfComponents == 3 else {
                throw FixtureFailure(message: "Unknown original snapshot layout/space; no conversion fallback")
            }
            let extent = CGRect(x: 0, y: 0, width: width, height: height)
            item.values["input_extent"] = fixtureRect(extent)
            guard FixtureFlightSDRMode.selected == .bakedPair else { return image }
            item.values["conversion_started_uptime"] = fixtureUptime()
            item.values["requested_tone_map_hdr_to_sdr"] = true
            item.values["actual_tone_mapping_applied"] = "unknown"
            item.values["input_color_space_override"] = false
            item.values["requested_output_format"] = "RGBA8"
            item.values["requested_output_color_space"] = "sRGB"
            item.values["deferred"] = false
            let input = CIImage(cgImage: image, options: [.toneMapHDRtoSDR: true])
            guard input.extent == extent, let destination = CGColorSpace(name: CGColorSpace.sRGB) else {
                throw FixtureFailure(message: "CI exact input extent/sRGB destination unavailable")
            }
            let renderer: CIContext
            if let context { renderer = context }
            else { renderer = CIContext(options: nil); context = renderer; contextCreates += 1 }
            guard let result = renderer.createCGImage(input, from: extent, format: .RGBA8,
                                                       colorSpace: destination, deferred: false),
                  result.width == width, result.height == height, result.bitsPerComponent == 8,
                  result.bitsPerPixel == 32, !result.bitmapInfo.contains(.floatComponents),
                  result.bytesPerRow >= width * 4 else {
                throw FixtureFailure(message: "Actual snapshot RGBA8 conversion failed; no fallback")
            }
            item.derived = result; conversions += 1
            item.values["derived_object_id"] = fixtureID(result)
            item.values["conversion_finished_uptime"] = fixtureUptime()
            return result
        } catch {
            problem = problem ?? String(describing: error); item.values["error"] = String(describing: error)
            return nil
        }
    }
    static func wrapped(_ image: NSImage, token: Int?) -> Bool {
        guard let token else { return true }
        let item = observations[token]
        guard problem == nil, item.displayImage == nil, image.size == CGSize(width: 320, height: 180) else {
            problem = problem ?? "Actual snapshot wrapper identity/size failed"; return false
        }
        item.displayImage = image; item.values["display_nsimage_id"] = fixtureID(image)
        item.values["nsimage_wrapped_uptime"] = fixtureUptime(); item.values["wrapped"] = true
        return true
    }
    static func noteTransition(_ time: Double) { transitionTime = time }
    static func observeFlight(_ from: NSImage, _ to: NSImage, started: Double, view: BernHeroFlightView) {
        FixtureFlightTiming.matchingEntered()
        // Called by the existing scalar observer, never creates/retains a flight or image.
        let left = observations.enumerated().filter { $0.element.displayImage === from }
        let right = observations.enumerated().filter { $0.element.displayImage === to }
        guard observations.count == 2, left.count == 1, right.count == 1,
              left[0].offset != right[0].offset else { problem = problem ?? "Actual Flight.from/to do not uniquely match the two snapshot wrappers"; return }
        let identity = String(describing: ObjectIdentifier(view))
        if let old = mapping["flight_identity"] as? String, old != identity {
            problem = problem ?? "Actual flight identity changed"; return
        }
        observations[left[0].offset].values["flight_role"] = "from"
        observations[right[0].offset].values["flight_role"] = "to"
        if mapping.isEmpty {
            mapping = ["flight_identity": identity, "flight_started_uptime": started,
                       "first_live_observation_uptime": fixtureUptime(),
                       "from_ordinal": left[0].offset + 1, "to_ordinal": right[0].offset + 1,
                       "from_nsimage_id": fixtureID(from), "to_nsimage_id": fixtureID(to)]
        }
        FixtureFlightTiming.existingFirstStamp(mapping["first_live_observation_uptime"] as? Double)
    }
    static func check() throws { if let problem { throw FixtureFailure(message: problem) } }
    static func freezePrimary() { primary = false }
    private static func spaceMetadata(_ space: CGColorSpace?) -> [String: Any] {
        guard let space else { return ["present": false] }
        let profile = space.copyICCData().map { $0 as Data }
        return ["present": true, "name": space.name.map { $0 as String as Any } ?? NSNull(),
                "model_raw": space.model.rawValue, "components": space.numberOfComponents,
                "icc_byte_count": profile?.count ?? 0, "icc_sha256": profile.map { fixtureHash($0) } ?? "absent",
                "stage": "after_existing_window_teardown"]
    }
    static func finish(acquisitionSucceeded: Bool) -> [String: Any] {
        let count = observations.count, derivedCount = observations.filter { $0.derived != nil }.count
        if problem == nil, FixtureFlightSDRMode.selected == nil { problem = "Invalid flight SDR mode" }
        if problem == nil, !acquisitionSucceeded { problem = "Original native acquisition incomplete" }
        if problem == nil, count != 2 || mapping.isEmpty || transitionTime == nil ||
            observations.contains(where: { $0.values["wrapped"] as? Bool != true }) {
            problem = "Incomplete actual two-snapshot/one-flight mapping"
        }
        if problem == nil, FixtureFlightSDRMode.selected == .bakedPair,
           conversions != 2 || contextCreates != 1 || derivedCount != 2 { problem = "Incomplete actual two-output/one-context recipe" }
        if problem == nil, FixtureFlightSDRMode.selected == .default,
           conversions != 0 || contextCreates != 0 || derivedCount != 0 { problem = "Default unexpectedly created CI/output" }
        var records: [[String: Any]] = []
        for item in observations {
            var value = item.values; value["input_color_space"] = spaceMetadata(item.inputSpace)
            if let image = item.derived {
                value["derived_layout"] = layout(image); value["derived_color_space"] = spaceMetadata(image.colorSpace)
            }
            records.append(value)
            item.derived = nil; item.inputSpace = nil; item.displayImage = nil; item.anchor = nil
        }
        mapping["transition_uptime"] = transitionTime.map { $0 as Any } ?? NSNull()
        observations.removeAll(); context = nil; finalizationFailed = problem != nil
        return ["requested": FixtureFlightSDRMode.requested.map { $0 as Any } ?? NSNull(),
                "selected": FixtureFlightSDRMode.selected.map { $0.rawValue as Any } ?? NSNull(),
                "success": !finalizationFailed, "error": problem.map { $0 as Any } ?? NSNull(),
                "primary_snapshot_count": count, "cleanup_snapshot_count": cleanupCount,
                "conversion_count": conversions, "context_create_count": contextCreates,
                "derived_cache_count_before_release": derivedCount, "records": records, "flight_mapping": mapping,
                "primary_frozen": !primary, "helper_references_cleared": observations.isEmpty && context == nil,
                "release_scope": "Helper-owned derived cache/context/color-space and weak refs cleared; no global deallocation claim",
                "helper_retained_original_cgimage_count": 0, "helper_original_provider_read_count": 0]
    }
}

// Independent bounded scalar observer. No object references, queries or animation control.
@MainActor private enum FixtureFlightTiming {
    private static var recording = true
    private static var native: [String: [String: Any]] = [:] // Exactly three named slots.
    private static var live: [[String: Any]] = [] // First two live sampler callbacks only.
    private static var pending: [String: Any]?
    private static var timerAddedCount = 0
    private static var problem: String?

    static func timerAdded(key: String, started: Double) {
        guard recording else { return }
        timerAddedCount += 1
        guard timerAddedCount == 1 else { problem = problem ?? "More than one native timer registration"; return }
        native["timer_added"] = ["key": key, "flight_started_uptime": started, "uptime": fixtureUptime()]
    }
    static func tick(key: String, started: Double, now: Double) {
        guard recording, native["first_tick"] == nil else { return }
        native["first_tick"] = ["key": key, "flight_started_uptime": started, "now_uptime": now]
    }
    static func applied(key: String, started: Double, now: Double, progress: Double) {
        guard recording, native["first_applied"] == nil else { return }
        native["first_applied"] = ["key": key, "flight_started_uptime": started,
                                   "now_uptime": now, "progress": progress]
    }
    static func callbackEntered(_ identity: Int) {
        guard recording, live.count < 2 else { return }
        pending = ["callback_id": identity, "callback_entered_uptime": fixtureUptime()]
    }
    static func mark(_ field: String) {
        guard recording, live.count < 2, pending != nil else { return }
        pending?[field] = fixtureUptime()
    }
    static func matchingEntered() { mark("matching_begin_uptime") }
    static func existingFirstStamp(_ time: Double?) {
        guard recording, live.count < 2, pending != nil else { return }
        pending?["existing_first_live_observation_uptime"] = time.map { $0 as Any } ?? NSNull()
    }
    static func keepLive(sample: Int, stateTime: Double, identity: String, started: Double?, progress: Double) {
        guard recording, live.count < 2 else { return }
        guard var value = pending else { problem = problem ?? "Missing live callback prefix"; return }
        value["sample_index"] = sample; value["state_uptime"] = stateTime
        value["flight_identity"] = identity; value["flight_started_uptime"] = started.map { $0 as Any } ?? NSNull()
        value["progress"] = progress; live.append(value); pending = nil
    }
    static func freeze() { recording = false }
    static func finish(acquisitionSucceeded: Bool) -> [String: Any] {
        let required = ["callback_entered_uptime", "window_info_begin_uptime", "window_info_end_uptime",
                        "scalars_begin_uptime", "matching_begin_uptime", "state_uptime", "scalars_end_uptime"]
        if problem == nil, recording || native.count != 3 || timerAddedCount != 1 || live.count != 2 {
            problem = "Incomplete frozen three-event/two-live-sample timing trace"
        }
        for sample in live {
            let times = required.compactMap { sample[$0] as? Double }
            if times.count != required.count || !times.allSatisfy({ $0.isFinite }) ||
                zip(times, times.dropFirst()).contains(where: { $0.0 > $0.1 }) {
                problem = problem ?? "Missing/nonfinite/out-of-order callback timing fields"
            }
        }
        if live.count == 2 {
            let a = live[0], b = live[1]
            if let ca = a["callback_id"] as? Int, let cb = b["callback_id"] as? Int,
               let sa = a["sample_index"] as? Int, let sb = b["sample_index"] as? Int,
               let identity = a["flight_identity"] as? String, !identity.isEmpty,
               let started = a["flight_started_uptime"] as? Double,
               let stamp = a["existing_first_live_observation_uptime"] as? Double,
               let matching = a["matching_begin_uptime"] as? Double, let state = a["state_uptime"] as? Double {
                if cb != ca + 1 || sb != sa + 1 || b["flight_identity"] as? String != identity ||
                    b["flight_started_uptime"] as? Double != started || b["existing_first_live_observation_uptime"] as? Double != stamp ||
                    !started.isFinite || !stamp.isFinite || stamp < matching || stamp > state {
                    problem = problem ?? "Live samples are not adjacent observations of one pinned native flight"
                }
                for event in native.values {
                    let time = (event["uptime"] ?? event["now_uptime"]) as? Double
                    if event["key"] as? String != fixtureHeroKey || event["flight_started_uptime"] as? Double != started ||
                        time == nil || time?.isFinite != true || (time ?? 0) < started {
                        problem = problem ?? "Native scalar event identity/time incomplete"
                    }
                }
                if let tick = native["first_tick"]?["now_uptime"] as? Double,
                   let applied = native["first_applied"]?["now_uptime"] as? Double,
                   let progress = native["first_applied"]?["progress"] as? Double {
                    if applied < tick || !progress.isFinite { problem = problem ?? "First applied scalar timing incomplete" }
                } else { problem = problem ?? "Missing first native tick/applied scalars" }
            } else { problem = problem ?? "Missing live callback/sample/native identity fields" }
        }
        let complete = problem == nil
        return ["kind": "bounded_native_sampler_scalar_timing", "complete": complete,
                "success": complete && acquisitionSucceeded,
                "error": problem.map { $0 as Any } ?? (acquisitionSucceeded ? NSNull() : "Original acquisition incomplete" as Any),
                "native_events": native, "timer_added_count": timerAddedCount, "live_samples": live,
                "pending_callback": pending.map { $0 as Any } ?? NSNull(), "frozen_before_teardown": !recording,
                "limits": ["native_event_slots": 3, "live_samples": 2, "pending_callbacks": 1],
                "scope": "Monotonic scalar call boundaries only; neither rendered frames nor root cause"]
    }
}
