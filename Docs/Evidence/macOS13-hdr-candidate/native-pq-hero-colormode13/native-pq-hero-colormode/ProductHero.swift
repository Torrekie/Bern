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
        // Diagnostic only: default deliberately leaves the actual renderer unset.
        if let colorMode = FixtureHeroColorMode.selected?.rendererMode {
            renderer.colorMode = colorMode
        }
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
                #if compiler(>=6.0)
                MainActor.assumeIsolated { self?.tick() }
                #else
                // Diagnostic SDK14.2 only: this static-endpoint fixture must
                // never start the coordinator's clock. Keep the actual14 call.
                if #available(macOS 14, *) {
                    MainActor.assumeIsolated { self?.tick() }
                } else {
                    preconditionFailure("Static endpoint fixture unexpectedly started its excluded timer")
                }
                #endif
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

// Fixture-only entry point, appended in this file to preserve product access control.
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

// Diagnostic-only configuration: environment is read exactly once per process.
private enum FixtureHeroColorMode: String {
    case systemDefault = "default"
    case linear
    case extendedLinear
    case nonLinear

    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_COLOR_MODE"]
    static let selected = FixtureHeroColorMode(rawValue: requested ?? "default")

    var rendererMode: ColorRenderingMode? {
        switch self {
        case .systemDefault: return nil
        case .linear: return .linear
        case .extendedLinear: return .extendedLinear
        case .nonLinear: return .nonLinear
        }
    }
}

private struct FixtureFailure: Error { let message: String }
private func fixtureHash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
private func fixtureRect(_ r: CGRect) -> [String: Double] {
    ["x": r.minX, "y": r.minY, "width": r.width, "height": r.height]
}
private func fixtureSavePNG(_ image: CGImage, _ url: URL) throws {
    guard let d = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw FixtureFailure(message: "PNG destination unavailable")
    }
    CGImageDestinationAddImage(d, image, nil)
    guard CGImageDestinationFinalize(d) else { throw FixtureFailure(message: "PNG finalize failed") }
}
@MainActor private func fixtureLedger(_ urls: [URL]) throws -> [String: Any] {
    var result: [String: Any] = [:]
    for url in urls {
        guard let p = BernPictures.shared.cached(url.absoluteString),
              let bytes = p.image.dataProvider?.data, let icc = p.image.colorSpace?.copyICCData() else {
            throw FixtureFailure(message: "Product cache/provider/ICC missing")
        }
        let d = p.legacyStandardPQImage
        var item: [String: Any] = [:]
        item["image_id"] = String(describing: ObjectIdentifier(p.image))
        item["original_provider_sha256"] = fixtureHash(bytes as Data)
        item["original_icc_sha256"] = fixtureHash(icc as Data)
        item["file_sha256"] = fixtureHash(try Data(contentsOf: url))
        item["orientation"] = String(describing: p.orientation); item["ratio"] = p.ratio
        item["original_size"] = [p.image.width, p.image.height]
        item["original_bitmap_info"] = p.image.bitmapInfo.rawValue
        item["original_alpha_info"] = p.image.alphaInfo.rawValue
        item["original_space_name"] = p.image.colorSpace?.name as String? ?? "unnamed"
        item["original_uses_2100_tf"] = p.image.colorSpace.map { CGColorSpaceUsesITUR_2100TF($0) } ?? false
        item["legacy_hdr_space_name"] = p.legacyHDRColorSpace?.name as String? ?? "nil"
        item["derived_is_pq_based"] = d?.colorSpace.map { CGColorSpaceIsPQBased($0) } ?? false
        item["cached_average_rgb"] = BernPictures.shared.averages[url.absoluteString].map { $0 as Any } ?? NSNull()
        item["derived_id"] = d.map { String(describing: ObjectIdentifier($0)) } ?? "nil"
        item["derived_provider_sha256"] = d?.dataProvider?.data.map { fixtureHash($0 as Data) } ?? "nil"
        item["derived_icc_sha256"] = d?.colorSpace?.copyICCData().map { fixtureHash($0 as Data) } ?? "nil"
        result[url.lastPathComponent] = item
    }
    return result
}
private final class FixtureWindow: NSWindow {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
private final class FixtureRoot: NSView {
    override var isFlipped: Bool { true }
    override var isOpaque: Bool { true }
    override func draw(_ dirtyRect: NSRect) { NSColor.white.setFill(); dirtyRect.fill() }
}
extension BernWindowImageHeroes {
    fileprivate func fixtureSnapshot(_ anchor: BernPictureHeroAnchor) -> BernHeroPicture? {
        guard prepareOverlay() else { return nil }
        return anchor.snapshot(in: overlay)
    }
    fileprivate var fixtureState: [String: Any] {
        ["entries": entries.mapValues { $0.compactMap { $0.anchor?.key } },
         "flight_count": flights.count, "timer_exists": timer != nil,
         "overlay_frame": fixtureRect(overlay.frame), "overlay_bounds": fixtureRect(overlay.bounds),
         "overlay_attached": overlay.window != nil]
    }
}
@MainActor private func fixtureDescendants(_ view: NSView) -> [NSView] {
    [view] + view.subviews.flatMap { fixtureDescendants($0) }
}
@MainActor private func fixtureMount<V: View>(_ content: V, _ frame: CGRect, _ root: NSView) -> NSView {
    let host = NSHostingView(rootView: content.environment(\.colorScheme, .light))
    host.frame = frame
    root.addSubview(host)
    return host
}
@MainActor private func fixtureImageMetadata(_ p: BernHeroPicture) -> [String: Any] {
    ["rect_in_actual_overlay": fixtureRect(p.rect), "corner": p.corner,
     "nsimage_size": [p.image.size.width, p.image.size.height],
     "representations": p.image.representations.map {
        ["class": NSStringFromClass(type(of: $0)), "pixels_wide": $0.pixelsWide,
         "pixels_high": $0.pixelsHigh, "bits_per_sample": $0.bitsPerSample,
         "has_alpha": $0.hasAlpha, "color_space_name": $0.colorSpaceName.rawValue] as [String: Any]
     },
     "readback_policy": "Public NSImageRep metadata only; no CGImage/TIFF/bitmap recache conversion"]
}
@main private enum HeroBaselineMain {
    @MainActor static func main() { exit(run()) }
    @MainActor private static func run() -> Int32 {
        guard CommandLine.arguments.count == 4 else { return 2 }
        let urls = CommandLine.arguments[1...2].map { URL(fileURLWithPath: $0) }
        let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
        let front = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window: NSWindow?, root: FixtureRoot?, began: Date?, watchdog: DispatchSourceTimer?
        var samples: [[String: Any]] = [], captures: [[String: Any]] = []
        var report: [String: Any] = [
            "success": false, "product_head": "b08db54e01ac2ec54fb84e6f2a70041f1f4c3604",
            "scope": "Actual BernImage(hero: unique nonnil keys) body/modifier/anchor/manager/snapshot; actual BernHeroFlightView.draw at fixed progress0/1, same opaque image at both endpoints. Static endpoints only, no actual coordinated flight or lifecycle acceptance.",
            "activation_calls": 0, "collection_seconds": 7.2, "watchdog_seconds": 7.9,
            "image_equality_collection_gate": false,
            "snapshot_cgimage_metadata": "Not exposed by actual snapshot; no observer hook or recaching conversion added"
        ]
        report["hero_color_mode_environment"] = FixtureHeroColorMode.requested ?? "(unset)"
        report["hero_color_mode_selected"] = FixtureHeroColorMode.selected?.rawValue ?? "invalid"
        report["hero_color_mode_assignment_requested"] = FixtureHeroColorMode.selected?.rendererMode != nil
        defer {
            report["normal_after"] = ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            if let r = root { report["metal_count_before_cleanup"] = fixtureDescendants(r).filter { $0 is MTKView }.count }
            window?.orderOut(nil); window?.contentView = nil; window?.close(); watchdog?.cancel()
            if let began { report["window_seconds"] = Date().timeIntervalSince(began) }
            report["samples"] = samples; report["captures"] = captures
            report["frontmost_before"] = front
            report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString
            try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard FixtureHeroColorMode.selected != nil else {
                throw FixtureFailure(message: "Unknown BERN_HERO_COLOR_MODE; expected default, linear, extendedLinear or nonLinear")
            }
            guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 13, CGPreflightScreenCaptureAccess() else {
                throw FixtureFailure(message: "Actual13 and existing screen permission required; no prompt")
            }
            func normal() -> [String: Bool] {
                ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                 "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                 "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            }
            report["normal_before"] = normal()
            guard normal().values.allSatisfy({ !$0 }) else { throw FixtureFailure(message: "Normal flags required") }
            let app = NSApplication.shared
            app.setActivationPolicy(.accessory); app.appearance = NSAppearance(named: .aqua); app.finishLaunching()
            var loaded = false, loadOK = false
            Task { @MainActor in
                let a = await BernPictures.shared.load(urls[0].absoluteString)
                let b = await BernPictures.shared.load(urls[1].absoluteString)
                loadOK = a != nil && b != nil; loaded = true
            }
            let preloadDeadline = Date(timeIntervalSinceNow: 10)
            while !loaded && Date() < preloadDeadline { RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.02)) }
            guard loaded, loadOK, let named = BernPictures.shared.cached(urls[0].absoluteString) else {
                throw FixtureFailure(message: "Actual cache preload failed")
            }
            let before = try fixtureLedger(urls); report["cache_before"] = before
            let r = FixtureRoot(frame: CGRect(x: 0, y: 0, width: 1024, height: 440)); root = r
            let topY: CGFloat = 24, bottomY: CGFloat = 244
            let xs: [CGFloat] = [16, 352, 688]
            var regions: [String: NSView] = [:]
            for (i, name) in ["body-named", "body-custom"].enumerated() {
                let v = BernImage(url: urls[i].absoluteString, label: nil, width: 320, height: 180,
                                  fit: .fill, rendering: .original, dynamicRange: .standard,
                                  hero: "baseline-\(name)")
                regions[name] = fixtureMount(v, CGRect(x: xs[i], y: topY, width: 320, height: 180), r)
            }
            func oracle(_ y: CGFloat) -> NSView {
                fixtureMount(Image(decorative: named.image, scale: 1).renderingMode(.original)
                    .resizable().frame(width: 320, height: 180),
                    CGRect(x: xs[2], y: y, width: 320, height: 180), r)
            }
            regions["oracle-top"] = oracle(topY); regions["oracle-bottom"] = oracle(bottomY)
            for (i, title) in ["Actual named PQ", "Actual custom cICP PQ", "Native named PQ oracle"].enumerated() {
                for y: CGFloat in [2, 222] {
                    let label = NSTextField(labelWithString: title)
                    label.font = .systemFont(ofSize: 12); label.textColor = .black
                    label.frame = CGRect(x: xs[i], y: y, width: 320, height: 18); r.addSubview(label)
                }
            }
            let w = FixtureWindow(contentRect: CGRect(x: 100, y: 100, width: 1024, height: 440),
                                  styleMask: [.titled], backing: .buffered, defer: false)
            window = w; w.isReleasedWhenClosed = false; w.isRestorable = false
            w.title = "Bern actual PQ hero baseline"; w.contentView = r
            let timer = DispatchSource.makeTimerSource(queue: .global(qos: .userInitiated)); watchdog = timer
            timer.setEventHandler {
                try? Data("Own hero fixture7.9second watchdog; incomplete evidence.\n".utf8)
                    .write(to: output.appendingPathComponent("hard-deadline.txt"))
                _exit(124)
            }
            began = Date(); timer.schedule(deadline: .now() + 7.9); timer.resume(); w.orderFrontRegardless()
            let initialFrame = w.frame, deadline = Date(timeIntervalSinceNow: 7.2)
            let manager = BernWindowImageHeroes.forWindow(w)
            var flights: [BernHeroFlightView] = [], phase = 0, identical = 0, previousHash = ""
            var phaseBegan = Date(), snapshotTaken = false
            while Date() < deadline && phase < 2 {
                r.layoutSubtreeIfNeeded(); r.displayIfNeeded()
                RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.08))
                let views = fixtureDescendants(r), anchors = views.compactMap { $0 as? BernPictureHeroAnchor }
                let metal = views.filter { $0 is MTKView }.count
                let infos = CGWindowListCopyWindowInfo(.optionIncludingWindow, CGWindowID(w.windowNumber)) as? [[String: Any]] ?? []
                guard let info = infos.first, info[kCGWindowOwnerPID as String] as? pid_t == getpid(),
                      info[kCGWindowNumber as String] as? Int == w.windowNumber,
                      info[kCGWindowIsOnscreen as String] as? Bool == true,
                      w.isVisible, !w.isKeyWindow, !app.isActive, w.frame == initialFrame,
                      NSWorkspace.shared.frontmostApplication?.processIdentifier == front, metal == 0 else {
                    throw FixtureFailure(message: "Own window/foreground/fixed-frame/no-Metal contract failed")
                }
                guard anchors.count == 2, anchors.allSatisfy({ $0.attached && $0.window === w && $0.bounds.size == CGSize(width: 320, height: 180) }) else { continue }
                if !snapshotTaken {
                    var anchorInfo: [[String: Any]] = []
                    for (i, name) in ["body-named", "body-custom"].enumerated() {
                        guard let a = anchors.first(where: { $0.key == "baseline-\(name)" }),
                              let p = manager.fixtureSnapshot(a) else { throw FixtureFailure(message: "Actual anchor snapshot failed") }
                        var metadata = fixtureImageMetadata(p)
                        metadata["key"] = a.key; metadata["attached"] = a.attached
                        metadata["anchor_frame_in_root"] = fixtureRect(a.convert(a.bounds, to: r))
                        metadata["anchor_bounds"] = fixtureRect(a.bounds); metadata["captures_view"] = a.capturesView
                        anchorInfo.append(metadata)
                        let f = BernHeroFlightView(from: p.image, to: p.image)
                        f.corner = p.corner; f.frame = CGRect(x: xs[i], y: bottomY, width: 320, height: 180)
                        r.addSubview(f); flights.append(f); regions[i == 0 ? "flight-named" : "flight-custom"] = f
                    }
                    report["snapshots"] = anchorInfo; snapshotTaken = true; phaseBegan = Date(); continue
                }
                guard (manager.fixtureState["flight_count"] as? Int) == 0,
                      (manager.fixtureState["timer_exists"] as? Bool) == false else {
                    throw FixtureFailure(message: "Unique keys unexpectedly started coordinator flight")
                }
                guard Date().timeIntervalSince(phaseBegan) >= 0.24 else { continue }
                guard let screen = w.screen,
                      let shot = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(w.windowNumber), .boundsIgnoreFraming),
                      let buffer = shot.dataProvider?.data else { throw FixtureFailure(message: "Own raw window capture unavailable") }
                let rawHash = fixtureHash(buffer as Data)
                identical = rawHash == previousHash ? identical + 1 : 1; previousHash = rawHash
                var rois: [String: Any] = [:]
                for (name, view) in regions {
                    let f = view.convert(view.bounds, to: r)
                    guard f.width == 320, f.height == 180 else { throw FixtureFailure(message: "Public image frame changed") }
                    let win = r.convert(f, to: nil)
                    let top = CGRect(x: win.minX, y: w.frame.height - win.maxY, width: win.width, height: win.height)
                    let pixels = CGRect(x: top.minX * CGFloat(shot.width) / w.frame.width,
                                        y: top.minY * CGFloat(shot.height) / w.frame.height,
                                        width: top.width * CGFloat(shot.width) / w.frame.width,
                                        height: top.height * CGFloat(shot.height) / w.frame.height)
                    rois[name] = ["host_top_left_points": fixtureRect(f), "screenshot_pixels": fixtureRect(pixels)]
                }
                let sample: [String: Any] = [
                    "phase": "progress-\(phase)", "elapsed_seconds": Date().timeIntervalSince(began!),
                    "raw_buffer_sha256": rawHash, "consecutive_equal_buffers": identical,
                    "window_id": w.windowNumber, "owner_pid": getpid(), "window_bounds": info[kCGWindowBounds as String] ?? NSNull(),
                    "window_frame": fixtureRect(w.frame), "root_bounds": fixtureRect(r.bounds),
                    "capture_size": [shot.width, shot.height], "rois": rois,
                    "capture_space_name": shot.colorSpace?.name as String? ?? "unnamed",
                    "capture_icc_sha256": shot.colorSpace?.copyICCData().map { fixtureHash($0 as Data) } ?? "absent",
                    "current_headroom": screen.maximumExtendedDynamicRangeColorComponentValue,
                    "potential_headroom": screen.maximumPotentialExtendedDynamicRangeColorComponentValue,
                    "live_metal_count": metal, "manager": manager.fixtureState,
                    "key": w.isKeyWindow, "active": app.isActive,
                    "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
                ]
                samples.append(sample)
                if identical >= 5 {
                    let filename = "progress-\(phase).png", url = output.appendingPathComponent(filename)
                    try fixtureSavePNG(shot, url)
                    var capture = sample; capture["png"] = filename
                    capture["png_sha256"] = fixtureHash(try Data(contentsOf: url)); captures.append(capture)
                    phase += 1; identical = 0; previousHash = ""; phaseBegan = Date()
                    for f in flights { f.progress = CGFloat(phase); f.needsDisplay = true }
                }
            }
            report["completed_phases"] = phase
            guard phase == 2 else { throw FixtureFailure(message: "Collection deadline; incomplete endpoints") }
            let after = try fixtureLedger(urls); report["cache_after"] = after
            let unchanged = NSDictionary(dictionary: after).isEqual(to: before); report["cache_unchanged"] = unchanged
            report["normal_after"] = normal()
            guard unchanged, normal().values.allSatisfy({ !$0 }),
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == front else {
                throw FixtureFailure(message: "Cache/normal/foreground final contract failed")
            }
            report["success"] = true; return 0
        } catch {
            report["error"] = String(describing: error)
            FileHandle.standardError.write(Data("Hero baseline incomplete: \(error)\n".utf8)); return 1
        }
    }
}
