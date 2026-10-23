// Standalone macOS 14 diagnostic; does not use or alter Bern's runtime.
// swiftc -target arm64-apple-macos14.0 scroll-transition-probe.swift -o probe
// ./probe OUTPUT_DIR
import AppKit
import SwiftUI
import ImageIO
import UniformTypeIdentifiers

private struct Frames: PreferenceKey {
    static var defaultValue: [Int: CGRect] = [:]
    static func reduce(value: inout [Int: CGRect], nextValue: () -> [Int: CGRect]) {
        value.merge(nextValue(), uniquingKeysWith: { _, new in new })
    }
}

@MainActor private final class Model: ObservableObject {
    @Published var margin: CGFloat = 0
    var receive: ([Int: CGRect]) -> Void = { _ in }
}

private struct Content: View {
    @ObservedObject var model: Model
    var body: some View {
        ScrollView(.horizontal, showsIndicators: false) {
            HStack(spacing: 30) {
                ForEach(0..<9) { index in
                    Rectangle().fill(Color.red)
                        .frame(width: 240, height: 120)
                        .scrollTransition(.interactive(timingCurve: .linear).threshold(.centered), axis: .horizontal) { view, phase in
                            view.scaleEffect(phase.isIdentity ? 1.12 : 1)
                                .opacity(phase.isIdentity ? 1 : 0.6)
                        }
                        // This clear background measures the layout frame;
                        // it is outside the visual-only scroll transition.
                        .background(GeometryReader { geometry in
                            Color.clear.preference(key: Frames.self, value: [index: geometry.frame(in: .named("viewport"))])
                        })
                }
            }.frame(height: 220)
        }
        .contentMargins(.horizontal, model.margin, for: .scrollContent)
        .frame(width: 709, height: 220)
        .coordinateSpace(name: "viewport")
        .background(Color.white)
        .onPreferenceChange(Frames.self) { model.receive($0) }
    }
}

@MainActor private final class Runner {
    private let output: URL
    private let model = Model()
    private let margins: [CGFloat] = [0, 100, 234.5]
    private let desiredOffset: CGFloat = 120
    private let target = 4
    private var frames: [Int: CGRect] = [:]
    private var window: NSWindow!
    private var timer: Timer?
    private var index = 0
    private var trialTicks = 0
    private var stable = 0
    private var previousPixels: Data?
    private var previousFrame: CGRect?
    private var started = Date()
    private var records: [[String: Any]] = []

    init(output: URL) { self.output = output }

    func start() {
        model.receive = { [weak self] in self?.frames = $0 }
        window = NSWindow(contentRect: CGRect(x: 120, y: 200, width: 709, height: 220),
                          styleMask: [.titled, .closable], backing: .buffered, defer: false)
        window.title = "Scroll transition calibration"
        window.contentView = NSHostingView(rootView: Content(model: model))
        window.setContentSize(CGSize(width: 709, height: 220))
        window.makeKeyAndOrderFront(nil)
        NSApplication.shared.activate(ignoringOtherApps: true)
        started = Date()
        timer = Timer.scheduledTimer(withTimeInterval: 0.12, repeats: true) { [weak self] _ in
            MainActor.assumeIsolated { self?.tick() }
        }
    }

    private func findScroll(in view: NSView) -> NSScrollView? {
        if let scroll = view as? NSScrollView { return scroll }
        for child in view.subviews {
            if let found = findScroll(in: child) { return found }
        }
        return nil
    }

    private func tick() {
        guard Date().timeIntervalSince(started) < 30 else { finish(error: "30-second deadline exceeded"); return }
        trialTicks += 1
        guard trialTicks >= 3, let root = window.contentView,
              let scroll = findScroll(in: root), let frame = frames[target] else { return }
        let desiredCenter: CGFloat = 709 / 2 + desiredOffset
        let correction = frame.midX - desiredCenter
        if abs(correction) > 0.25 {
            stable = 0; previousPixels = nil; previousFrame = nil
            var origin = scroll.contentView.bounds.origin
            origin.x += correction
            scroll.contentView.scroll(to: origin)
            scroll.reflectScrolledClipView(scroll.contentView)
            return
        }
        guard let image = CGWindowListCreateImage(.null, .optionIncludingWindow,
                    CGWindowID(window.windowNumber), .boundsIgnoreFraming),
              let raw = image.dataProvider?.data else { finish(error: "WindowServer capture unavailable"); return }
        let pixels = raw as Data
        if previousPixels == pixels, previousFrame == frame { stable += 1 }
        else { stable = 1 }
        previousPixels = pixels; previousFrame = frame
        guard stable >= 4 else { return }
        let name = "margin-\(index)-offset-120.png"
        guard let writer = CGImageDestinationCreateWithURL(output.appendingPathComponent(name) as CFURL,
                    UTType.png.identifier as CFString, 1, nil) else { finish(error: "Cannot create PNG"); return }
        CGImageDestinationAddImage(writer, image, nil)
        guard CGImageDestinationFinalize(writer) else { finish(error: "Cannot finish PNG"); return }
        let inset = scroll.contentInsets
        records.append([
            "png": name, "margin_requested": Double(margins[index]),
            "target": target, "desired_center_offset": Double(desiredOffset),
            "actual_center_offset": Double(frame.midX - 709 / 2),
            "target_layout_frame": rect(frame),
            "all_layout_frames": frames.mapValues { rect($0) }.reduce(into: [String: Any]()) { $0[String($1.key)] = $1.value },
            "scroll_frame": rect(scroll.frame), "scroll_bounds": rect(scroll.bounds),
            "clip_bounds": rect(scroll.contentView.bounds),
            "document_frame": rect(scroll.documentView?.frame ?? .zero),
            "content_insets": ["top": Double(inset.top), "left": Double(inset.left), "bottom": Double(inset.bottom), "right": Double(inset.right)],
            "automatic_content_insets": scroll.automaticallyAdjustsContentInsets,
            "window_frame": rect(window.frame), "content_bounds": rect(root.bounds),
            "window_number": window.windowNumber,
            "backing_scale": Double(window.backingScaleFactor),
            "pixels": ["width": image.width, "height": image.height],
            "stable_identical_captures": stable,
            "elapsed_seconds": Date().timeIntervalSince(started)
        ])
        index += 1
        guard index < margins.count else { finish(); return }
        trialTicks = 0; stable = 0; previousPixels = nil; previousFrame = nil
        model.margin = margins[index]
    }

    private func rect(_ value: CGRect) -> [String: Double] {
        ["x": Double(value.minX), "y": Double(value.minY), "width": Double(value.width), "height": Double(value.height)]
    }

    private func finish(error: String? = nil) {
        timer?.invalidate(); timer = nil
        let report: [String: Any] = [
            "success": error == nil, "error": error.map { $0 as Any } ?? NSNull(),
            "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "capture": "CGWindowListCreateImage / WindowServer; no offscreen rendering",
            "viewport": ["width": 709, "height": 220],
            "item": ["width": 240, "height": 120], "gap": 30,
            "configuration": "interactive(timingCurve: .linear).threshold(.centered)",
            "scale_identity": 1.12, "scale_hidden": 1.0,
            "opacity_identity": 1.0, "opacity_hidden": 0.6,
            "note": "Diagnostic fixture, not Gallery. Cards are 120pt high; Gallery cards are 135pt. Geometry is before visual effects. No user gestures or TCC modifications.",
            "samples": records
        ]
        do {
            let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
            try data.write(to: output.appendingPathComponent("report.json"), options: .atomic)
        } catch { fputs("Cannot write report: \(error)\n", stderr); exit(1) }
        exit(error == nil ? 0 : 1)
    }
}

guard CommandLine.arguments.count == 2 else { fputs("Usage: scroll-transition-probe OUTPUT_DIR\n", stderr); exit(2) }
let output = URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true)
try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
let application = NSApplication.shared
application.setActivationPolicy(.regular)
private let runner = MainActor.assumeIsolated { () -> Runner in
    let runner = Runner(output: output)
    runner.start()
    return runner
}
application.run()
