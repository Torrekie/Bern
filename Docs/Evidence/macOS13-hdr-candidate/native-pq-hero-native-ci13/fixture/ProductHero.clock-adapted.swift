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
