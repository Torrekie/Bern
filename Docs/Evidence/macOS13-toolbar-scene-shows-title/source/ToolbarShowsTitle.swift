import AppKit
import SwiftUI
import Foundation

// One immutable Boolean selects the Scene parameter; no style/role matrix.
private struct Configuration {
    let mode: String
    let showsTitle: Bool
    let output: URL?
    let error: String?
    let title = "Buttons"

    init() {
        let arguments = Array(CommandLine.arguments.dropFirst())
        mode = arguments.first ?? "invalid"
        showsTitle = mode == "true"
        var failure: String?
        if arguments.count != 1 || !["true", "false"].contains(mode) {
            failure = "Expected exactly one argument: true or false"
        }
        let path = ProcessInfo.processInfo.environment["BERN_TOOLBAR_PROBE_OUTPUT"] ?? ""
        var directory: ObjCBool = false
        if path.hasPrefix("/"), FileManager.default.fileExists(atPath: path, isDirectory: &directory), directory.boolValue {
            output = URL(fileURLWithPath: path, isDirectory: true)
        } else {
            output = nil
            failure = failure ?? "BERN_TOOLBAR_PROBE_OUTPUT must name an existing absolute directory"
        }
        error = failure
    }
}
private let configuration = Configuration()

@MainActor
private struct ProbeRoot: View {
    @State private var selected: String? = "Buttons"
    @State private var search = ""

    var body: some View {
        NavigationSplitView {
            List(selection: $selected) {
                Section("Controls") {
                    Label("Text", systemImage: "textformat").tag("Text")
                    Label("Buttons", systemImage: "hand.tap").tag("Buttons")
                    Label("Switches & Sliders", systemImage: "switch.2").tag("Controls")
                    Label("Text Fields", systemImage: "character.cursor.ibeam").tag("Inputs")
                    Label("Images & Layout", systemImage: "photo").tag("Layout")
                }
                Section("Data") {
                    Label("List & Detail", systemImage: "list.bullet.rectangle").tag("Library")
                    Label("Video", systemImage: "play.rectangle").tag("Media")
                }
            }
            .navigationSplitViewColumnWidth(min: 180, ideal: 210, max: 320)
            .searchable(text: $search, placement: .sidebar, prompt: "Search")
        } detail: {
            Form {
                Section("Button Styles") {
                    Text("Independent native toolbar layout fixture")
                }
            }
            .formStyle(.grouped)
            .navigationTitle(configuration.title)
            .toolbar {
                ToolbarItemGroup(placement: .automatic) {
                    Button {} label: { Label("Toolbar Button", systemImage: "plus") }
                }
            }
        }
        .onAppear { NativeSamples.shared.start() }
    }
}

@MainActor
private final class NativeSamples {
    static let shared = NativeSamples()
    private var started = false
    private weak var observedWindow: NSWindow?
    private var initialFrame: [String: CGFloat]?
    private var samples = [[String: Any]]()
    private let files = FileManager.default

    private func rect(_ value: NSRect) -> [String: CGFloat] {
        ["x": value.minX, "y": value.minY, "width": value.width, "height": value.height]
    }
    private func windowRect(_ value: NSRect, _ window: NSWindow) -> [String: CGFloat] {
        ["x": value.minX, "y_from_bottom": value.minY,
         "y_from_top": window.frame.height - value.maxY,
         "width": value.width, "height": value.height]
    }
    private func descendants(_ root: NSView) -> (nodes: [NSView], truncated: Bool) {
        var pending = [root], result = [NSView]()
        while let node = pending.popLast() {
            if result.count == 512 { return (result, true) }
            result.append(node)
            pending.append(contentsOf: node.subviews.reversed())
        }
        return (result, false)
    }
    private func node(_ view: NSView, window: NSWindow) -> [String: Any] {
        var value: [String: Any] = [
            "class": NSStringFromClass(type(of: view)),
            "frame_window": windowRect(view.convert(view.bounds, to: nil), window),
            "hidden_or_hidden_ancestor": view.isHiddenOrHasHiddenAncestor,
            "alpha_value": view.alphaValue,
            "visible_rect_local": rect(view.visibleRect),
            "visible_rect_empty": view.visibleRect.isEmpty,
        ]
        if let button = view as? NSButton {
            value["button_title"] = button.title
            value["accessibility_label"] = button.accessibilityLabel() ?? ""
        }
        return value
    }
    private func snapshot(_ window: NSWindow, index: Int) -> [String: Any] {
        let root = window.contentView?.superview
        let tree = root.map { descendants($0) } ?? (nodes: [], truncated: false)
        let titleStrings = Set([configuration.title, "Toolbar Fixture", window.title])
        let titles = tree.nodes.compactMap { $0 as? NSTextField }
            .filter { titleStrings.contains($0.stringValue) }
            .map { field -> [String: Any] in
                var value = node(field, window: window)
                value["text"] = field.stringValue
                value["matches_selected_page_title"] = field.stringValue == configuration.title
                value["matches_logical_window_title"] = field.stringValue == window.title
                return value
            }
        let toolbarItems = (window.toolbar?.items ?? []).map { item -> [String: Any] in
            var value: [String: Any] = ["identifier": item.itemIdentifier.rawValue, "label": item.label]
            if let view = item.view {
                let children = descendants(view)
                value["view"] = node(view, window: window)
                value["descendants"] = children.nodes.dropFirst().map { node($0, window: window) }
                value["descendants_truncated"] = children.truncated
            } else {
                value["view"] = NSNull()
                value["descendants"] = []
                value["descendants_truncated"] = false
            }
            return value
        }
        let splits = tree.nodes.compactMap { $0 as? NSSplitView }.map { split -> [String: Any] in
            ["vertical": split.isVertical,
             "frame_window": windowRect(split.convert(split.bounds, to: nil), window),
             "arranged_subviews": split.arrangedSubviews.map { node($0, window: window) }]
        }
        var value: [String: Any] = [
            "index": index, "observed_uptime_seconds": ProcessInfo.processInfo.systemUptime,
            "window_number": window.windowNumber, "visible": window.isVisible,
            "key": window.isKeyWindow, "main": window.isMainWindow,
            "logical_window_title": window.title,
            "window_frame_screen_bottom_left": rect(window.frame),
            "content_rect_from_frame_screen_bottom_left": rect(window.contentRect(forFrameRect: window.frame)),
            "content_layout_rect_window_base": rect(window.contentLayoutRect),
            "toolbar_style_raw": window.toolbarStyle.rawValue,
            "title_visibility_raw": window.titleVisibility.rawValue,
            "toolbar_present": window.toolbar != nil,
            "toolbar_visible": window.toolbar.map { $0.isVisible as Any } ?? NSNull(),
            "activation_policy_raw": NSApp.activationPolicy().rawValue,
            "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,
            "backing_scale_factor": window.backingScaleFactor,
            "title_fields": titles, "title_field_matches_count": titles.count,
            "toolbar_items": toolbarItems, "split_views": splits,
            "window_view_tree_truncated": tree.truncated,
        ]
        if let content = window.contentView {
            value["content_view"] = node(content, window: window)
            let insets = content.safeAreaInsets
            value["content_safe_area_insets"] = ["top": insets.top, "left": insets.left, "bottom": insets.bottom, "right": insets.right]
        }
        return value
    }
    private func write(_ object: [String: Any], name: String) throws {
        guard let output = configuration.output else { throw CocoaError(.fileNoSuchFile) }
        let bytes = try JSONSerialization.data(withJSONObject: object, options: [.prettyPrinted, .sortedKeys])
        guard bytes.count <= 512 * 1024 else { throw CocoaError(.fileWriteOutOfSpace) }
        try bytes.write(to: output.appendingPathComponent(name), options: .atomic)
    }
    private func fail(_ message: String) {
        FileHandle.standardError.write(Data((message + "\n").utf8))
        try? write(["ready": false, "pid": getpid(), "mode": configuration.mode,
                    "error": message, "scope": "Capture preparation failed; process stays alive for external cleanup"], name: "ready.json")
    }
    func start() {
        guard !started else { return }
        started = true
        guard configuration.error == nil else { fail(configuration.error!); return }
        guard let output = configuration.output,
              !files.fileExists(atPath: output.appendingPathComponent("ready.json").path),
              !files.fileExists(atPath: output.appendingPathComponent("native.json").path) else {
            fail("Fresh native.json/ready.json paths required"); return
        }
        findWindow(attempt: 0)
    }
    private func findWindow(attempt: Int) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) { [self] in
            let windows = NSApp.windows.filter { $0.level == .normal && $0.contentView != nil && $0.frame.width > 500 && $0.frame.height > 300 }
            guard windows.count == 1, let window = windows.first else {
                if attempt < 9 { findWindow(attempt: attempt + 1) }
                else { fail("Expected exactly one actual Scene-created normal window") }
                return
            }
            observedWindow = window
            initialFrame = rect(window.frame)
            // Same one-shot outer normalization and activation for both Boolean values.
            window.setFrame(NSRect(origin: window.frame.origin, size: NSSize(width: 920, height: 668)), display: true)
            window.makeKeyAndOrderFront(nil)
            NSApp.activate(ignoringOtherApps: true)
            collect(index: 0)
        }
    }
    private func collect(index: Int) {
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.2) { [self] in
            guard let window = observedWindow else { fail("Observed Scene window disappeared"); return }
            samples.append(snapshot(window, index: index))
            do {
                try write(["schema": "bern_toolbar_shows_title_native_v1", "pid": getpid(),
                           "mode": configuration.mode, "shows_title_parameter": configuration.showsTitle,
                           "os": ProcessInfo.processInfo.operatingSystemVersionString,
                           "bundle_identifier": Bundle.main.bundleIdentifier ?? "",
                           "initial_window_frame_screen_bottom_left": initialFrame ?? [:],
                           "normalization": "one outer setFrame920x668, preserving initial origin; no content inset compensation",
                           "samples": samples, "sample_count": samples.count,
                           "scope": "Public native getters only; logical title and nonhidden field are not proof of visible glyph ink"], name: "native.json")
                if index < 2 { collect(index: index + 1); return }
                try write(["ready": true, "pid": getpid(), "mode": configuration.mode,
                           "windowNumber": window.windowNumber, "sample_count": samples.count,
                           "native_file": "native.json", "visible": window.isVisible,
                           "key": window.isKeyWindow, "main": window.isMainWindow,
                           "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,
                           "scope": "Three bounded native snapshots written; external capture and cleanup remain"], name: "ready.json")
            } catch { fail("Native evidence write failed: \(error)") }
        }
    }
}

@main
@MainActor
struct ToolbarShowsTitleApp: App {
    init() { _ = NSApplication.shared.setActivationPolicy(.regular) }
    var body: some Scene {
        Window("Toolbar Fixture", id: "toolbar-shows-title") { ProbeRoot() }
            .defaultSize(width: 920, height: 668)
            .windowToolbarStyle(.unifiedCompact(showsTitle: configuration.showsTitle))
    }
}
