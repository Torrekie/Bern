// Standalone layout diagnostic, never linked into Bern.
// swiftc -swift-version 5 -parse-as-library -target arm64-apple-macos13.0 \
//   -framework SwiftUI -framework AppKit -framework ImageIO -framework ColorSync \
//   image-layout-probe.swift -o ImageLayoutProbe
// ImageLayoutProbe RESOURCES_IMAGES OUTPUT [--show-window] [--require-windowserver]
// A SDK26-built executable can be run unchanged on both macOS13 and14.
import AppKit
import SwiftUI
import ImageIO
import ColorSync
import CryptoKit
import CoreText
import UniformTypeIdentifiers

private struct Failure: Error, CustomStringConvertible { let description: String }
private func rect(_ r: CGRect) -> [String: Double] {
    ["x": r.minX, "y": r.minY, "width": r.width, "height": r.height]
}
private enum Variant: String, CaseIterable { case upstream, standardHelper, availabilityWrapper }
private enum Fit { case contain, cover, fill }
private struct Picture {
    let image: CGImage
    var ratio: CGFloat { CGFloat(image.width) / CGFloat(image.height) }
}
private struct Assets {
    let images: [String: Picture]
    let metadata: [[String: Any]]
    init(_ directory: URL) throws {
        var images: [String: Picture] = [:], metadata: [[String: Any]] = []
        for name in ["landscape.jpg", "bern.png", "hdr-gainmap.jpg", "hdr-pq.png"] {
            let url = directory.appendingPathComponent(name)
            guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
                  let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else {
                throw Failure(description: "Cannot decode bundled fixture asset \(name)")
            }
            let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any]
            let space = image.colorSpace
            let icc = space.flatMap { $0.copyICCData() } as Data?
            var cicp = Data()
            if let icc, let profile = ColorSyncProfileCreate(icc as CFData, nil)?.takeRetainedValue(),
               let tag = ColorSyncProfileCopyTag(profile, "cicp" as CFString)?.takeRetainedValue() { cicp = tag as Data }
            images[name] = Picture(image: image)
            metadata.append([
                "name": name, "sha256": SHA256.hash(data: try Data(contentsOf: url)).description,
                "width": image.width, "height": image.height,
                "orientation": properties?[kCGImagePropertyOrientation] as? Int ?? 1,
                "profile_name": properties?[kCGImagePropertyProfileName] as? String ?? "unknown",
                "cg_color_space_name": space?.name as String? ?? "unknown",
                "cg_uses_itur2100_tf": space.map(CGColorSpaceUsesITUR_2100TF) ?? false,
                "cg_is_pq": space.map(CGColorSpaceIsPQBased) ?? false,
                "cg_is_hlg": space.map(CGColorSpaceIsHLGBased) ?? false,
                "icc_sha256": icc.map { SHA256.hash(data: $0).description } ?? "none",
                "icc_bytes": icc?.count ?? 0,
                "cicp_tag_hex": cicp.map { String(format: "%02x", $0) }.joined(),
            ])
        }
        self.images = images; self.metadata = metadata
    }
}

private extension View {
    @ViewBuilder func dynamicRangeWhereAvailable() -> some View {
        if #available(macOS 14, *) { allowedDynamicRange(.high) } else { self }
    }
}
private struct InactivePictureHero: ViewModifier {
    let id: String? = nil
    @State private var flying = false
    @ViewBuilder func body(content: Content) -> some View {
        if id != nil { content.opacity(flying ? 0 : 1) } else { content }
    }
}
// Preserve the upstream Group/conditional/fit construction, then compare the
// extraction and availability layers independently. HDR sections use ordinary
// Image in this geometry probe; Metal/EDR routing and luminance are out of scope.
private struct ProbeImage: View {
    let variant: Variant
    let picture: Picture
    let width: CGFloat
    var height: CGFloat? = nil
    var fit: Fit = .contain
    private let aspect: CGFloat? = nil
    @State private var fetched: Picture?
    private let url: String? = nil

    @ViewBuilder private func standardImage(_ picture: Picture) -> some View {
        let image = Image(decorative: picture.image, scale: 1, orientation: .up).renderingMode(.original)
        switch fit {
        case .contain: image.resizable().aspectRatio(contentMode: .fit)
        case .cover: image.resizable().aspectRatio(contentMode: .fill)
        case .fill: image.resizable()
        }
    }
    @ViewBuilder private var content: some View {
        let loaded: Picture? = picture
        switch variant {
        case .upstream:
            Group {
                if let loaded {
                    let image = Image(decorative: loaded.image, scale: 1, orientation: .up).renderingMode(.original)
                    switch fit {
                    case .contain: image.resizable().aspectRatio(contentMode: .fit)
                    case .cover: image.resizable().aspectRatio(contentMode: .fill)
                    case .fill: image.resizable()
                    }
                } else { Color.clear }
            }
        case .standardHelper:
            Group { if let loaded { standardImage(loaded) } else { Color.clear } }
        case .availabilityWrapper:
            Group {
                if let loaded {
                    if #available(macOS 14, *) { standardImage(loaded) }
                    else { standardImage(loaded) }
                } else { Color.clear }
            }
        }
    }
    var body: some View {
        let content = self.content.dynamicRangeWhereAvailable()
        let shown = Group {
            if let aspect {
                Color.clear.aspectRatio(max(0.01, aspect), contentMode: .fit)
                    .overlay { content }.clipped().frame(width: width, height: height)
            } else {
                content.frame(width: width, height: height ?? width / picture.ratio).clipped()
            }
        }.task(id: url) { guard url != nil else { return }; fetched = picture }
            .modifier(InactivePictureHero())
        shown.accessibilityElement().accessibilityLabel(Text("Bundled image")).accessibilityAddTraits(.isImage)
    }
}

private struct Anchors: PreferenceKey {
    static var defaultValue: [String: [Anchor<CGRect>]] = [:]
    static func reduce(value: inout [String: [Anchor<CGRect>]], nextValue: () -> [String: [Anchor<CGRect>]]) {
        value.merge(nextValue(), uniquingKeysWith: +)
    }
}
private struct Frames: PreferenceKey {
    static var defaultValue: [String: [CGRect]] = [:]
    static func reduce(value: inout [String: [CGRect]], nextValue: () -> [String: [CGRect]]) {
        value.merge(nextValue(), uniquingKeysWith: +)
    }
}
private extension View {
    func probe(_ name: String) -> some View {
        transformAnchorPreference(key: Anchors.self, value: .bounds) { values, anchor in
            values[name, default: []].append(anchor)
        }
    }
}
@MainActor private final class Measurements: ObservableObject {
    var frames: [String: [CGRect]] = [:]
    var environment: [String: Any] = [:]
    var widthEvents: [CGFloat] = []
}
private struct EnvironmentProbe: View {
    let receive: ([String: Any]) -> Void
    @Environment(\.dynamicTypeSize) private var dynamicType
    @Environment(\.sizeCategory) private var category
    @Environment(\.defaultMinListRowHeight) private var rowHeight
    @Environment(\.controlSize) private var controls
    @Environment(\.colorScheme) private var scheme
    @Environment(\.colorSchemeContrast) private var contrast
    @Environment(\.layoutDirection) private var direction
    @Environment(\.displayScale) private var scale
    @Environment(\.locale) private var locale
    @Environment(\.font) private var font
    var body: some View {
        Color.clear.onAppear {
            receive(["dynamic_type_size": String(describing: dynamicType), "size_category": String(describing: category),
                     "default_min_list_row_height": rowHeight, "control_size": String(describing: controls),
                     "color_scheme": String(describing: scheme), "contrast": String(describing: contrast),
                     "layout_direction": String(describing: direction), "display_scale": scale,
                     "locale": locale.identifier, "font": font.map { String(describing: $0) } ?? "inherited nil"])
        }.allowsHitTesting(false)
    }
}
// Same column-count calculation and initial width0 state as BernAdaptiveGrid.
@MainActor private struct AdaptiveGrid<Content: View>: View {
    let minimum: CGFloat
    let measurements: Measurements
    @ViewBuilder let content: Content
    @State private var width: CGFloat = 0
    var body: some View {
        let columns = max(1, Int((width + 16) / max(1, minimum + 16)))
        let grid = LazyVGrid(columns: Array(repeating: GridItem(.flexible(minimum: 0), spacing: 16, alignment: .top), count: columns), alignment: .leading, spacing: 16) { content }
            .frame(maxWidth: .infinity, alignment: .leading)
        #if compiler(>=6.0)
        grid.onGeometryChange(for: CGFloat.self) { $0.size.width } action: { measure($0) }
        #else
        // Only for the installed Swift5.9/SDK14.2 diagnostic build. The SDK26
        // artifact uses upstream onGeometryChange unchanged on both13 and14.
        grid.background(GeometryReader { g in
            Color.clear.onAppear { measure(g.size.width) }.onChange(of: g.size.width) { measure($0) }
        })
        #endif
    }
    private func measure(_ measured: CGFloat) {
        guard measured.isFinite, measured != width else { return }
        measurements.widthEvents.append(measured)
        var transaction = Transaction(); transaction.disablesAnimations = true
        withTransaction(transaction) { width = measured }
    }
}
// Upstream BernFormRows with nil custom background/insets: retain its Group
// and conditional shape without importing the product's state machinery.
private struct FormRows: ViewModifier {
    private let row: Color? = nil
    private let insets: EdgeInsets? = nil
    @ViewBuilder func body(content: Content) -> some View {
        let filled = Group { if let row { content.listRowBackground(row) } else { content } }
        if let insets { filled.listRowInsets(insets) } else { filled }
    }
}
@MainActor private struct LayoutForm: View {
    let variant: Variant
    let assets: Assets
    let measurements: Measurements
    let minimumRow: CGFloat?
    private let captions = ["Contain", "Cover", "Fill", "Width only"]
    private func picture(_ name: String, width: CGFloat, height: CGFloat? = nil, fit: Fit = .contain) -> some View {
        ProbeImage(variant: variant, picture: assets.images[name]!, width: width, height: height, fit: fit)
    }
    private func caption(_ text: String, _ key: String) -> some View {
        Text(verbatim: text).font(.caption).foregroundStyle(.secondary).probe("caption.\(key)")
    }
    private var form: some View {
        Form {
            Section {
                AdaptiveGrid(minimum: 120, measurements: measurements) {
                    ForEach(0..<4, id: \.self) { i in
                        VStack(alignment: .center, spacing: 6) {
                            picture(i == 3 ? "bern.png" : "landscape.jpg", width: i == 3 ? 64 : 120, height: i == 3 ? nil : 90, fit: i == 1 ? .cover : i == 2 ? .fill : .contain).probe("image.images.\(i)")
                            caption(captions[i], "images.\(i)")
                        }.probe("column.images.\(i)")
                    }
                }.probe("grid.images").probe("row.images")
            } header: { Text("Images").probe("header.images") }
              footer: { Text("Pictures are bundled resources. The same 16:9 picture in a 120×90 frame: Contain leaves bars, Cover crops the sides, Fill stretches it.").probe("footer.images") }
                .modifier(FormRows()).probe("section.images.semantic_anchor")
            Section {
                AdaptiveGrid(minimum: 192, measurements: measurements) {
                    VStack(alignment: .center, spacing: 6) {
                        picture("hdr-gainmap.jpg", width: 192, height: 108).probe("image.hdr.gainmap")
                        caption("Gain map JPEG", "hdr.gainmap")
                    }.probe("column.hdr.gainmap")
                    VStack(alignment: .center, spacing: 6) {
                        picture("hdr-pq.png", width: 192, height: 108).probe("image.hdr.pq")
                        caption("PQ PNG", "hdr.pq")
                    }.probe("column.hdr.pq")
                }.probe("grid.hdr").probe("row.hdr")
            } header: { Text("HDR Pictures").probe("header.hdr") }
              footer: { Text("The left half is SDR white, the right half four times as bright. On a display that shows HDR the right half is brighter; elsewhere the author's SDR version or compressed highlights show.").probe("footer.hdr") }
                .modifier(FormRows()).probe("section.hdr.semantic_anchor")
            Section {
                ZStack(alignment: .topTrailing) {
                    picture("landscape.jpg", width: 320, height: 180, fit: .cover).probe("image.layers.background")
                    VStack(alignment: .leading) { picture("bern.png", width: 40).probe("image.layers.mark") }.padding(8)
                }.probe("row.layers")
            } header: { Text("Layers").probe("header.layers") }
              footer: { Text("Later layers sit on top; the mark aligns to the top trailing corner.").probe("footer.layers") }
                .modifier(FormRows()).probe("section.layers.semantic_anchor")
            Section {
                ProgressView("Committed volume", value: 50, total: 100).probe("row.progress.volume")
                ProgressView("Brightness", value: 0.6).probe("row.progress.brightness")
                Slider(value: .constant(0.6), in: 0...1).probe("row.progress.slider")
                ProgressView("Waiting…").probe("row.progress.waiting")
            } header: { Text("Progress").probe("header.progress") }
              footer: { Text("Progress bars follow engine state or session drafts; without a value, progress is indeterminate.").probe("footer.progress") }
                .modifier(FormRows()).probe("section.progress.semantic_anchor")
            Section {
                AdaptiveGrid(minimum: 140, measurements: measurements) {
                    ForEach(Array(["Documents", "Photos", "Music", "Movies", "Downloads"].enumerated()), id: \.offset) { i, name in
                        VStack(alignment: .leading, spacing: 4) { Label(name, systemImage: "doc"); Text("\(i + 1) items").font(.caption).foregroundStyle(.secondary) }.probe("column.items.\(i)")
                    }
                }.probe("grid.items").probe("row.items")
            } header: { Text("Grid").probe("header.items") }
              footer: { Text("Columns are at least 140 wide; widening the window adds columns. Items come from engine state.").probe("footer.items") }
                .modifier(FormRows()).probe("section.items.semantic_anchor")
            Section {
                Color.clear.frame(height: 109).probe("row.fixed109")
            } header: { Text("Control: fixed109pt single child").probe("header.fixed109") }
                .modifier(FormRows()).probe("section.fixed109.semantic_anchor")
            Section {
                caption("Single caption", "single").probe("row.single_caption")
            } header: { Text("Control: single caption").probe("header.single_caption") }
                .modifier(FormRows()).probe("section.single_caption.semantic_anchor")
            Section {
                HStack(spacing: 12) {
                    Color(nsColor: .windowBackgroundColor).frame(width: 100, height: 24).probe("color.windowBackground")
                    Color(nsColor: .controlBackgroundColor).frame(width: 100, height: 24).probe("color.controlBackground")
                }.probe("row.semantic_colors")
            } header: { Text("Control: semantic NSColor fills").probe("header.semantic_colors") }
                .modifier(FormRows()).probe("section.semantic_colors.semantic_anchor")
        }.formStyle(.grouped).probe("form")
    }
    @ViewBuilder var body: some View {
        let measured = form.overlayPreferenceValue(Anchors.self) { anchors in
            GeometryReader { geometry in
                Color.clear.preference(key: Frames.self, value: anchors.mapValues { $0.map { geometry[$0] } })
            }.allowsHitTesting(false)
        }
        .onPreferenceChange(Frames.self) { measurements.frames = $0 }
        .background(EnvironmentProbe { measurements.environment = $0 })
        if let minimumRow { measured.environment(\.defaultMinListRowHeight, minimumRow) } else { measured }
    }
}

@MainActor private final class Runner {
    let output: URL
    let assets: Assets
    let show: Bool
    let requireCapture: Bool
    private let started = Date()
    private let before = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
    private var cases: [[String: Any]] = []
    private var window: NSWindow?
    init(output: URL, assets: Assets, show: Bool, requireCapture: Bool) {
        self.output = output; self.assets = assets; self.show = show; self.requireCapture = requireCapture
    }
    private func pump(_ seconds: TimeInterval) throws {
        guard Date().timeIntervalSince(started) < 90 else { throw Failure(description: "90-second probe deadline exceeded") }
        RunLoop.main.run(until: Date(timeIntervalSinceNow: seconds))
    }
    private func views(_ root: NSView) -> [NSView] { [root] + root.subviews.flatMap(views) }
    private func scroll(_ host: NSView, fraction: CGFloat, centeredRow: CGRect? = nil) -> [String: Any] {
        guard let scroll = views(host).compactMap({ $0 as? NSScrollView }).first,
              let document = scroll.documentView else { return ["found": false] }
        let start = document.bounds.minY, end = max(start, document.bounds.maxY - scroll.contentView.bounds.height)
        let y: CGFloat
        if let centeredRow {
            let delta = centeredRow.midY - host.bounds.midY
            y = min(end, max(start, scroll.contentView.bounds.minY + (document.isFlipped ? delta : -delta)))
        } else { y = document.isFlipped ? start + (end - start) * fraction : end - (end - start) * fraction }
        scroll.contentView.scroll(to: CGPoint(x: scroll.contentView.bounds.minX, y: y))
        scroll.reflectScrolledClipView(scroll.contentView)
        return ["found": true, "clip": rect(scroll.contentView.bounds), "document": rect(document.bounds), "document_flipped": document.isFlipped]
    }
    private func settled(_ model: Measurements, host: NSView) throws -> Int {
        var previous: [String: [CGRect]] = [:], stable = 0
        for _ in 0..<30 {
            host.layoutSubtreeIfNeeded(); try pump(0.08)
            if model.frames == previous, (model.frames["form"]?.first?.width ?? 0) > 500 { stable += 1 } else { stable = 0 }
            previous = model.frames
            if stable >= 3 { return stable }
        }
        throw Failure(description: "Public layout frames did not settle")
    }
    private func capture(_ window: NSWindow, name: String) throws -> CGImage? {
        guard show else { return nil }
        guard let image = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(window.windowNumber), .boundsIgnoreFraming) else {
            if requireCapture { throw Failure(description: "WindowServer capture unavailable; no offscreen fallback") }; return nil
        }
        guard let writer = CGImageDestinationCreateWithURL(output.appendingPathComponent(name) as CFURL, UTType.png.identifier as CFString, 1, nil) else { throw Failure(description: "Cannot create PNG") }
        CGImageDestinationAddImage(writer, image, nil)
        guard CGImageDestinationFinalize(writer) else { throw Failure(description: "Cannot finish PNG") }
        return image
    }
    // The system card has no public NSView frame. Measure its painted border
    // independently, at a blank trailing column, rather than declaring a
    // Section anchor (which may be transparently propagated) to be that frame.
    private func card(_ row: CGRect, image: CGImage, host: NSView, window: NSWindow) -> [String: Any]? {
        let converted = host.convert(row, to: nil)
        let r = CGRect(x: converted.minX, y: window.frame.height - converted.maxY, width: converted.width, height: converted.height)
        let content = host.convert(host.bounds, to: nil)
        let viewport = CGRect(x: content.minX, y: window.frame.height - content.maxY, width: content.width, height: content.height)
        guard r.minY >= viewport.minY + 12, r.maxY <= viewport.maxY - 12 else { return nil }
        let sx = CGFloat(image.width) / window.frame.width, sy = CGFloat(image.height) / window.frame.height
        var pixels = [UInt8](repeating: 0, count: image.width * image.height * 4)
        let drawn = pixels.withUnsafeMutableBytes { bytes -> Bool in
            guard let context = CGContext(data: bytes.baseAddress, width: image.width, height: image.height, bitsPerComponent: 8,
                                          bytesPerRow: image.width * 4, space: CGColorSpace(name: CGColorSpace.sRGB)!,
                                          bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.byteOrder32Big.rawValue) else { return false }
            context.draw(image, in: CGRect(x: 0, y: 0, width: image.width, height: image.height))
            return true
        }
        guard drawn else { return nil }
        func rgb(_ x: Int, _ y: Int) -> [Int] { let i = (y * image.width + x) * 4; return [Int(pixels[i]), Int(pixels[i+1]), Int(pixels[i+2])] }
        func distance(_ a: [Int], _ b: [Int]) -> Int { zip(a, b).map { abs($0 - $1) }.max() ?? 0 }
        let x = Int((viewport.maxX - 45) * sx), y = Int(r.midY * sy)
        guard x >= 0, y >= 0, x < image.width, y < image.height else { return nil }
        let page = rgb(Int((viewport.minX + 5) * sx), y), fill = rgb(x, y)
        guard distance(page, fill) >= 3 else { return nil }
        var top = y, bottom = y, left = Int((viewport.minX + 8) * sx), right = Int((viewport.maxX - 12) * sx)
        while top > Int(viewport.minY * sy), distance(rgb(x, top - 1), page) > 1 { top -= 1 }
        while bottom + 1 < Int(viewport.maxY * sy), distance(rgb(x, bottom + 1), page) > 1 { bottom += 1 }
        while left < x, distance(rgb(left, y), page) <= 1 { left += 1 }
        while right > x, distance(rgb(right, y), page) <= 1 { right -= 1 }
        let bounds = CGRect(x: CGFloat(left) / sx, y: CGFloat(top) / sy, width: CGFloat(right - left + 1) / sx, height: CGFloat(bottom - top + 1) / sy)
        guard bounds.minY > viewport.minY, bounds.maxY < viewport.maxY,
              bounds.height >= r.height - 1, bounds.height < r.height + 180 else { return nil }
        return ["frame_window_top_left_points": rect(bounds), "row_window_top_left_points": rect(r),
                "method": "WindowServer PNG converted to sRGB; page-color transition at blank trailing column; one-pixel boundary uncertainty",
                "uncertainty_points": max(1 / sx, 1 / sy), "page_srgb": page, "card_srgb": fill]
    }
    func run() throws {
        for variant in Variant.allCases {
            for minimum: CGFloat? in [nil, 0, 150] {
                let label = minimum.map { String(Int($0)) } ?? "inherited"
                let key = "\(variant.rawValue)-minrow-\(label)"
                let model = Measurements()
                let host = NSHostingView(rootView: LayoutForm(variant: variant, assets: assets, measurements: model, minimumRow: minimum))
                let window = NSWindow(contentRect: CGRect(x: 100, y: 120, width: 779, height: 616), styleMask: [.titled, .closable], backing: .buffered, defer: false)
                self.window = window; window.isReleasedWhenClosed = false; window.isRestorable = false
                window.title = "Image layout probe: \(key)"; window.contentView = host
                window.setContentSize(CGSize(width: 779, height: 616))
                if show { window.orderBack(nil) } else { window.orderOut(nil) }
                var phases: [[String: Any]] = [], cards: [String: Any] = [:], expectedFramesObserved = false
                for (phase, fraction) in [("top", CGFloat(0)), ("middle", CGFloat(0.5)), ("bottom", CGFloat(1))] {
                    _ = try settled(model, host: host)
                    let scrollInfo = scroll(host, fraction: fraction, centeredRow: phase == "middle" ? model.frames["row.layers"]?.first : nil)
                    let stable = try settled(model, host: host)
                    if model.frames["caption.images.0"]?.count == 1, model.frames["grid.images"]?.count == 1 { expectedFramesObserved = true }
                    let name = "\(key)-\(phase).png"
                    let image = try capture(window, name: name)
                    if let image {
                        for section in ["images", "hdr", "layers", "fixed109", "single_caption"] {
                            if let row = model.frames["row.\(section)"]?.first,
                               let bounds = card(row, image: image, host: host, window: window) { cards[section] = bounds }
                        }
                    }
                    phases.append(["phase": phase, "scroll": scrollInfo, "stable_equal_frame_samples": stable,
                                   "frames_form_top_left_points": model.frames.mapValues { $0.map(rect) },
                                   "png": image == nil ? NSNull() : name as Any,
                                   "window_frame": rect(window.frame), "content_bounds": rect(host.bounds),
                                   "visible": window.isVisible, "key": window.isKeyWindow, "backing_scale": window.backingScaleFactor,
                                   "effective_appearance": window.effectiveAppearance.name.rawValue,
                                   "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
                }
                let complete = ["images", "hdr", "layers"].allSatisfy { cards[$0] != nil }
                cases.append(["case": key, "variant": variant.rawValue, "minimum_row_requested": minimum.map { Double($0) as Any } ?? NSNull(),
                              "environment": model.environment, "grid_width_events": model.widthEvents,
                              "phases": phases, "native_cards_from_pixels": cards, "three_image_cards_pixel_detection_complete": complete])
                try save(success: false, error: "Probe still running")
                window.orderOut(nil); window.contentView = nil; window.close(); self.window = nil
                guard expectedFramesObserved, !model.environment.isEmpty else { throw Failure(description: "Missing or ambiguous public probe frames in \(key)") }
                if requireCapture && !complete { throw Failure(description: "Native image-card borders not fully detected in \(key); inspect PNGs and public frames") }
            }
        }
        try save(success: true)
    }
    func save(success: Bool, error: String? = nil) throws {
        let font = NSFont.preferredFont(forTextStyle: .caption1)
        let fontMetrics = ["point_size": font.pointSize, "ascender": font.ascender, "descender": font.descender, "leading": font.leading]
        var colors: [String: Any] = [:]
        NSAppearance.currentDrawing().performAsCurrentDrawingAppearance {
            for (name, color) in [("windowBackground", NSColor.windowBackgroundColor), ("controlBackground", NSColor.controlBackgroundColor)] {
                if let c = color.usingColorSpace(.sRGB) { colors[name] = ["red": c.redComponent, "green": c.greenComponent, "blue": c.blueComponent, "alpha": c.alphaComponent] }
            }
        }
        let report: [String: Any] = ["success": success, "error": error as Any? ?? NSNull(),
            "probe_source_sha": ProcessInfo.processInfo.environment["BERN_PROBE_SHA"] ?? "local",
            "os": ProcessInfo.processInfo.operatingSystemVersionString, "architecture": ProcessInfo.processInfo.machineArchitecture,
            "bundle_identifier": Bundle.main.bundleIdentifier ?? "standalone executable",
            "scope": "Standalone public SwiftUI layout plus real WindowServer card-border measurement. Not the Bern application; HDR pixels/EDR and model behavior are excluded.",
            "section_anchor_contract": "Section is a semantic container. All raw anchor samples and their counts are retained; they are not asserted to be native card allocation. Header/row/footer union can be derived. Native card borders are independently measured from PNGs.",
            "capture_contract": "No offscreen screenshot fallback. Unordered mode supplies geometry only. --require-windowserver requires real PNGs and all three image cards per case.",
            "compiler_contract": "SDK26/Swift6 uses original onGeometryChange. Swift5.9/SDK14.2 local diagnostic uses a GeometryReader width adapter; same SDK26 binary should be rerun on13 for a strict compiler-controlled comparison.",
            "assets": assets.metadata, "native_caption1_font_metrics": fontMetrics, "semantic_nscolor_srgb": colors,
            "system_preferences": ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                                   "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                                   "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
            "window_requested_content_points": ["width": 779, "height": 616], "shown": show,
            "frontmost_pid_before": before, "frontmost_pid_after": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,
            "elapsed_seconds": Date().timeIntervalSince(started), "cases": cases]
        try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys]).write(to: output.appendingPathComponent("report.json"), options: .atomic)
    }
    func cleanup() {
        window?.orderOut(nil); window?.close(); window = nil
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid(), let previous = NSRunningApplication(processIdentifier: before) { _ = previous.activate(options: []) }
    }
}
private extension ProcessInfo {
    var machineArchitecture: String {
        var info = utsname(); uname(&info)
        let capacity = MemoryLayout.size(ofValue: info.machine)
        return withUnsafePointer(to: &info.machine) { $0.withMemoryRebound(to: CChar.self, capacity: capacity) { String(cString: $0) } }
    }
}
@main private enum Main {
    @MainActor static func main() {
        guard CommandLine.arguments.count >= 3 else { fputs("usage: ImageLayoutProbe RESOURCES_IMAGES OUTPUT [--show-window] [--require-windowserver]\n", stderr); exit(2) }
        let output = URL(fileURLWithPath: CommandLine.arguments[2], isDirectory: true)
        var runner: Runner?
        do {
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            let assets = try Assets(URL(fileURLWithPath: CommandLine.arguments[1], isDirectory: true))
            let show = CommandLine.arguments.contains("--show-window"), required = CommandLine.arguments.contains("--require-windowserver")
            guard !required || show else { throw Failure(description: "--require-windowserver also requires --show-window") }
            let app = NSApplication.shared; app.setActivationPolicy(show ? .accessory : .prohibited)
            app.appearance = NSAppearance(named: .aqua); app.finishLaunching()
            let task = Runner(output: output, assets: assets, show: show, requireCapture: required); runner = task
            defer { task.cleanup() }
            try task.run()
        } catch {
            try? runner?.save(success: false, error: String(describing: error)); runner?.cleanup()
            fputs("Image layout probe failed: \(error)\n", stderr); exit(1)
        }
    }
}
