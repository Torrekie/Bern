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
        fixtureObserveSnapshotCGImage(pixels, key: key)
        guard let displayPixels = FixtureSnapshotSDR.pixels(pixels, key: key, size: bounds.size) else { return nil }
        let displayImage = NSImage(cgImage: displayPixels, size: bounds.size)
        guard FixtureSnapshotSDR.bindDisplay(displayImage, key: key) else { return nil }
        return BernHeroPicture(rect: rect, image: displayImage,
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

// Isolated fixture only. Raw provider access is deferred until the original teardown.
private enum FixtureFloatCaptureMode: String {
    case off, on
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_FLOAT_CAPTURE"]
    static let selected = FixtureFloatCaptureMode(rawValue: requested ?? "off")
}

@MainActor private enum FixtureSnapshotFloatCapture {
    private struct Held {
        let key: String
        let image: CGImage
        let retainedAt: TimeInterval
    }
    private static let names = [("baseline-body-named", "snapshot-named.bin"),
                                ("baseline-body-custom", "snapshot-custom.bin")]
    private static let maximumBytes = 4 * 1024 * 1024
    private static var primary = true
    private static var primaryCount = 0
    private static var cleanupCount = 0
    private static var primaryKeys: [String] = []
    private static var held: [Held] = []
    private static var peakRetained = 0
    private static var frozenAt: TimeInterval?
    private static var observationError: String?
    private static var exported: [[String: Any]] = []
    private static var providerCopyCalls = 0
    private(set) static var finalizationFailed = false

    static func observe(_ image: CGImage, key: String) {
        guard primary else { cleanupCount += 1; return }
        primaryCount += 1
        primaryKeys.append(key)
        guard FixtureFloatCaptureMode.selected == .on else { return }
        guard held.count < 2, names.contains(where: { $0.0 == key }),
              !held.contains(where: { $0.key == key }) else {
            observationError = "Unexpected/duplicate primary image; actual count/key retained in report"
            return
        }
        held.append(Held(key: key, image: image, retainedAt: ProcessInfo.processInfo.systemUptime))
        peakRetained = max(peakRetained, held.count)
    }

    static func freezePrimary() {
        primary = false
        frozenAt = ProcessInfo.processInfo.systemUptime
    }

    // Public image drawing semantics only; caller is already post-teardown.
    private static func drawingSemantics(_ image: CGImage, key: String) -> [String: Any] {
        let began = ProcessInfo.processInfo.systemUptime
        var record: [String: Any] = [
            "stage": "after_existing_window_teardown_before_primary_release",
            "success": false, "error": NSNull(),
            "rendering_intent_raw": NSNull(), "is_mask": NSNull(), "should_interpolate": NSNull(),
            "color_space_model_raw": NSNull(), "color_space_components": NSNull(),
            "decode_present": NSNull(), "decode_count": NSNull(),
            "decode_nonfinite_index": NSNull(), "observed_at_uptime_seconds": began
        ]
        var values: [Double] = [], bits: [String] = []
        do {
            // Each of the four image getters is called exactly once for this record.
            let intent = image.renderingIntent
            let mask = image.isMask
            let interpolate = image.shouldInterpolate
            let decode = image.decode
            record["rendering_intent_raw"] = intent.rawValue
            record["is_mask"] = mask; record["should_interpolate"] = interpolate
            record["decode_present"] = decode != nil
            // Original hook appends this primary descriptor before observing the same image.
            let primaryDescriptors = fixtureSnapshotCGImageObservations.prefix(2)
            let matches = primaryDescriptors.filter { $0.scalars["key"] as? String == key }
            guard !mask, primaryDescriptors.count == 2, matches.count == 1,
                  let descriptor = matches.first, let space = descriptor.space else {
                throw FixtureFailure(message: "CGImage semantics requires one existing primary descriptor/key and a nonmask image with a color space")
            }
            let model = space.model, components = space.numberOfComponents
            record["color_space_model_raw"] = model.rawValue
            record["color_space_components"] = components
            guard model == .rgb, components == 3, MemoryLayout<CGFloat>.size == 8,
                  MemoryLayout<CGFloat>.stride == 8, MemoryLayout<Double>.size == 8 else {
                throw FixtureFailure(message: "CGImage semantics requires RGB3 and64bit CGFloat; no decode pointer scan")
            }
            if let decode {
                record["decode_count"] = 6
                for index in 0..<6 {
                    let value = Double(decode[index])
                    let hex = String(value.bitPattern, radix: 16)
                    bits.append("0x" + String(repeating: "0", count: 16 - hex.count) + hex)
                    guard value.isFinite else {
                        record["decode_nonfinite_index"] = index
                        throw FixtureFailure(message: "Nonfinite CGImage decode value; partial finite values/bits retained")
                    }
                    values.append(value) // Preserve the sign of zero; bits are recorded separately.
                }
            } else { record["decode_count"] = 0 }
            record["success"] = true
        } catch { record["error"] = String(describing: error) }
        record["decode_values"] = values; record["decode_value_bits"] = bits
        record["decode_values_read"] = bits.count
        record["observation_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - began
        return record
    }

    private static func export(_ output: URL) throws {
        var layouts: [String: ([String: Any], Int)] = [:]
        var requiredTotal = 0
        // Validate all layouts/budget before the first provider read.
        for entry in held {
            let image = entry.image
            let (tightRow, rowOverflow) = image.width.multipliedReportingOverflow(by: 8)
            let (required, sizeOverflow) = image.bytesPerRow.multipliedReportingOverflow(by: image.height)
            let (sum, totalOverflow) = requiredTotal.addingReportingOverflow(required)
            guard image.width > 0, image.height > 0, image.bitsPerComponent == 16,
                  image.bitsPerPixel == 64, image.bitmapInfo.rawValue == 4353,
                  image.alphaInfo.rawValue == 1, image.byteOrderInfo.rawValue == 4096,
                  image.pixelFormatInfo.rawValue == 0, image.bitmapInfo.contains(.floatComponents),
                  !rowOverflow, !sizeOverflow, !totalOverflow, image.bytesPerRow >= tightRow,
                  required > 0, sum <= maximumBytes else {
                throw FixtureFailure(message: "Unknown snapshot layout or >4MiB raw budget; no conversion/fallback")
            }
            requiredTotal = sum
            layouts[entry.key] = ([
                "key": entry.key, "width": image.width, "height": image.height,
                "bits_per_component": image.bitsPerComponent, "bits_per_pixel": image.bitsPerPixel,
                "bytes_per_row": image.bytesPerRow, "bitmap_info_raw": image.bitmapInfo.rawValue,
                "alpha_info_raw": image.alphaInfo.rawValue, "byte_order_raw": image.byteOrderInfo.rawValue,
                "pixel_format_raw": image.pixelFormatInfo.rawValue,
                "float_components": image.bitmapInfo.contains(.floatComponents),
                "retained_at_uptime_seconds": entry.retainedAt,
                "export_stage": "after_existing_window_teardown"
            ], required)
        }
        for (key, name) in names {
            guard let entry = held.first(where: { $0.key == key }),
                  let (layout, required) = layouts[key] else {
                throw FixtureFailure(message: "Missing primary image/layout; no export fallback")
            }
            let destination = output.appendingPathComponent(name)
            guard !FileManager.default.fileExists(atPath: destination.path) else {
                throw FixtureFailure(message: "Refuse to overwrite existing snapshot dump")
            }
            let began = ProcessInfo.processInfo.systemUptime
            guard let provider = entry.image.dataProvider else {
                throw FixtureFailure(message: "Original snapshot has no provider")
            }
            providerCopyCalls += 1
            guard let source = provider.data else {
                throw FixtureFailure(message: "Original snapshot provider copy failed")
            }
            let data = source as Data
            guard data.count == required else {
                throw FixtureFailure(message: "Provider length differs from rowbytes*height; no conversion/fallback")
            }
            try data.write(to: destination, options: .atomic)
            var record = layout
            record["file"] = name
            record["byte_count"] = data.count
            record["sha256"] = fixtureHash(data)
            record["provider_read_at_uptime_seconds"] = began
            record["export_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - began
            let semantics = drawingSemantics(entry.image, key: key)
            record["drawing_semantics"] = semantics
            exported.append(record) // Keep raw export and partial semantics even on rejection.
            guard semantics["success"] as? Bool == true else {
                throw FixtureFailure(message: "CGImage drawing semantics rejected: \(semantics["error"] as? String ?? "unknown")")
            }
        }
    }

    static func finish(output: URL, acquisitionSucceeded: Bool) -> [String: Any] {
        let began = ProcessInfo.processInfo.systemUptime
        var problem = observationError
        if FixtureFloatCaptureMode.selected == nil {
            problem = "Invalid BERN_HERO_FLOAT_CAPTURE; off/on required"
        } else if !acquisitionSucceeded {
            problem = "Acquisition incomplete; provider export not attempted"
        } else if primaryCount != 2 || Set(primaryKeys) != Set(names.map { $0.0 }) {
            problem = "Expected exactly two actual primary observations/keys"
        }
        if problem == nil, FixtureFloatCaptureMode.selected == .on {
            if held.count != 2 {
                problem = "Expected two original primary CGImages"
            } else {
                do { try export(output) }
                catch { problem = String(describing: error) }
            }
        }
        // Release this fixture's references on success and every failure; do not claim deallocation.
        held.removeAll()
        let releasedAt = ProcessInfo.processInfo.systemUptime
        finalizationFailed = problem != nil
        return [
            "requested": FixtureFloatCaptureMode.requested.map { $0 as Any } ?? NSNull(),
            "selected": FixtureFloatCaptureMode.selected.map { $0.rawValue as Any } ?? NSNull(),
            "primary_observation_count": primaryCount, "cleanup_observation_count": cleanupCount,
            "primary_observation_keys": primaryKeys,
            "success": problem == nil, "error": problem.map { $0 as Any } ?? NSNull(),
            "records": exported, "provider_copy_calls": providerCopyCalls,
            "retained_primary_peak_count": peakRetained,
            "fixture_retained_images_after_export": held.count,
            "primary_frozen_at_uptime_seconds": frozenAt.map { $0 as Any } ?? NSNull(),
            "released_at_uptime_seconds": releasedAt,
            "export_elapsed_seconds": releasedAt - began,
            "export_stage": "after_existing_window_teardown",
            "maximum_total_raw_bytes": maximumBytes,
            "total_raw_bytes": exported.reduce(0) { $0 + ($1["byte_count"] as? Int ?? 0) },
            "retention_scope": "on: actual renderer-return object until post-teardown export; off: no CGImage retained; cleanup: no CGImage retained",
            "row_direction": "unverified",
            "observer_effect": "Changed object lifetime/provider access requires off/on pixel controls; zero observer effect is not claimed"
        ]
    }
}

// Isolated fixed-endpoint Standard-display recipe; never changes the original raw capture.
import CoreImage

private enum FixtureSnapshotSDRMode: String {
    case `default`, bakedNamed = "baked-named"
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_SNAPSHOT_SDR"]
    static let selected = FixtureSnapshotSDRMode(rawValue: requested ?? "default")
}

@MainActor private enum FixtureSnapshotSDR {
    private static var primary = true
    private static var context: CIContext?
    private static var derived: CGImage?
    private static var inputID: ObjectIdentifier?
    private static weak var displayImage: NSImage?
    private static var record: [String: Any] = [:]
    private static var phaseChecks: [[String: Any]] = []
    private static var problem: String?
    private static var conversions = 0, contextCreates = 0, cacheHits = 0, cleanupPasses = 0
    private(set) static var finalizationFailed = false

    static func pixels(_ image: CGImage, key: String, size: CGSize) -> CGImage? {
        // Default does not create CI objects, inspect image properties, or bind a display image.
        guard FixtureSnapshotSDRMode.selected == .bakedNamed else { return image }
        guard primary else { cleanupPasses += 1; return image }
        guard key == "baseline-body-named" else { return image }
        guard problem == nil else { return nil }
        let started = ProcessInfo.processInfo.systemUptime
        do {
            if let derived {
                guard inputID == ObjectIdentifier(image) else { throw FixtureFailure(message: "Named SDR cache input identity changed") }
                cacheHits += 1; return derived
            }
            let matches = fixtureSnapshotCGImageObservations.filter { $0.scalars["key"] as? String == key }
            guard size == CGSize(width: 320, height: 180), matches.count == 1,
                  let descriptor = matches.first, let space = descriptor.space,
                  space.model == .rgb, space.numberOfComponents == 3,
                  let width = descriptor.scalars["width"] as? Int,
                  let height = descriptor.scalars["height"] as? Int,
                  (width == 320 || width == 640), height == width * 9 / 16,
                  let rowBytes = descriptor.scalars["bytes_per_row"] as? Int, rowBytes >= width * 8,
                  descriptor.scalars["bits_per_component"] as? Int == 16,
                  descriptor.scalars["bits_per_pixel"] as? Int == 64,
                  descriptor.scalars["bitmap_info_raw"] as? UInt32 == 4353,
                  descriptor.scalars["alpha_info_raw"] as? UInt32 == 1,
                  descriptor.scalars["byte_order_raw"] as? UInt32 == 4096,
                  descriptor.scalars["pixel_format_raw"] as? UInt32 == 0,
                  descriptor.scalars["float_components"] as? Bool == true else {
                throw FixtureFailure(message: "Unknown named snapshot layout/extent; no SDR fallback")
            }
            let extent = CGRect(x: 0, y: 0, width: width, height: height)
            record = ["key": key, "input_object_id": String(describing: ObjectIdentifier(image)),
                      "input_layout": descriptor.scalars, "input_extent": fixtureRect(extent),
                      "logical_size": [size.width, size.height], "requested_tone_map_hdr_to_sdr": true,
                      "actual_tone_mapping_applied": "unknown", "input_color_space_override": false,
                      "requested_output_format": "RGBA8", "requested_output_color_space": "sRGB",
                      "deferred": false, "conversion_started_uptime_seconds": started]
            let input = CIImage(cgImage: image, options: [.toneMapHDRtoSDR: true])
            guard input.extent == extent, let destination = CGColorSpace(name: CGColorSpace.sRGB) else {
                throw FixtureFailure(message: "CI input extent or sRGB destination unavailable")
            }
            let renderer = CIContext(options: nil); context = renderer; contextCreates += 1
            guard let result = renderer.createCGImage(input, from: extent, format: .RGBA8,
                                                       colorSpace: destination, deferred: false),
                  result.width == width, result.height == height,
                  result.bitsPerComponent == 8, result.bitsPerPixel == 32,
                  !result.bitmapInfo.contains(.floatComponents), result.bytesPerRow >= width * 4 else {
                throw FixtureFailure(message: "CI RGBA8 exact-extent conversion failed; no fallback")
            }
            inputID = ObjectIdentifier(image); derived = result; conversions += 1
            record["output_object_id"] = String(describing: ObjectIdentifier(result))
            record["conversion_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - started
            return result
        } catch { problem = String(describing: error); return nil }
    }

    static func bindDisplay(_ image: NSImage, key: String) -> Bool {
        guard FixtureSnapshotSDRMode.selected == .bakedNamed, primary,
              key == "baseline-body-named" else { return true }
        guard problem == nil, derived != nil, displayImage == nil,
              image.size == CGSize(width: 320, height: 180) else {
            problem = problem ?? "Named derived NSImage binding failed"; return false
        }
        displayImage = image
        record["derived_display_nsimage_id"] = String(describing: ObjectIdentifier(image))
        return true
    }

    static func check(_ flights: [BernHeroFlightView], stage: String, phase: Int) throws {
        if let problem { throw FixtureFailure(message: problem) }
        guard FixtureSnapshotSDRMode.selected == .bakedNamed else { return }
        guard flights.count == 2, let image = displayImage, let named = flights.first,
              derived != nil, conversions == 1, contextCreates == 1,
              named.from === image, named.to === image, image.size == CGSize(width: 320, height: 180),
              named.bounds.size == image.size, named.corner == 0 else {
            problem = "Named derived display identity/geometry changed"; throw FixtureFailure(message: problem!)
        }
        phaseChecks.append(["stage": stage, "phase": phase, "uptime_seconds": ProcessInfo.processInfo.systemUptime,
                            "display_nsimage_id": String(describing: ObjectIdentifier(image)),
                            "derived_cgimage_id": String(describing: ObjectIdentifier(derived!)),
                            "same_from_to_display_image": true])
    }

    static func freezePrimary() { primary = false }

    static func finish(acquisitionSucceeded: Bool) -> [String: Any] {
        // All PNGs and original window teardown already completed. No provider is read.
        if let image = derived {
            let scalars: [String: Any] = ["width": image.width, "height": image.height,
                "bits_per_component": image.bitsPerComponent, "bits_per_pixel": image.bitsPerPixel,
                "bytes_per_row": image.bytesPerRow, "bitmap_info_raw": image.bitmapInfo.rawValue,
                "alpha_info_raw": image.alphaInfo.rawValue, "byte_order_raw": image.byteOrderInfo.rawValue,
                "pixel_format_raw": image.pixelFormatInfo.rawValue,
                "float_components": image.bitmapInfo.contains(.floatComponents)]
            record["output_metadata"] = FixtureSnapshotCGImageDescriptor(scalars: scalars, space: image.colorSpace).metadata()
        }
        if problem == nil, FixtureSnapshotSDRMode.selected == nil { problem = "Invalid snapshot SDR mode" }
        if problem == nil, !acquisitionSucceeded { problem = "Native acquisition incomplete" }
        if problem == nil, FixtureSnapshotSDRMode.selected == .bakedNamed,
           (conversions != 1 || contextCreates != 1 || phaseChecks.filter({ $0["stage"] as? String == "after_png" }).count != 2) {
            problem = "Incomplete one-cache/two-phase SDR display recipe"
        }
        derived = nil; context = nil; inputID = nil; displayImage = nil
        finalizationFailed = problem != nil
        return ["requested": FixtureSnapshotSDRMode.requested.map { $0 as Any } ?? NSNull(),
                "selected": FixtureSnapshotSDRMode.selected.map { $0.rawValue as Any } ?? NSNull(),
                "success": !finalizationFailed, "error": problem.map { $0 as Any } ?? NSNull(),
                "primary_frozen": !primary, "conversion_count": conversions,
                "context_create_count": contextCreates, "cache_hit_count": cacheHits,
                "cleanup_passthrough_count": cleanupPasses, "records": record.isEmpty ? [] : [record],
                "phase_checks": phaseChecks, "metadata_stage": "after_existing_window_teardown",
                "helper_references_cleared": derived == nil && context == nil && displayImage == nil,
                "release_scope": "Only helper-owned derived/context and weak display reference; no deallocation claim"]
    }
}


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

// Fixture-only entry point, appended in this file to preserve product access control.
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

private struct FixtureFailure: Error { let message: String }
private func fixtureHash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
// Fixture-only observer: hold scalar descriptors and a color-space reference, never an image.
// ICC export/classification happens only after all PNGs and existing window teardown.
@MainActor private struct FixtureSnapshotCGImageDescriptor {
    let scalars: [String: Any]
    let space: CGColorSpace?
    func metadata() -> [String: Any] {
        var record = scalars
        record["color_space_metadata_stage"] = "after_existing_window_teardown"
        for field in ["color_space_name", "color_space_model_raw", "color_space_components",
                      "icc_present", "icc_byte_count", "icc_sha256", "icc_base64",
                      "icc_base64_omitted_reason", "wide_gamut_rgb",
                      "uses_extended_range", "uses_itur2100_tf", "is_pq_based", "is_hlg_based"] {
            record[field] = NSNull()
        }
        if let space {
            if let name = space.name { record["color_space_name"] = name as String }
            record["color_space_model_raw"] = space.model.rawValue
            record["color_space_components"] = space.numberOfComponents
            record["wide_gamut_rgb"] = space.isWideGamutRGB
            record["uses_extended_range"] = CGColorSpaceUsesExtendedRange(space)
            record["uses_itur2100_tf"] = CGColorSpaceUsesITUR_2100TF(space)
            record["is_pq_based"] = CGColorSpaceIsPQBased(space)
            record["is_hlg_based"] = CGColorSpaceIsHLGBased(space)
            if let profile = space.copyICCData() {
                let data = profile as Data
                record["icc_present"] = true
                record["icc_byte_count"] = data.count
                record["icc_sha256"] = fixtureHash(data)
                if data.count <= 65_536 {
                    record["icc_base64"] = data.base64EncodedString()
                } else {
                    record["icc_base64_omitted_reason"] = "profile_exceeds_65536_bytes"
                }
            } else {
                record["icc_present"] = false
                record["icc_byte_count"] = 0
                record["icc_base64_omitted_reason"] = "no_icc_profile"
            }
        }
        return record
    }
}
@MainActor private var fixtureSnapshotCGImageObservations: [FixtureSnapshotCGImageDescriptor] = []
@MainActor private func fixtureObserveSnapshotCGImage(_ image: CGImage, key: String) {
    var record: [String: Any] = [:]
    record["key"] = key
    record["observation_site"] = "snapshot_descriptors_before_NSImage_color_metadata_after_window_teardown"
    record["width"] = image.width
    record["height"] = image.height
    record["bits_per_component"] = image.bitsPerComponent
    record["bits_per_pixel"] = image.bitsPerPixel
    record["bytes_per_row"] = image.bytesPerRow
    record["bitmap_info_raw"] = image.bitmapInfo.rawValue
    record["alpha_info_raw"] = image.alphaInfo.rawValue
    record["float_components"] = image.bitmapInfo.contains(.floatComponents)
    record["byte_order_raw"] = image.byteOrderInfo.rawValue
    record["pixel_format_raw"] = image.pixelFormatInfo.rawValue
    let space = image.colorSpace
    record["color_space_present"] = space != nil
    fixtureSnapshotCGImageObservations.append(FixtureSnapshotCGImageDescriptor(scalars: record, space: space))
    FixtureSnapshotFloatCapture.observe(image, key: key)
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
    @MainActor static func main() {
        let status = run()
        exit(status == 0 && (FixtureSnapshotFloatCapture.finalizationFailed || FixtureSnapshotSDR.finalizationFailed) ? 1 : status)
    }
    @MainActor private static func run() -> Int32 {
        guard CommandLine.arguments.count == 4 else { return 2 }
        let urls = CommandLine.arguments[1...2].map { URL(fileURLWithPath: $0) }
        let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
        let expectedOS = Int(ProcessInfo.processInfo.environment["BERN_HERO_EXPECT_OS"] ?? "13") ?? -1
        let actualOS = ProcessInfo.processInfo.operatingSystemVersion.majorVersion
        let front = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window: NSWindow?, root: FixtureRoot?, began: Date?, watchdog: DispatchSourceTimer?
        var samples: [[String: Any]] = [], captures: [[String: Any]] = []
        var report: [String: Any] = [
            "success": false, "product_head": "b08db54e01ac2ec54fb84e6f2a70041f1f4c3604",
            "expected_os_major": expectedOS, "actual_os_major": actualOS,
            "scope": "Actual BernImage(hero: unique nonnil keys) body/modifier/anchor/manager/snapshot; actual BernHeroFlightView.draw at fixed progress0/1, same opaque image at both endpoints. Static endpoints only, no actual coordinated flight or lifecycle acceptance.",
            "activation_calls": 0, "collection_seconds": 7.2, "watchdog_seconds": 7.9,
            "image_equality_collection_gate": false,
            "snapshot_cgimage_metadata": "Fixture-only public CGImage scalar descriptors and color-space reference at the actual renderer.cgImage result; classification/ICC hash/bounded profile serialization only after all PNG captures and original window teardown. The v2 metadata observer retains no image; separate opt-in raw capture lifetime/provider reads are reported in snapshot_float_capture. The snapshot_sdr_display recipe may create one named RGBA8/sRGB display derivative; original renderer pixels/raw export stay original, without relabel or NSImage recache. Not a zero-observer-effect claim."
        ]
        report["backing_observation"] = FixtureBackingObservation.initial()
        defer {
            FixtureSnapshotSDR.freezePrimary()
            FixtureSnapshotFloatCapture.freezePrimary()
            let observationsBeforeCleanup = fixtureSnapshotCGImageObservations
            report["snapshot_cgimage_observations_scope"] = "before_existing_window_teardown"
            report["normal_after"] = ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            if let r = root { report["metal_count_before_cleanup"] = fixtureDescendants(r).filter { $0 is MTKView }.count }
            window?.orderOut(nil); window?.contentView = nil; window?.close(); watchdog?.cancel()
            if let began { report["window_seconds"] = Date().timeIntervalSince(began) }
            report["snapshot_cgimage_observations"] = observationsBeforeCleanup.map { $0.metadata() }
            report["snapshot_cgimage_cleanup_observations"] = fixtureSnapshotCGImageObservations.dropFirst(observationsBeforeCleanup.count).map { $0.metadata() }
            report["samples"] = samples; report["captures"] = captures
            report["frontmost_before"] = front
            report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString
            let floatCapture = FixtureSnapshotFloatCapture.finish(output: output, acquisitionSucceeded: report["success"] as? Bool == true)
            report["snapshot_float_capture"] = floatCapture
            if floatCapture["success"] as? Bool != true {
                report["success"] = false
                if report["error"] == nil { report["error"] = floatCapture["error"] }
            }
            let snapshotSDR = FixtureSnapshotSDR.finish(acquisitionSucceeded: report["success"] as? Bool == true)
            report["snapshot_sdr_display"] = snapshotSDR
            if snapshotSDR["success"] as? Bool != true {
                report["success"] = false
                if report["error"] == nil { report["error"] = snapshotSDR["error"] }
            }
            try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard FixtureSnapshotSDRMode.selected != nil, FixtureFloatCaptureMode.selected == .on,
                  FixtureBackingMode.selected == "off", expectedOS == 13, actualOS == 13 else {
                throw FixtureFailure(message: "Snapshot SDR recipe requires default/baked-named, float on, backing off and OS13 before window creation")
            }
            guard FixtureBackingMode.selected != nil else {
                throw FixtureFailure(message: "Invalid BERN_HERO_LAYER_OBSERVE; off/on required before window creation")
            }
            guard FixtureFloatCaptureMode.selected != nil else {
                throw FixtureFailure(message: "Invalid BERN_HERO_FLOAT_CAPTURE; off/on required before window creation")
            }
            guard (expectedOS == 13 || expectedOS == 14), actualOS == expectedOS, CGPreflightScreenCaptureAccess() else {
                throw FixtureFailure(message: "Expected13/14 and existing screen permission required; no prompt")
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
            guard named.orientation == .up,
                  fixtureHash(try Data(contentsOf: urls[0])) == "3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b" else {
                throw FixtureFailure(message: "Known opaque/up named atlas fixture input required")
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
                try FixtureSnapshotSDR.check(flights, stage: "before_capture", phase: phase)
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
                    try FixtureSnapshotSDR.check(flights, stage: "after_png", phase: phase)
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
            try FixtureSnapshotSDR.check(flights, stage: "after_final_guards", phase: phase)
            report["backing_observation"] = try FixtureBackingObservation.finish(flights, root: r, manager: manager, window: w)
            report["success"] = true; return 0
        } catch {
            var backing = report["backing_observation"] as? [String: Any] ?? FixtureBackingObservation.initial()
            if backing["success"] as? Bool != true { backing["error"] = String(describing: error) }
            report["backing_observation"] = backing
            report["error"] = String(describing: error)
            FileHandle.standardError.write(Data("Hero baseline incomplete: \(error)\n".utf8)); return 1
        }
    }
}
