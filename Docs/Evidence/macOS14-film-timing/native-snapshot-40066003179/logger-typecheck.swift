import AppKit
import Foundation
// Diagnostic-only, non-observable logger. No View modifiers or Binding wrappers.
@MainActor
private enum BernScrollTrace {
    private final class Scope {
        weak var owner: AnyObject?
        let id = UUID().uuidString
        let kind: String
        init(_ owner: AnyObject) { self.owner = owner; kind = String(reflecting: type(of: owner)) }
    }
    private static let directory = ProcessInfo.processInfo.environment["BERN_SCROLL_TRACE_DIR"]
        .flatMap { $0.isEmpty ? nil : URL(fileURLWithPath: $0, isDirectory: true) }
    private static var scopes: [ObjectIdentifier: Scope] = [:]
    private static var scopeMetadata = [[String: String]]()
    private static var events = [[String: Any]]()
    private static var dropped = 0
    private static var firstExpect: Double?
    private static var written = false
    static func identifier(_ owner: AnyObject) -> String {
        guard directory != nil else { return "disabled" }
        let key = ObjectIdentifier(owner)
        if let scope = scopes[key], scope.owner === owner { return scope.id }
        let scope = Scope(owner); scopes[key] = scope
        scopeMetadata.append(["id": scope.id, "kind": scope.kind])
        return scope.id
    }
    static func record(_ owner: AnyObject, _ event: String, _ fields: () -> [String: Any] = { [:] }) {
        guard directory != nil, !written else { return }
        guard events.count < 4096 else { dropped += 1; return }
        let scope = identifier(owner)
        events.append(["sequence": events.count, "uptime": ProcessInfo.processInfo.systemUptime,
            "scope": scope, "event": event, "fields": fields()])
    }
    static func arm(_ owner: AnyObject) {
        guard directory != nil, firstExpect == nil else { return }
        firstExpect = ProcessInfo.processInfo.systemUptime
        record(owner, "trace.first-expect")
        Task { @MainActor in
            try? await Task.sleep(for: .seconds(2))
            flush()
        }
    }
    // Read public native geometry only after the original two-second event
    // interval. This does not add a view or intervene in layout/scroll callbacks.
    private static func nativeSnapshot() -> [String: Any] {
        #if os(macOS)
        func r(_ value: NSRect) -> [String: Any] { rectangle(value) }
        func insets(_ value: NSEdgeInsets) -> [String: CGFloat] {
            ["top": value.top, "left": value.left, "bottom": value.bottom, "right": value.right]
        }
        var windows = [[String: Any]]()
        for window in NSApplication.shared.windows.prefix(8) {
            var queue: [(NSView, Int)] = window.contentView.map { [($0, 0)] } ?? []
            var index = 0, scrolls = [[String: Any]]()
            while index < queue.count && index < 4096 {
                let (view, depth) = queue[index]; index += 1
                if let scroll = view as? NSScrollView {
                    let clip = scroll.contentView
                    var row: [String: Any] = ["class": String(reflecting: type(of: scroll)),
                        "frame_in_parent": r(scroll.frame), "bounds": r(scroll.bounds),
                        "frame_in_window": r(scroll.convert(scroll.bounds, to: nil)),
                        "content_size": [scroll.contentSize.width, scroll.contentSize.height],
                        "content_insets": insets(scroll.contentInsets),
                        "automatically_adjusts_content_insets": scroll.automaticallyAdjustsContentInsets,
                        "clip_frame_in_scroll": r(clip.frame), "clip_bounds": r(clip.bounds),
                        "clip_frame_in_window": r(clip.convert(clip.bounds, to: nil)),
                        "clip_document_rect": r(clip.documentRect),
                        "clip_document_visible_rect": r(clip.documentVisibleRect),
                        "clip_flipped": clip.isFlipped, "depth": depth]
                    if let document = scroll.documentView {
                        row["document"] = ["class": String(reflecting: type(of: document)),
                            "frame_in_clip": r(document.frame), "bounds": r(document.bounds),
                            "frame_in_window": r(document.convert(document.bounds, to: nil)),
                            "flipped": document.isFlipped]
                    }
                    scrolls.append(row)
                }
                if depth < 32 { queue += view.subviews.map { ($0, depth + 1) } }
            }
            windows.append(["window_number": window.windowNumber, "frame": r(window.frame),
                "content_layout_rect": r(window.contentLayoutRect), "visible": window.isVisible,
                "key": window.isKeyWindow, "main": window.isMainWindow,
                "visited_views": index, "queue_count": queue.count,
                "truncated": index < queue.count, "scroll_views": scrolls])
        }
        return ["contract": "public AppKit reads at trace flush only; no view-tree or scroll mutation",
            "uptime": ProcessInfo.processInfo.systemUptime, "application_active": NSApplication.shared.isActive,
            "window_limit": 8, "windows": windows]
        #else
        return ["unavailable": "AppKit snapshot is macOS-only"]
        #endif
    }
    private static func flush() {
        guard let directory, !written else { return }
        written = true
        let report: [String: Any] = ["schema": 1, "pid": ProcessInfo.processInfo.processIdentifier,
            "base_source": "f9e08b1d55bed4b9d880b19934abe48281057bb3",
            "os": ProcessInfo.processInfo.operatingSystemVersionString,
            "first_expect_uptime": firstExpect ?? 0, "flush_uptime": ProcessInfo.processInfo.systemUptime,
            "limit": 4096, "dropped": dropped,
            "binding_scope": "Original $target Binding unchanged; target.observed is the existing onChange callback, not each native setter invocation.",
            "scope_relationships": "Weak object-instance IDs; snap and position scopes are not automatically assigned a window or cross-linked.",
            "scopes": scopeMetadata, "events": events, "native_snapshot": nativeSnapshot()]
        do {
            let data = try JSONSerialization.data(withJSONObject: jsonValue(report), options: [.prettyPrinted, .sortedKeys])
            try FileManager.default.createDirectory(at: directory, withIntermediateDirectories: true)
            try data.write(to: directory.appendingPathComponent("scroll-\(ProcessInfo.processInfo.processIdentifier).json"), options: .atomic)
        } catch { FileHandle.standardError.write(Data("Bern scroll diagnostic write failed: \(error)\n".utf8)) }
        events.removeAll(keepingCapacity: false)
    }
    static func key(_ value: AnyHashable?) -> Any {
        guard let value else { return NSNull() }
        return ["type": String(reflecting: type(of: value.base)), "value": String(describing: value.base)]
    }
    static func rectangle(_ r: CGRect) -> [String: Any] {
        guard [r.minX, r.minY, r.width, r.height].allSatisfy({ $0.isFinite }) else { return ["nonfinite": true] }
        return ["x": r.minX, "y": r.minY, "width": r.width, "height": r.height]
    }
    private static func jsonValue(_ value: Any) -> Any {
        if let n = value as? NSNumber, !n.doubleValue.isFinite { return ["nonfinite_number": n.stringValue] }
        if let d = value as? [String: Any] { return d.mapValues { jsonValue($0) } }
        if let a = value as? [Any] { return a.map { jsonValue($0) } }
        return value
    }
}

