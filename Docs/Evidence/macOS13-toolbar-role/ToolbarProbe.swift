import AppKit
import SwiftUI
import Foundation

struct Configuration {
    let key: String
    let outer: Bool
    let unified: Bool
    let picker: Bool
    let ordered: Bool
    init() {
        key = CommandLine.arguments.dropFirst().first ?? "automatic"
        outer = false
        unified = false
        picker = false
        ordered = false
    }
    var title: String { picker ? "Switches & Sliders" : "Buttons" }
}
let configuration = Configuration()
func trace(_ stage: String) {
    FileHandle.standardError.write(Data((stage + "\n").utf8))
}
var frontmostBefore: pid_t = 0
var samples = [[String: Any]]()

struct ProbeRoot: View {
    @State private var selected: String? = "Buttons"
    @State private var search = ""
    @State private var filter = "All"
    var body: some View {
        if configuration.key == "split-editor" { split.toolbarRole(.editor) }
        else { split }
    }
    private var split: some View {
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
            if configuration.key == "detail-editor" {
                page.navigationTitle(configuration.title).toolbar { items }.toolbarRole(.editor)
            } else { page.navigationTitle(configuration.title).toolbar { items } }
        }
    }
    private var page: some View {
        Form { Section("Button Styles") { Text("Independent native toolbar layout fixture") } }
            .formStyle(.grouped)
    }
    @ToolbarContentBuilder private var items: some ToolbarContent {
        ToolbarItemGroup(placement: .automatic) {
            if configuration.picker {
                Picker("Show", selection: $filter) {
                    Text("All").tag("All")
                    Text("Favorites").tag("Favorites")
                }.pickerStyle(.segmented)
            } else {
                Button {} label: { Label("Toolbar Button", systemImage: "plus") }
            }
        }
    }
}

func rectangle(_ rect: NSRect, window: NSWindow) -> [String: CGFloat] {
    ["x": rect.minX, "y_from_bottom": rect.minY, "y_from_top": window.frame.height - rect.maxY,
     "width": rect.width, "height": rect.height]
}
func allViews(_ view: NSView) -> [NSView] { [view] + view.subviews.flatMap(allViews) }
func snapshot(_ window: NSWindow) -> [String: Any] {
    let root = window.contentView?.superview
    let views = root.map(allViews) ?? []
    let text = views.compactMap { $0 as? NSTextField }.filter { $0.stringValue == configuration.title }.map { field -> [String: Any] in
        ["class": NSStringFromClass(type(of: field)), "text": field.stringValue,
         "frame_window": rectangle(field.convert(field.bounds, to: nil), window: window), "hidden": field.isHiddenOrHasHiddenAncestor]
    }
    let items = (window.toolbar?.items ?? []).map { item -> [String: Any] in
        var result: [String: Any] = ["identifier": item.itemIdentifier.rawValue, "label": item.label]
        if let view = item.view {
            result["view_class"] = NSStringFromClass(type(of: view))
            result["frame_window"] = rectangle(view.convert(view.bounds, to: nil), window: window)
            result["hidden"] = view.isHiddenOrHasHiddenAncestor
            result["descendants"] = allViews(view).dropFirst().map { child -> [String: Any] in
                var node: [String: Any] = ["class": NSStringFromClass(type(of: child)), "frame_window": rectangle(child.convert(child.bounds, to: nil), window: window)]
                if let button = child as? NSButton { node["title"] = button.title; node["accessibility_label"] = button.accessibilityLabel() ?? "" }
                return node
            }
        }
        return result
    }
    let splits = views.compactMap { $0 as? NSSplitView }.map { split -> [String: Any] in
        ["vertical": split.isVertical, "frame": rectangle(split.convert(split.bounds, to: nil), window: window),
         "arranged": split.arrangedSubviews.map { rectangle($0.convert($0.bounds, to: nil), window: window) }, "autosave": split.autosaveName ?? ""]
    }
    return ["visible": window.isVisible, "key": window.isKeyWindow, "title": window.title,
            "window_frame": NSStringFromRect(window.frame), "toolbar_style": window.toolbarStyle.rawValue,
            "toolbar_items": items, "title_fields": text, "split_views": splits,
            "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0]
}
final class Delegate: NSObject, NSApplicationDelegate {
    private var prepared = false
    func applicationWillFinishLaunching(_ notification: Notification) {
        trace("applicationWillFinishLaunching")
        _ = NSApplication.shared.setActivationPolicy(.accessory)
        NSWindow.allowsAutomaticWindowTabbing = false
    }
    func applicationDidFinishLaunching(_ notification: Notification) {
        trace("applicationDidFinishLaunching")
        collect(index: 0)
    }
    func applicationShouldTerminateAfterLastWindowClosed(_ sender: NSApplication) -> Bool { false }
    private func collect(index: Int) {
        DispatchQueue.main.asyncAfter(deadline: .now() + (index == 0 ? 0.15 : 0.4)) { [self] in
            guard let window = NSApp.windows.first(where: { $0.level == .normal && $0.frame.width > 500 && $0.frame.height > 300 }) else {
                if index < 5 { collect(index: index + 1); return }
                finish(error: "No Scene-created normal window"); return
            }
            if !prepared {
                window.isRestorable = false
                window.setFrame(NSRect(x: 50, y: 50, width: 920, height: 668), display: false)
                if configuration.ordered { window.orderBack(nil) } else { window.orderOut(nil) }
                _ = NSApplication.shared.setActivationPolicy(.prohibited)
                prepared = true
            }
            window.contentView?.layoutSubtreeIfNeeded()
            samples.append(snapshot(window))
            if samples.count < 3 { collect(index: index + 1) }
            else { window.orderOut(nil); finish(error: nil) }
        }
    }
    private func finish(error: String?) {
        let frontmostBeforeRestore = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        if frontmostBeforeRestore == getpid(), let previous = NSRunningApplication(processIdentifier: frontmostBefore) {
            _ = previous.activate(options: [])
            RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.1))
        }
        var result: [String: Any] = ["pid": getpid(), "mode": configuration.key, "bundle_identifier": Bundle.main.bundleIdentifier ?? "", "ordered_requested": configuration.ordered, "toolbar_role_placement": configuration.key,
                                    "os": ProcessInfo.processInfo.operatingSystemVersionString, "frontmost_pid_before": frontmostBefore,
                                    "frontmost_pid_before_restore": frontmostBeforeRestore,
                                    "frontmost_pid_after": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0, "samples": samples,
                                    "scope": "Real SwiftUI App.Scene Window. Accessory activation policy; no NSToolbar delegate/reordering, orderFront call, main-app actions or defaults edits. Window ordered out, unless explicitly requested orderBack. Restores original foreground app if Scene startup changed it."]
        if let error { result["error"] = error }
        if let data = try? JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys]) {
            FileHandle.standardOutput.write(data); FileHandle.standardOutput.write(Data([10]))
        }
        exit(error == nil ? 0 : 1)
    }
}
@main struct ToolbarProbeApp: App {
    @NSApplicationDelegateAdaptor(Delegate.self) private var delegate
    init() {
        trace("App.init")
        frontmostBefore = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        _ = NSApplication.shared.setActivationPolicy(.accessory)
    }
    var body: some Scene {
        trace("App.body")
        return scene
    }
    private var scene: some Scene {
        Window("Toolbar Fixture", id: configuration.key) { ProbeRoot() }
            .defaultSize(width: 920, height: 668)
#if UNIFIED
            .windowToolbarStyle(.unified(showsTitle: true))
#endif
    }
}
