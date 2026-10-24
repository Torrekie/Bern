import AppKit
import SwiftUI
// MARK: - Window-level image heroes

/// A geometry probe leaves the SwiftUI image's layout and accessibility
/// intact. Only its pixels move to the window overlay during a flight.
struct BernPictureHeroProbe: NSViewRepresentable {
    let id: String
    let picture: BernImage.Picture?
    let fit: BernImageFit
    let corner: CGFloat
    let motion: BernMotion
    let reduced: Bool
    /// Fly what the window shows where the element is, for elements other
    /// than images.
    var capturesView = false
    let visibility: (Bool) -> Void

    func makeNSView(context: Context) -> BernPictureHeroAnchor { BernPictureHeroAnchor() }
    func updateNSView(_ view: BernPictureHeroAnchor, context: Context) {
        if view.key != id { view.detach() }
        view.key = id
        view.picture = picture
        view.capturesView = capturesView
        view.fit = fit
        view.corner = corner
        view.motion = motion
        view.reduced = reduced
        view.visibility = visibility
        view.schedule()
    }
    static func dismantleNSView(_ view: BernPictureHeroAnchor, coordinator: ()) { view.detach() }
}

@MainActor
final class BernPictureHeroAnchor: NSView {
    var key = ""
    var picture: BernImage.Picture?
    var fit = BernImageFit.cover
    var corner: CGFloat = 0
    var motion = BernMotion(period: 0.48, damping: 0.86)
    var reduced = false
    var capturesView = false
    var visibility: ((Bool) -> Void)?
    weak var heroes: BernWindowImageHeroes?
    var attached = false
    /// Where the element was at its last layout, in the overlay, for when
    /// its container leaves the window before it does.
    var lastRect: CGRect?
    private var scheduled = false

    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    override func viewWillMove(toWindow newWindow: NSWindow?) {
        if newWindow !== window { detach() }
        super.viewWillMove(toWindow: newWindow)
    }
    override func viewDidMoveToWindow() { super.viewDidMoveToWindow(); schedule() }
    override func layout() { super.layout(); schedule() }

    func schedule() {
        guard !scheduled else { return }
        scheduled = true
        DispatchQueue.main.async { [weak self] in
            guard let self else { return }
            self.scheduled = false
            guard let window = self.window, self.bounds.width > 0, self.bounds.height > 0,
                  self.picture != nil || self.capturesView else { return }
            let heroes = BernWindowImageHeroes.forWindow(window)
            self.heroes = heroes
            self.lastRect = heroes.rect(of: self)
            if self.reduced { heroes.finish(self.key) }
            guard !self.attached else { return }
            self.attached = true
            heroes.enter(self)
        }
    }

    func detach() {
        guard attached else { return }
        heroes?.leave(self)
        attached = false
    }

    fileprivate func snapshot(in overlay: NSView) -> BernHeroPicture? {
        if capturesView { return capture(in: overlay) }
        guard let picture, window != nil, bounds.width > 0, bounds.height > 0 else { return nil }
        let rect = convert(bounds, to: overlay)
        guard rect.width > 0, rect.height > 0 else { return nil }
        let image = SwiftUI.Image(decorative: picture.image, scale: 1, orientation: picture.orientation).resizable()
        let fitted: AnyView
        switch fit {
        case .cover: fitted = AnyView(image.aspectRatio(contentMode: .fill))
        case .contain: fitted = AnyView(image.aspectRatio(contentMode: .fit))
        case .fill: fitted = AnyView(image)
        }
        let renderer = ImageRenderer(content: fitted.frame(width: bounds.width, height: bounds.height).clipped())
        renderer.scale = window?.backingScaleFactor ?? 2
        guard let pixels = renderer.cgImage else { return nil }
        return BernHeroPicture(rect: rect, image: NSImage(cgImage: pixels, size: bounds.size),
            corner: corner * rect.width / bounds.width)
    }
}

extension BernPictureHeroAnchor {
    /// What the window draws over the element's frame.
    fileprivate func capture(in overlay: NSView) -> BernHeroPicture? {
        guard let content = window?.contentView, bounds.width > 0, bounds.height > 0 else { return nil }
        let rect = convert(bounds, to: content).intersection(content.bounds)
        guard rect.width > 0, rect.height > 0,
              let pixels = content.bitmapImageRepForCachingDisplay(in: rect) else { return nil }
        content.cacheDisplay(in: rect, to: pixels)
        let image = NSImage(size: rect.size)
        image.addRepresentation(pixels)
        return BernHeroPicture(rect: content.convert(rect, to: overlay), image: image, corner: corner)
    }
}

/// A shared element other than an image on macOS: during the change the
/// element is hidden and a picture of it flies above the window, from the
/// element it replaces, cross-fading between the two. The element itself
/// is never moved or scaled: a split view laid out or transformed on the
/// way loses its toolbar safe area for good, its columns ending up under
/// the title bar.
struct BernViewHero: ViewModifier {
    let id: String
    let motion: BernMotion
    @BernReducedMotion private var reduce
    @State private var flying = false

    func body(content: Content) -> some View {
        content
            .opacity(flying ? 0 : 1)
            .background(BernPictureHeroProbe(id: id, picture: nil, fit: .fill, corner: 0,
                motion: motion, reduced: reduce || bernForcedReduceMotion, capturesView: true,
                visibility: { hidden in
                    var transaction = Transaction()
                    transaction.disablesAnimations = true
                    withTransaction(transaction) { flying = hidden }
                }))
    }
}

private struct BernHeroPicture {
    var rect: CGRect
    let image: NSImage
    var corner: CGFloat
}

/// Native view above every hosting view of the split. It never takes
/// clicks, focus or accessibility away from the real controls.
private final class BernHeroOverlay: NSView {
    override var isFlipped: Bool { true }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    override func accessibilityIsIgnored() -> Bool { true }
}

private final class BernHeroFlightView: NSView {
    let from: NSImage
    let to: NSImage
    var progress: CGFloat = 0
    var corner: CGFloat = 0
    init(from: NSImage, to: NSImage) {
        self.from = from; self.to = to
        super.init(frame: .zero)
    }
    required init?(coder: NSCoder) { fatalError("init(coder:) has not been implemented") }
    override var isFlipped: Bool { true }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    override func draw(_ dirtyRect: NSRect) {
        NSBezierPath(roundedRect: bounds, xRadius: max(0, corner), yRadius: max(0, corner)).addClip()
        from.draw(in: bounds, from: .zero, operation: .sourceOver, fraction: 1, respectFlipped: true, hints: nil)
        to.draw(in: bounds, from: .zero, operation: .sourceOver, fraction: min(1, max(0, progress)), respectFlipped: true, hints: nil)
    }
}

@MainActor
final class BernWindowImageHeroes {
    private static let windows = NSMapTable<NSWindow, BernWindowImageHeroes>.weakToStrongObjects()
    static func forWindow(_ window: NSWindow) -> BernWindowImageHeroes {
        if let existing = windows.object(forKey: window) { return existing }
        let heroes = BernWindowImageHeroes()
        heroes.window = window
        windows.setObject(heroes, forKey: window)
        return heroes
    }
    private weak var window: NSWindow?
    private let overlay = BernHeroOverlay()
    private class Entry {
        weak var anchor: BernPictureHeroAnchor?
        init(_ anchor: BernPictureHeroAnchor) { self.anchor = anchor }
    }
    private struct Departure {
        let picture: BernHeroPicture
        let time: TimeInterval
    }
    @MainActor private class Flight {
        let view: BernHeroFlightView
        let from: BernHeroPicture
        let to: BernHeroPicture
        weak var source: BernPictureHeroAnchor?
        weak var destination: BernPictureHeroAnchor?
        let motion: BernMotion
        let started = ProcessInfo.processInfo.systemUptime
        var progress: Double = 0
        init(from: BernHeroPicture, to: BernHeroPicture, source: BernPictureHeroAnchor?, destination: BernPictureHeroAnchor) {
            self.from = from; self.to = to; self.source = source; self.destination = destination
            self.motion = destination.motion
            view = BernHeroFlightView(from: from.image, to: to.image)
            view.frame = from.rect; view.corner = from.corner
        }
    }
    private var entries: [String: [Entry]] = [:]
    private var departed: [String: Departure] = [:]
    private var flights: [String: Flight] = [:]
    private var timer: Timer?

    private func prepareOverlay() -> Bool {
        guard let parent = window?.contentView?.superview ?? window?.contentView else { return false }
        if overlay.superview !== parent {
            overlay.removeFromSuperview()
            overlay.frame = parent.bounds
            overlay.autoresizingMask = [.width, .height]
            parent.addSubview(overlay, positioned: .above, relativeTo: nil)
        }
        return true
    }

    func enter(_ anchor: BernPictureHeroAnchor) {
        guard prepareOverlay() else { return }
        let key = anchor.key
        var previous = entries[key]?.last?.anchor
        var from = previous?.snapshot(in: overlay)
        if let departure = departed.removeValue(forKey: key),
           ProcessInfo.processInfo.systemUptime - departure.time < 0.3 {
            from = departure.picture
            previous = nil
        }
        // Reverse from the pixels currently on screen, including when
        // another state change arrives before the first flight settles.
        if let flight = flights[key] {
            from = BernHeroPicture(rect: flight.view.frame, image: flight.to.image, corner: flight.view.corner)
            previous = flight.destination
            finish(key)
        }
        entries[key, default: []].removeAll { $0.anchor == nil || $0.anchor === anchor }
        entries[key, default: []].append(Entry(anchor))
        guard !anchor.reduced, let from, let to = anchor.snapshot(in: overlay),
              from.rect != to.rect else { return }
        let flight = Flight(from: from, to: to, source: previous, destination: anchor)
        flights[key] = flight
        previous?.visibility?(true)
        anchor.visibility?(true)
        overlay.addSubview(flight.view)
        if timer == nil {
            let clock = Timer(timeInterval: 1 / 120.0, repeats: true) { [weak self] _ in
                MainActor.assumeIsolated { self?.tick() }
            }
            timer = clock
            RunLoop.main.add(clock, forMode: .common)
        }
    }

    /// Where `anchor` is in the overlay.
    func rect(of anchor: BernPictureHeroAnchor) -> CGRect? {
        guard prepareOverlay() else { return nil }
        return anchor.convert(anchor.bounds, to: overlay)
    }

    func leave(_ anchor: BernPictureHeroAnchor) {
        let key = anchor.key
        // An element whose container has already left the window no longer
        // converts to it; it departs from where it was last laid out.
        let connected = anchor.window?.contentView.map { anchor.isDescendant(of: $0) } == true
        if entries[key]?.last?.anchor === anchor,
           let from = connected ? rect(of: anchor) : anchor.lastRect,
           var picture = anchor.snapshot(in: overlay) {
            picture.rect = from
            departed[key] = Departure(picture: picture, time: ProcessInfo.processInfo.systemUptime)
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) { [weak self] in
                guard let self, let record = self.departed[key],
                      ProcessInfo.processInfo.systemUptime - record.time >= 0.3 else { return }
                self.departed.removeValue(forKey: key)
            }
        }
        entries[key]?.removeAll { $0.anchor == nil || $0.anchor === anchor }
        if entries[key]?.isEmpty == true { entries.removeValue(forKey: key) }
        // A replacement may mount later in this layout pass. Let it
        // retarget before retiring a flight whose destination was removed.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.05) { [weak self] in
            guard let self, let flight = self.flights[key], flight.destination?.attached != true else { return }
            self.finish(key)
        }
    }

    func finish(_ key: String) {
        guard let flight = flights.removeValue(forKey: key) else { return }
        flight.source?.visibility?(false)
        flight.destination?.visibility?(false)
        flight.view.removeFromSuperview()
        if flights.isEmpty { timer?.invalidate(); timer = nil }
    }

    private func tick() {
        let now = ProcessInfo.processInfo.systemUptime
        for (key, flight) in flights {
            guard window?.isVisible == true, flight.destination?.reduced != true else { finish(key); continue }
            // Keep the last pixels while the next layout pass mounts a
            // replacement; leave() retires abandoned destinations.
            guard flight.destination?.attached == true else { continue }
            let t = (now - flight.started) / bernMotionScale
            let omega = 2 * Double.pi / max(0.01, flight.motion.period)
            let damping = max(0.01, flight.motion.damping)
            let p: Double
            if damping < 1 {
                let frequency = omega * sqrt(1 - damping * damping)
                p = 1 - exp(-damping * omega * t) * (cos(frequency * t) + damping * omega / frequency * sin(frequency * t))
            } else if damping == 1 {
                p = 1 - exp(-omega * t) * (1 + omega * t)
            } else {
                let root = sqrt(damping * damping - 1)
                let a = -omega * (damping - root), b = -omega * (damping + root)
                p = 1 - (b * exp(a * t) - a * exp(b * t)) / (b - a)
            }
            let mix = { (a: CGFloat, b: CGFloat) in a + (b - a) * p }
            flight.view.frame = CGRect(x: mix(flight.from.rect.minX, flight.to.rect.minX),
                y: mix(flight.from.rect.minY, flight.to.rect.minY),
                width: max(1, mix(flight.from.rect.width, flight.to.rect.width)),
                height: max(1, mix(flight.from.rect.height, flight.to.rect.height)))
            flight.view.corner = mix(flight.from.corner, flight.to.corner)
            flight.view.progress = p
            flight.view.needsDisplay = true
            let settled = abs(p - 1) < 0.0001 && abs(p - flight.progress) < 0.0001
            flight.progress = p
            if (t > flight.motion.period && settled) || t > 5 { finish(key) }
        }
    }
}

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
@main private enum HeroCoordinatorMain {
    @MainActor private static var finalizationFailed = false
    @MainActor static func main() {
        let status = run(); exit(status == 0 && finalizationFailed ? 1 : status)
    }
    @MainActor private static func run() -> Int32 {
        guard CommandLine.arguments.count == 3 else {
            FileHandle.standardError.write(Data("Usage: binary namedAsset output\n".utf8)); return 2
        }
        let asset = URL(fileURLWithPath: CommandLine.arguments[1])
        let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
        guard !FileManager.default.fileExists(atPath: output.appendingPathComponent("report.json").path) else {
            FileHandle.standardError.write(Data("Refuse to overwrite existing report\n".utf8)); return 2
        }
        let expected = Int(ProcessInfo.processInfo.environment["BERN_HERO_EXPECT_OS"] ?? "13") ?? -1
        let front = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window: NSWindow?, host: NSView?, watchdog: DispatchSourceTimer?
        weak var manager: BernWindowImageHeroes?
        var started: Double?, samples: [[String: Any]] = [], captures: [[String: Any]] = []
        var report: [String: Any] = ["success": false, "activation_calls": 0,
            "expected_os_major": expected, "actual_os_major": ProcessInfo.processInfo.operatingSystemVersion.majorVersion,
            "scope": "One actual same-key SwiftUI conditional BernImage replacement and original coordinator clock; native acquisition gates only",
            "pixel_acceptance": "Not performed; before/mid/settled PNGs require offline visibility/color/timing review",
            "watchdog_seconds": 7.9, "collection_seconds": 7.2, "preload_seconds_limit": 3,
            "sample_limit": 512, "nominal_poll_hz": 60, "maximum_pngs": 3]
        defer {
            report["samples"] = samples; report["captures"] = captures
            if let root = host, let heroes = manager { report["before_cleanup_state"] = heroes.fixtureScalars(root: root) }
            window?.orderOut(nil); window?.contentView = nil; window?.close(); watchdog?.cancel()
            report["window_seconds"] = started.map { (fixtureUptime() - $0) as Any } ?? NSNull()
            report["normal_after"] = fixtureNormal(); report["frontmost_before"] = front
            report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            if !fixtureNormal().values.allSatisfy({ !$0 }) || NSWorkspace.shared.frontmostApplication?.processIdentifier != front {
                report["success"] = false; report["error"] = "Final normal/front contract failed"; finalizationFailed = true
            }
            do { try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic) }
            catch { finalizationFailed = true; FileHandle.standardError.write(Data("Report write failed: \(error)\n".utf8)) }
        }
        do {
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard [13, 14].contains(expected), ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expected,
                  CGPreflightScreenCaptureAccess(), !bernForcedReduceMotion, bernMotionScale == 1,
                  fixtureHash(try Data(contentsOf: asset)) == "3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b" else {
                throw FixtureFailure(message: "Fresh output, exact named asset, expected13/14, screen permission and default motion required")
            }
            report["normal_before"] = fixtureNormal()
            guard fixtureNormal().values.allSatisfy({ !$0 }) else { throw FixtureFailure(message: "Normal flags required") }
            let app = NSApplication.shared; app.setActivationPolicy(.accessory)
            app.appearance = NSAppearance(named: .aqua); app.finishLaunching()
            var loaded = false, loadOK = false
            Task { @MainActor in loadOK = await BernPictures.shared.load(asset.absoluteString) != nil; loaded = true }
            let preloadEnd = fixtureUptime() + 3
            while !loaded && fixtureUptime() < preloadEnd { RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.02)) }
            guard loaded, loadOK else { throw FixtureFailure(message: "Actual preload deadline") }
            let ledgerBefore = try fixtureLedger(asset); report["cache_before"] = ledgerBefore
            let model = FixtureModel(), refs = FixtureWeakRefs()
            let root = NSHostingView(rootView: FixtureScene(model: model, url: asset.absoluteString))
            root.frame = CGRect(x: 0, y: 0, width: 1024, height: 440); host = root
            let w = FixtureWindow(contentRect: CGRect(x: 100, y: 100, width: 1024, height: 440), styleMask: [.titled], backing: .buffered, defer: false)
            window = w; w.isReleasedWhenClosed = false; w.isRestorable = false
            w.title = "Bern actual coordinator"; w.contentView = root
            let timer = DispatchSource.makeTimerSource(queue: .global(qos: .userInitiated)); watchdog = timer
            timer.setEventHandler {
                let failure: [String: Any] = ["success": false, "error": "Own7.9second watchdog; partial files only", "own_pid": getpid()]
                try? JSONSerialization.data(withJSONObject: failure, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic)
                _exit(124)
            }
            started = fixtureUptime(); timer.schedule(deadline: .now() + 7.9); timer.resume(); w.orderFrontRegardless()
            let initialFrame = w.frame, deadline = started! + 7.2
            var stage = "before", previousHash = "", equalBuffers = 0, transitionCount = 0
            var sawFlight = false, sawMovement = false, midAttempted = false, previousLiveFrame: [String: Double]?, previousProgress: Double?
            var sourceID = "", sourceRect: CGRect?, sawSourceDetached = false
            var observedFlightID: String?
            while fixtureUptime() < deadline && stage != "complete" {
                guard samples.count < 512 else { throw FixtureFailure(message: "Sample bound; incomplete") }
                RunLoop.main.run(until: Date(timeIntervalSinceNow: 1.0 / 60))
                _ = try fixtureWindowInfo(w, initialFrame: initialFrame, front: front, manager: manager, root: root)
                // These local arrays end this iteration, before the next runloop/dismantle pass.
                var anchors = fixtureDescendants(root).compactMap { $0 as? BernPictureHeroAnchor }
                if manager == nil {
                    guard fixtureUptime() - started! < 1.5 else { throw FixtureFailure(message: "Actual attached-source manager readiness deadline") }
                    manager = anchors.first(where: { $0.key == fixtureHeroKey && $0.attached && $0.picture != nil })?.heroes
                }
                guard let heroes = manager else { continue }
                let state = heroes.fixtureScalars(root: root)
                guard anchors.allSatisfy({ $0.key == fixtureHeroKey && !$0.reduced }),
                      Set(state["entry_keys"] as? [String] ?? []).isSubset(of: [fixtureHeroKey]) else { throw FixtureFailure(message: "Unexpected key/reduced motion") }
                let flights = state["flights"] as? [[String: Any]] ?? []
                let timerExists = state["timer_exists"] as? Bool == true
                var sample = state; sample["stage"] = stage; sample["elapsed_seconds"] = fixtureUptime() - started!
                sample["anchor_count"] = anchors.count; samples.append(sample)
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
                    if !midAttempted && progress > 0.2 && progress < 0.8 {
                        midAttempted = true
                        let (image, shot) = try fixtureShot(w, root: root, manager: heroes, initialFrame: initialFrame, front: front, rois: rois)
                        var value = shot; value["trigger_state"] = state; value["trigger_progress"] = progress
                        value["consecutive_equal_buffers_required"] = false
                        captures.append(try fixtureSave(image, record: value, phase: "in-flight", output: output))
                    }
                    continue
                }
                if stage == "before" {
                    guard fixtureUptime() - started! < 1.5 else { throw FixtureFailure(message: "Initial source readiness/stability deadline") }
                    guard anchors.count == 1, let source = anchors.first, source.attached, source.picture != nil,
                          source.bounds.size == CGSize(width: 320, height: 180), !timerExists else { continue }
                    let rect = source.convert(source.bounds, to: root)
                    guard root.bounds.contains(rect), fixtureNear(rect, CGRect(x: 16, y: 24, width: 320, height: 180)) else { throw FixtureFailure(message: "Source rectangle outside root/not at prescribed rect") }
                    refs.source = source; sourceID = String(describing: ObjectIdentifier(source)); sourceRect = rect
                    rois["source"] = rect
                } else {
                    let sourceGone = refs.source == nil || refs.source?.attached == false
                    let viewRemoved = refs.flight == nil || refs.flight?.superview == nil
                    let entries = state["entries"] as? [String: [[String: Any]]] ?? [:]
                    let liveEntries = entries[fixtureHeroKey] ?? []
                    let ready = sawFlight && sawMovement && midAttempted && captures.contains(where: { $0["phase"] as? String == "in-flight" }) &&
                        !timerExists && state["temporary_flight_view_count"] as? Int == 0 && sourceGone && viewRemoved &&
                        liveEntries.count == 1 && liveEntries.first?["identity"] as? String != sourceID && anchors.count == 1
                    guard ready, let destination = anchors.first, destination.attached, destination.picture != nil,
                          destination.bounds.size == CGSize(width: 320, height: 180) else {
                        previousHash = ""; equalBuffers = 0
                        if stage == "settled" { throw FixtureFailure(message: "Native state changed during settled stability gate") }
                        continue
                    }
                    let rect = destination.convert(destination.bounds, to: root)
                    guard root.bounds.contains(rect), rect != sourceRect,
                          fixtureNear(rect, CGRect(x: 352, y: 244, width: 320, height: 180)) else { throw FixtureFailure(message: "Destination rect invalid/not at prescribed distinct rect") }
                    rois["destination"] = rect; stage = "settled"
                }
                let (image, shot) = try fixtureShot(w, root: root, manager: heroes, initialFrame: initialFrame, front: front, rois: rois)
                guard ["state_before", "state_after"].allSatisfy({ key in
                    let s = shot[key] as? [String: Any] ?? [:]
                    return s["flight_count"] as? Int == 0 && s["timer_exists"] as? Bool == false && s["temporary_flight_view_count"] as? Int == 0
                }) else { throw FixtureFailure(message: "Endpoint capture crossed a live coordinator state") }
                let hash = shot["raw_buffer_sha256"] as? String ?? ""
                equalBuffers = hash == previousHash ? equalBuffers + 1 : 1; previousHash = hash
                guard equalBuffers >= 5 else { continue }
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
            guard stage == "complete", transitionCount == 1, sawFlight, sawMovement, captures.count == 3,
                  captures.map({ $0["phase"] as? String ?? "" }) == ["before", "in-flight", "settled"] else { throw FixtureFailure(message: "Lifecycle/midband/settled deadline; incomplete") }
            let ledgerAfter = try fixtureLedger(asset); report["cache_after"] = ledgerAfter
            let unchanged = NSDictionary(dictionary: ledgerAfter).isEqual(to: ledgerBefore); report["cache_unchanged"] = unchanged
            guard unchanged, fixtureNormal().values.allSatisfy({ !$0 }), NSWorkspace.shared.frontmostApplication?.processIdentifier == front else { throw FixtureFailure(message: "Final cache/normal/front gate failed") }
            report["native_gates"] = ["transition_count": transitionCount, "actual_flight_seen": sawFlight,
                "actual_frame_and_progress_changed": sawMovement, "midband_captured": midAttempted,
                "observed_flight_identities": observedFlightID.map { [$0] } ?? [],
                "source_detached_observed": sawSourceDetached, "source_weak_deallocated": refs.source == nil,
                "source_no_longer_attached": refs.source == nil || refs.source?.attached == false,
                "temporary_view_removed": refs.flight == nil || refs.flight?.superview == nil]
            report["success"] = true; return 0
        } catch {
            report["error"] = String(describing: error)
            FileHandle.standardError.write(Data("Coordinator gate incomplete: \(error)\n".utf8)); return 1
        }
    }
}
