import AppKit
import SwiftUI
import Foundation

private func bernPictureRect(_ r: CGRect) -> [String: Double] {
    ["x": Double(r.origin.x), "y": Double(r.origin.y), "width": Double(r.width), "height": Double(r.height)]
}
private func bernPictureValid(_ r: CGRect, positive: Bool = false) -> Bool {
    [r.origin.x, r.origin.y, r.width, r.height].allSatisfy { $0.isFinite }
        && r.width >= 0 && r.height >= 0 && (!positive || (r.width > 0 && r.height > 0))
}

@MainActor private final class BernPictureObservationStore {
    static let shared = BernPictureObservationStore()
    static let labels: Set<String> = [
        "form-root", "images-grid", "hdr-grid",
        "images-contain-column", "images-contain-image", "images-contain-caption",
        "images-cover-column", "images-cover-image", "images-cover-caption",
        "images-fill-column", "images-fill-image", "images-fill-caption",
        "images-mark-column", "images-mark-image", "images-mark-caption",
        "hdr-gainmap-column", "hdr-gainmap-image", "hdr-gainmap-caption",
        "hdr-pq-column", "hdr-pq-image", "hdr-pq-caption"
    ]
    private let output: URL?
    private let pid = ProcessInfo.processInfo.processIdentifier
    private var events: [[String: Any]] = []
    private var last: [String: Data] = [:]
    private var stopped = false
    var acceptsEvents: Bool { output != nil && !stopped }

    private init() {
        guard let path = ProcessInfo.processInfo.environment["BERN_PICTURE_OBSERVER_OUTPUT_DIR"], !path.isEmpty else {
            output = nil; return
        }
        var directory: ObjCBool = false
        let folder = URL(fileURLWithPath: path, isDirectory: true)
        let file = folder.appendingPathComponent("picture-observer-\(ProcessInfo.processInfo.processIdentifier).json")
        guard FileManager.default.fileExists(atPath: folder.path, isDirectory: &directory), directory.boolValue,
              !FileManager.default.fileExists(atPath: file.path) else { output = nil; return }
        output = file
    }

    func append(_ observation: [String: Any], label: String, callback: String) {
        guard acceptsEvents, let output, Self.labels.contains(label) else { return }
        do {
            let fingerprint = try JSONSerialization.data(withJSONObject: observation, options: [.sortedKeys])
            guard last[label] != fingerprint else { return }
            guard events.count < 256 else { stopped = true; return }
            var event = observation
            event["sequence"] = events.count
            event["observed_uptime_seconds"] = ProcessInfo.processInfo.systemUptime
            event["callback"] = callback
            let next = events + [event]
            let packet: [String: Any] = [
                "schema": "bern_picture_public_geometry_v1", "pid": pid,
                "event_limit": 256, "file_byte_limit": 512 * 1024,
                "end_state": "not_observed", "events": next
            ]
            let data = try JSONSerialization.data(withJSONObject: packet, options: [.sortedKeys])
            guard data.count <= 512 * 1024 else { stopped = true; return }
            try data.write(to: output, options: events.isEmpty ? [.withoutOverwriting] : [.atomic])
            events = next
            last[label] = fingerprint
        } catch {
            // Keep the last successful append-only history. No alternate path or unmount write.
            stopped = true
        }
    }
}

@MainActor private final class BernPictureObservationView: NSView {
    var label = ""
    var inheritedEnvironment: [String: Any] = [:]
    var resolvedSize: CGSize = .zero
    var swiftUIGlobalFrame: CGRect = .zero
    override var isOpaque: Bool { false }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }
    override func viewDidMoveToWindow() { super.viewDidMoveToWindow(); observe("viewDidMoveToWindow") }
    override func layout() { super.layout(); observe("layout") }
    override func setFrameOrigin(_ origin: NSPoint) { super.setFrameOrigin(origin); observe("setFrameOrigin") }
    override func setFrameSize(_ size: NSSize) { super.setFrameSize(size); observe("setFrameSize") }

    private func node(_ view: NSView, in window: NSWindow) -> [String: Any]? {
        guard view.window === window else { return nil }
        let base = view.convert(view.bounds, to: nil)
        let screen = window.convertToScreen(base)
        let probe = convert(bounds, to: view)
        guard [view.frame, view.bounds, base, screen, probe].allSatisfy({ bernPictureValid($0) }) else { return nil }
        return [
            "class": NSStringFromClass(type(of: view)), "object_id": String(describing: ObjectIdentifier(view)),
            "is_flipped": view.isFlipped, "frame_in_superview": bernPictureRect(view.frame),
            "bounds_local": bernPictureRect(view.bounds), "bounds_in_window_base": bernPictureRect(base),
            "bounds_in_screen_bottom_left": bernPictureRect(screen), "probe_bounds_in_node": bernPictureRect(probe)
        ]
    }

    func observe(_ callback: String) {
        let store = BernPictureObservationStore.shared
        guard store.acceptsEvents, BernPictureObservationStore.labels.contains(label), let window,
              bernPictureValid(bounds, positive: true), bernPictureValid(window.frame, positive: true),
              bernPictureValid(CGRect(origin: .zero, size: resolvedSize), positive: true),
              bernPictureValid(swiftUIGlobalFrame, positive: true), bernPictureValid(window.contentLayoutRect),
              let probe = node(self, in: window), let content = window.contentView,
              let contentNode = node(content, in: window) else { return }
        var ancestors: [[String: Any]] = []
        var parent = superview
        for _ in 0..<6 {
            guard let view = parent else { break }
            guard let value = node(view, in: window) else { return }
            ancestors.append(value)
            parent = view.superview
        }
        var scrollRecord: Any = NSNull()
        if let scroll = enclosingScrollView {
            guard let scrollNode = node(scroll, in: window), let clip = node(scroll.contentView, in: window) else { return }
            var document: Any = NSNull()
            if let view = scroll.documentView {
                guard let value = node(view, in: window) else { return }
                document = value
            }
            scrollRecord = ["scroll_view": scrollNode, "clip_view": clip, "document_view": document]
        }
        store.append([
            "label": label, "environment_at_probe": inheritedEnvironment,
            "resolved_size": ["width": Double(resolvedSize.width), "height": Double(resolvedSize.height)],
            "swiftui_global_frame": bernPictureRect(swiftUIGlobalFrame),
            "probe_bounds_size_equals_resolved_size": bounds.size == resolvedSize,
            "probe": probe, "content_view": contentNode,
            "window": ["number": window.windowNumber, "frame_in_screen_bottom_left": bernPictureRect(window.frame),
                       "content_layout_rect": bernPictureRect(window.contentLayoutRect),
                       "backing_scale_factor": Double(window.backingScaleFactor),
                       "is_visible": window.isVisible, "is_key": window.isKeyWindow, "is_main": window.isMainWindow,
                       "level_raw": window.level.rawValue],
            "nearest_enclosing_scroll_view": scrollRecord,
            "ancestors_nearest_first": ancestors, "ancestor_limit": 6, "ancestor_chain_truncated": parent != nil
        ], label: label, callback: callback)
    }
}

@MainActor private struct BernPictureNativeObservation: NSViewRepresentable {
    let label: String
    let environment: [String: Any]
    let size: CGSize
    let globalFrame: CGRect
    func makeNSView(context: Context) -> BernPictureObservationView { BernPictureObservationView(frame: .zero) }
    func updateNSView(_ view: BernPictureObservationView, context: Context) {
        view.label = label
        view.inheritedEnvironment = environment
        view.resolvedSize = size
        view.swiftUIGlobalFrame = globalFrame
        view.observe("updateNSView")
    }
    // No dismantle action: a late unmount must not replace the valid attached history.
}

@MainActor private struct BernPictureMeasurement: ViewModifier {
    let label: String
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
    func body(content: Content) -> some View {
        content.background {
            GeometryReader { geometry in
                BernPictureNativeObservation(label: label, environment: [
                    "dynamic_type_size": String(describing: dynamicType), "size_category": String(describing: category),
                    "default_min_list_row_height": Double(rowHeight), "control_size": String(describing: controls),
                    "color_scheme": String(describing: scheme), "contrast": String(describing: contrast),
                    "layout_direction": String(describing: direction), "display_scale": Double(scale),
                    "locale": locale.identifier, "font": font.map { String(describing: $0) } ?? "inherited nil"
                ], size: geometry.size, globalFrame: geometry.frame(in: .global))
            }
            .allowsHitTesting(false)
            .accessibilityHidden(true)
        }
    }
}

@MainActor extension View {
    func bernPictureMeasure(_ label: String) -> some View { modifier(BernPictureMeasurement(label: label)) }
}
