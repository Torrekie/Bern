
// Append to AppKit/SwiftUI imports + unchanged ProductHero.exact.swift.
import Combine
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

private let fixtureHeroKey = "coordinator-one"
private struct FixtureFailure: Error { let message: String }
private func fixtureUptime() -> Double { ProcessInfo.processInfo.systemUptime }
private func fixtureHash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
private func fixtureRect(_ r: CGRect) -> [String: Double] {
    ["x": r.minX, "y": r.minY, "width": r.width, "height": r.height]
}
private func fixtureNear(_ actual: CGRect, _ expected: CGRect) -> Bool {
    max(max(abs(actual.minX - expected.minX), abs(actual.minY - expected.minY)),
        max(abs(actual.width - expected.width), abs(actual.height - expected.height))) <= 0.000001
}
private func fixtureID(_ object: AnyObject?) -> Any {
    object.map { String(describing: ObjectIdentifier($0)) as Any } ?? NSNull()
}
@MainActor private final class FixtureModel: ObservableObject {
    @Published var atDestination = false
}
@MainActor private struct FixtureScene: View {
    @ObservedObject var model: FixtureModel
    let url: String
    var body: some View {
        ZStack(alignment: .topLeading) {
            Color.white
            if model.atDestination {
                picture.id("destination").offset(x: 352, y: 244)
            } else {
                picture.id("source").offset(x: 16, y: 24)
            }
        }
        .frame(width: 1024, height: 440, alignment: .topLeading)
        .environment(\.colorScheme, .light)
    }
    private var picture: some View {
        BernImage(url: url, label: nil, width: 320, height: 180, fit: .fill,
                  rendering: .original, dynamicRange: .standard, hero: fixtureHeroKey)
    }
}
private final class FixtureWindow: NSWindow {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
@MainActor private final class FixtureWeakRefs {
    weak var source: BernPictureHeroAnchor?
    weak var flight: BernHeroFlightView?
}
extension BernWindowImageHeroes {
    fileprivate func fixtureScalars(root: NSView) -> [String: Any] {
        var entryValues: [String: [[String: Any]]] = [:]
        for (key, list) in entries {
            entryValues[key] = list.compactMap { entry in
                guard let anchor = entry.anchor else { return nil }
                return ["identity": fixtureID(anchor), "attached": anchor.attached,
                        "window_number": anchor.window.map { $0.windowNumber as Any } ?? NSNull(),
                        "reduced": anchor.reduced, "last_rect": anchor.lastRect.map { fixtureRect($0) as Any } ?? NSNull()]
            }
        }
        let live = flights.keys.sorted().compactMap { key -> [String: Any]? in
            guard let flight = flights[key] else { return nil }
            let view = flight.view
            return ["key": key, "view_identity": fixtureID(view), "frame": fixtureRect(view.frame),
                    "bounds": fixtureRect(view.bounds), "progress": Double(view.progress), "corner": Double(view.corner),
                    "from_rect": fixtureRect(flight.from.rect), "to_rect": fixtureRect(flight.to.rect),
                    "parent_is_actual_overlay": view.superview === overlay,
                    "window_number": view.window.map { $0.windowNumber as Any } ?? NSNull(),
                    "rect_in_root": view.window === root.window ? fixtureRect(view.convert(view.bounds, to: root)) as Any : NSNull(),
                    "source_identity": fixtureID(flight.source), "destination_identity": fixtureID(flight.destination),
                    "source_attached": flight.source.map { $0.attached as Any } ?? NSNull(),
                    "destination_attached": flight.destination.map { $0.attached as Any } ?? NSNull()]
        }
        return ["uptime": fixtureUptime(), "entries": entryValues, "entry_keys": entries.keys.sorted(),
                "departed": departed.mapValues { ["rect": fixtureRect($0.picture.rect), "time": $0.time] as [String: Any] },
                "flights": live, "flight_count": flights.count, "timer_exists": timer != nil,
                "overlay_attached": overlay.window != nil, "overlay_frame": fixtureRect(overlay.frame),
                "temporary_flight_view_count": overlay.subviews.filter { $0 is BernHeroFlightView }.count]
    }
    fileprivate func fixtureTrackFlight(_ refs: FixtureWeakRefs) {
        if let flight = flights[fixtureHeroKey] { refs.flight = flight.view }
    }
    fileprivate func fixtureMetalCount(root: NSView) -> Int {
        var seen = Set<ObjectIdentifier>()
        return (fixtureDescendants(root) + fixtureDescendants(overlay)).filter {
            seen.insert(ObjectIdentifier($0)).inserted && $0 is MTKView
        }.count
    }
}
@MainActor private func fixtureDescendants(_ root: NSView) -> [NSView] {
    [root] + root.subviews.flatMap { fixtureDescendants($0) }
}
@MainActor private func fixtureNormal() -> [String: Bool] {
    ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
     "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
     "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
}
@MainActor private func fixtureLedger(_ url: URL) throws -> [String: Any] {
    guard let picture = BernPictures.shared.cached(url.absoluteString),
          let bytes = picture.image.dataProvider?.data, let profile = picture.image.colorSpace?.copyICCData() else {
        throw FixtureFailure(message: "Actual cache/provider/ICC missing")
    }
    let derived = picture.legacyStandardPQImage
    return ["image_identity": fixtureID(picture.image), "file_sha256": fixtureHash(try Data(contentsOf: url)),
            "original_provider_sha256": fixtureHash(bytes as Data), "original_icc_sha256": fixtureHash(profile as Data),
            "orientation": String(describing: picture.orientation), "ratio": picture.ratio,
            "original_size": [picture.image.width, picture.image.height],
            "original_bitmap_info": picture.image.bitmapInfo.rawValue, "original_alpha_info": picture.image.alphaInfo.rawValue,
            "derived_identity": fixtureID(derived),
            "derived_provider_sha256": derived?.dataProvider?.data.map { fixtureHash($0 as Data) } ?? "nil",
            "derived_icc_sha256": derived?.colorSpace?.copyICCData().map { fixtureHash($0 as Data) } ?? "nil",
            "average_rgb": BernPictures.shared.averages[url.absoluteString].map { $0 as Any } ?? NSNull()]
}
@MainActor private func fixtureWindowInfo(_ window: NSWindow, initialFrame: CGRect, front: pid_t,
                                         manager: BernWindowImageHeroes?, root: NSView) throws -> [String: Any] {
    let rows = CGWindowListCopyWindowInfo(.optionIncludingWindow, CGWindowID(window.windowNumber)) as? [[String: Any]] ?? []
    let metal = manager?.fixtureMetalCount(root: root) ?? fixtureDescendants(root).filter { $0 is MTKView }.count
    guard rows.count == 1, let row = rows.first, row[kCGWindowOwnerPID as String] as? pid_t == getpid(),
          row[kCGWindowNumber as String] as? Int == window.windowNumber,
          row[kCGWindowIsOnscreen as String] as? Bool == true, window.isVisible,
          !window.isKeyWindow, !NSApplication.shared.isActive, window.frame == initialFrame,
          NSWorkspace.shared.frontmostApplication?.processIdentifier == front,
          fixtureNormal().values.allSatisfy({ !$0 }), metal == 0 else {
        throw FixtureFailure(message: "Own onscreen window/nonkey/inactive/front/frame/normal/no-Metal gate failed")
    }
    return row
}
@MainActor private func fixtureShot(_ window: NSWindow, root: NSView, manager: BernWindowImageHeroes,
                                   initialFrame: CGRect, front: pid_t, rois: [String: CGRect]) throws -> (CGImage, [String: Any]) {
    _ = try fixtureWindowInfo(window, initialFrame: initialFrame, front: front, manager: manager, root: root)
    let beforeTime = fixtureUptime(), before = manager.fixtureScalars(root: root)
    guard let image = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(window.windowNumber), .boundsIgnoreFraming),
          let bytes = image.dataProvider?.data, let profile = image.colorSpace?.copyICCData(), let screen = window.screen else {
        throw FixtureFailure(message: "Own WindowServer image/buffer/ICC/screen missing")
    }
    let afterTime = fixtureUptime(), after = manager.fixtureScalars(root: root)
    var regions: [String: Any] = [:]
    for (name, rect) in rois {
        let win = root.convert(rect, to: nil)
        let pixels = CGRect(x: win.minX * CGFloat(image.width) / window.frame.width,
                            y: (window.frame.height - win.maxY) * CGFloat(image.height) / window.frame.height,
                            width: win.width * CGFloat(image.width) / window.frame.width,
                            height: win.height * CGFloat(image.height) / window.frame.height)
        regions[name] = ["root_points": fixtureRect(rect), "screenshot_pixels": fixtureRect(pixels)]
    }
    _ = try fixtureWindowInfo(window, initialFrame: initialFrame, front: front, manager: manager, root: root)
    return (image, ["capture_before_uptime": beforeTime, "capture_after_uptime": afterTime,
        "state_before": before, "state_after": after, "owner_pid": getpid(), "window_id": window.windowNumber,
        "window_frame": fixtureRect(window.frame), "capture_size": [image.width, image.height], "rois": regions,
        "raw_buffer_sha256": fixtureHash(bytes as Data), "capture_icc_sha256": fixtureHash(profile as Data),
        "capture_space_name": image.colorSpace?.name as String? ?? "unnamed",
        "current_headroom": screen.maximumExtendedDynamicRangeColorComponentValue,
        "potential_headroom": screen.maximumPotentialExtendedDynamicRangeColorComponentValue,
        "key": window.isKeyWindow, "active": NSApplication.shared.isActive, "live_metal_count": 0])
}
private func fixtureSave(_ image: CGImage, record: [String: Any], phase: String, output: URL) throws -> [String: Any] {
    let name = phase + ".png", url = output.appendingPathComponent(name)
    guard !FileManager.default.fileExists(atPath: url.path),
          let destination = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw FixtureFailure(message: "PNG exists or destination unavailable")
    }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else { throw FixtureFailure(message: "PNG finalize failed") }
    var value = record; value["phase"] = phase; value["png"] = name
    value["png_sha256"] = fixtureHash(try Data(contentsOf: url)); return value
}
@MainActor private final class FixtureAppRun: NSObject, NSApplicationDelegate {
    let asset: URL, output: URL
    let expected: Int, front: pid_t
    var window: NSWindow?, host: NSView?, watchdog: DispatchSourceTimer?, sampler: Timer?
    weak var manager: BernWindowImageHeroes?
    let model = FixtureModel(), refs = FixtureWeakRefs()
    var started: Double?, initialFrame = CGRect.zero, deadline = 0.0, preloadStarted: Double?, preloadCompleted: Double?
    var loaded = false, loadOK = false, terminal = false, result: Int32 = 1
    var samples: [[String: Any]] = [], captures: [[String: Any]] = [], ledgerBefore: [String: Any] = [:]
    var report: [String: Any]
    var stage = "preloading", previousHash = "", equalBuffers = 0, transitionCount = 0
    var sawFlight = false, sawMovement = false, nextSampleCaptured = false, previousLiveFrame: [String: Double]?, previousProgress: Double?
    var midArmed: [String: Any]?, sourceID = "", sourceRect: CGRect?, sawSourceDetached = false, observedFlightID: String?
    var midSampling: [String: Any] = ["policy": "first_band_arm_then_next_original_loop_sample",
        "armed": NSNull(), "capture_sample": NSNull(), "capture_attempted": false, "next_sample_captured": false]
    var launchCount = 0, entryCount = 0, returnCount = 0, callbackCount = 0, reentrantCount = 0, depth = 0, maximumDepth = 0
    var afterTerminalCallbacks = 0, terminalCount = 0, stopCalls = 0, wakeCount = 0
    var launchTime: Double?, entryTime: Double?, returnTime: Double?, terminalTime: Double?
    var samplerStopped = false, wakeAfterTerminal = false, wakePosted = false, observedModes = Set<String>()
    init(asset: URL, output: URL, expected: Int, front: pid_t) {
        self.asset = asset; self.output = output; self.expected = expected; self.front = front
        self.report = ["success": false, "activation_calls": 0,
            "expected_os_major": expected, "actual_os_major": ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
            "scope": "One actual same-key SwiftUI conditional BernImage replacement and original coordinator clock; native acquisition gates only",
            "pixel_acceptance": "Not performed; before/mid/settled PNGs require offline visibility/color/timing review",
            "watchdog_seconds": 7.9, "collection_seconds": 7.2, "preload_seconds_limit": 3,
            "sample_limit": 512, "nominal_poll_hz": 60, "maximum_pngs": 3]
        super.init(); report["midflight_sampling"] = midSampling
    }
    func validate() throws {
        try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
        guard [13, 14].contains(expected), ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expected,
              CGPreflightScreenCaptureAccess(), !bernForcedReduceMotion, bernMotionScale == 1,
              fixtureHash(try Data(contentsOf: asset)) == "3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b" else {
            throw FixtureFailure(message: "Fresh output, exact named asset, expected13/14, screen permission and default motion required")
        }
        report["normal_before"] = fixtureNormal()
        guard fixtureNormal().values.allSatisfy({ !$0 }) else { throw FixtureFailure(message: "Normal flags required") }
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        launchCount += 1; launchTime = fixtureUptime()
        guard launchCount == 1, !terminal else { finish(FixtureFailure(message: "Unexpected duplicate launch notification")); return }
        preloadStarted = fixtureUptime()
        let timer = Timer(timeInterval: 1.0 / 60, target: self, selector: #selector(sampleTimer(_:)), userInfo: nil, repeats: true)
        sampler = timer; RunLoop.main.add(timer, forMode: .default)
        let url = asset.absoluteString
        Task { @MainActor [weak self] in
            let ok = await BernPictures.shared.load(url) != nil
            guard let self, !self.terminal else { return }
            self.loadOK = ok; self.loaded = true; self.preloadCompleted = fixtureUptime()
        }
    }
    private func makeWindow() throws {
        ledgerBefore = try fixtureLedger(asset); report["cache_before"] = ledgerBefore
        let root = NSHostingView(rootView: FixtureScene(model: model, url: asset.absoluteString))
        root.frame = CGRect(x: 0, y: 0, width: 1024, height: 440); host = root
        let w = FixtureWindow(contentRect: CGRect(x: 100, y: 100, width: 1024, height: 440), styleMask: [.titled], backing: .buffered, defer: false)
        window = w; w.isReleasedWhenClosed = false; w.isRestorable = false
        w.title = "Bern actual coordinator"; w.contentView = root
        let timer = DispatchSource.makeTimerSource(queue: .global(qos: .userInitiated)); watchdog = timer
        timer.setEventHandler { [output = self.output] in
            let failure: [String: Any] = ["success": false, "error": "Own7.9second watchdog; partial files only", "own_pid": getpid()]
            try? JSONSerialization.data(withJSONObject: failure, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic)
            _exit(124)
        }
        started = fixtureUptime(); timer.schedule(deadline: .now() + 7.9); timer.resume(); w.orderFrontRegardless()
        initialFrame = w.frame; deadline = started! + 7.2
        stage = "before"
    }
    @objc private func sampleTimer(_ timer: Timer) {
        callbackCount += 1
        guard !terminal else { afterTerminalCallbacks += 1; return }
        depth += 1; maximumDepth = max(maximumDepth, depth); defer { depth -= 1 }
        guard depth == 1 else { reentrantCount += 1; finish(FixtureFailure(message: "Reentrant sampler callback")); return }
        observedModes.insert(RunLoop.current.currentMode?.rawValue ?? "nil")
        do {
            guard RunLoop.current.currentMode == .default else { throw FixtureFailure(message: "Sampler did not run in default mode") }
            if stage == "preloading" {
                guard let begin = preloadStarted else { throw FixtureFailure(message: "Preload not started") }
                if loaded {
                    guard loadOK, let completed = preloadCompleted, completed <= begin + 3 else { throw FixtureFailure(message: "Actual preload deadline/failure") }
                    try makeWindow()
                } else if fixtureUptime() >= begin + 3 { throw FixtureFailure(message: "Actual preload deadline") }
                return
            }
            guard fixtureUptime() < deadline, samples.count < 512 else { throw FixtureFailure(message: "Collection entry deadline/sample bound; incomplete") }
            try sampleOnce()
            guard !terminal else { return }
            if stage == "complete" { try validateFinal(); finish(nil) }
        } catch { finish(error) }
    }
    private func sampleOnce() throws {
        guard let w = window, let root = host else { throw FixtureFailure(message: "Missing owned window/root") }
        if midArmed != nil && !nextSampleCaptured && manager == nil { throw FixtureFailure(message: "Armed flight manager lost on the next original iteration") }
        _ = try fixtureWindowInfo(w, initialFrame: initialFrame, front: front, manager: manager, root: root)
        // These local arrays end this iteration, before the next runloop/dismantle pass.
        var anchors = fixtureDescendants(root).compactMap { $0 as? BernPictureHeroAnchor }
        if manager == nil {
            guard fixtureUptime() - started! < 1.5 else { throw FixtureFailure(message: "Actual attached-source manager readiness deadline") }
            manager = anchors.first(where: { $0.key == fixtureHeroKey && $0.attached && $0.picture != nil })?.heroes
        }
        guard let heroes = manager else { return }
        let state = heroes.fixtureScalars(root: root)
        guard let sampleUptime = state["uptime"] as? Double else { throw FixtureFailure(message: "Missing actual sample uptime") }
        let sampleIndex = samples.count
        guard anchors.allSatisfy({ $0.key == fixtureHeroKey && !$0.reduced }),
              Set(state["entry_keys"] as? [String] ?? []).isSubset(of: [fixtureHeroKey]) else { throw FixtureFailure(message: "Unexpected key/reduced motion") }
        let flights = state["flights"] as? [[String: Any]] ?? []
        let timerExists = state["timer_exists"] as? Bool == true
        var sample = state; sample["stage"] = stage; sample["elapsed_seconds"] = fixtureUptime() - started!
        sample["sample_index"] = sampleIndex; sample["anchor_count"] = anchors.count; samples.append(sample)
        if let source = refs.source, !source.attached { sawSourceDetached = true }
        var rois: [String: CGRect] = [:]
        for anchor in anchors where anchor.window === w { rois["anchor-" + String(describing: ObjectIdentifier(anchor))] = anchor.convert(anchor.bounds, to: root) }
        if !flights.isEmpty {
            guard stage == "transition", flights.count == 1, timerExists,
                  let live = flights.first, live["key"] as? String == fixtureHeroKey,
                  live["parent_is_actual_overlay"] as? Bool == true,
                  live["window_number"] as? Int == w.windowNumber,
                  let identity = live["view_identity"] as? String,
                  let frame = live["frame"] as? [String: Double], let progress = live["progress"] as? Double,
                  live["from_rect"] as? [String: Double] != live["to_rect"] as? [String: Double] else { throw FixtureFailure(message: "Actual flight/timer/overlay/distinct rect gate failed") }
            if let first = observedFlightID, first != identity { throw FixtureFailure(message: "Observed flight identity changed during the single transition") }
            observedFlightID = identity; report["observed_flight_identities"] = [identity]
            sawFlight = true; heroes.fixtureTrackFlight(refs)
            if let old = previousLiveFrame, old != frame, let p = previousProgress, p != progress { sawMovement = true }
            previousLiveFrame = frame; previousProgress = progress
            if let flight = refs.flight { rois["flight"] = flight.convert(flight.bounds, to: root) }
            if let armed = midArmed, !nextSampleCaptured {
                guard let armedIndex = armed["sample_index"] as? Int, sampleIndex == armedIndex + 1,
                      armed["flight_identity"] as? String == identity else {
                    throw FixtureFailure(message: "Armed capture did not reach the exact next sample of the same flight")
                }
                let captureSample: [String: Any] = ["sample_index": sampleIndex, "state": state,
                    "uptime": sampleUptime, "progress": progress, "flight_identity": identity]
                midSampling["capture_sample"] = captureSample; midSampling["capture_attempted"] = true
                report["midflight_sampling"] = midSampling
                let (image, shot) = try fixtureShot(w, root: root, manager: heroes, initialFrame: initialFrame, front: front, rois: rois)
                guard !terminal else { throw FixtureFailure(message: "Sampler terminated during capture") }
                var value = shot
                value["sampling_policy"] = midSampling["policy"]
                value["armed_sample_index"] = armed["sample_index"]; value["armed_sample_state"] = armed["state"]
                value["armed_sample_uptime"] = armed["uptime"]; value["armed_progress"] = armed["progress"]
                value["armed_flight_identity"] = armed["flight_identity"]
                value["capture_sample_index"] = sampleIndex; value["capture_sample_state"] = state
                value["capture_sample_uptime"] = sampleUptime; value["capture_sample_progress"] = progress
                value["capture_sample_flight_identity"] = identity
                value["trigger_state"] = armed["state"]; value["trigger_progress"] = armed["progress"]
                value["trigger_refers_to"] = "armed_sample"; value["consecutive_equal_buffers_required"] = false
                captures.append(try fixtureSave(image, record: value, phase: "in-flight", output: output))
                nextSampleCaptured = true; midSampling["next_sample_captured"] = true
                report["midflight_sampling"] = midSampling
            } else if midArmed == nil && progress > 0.2 && progress < 0.8 {
                let armed: [String: Any] = ["sample_index": sampleIndex, "state": state,
                    "uptime": sampleUptime, "progress": progress, "flight_identity": identity]
                midArmed = armed; midSampling["armed"] = armed
                report["midflight_sampling"] = midSampling // No capture on the arming iteration.
            }
            return
        }
        if midArmed != nil && !nextSampleCaptured { throw FixtureFailure(message: "Armed flight no longer live at its next sample; incomplete") }
        if stage == "before" {
            guard fixtureUptime() - started! < 1.5 else { throw FixtureFailure(message: "Initial source readiness/stability deadline") }
            guard anchors.count == 1, let source = anchors.first, source.attached, source.picture != nil,
                  source.bounds.size == CGSize(width: 320, height: 180), !timerExists else { return }
            let rect = source.convert(source.bounds, to: root)
            guard root.bounds.contains(rect), fixtureNear(rect, CGRect(x: 16, y: 24, width: 320, height: 180)) else { throw FixtureFailure(message: "Source rectangle outside root/not at prescribed rect") }
            refs.source = source; sourceID = String(describing: ObjectIdentifier(source)); sourceRect = rect
            rois["source"] = rect
        } else {
            let sourceGone = refs.source == nil || refs.source?.attached == false
            let viewRemoved = refs.flight == nil || refs.flight?.superview == nil
            let entries = state["entries"] as? [String: [[String: Any]]] ?? [:]
            let liveEntries = entries[fixtureHeroKey] ?? []
            let ready = sawFlight && sawMovement && midArmed != nil && nextSampleCaptured && captures.contains(where: { $0["phase"] as? String == "in-flight" }) &&
                !timerExists && state["temporary_flight_view_count"] as? Int == 0 && sourceGone && viewRemoved &&
                liveEntries.count == 1 && liveEntries.first?["identity"] as? String != sourceID && anchors.count == 1
            guard ready, let destination = anchors.first, destination.attached, destination.picture != nil,
                  destination.bounds.size == CGSize(width: 320, height: 180) else {
                previousHash = ""; equalBuffers = 0
                if stage == "settled" { throw FixtureFailure(message: "Native state changed during settled stability gate") }
                return
            }
            let rect = destination.convert(destination.bounds, to: root)
            guard root.bounds.contains(rect), rect != sourceRect,
                  fixtureNear(rect, CGRect(x: 352, y: 244, width: 320, height: 180)) else { throw FixtureFailure(message: "Destination rect invalid/not at prescribed distinct rect") }
            rois["destination"] = rect; stage = "settled"
        }
        let (image, shot) = try fixtureShot(w, root: root, manager: heroes, initialFrame: initialFrame, front: front, rois: rois)
        guard !terminal else { throw FixtureFailure(message: "Sampler terminated during capture") }
        guard ["state_before", "state_after"].allSatisfy({ key in
            let s = shot[key] as? [String: Any] ?? [:]
            return s["flight_count"] as? Int == 0 && s["timer_exists"] as? Bool == false && s["temporary_flight_view_count"] as? Int == 0
        }) else { throw FixtureFailure(message: "Endpoint capture crossed a live coordinator state") }
        let hash = shot["raw_buffer_sha256"] as? String ?? ""
        equalBuffers = hash == previousHash ? equalBuffers + 1 : 1; previousHash = hash
        guard equalBuffers >= 5 else { return }
        var value = shot; value["consecutive_equal_buffers"] = equalBuffers
        captures.append(try fixtureSave(image, record: value, phase: stage, output: output))
        if stage == "before" {
            report["source_identity"] = sourceID; report["source_rect_in_root"] = sourceRect.map { fixtureRect($0) as Any } ?? NSNull()
            report["transition_uptime"] = fixtureUptime(); transitionCount += 1
            anchors.removeAll() // Do not retain the source across the actual conditional dismantle.
            model.atDestination = true
            stage = "transition"; previousHash = ""; equalBuffers = 0
        } else { stage = "complete" }
    }
    private func validateFinal() throws {
        guard stage == "complete", transitionCount == 1, sawFlight, sawMovement, midArmed != nil, nextSampleCaptured, captures.count == 3,
              captures.map({ $0["phase"] as? String ?? "" }) == ["before", "in-flight", "settled"] else { throw FixtureFailure(message: "Lifecycle/armed-next-sample/settled deadline; incomplete") }
        let ledgerAfter = try fixtureLedger(asset); report["cache_after"] = ledgerAfter
        let unchanged = NSDictionary(dictionary: ledgerAfter).isEqual(to: ledgerBefore); report["cache_unchanged"] = unchanged
        guard unchanged, fixtureNormal().values.allSatisfy({ !$0 }), NSWorkspace.shared.frontmostApplication?.processIdentifier == front else { throw FixtureFailure(message: "Final cache/normal/front gate failed") }
        report["native_gates"] = ["transition_count": transitionCount, "actual_flight_seen": sawFlight,
            "actual_frame_and_progress_changed": sawMovement, "midband_armed": midArmed != nil,
            "next_sample_captured": nextSampleCaptured,
            "observed_flight_identities": observedFlightID.map { [$0] } ?? [],
            "source_detached_observed": sawSourceDetached, "source_weak_deallocated": refs.source == nil,
            "source_no_longer_attached": refs.source == nil || refs.source?.attached == false,
            "temporary_view_removed": refs.flight == nil || refs.flight?.superview == nil]
    }
    private func finish(_ failure: Error?) {
        guard !terminal else { return }
        terminal = true; terminalCount += 1; terminalTime = fixtureUptime()
        if let failure { report["error"] = String(describing: failure); report["success"] = false; result = 1
            FileHandle.standardError.write(Data("Coordinator gate incomplete: \(failure)\n".utf8))
        } else { report["success"] = true; result = 0 }
        sampler?.invalidate(); sampler = nil; samplerStopped = true
        stopCalls += 1; NSApplication.shared.stop(nil)
        if let wake = NSEvent.otherEvent(with: .applicationDefined, location: .zero, modifierFlags: [], timestamp: fixtureUptime(), windowNumber: 0, context: nil, subtype: 0, data1: 0, data2: 0) {
            wakeAfterTerminal = terminal; NSApplication.shared.postEvent(wake, atStart: false)
            wakeCount += 1; wakePosted = true
        } else { report["success"] = false; report["error"] = "Terminal wake event creation failed; incomplete"; result = 1 }
    }
    func noteLoopEntry() { entryCount += 1; entryTime = fixtureUptime() }
    func noteLoopReturn() {
        returnCount += 1; returnTime = fixtureUptime()
        if !terminal || launchCount != 1 || entryCount != 1 || returnCount != 1 || stopCalls != 1 || wakeCount != 1 || reentrantCount != 0 || afterTerminalCallbacks != 0 {
            result = 1; report["success"] = false
            report["execution_contract_error"] = "App loop execution contract incomplete"
            if report["error"] == nil { report["error"] = "App loop execution contract incomplete" }
        }
    }
    func executionModel() -> [String: Any] {
        ["kind": "nsapplication_run_delegate_default_timer", "launch_completed_count": launchCount,
         "launch_completed_uptime": launchTime.map { $0 as Any } ?? NSNull(),
         "loop_entry_count": entryCount, "loop_entry_uptime": entryTime.map { $0 as Any } ?? NSNull(),
         "loop_return_count": returnCount, "loop_return_uptime": returnTime.map { $0 as Any } ?? NSNull(),
         "sampler_mode": RunLoop.Mode.default.rawValue, "sampler_observed_modes": observedModes.sorted(),
         "sampler_interval_seconds": 1.0 / 60, "sampler_callback_count": callbackCount,
         "sampler_reentrant_callbacks": reentrantCount, "sampler_max_depth": maximumDepth,
         "sampler_callbacks_after_terminal": afterTerminalCallbacks, "sampler_invalidated_before_stop": samplerStopped,
         "terminal_count": terminalCount, "terminal_uptime": terminalTime.map { $0 as Any } ?? NSNull(),
         "stop_calls": stopCalls, "wake_count": wakeCount, "wake_after_terminal": wakeAfterTerminal,
         "wake_type": "applicationDefined", "wake_posted_to_own_app_queue": wakePosted,
         "preload_started_uptime": preloadStarted.map { $0 as Any } ?? NSNull(),
         "preload_completed_uptime": preloadCompleted.map { $0 as Any } ?? NSNull()]
    }
    func cleanupAndWrite() {
        report["samples"] = samples; report["captures"] = captures; report["execution_model"] = executionModel()
        if let root = host, let heroes = manager { report["before_cleanup_state"] = heroes.fixtureScalars(root: root) }
        sampler?.invalidate(); sampler = nil
        window?.orderOut(nil); window?.contentView = nil; window?.close(); watchdog?.cancel()
        report["window_seconds"] = started.map { (fixtureUptime() - $0) as Any } ?? NSNull()
        report["normal_after"] = fixtureNormal(); report["frontmost_before"] = front
        report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        if !fixtureNormal().values.allSatisfy({ !$0 }) || NSWorkspace.shared.frontmostApplication?.processIdentifier != front {
            report["success"] = false; report["error"] = "Final normal/front contract failed"; HeroCoordinatorMain.finalizationFailed = true
        }
        do { try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic) }
        catch { HeroCoordinatorMain.finalizationFailed = true; FileHandle.standardError.write(Data("Report write failed: \(error)\n".utf8)) }
    }
}
@main private enum HeroCoordinatorMain {
    @MainActor fileprivate static var finalizationFailed = false
    @MainActor static func main() { let status = run(); exit(status == 0 && finalizationFailed ? 1 : status) }
    @MainActor private static func run() -> Int32 {
        guard CommandLine.arguments.count == 3 else { FileHandle.standardError.write(Data("Usage: binary namedAsset output\n".utf8)); return 2 }
        let asset = URL(fileURLWithPath: CommandLine.arguments[1]), output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
        guard !FileManager.default.fileExists(atPath: output.appendingPathComponent("report.json").path) else {
            FileHandle.standardError.write(Data("Refuse to overwrite existing report\n".utf8)); return 2
        }
        let expected = Int(ProcessInfo.processInfo.environment["BERN_HERO_EXPECT_OS"] ?? "13") ?? -1
        let state = FixtureAppRun(asset: asset, output: output, expected: expected, front: NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0)
        defer { state.cleanupAndWrite() }
        do {
            try state.validate()
            let app = NSApplication.shared; app.setActivationPolicy(.accessory); app.appearance = NSAppearance(named: .aqua)
            app.delegate = state; state.noteLoopEntry(); app.run(); state.noteLoopReturn()
            return state.result
        } catch {
            state.report["error"] = String(describing: error)
            FileHandle.standardError.write(Data("Coordinator gate incomplete: \(error)\n".utf8)); return 1
        }
    }
}
