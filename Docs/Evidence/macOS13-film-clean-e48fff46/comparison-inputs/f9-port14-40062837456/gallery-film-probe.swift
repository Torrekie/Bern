// External, bounded observer of an already-built Gallery. No app source injection.
import AppKit
import ApplicationServices
import CoreGraphics
import Darwin
import Foundation
import ImageIO

struct Failure: Error, CustomStringConvertible { let description: String }
let fm = FileManager.default
guard CommandLine.arguments.count == 4 else {
    fputs("usage: gallery-film-probe APP CLI OUTPUT\n", stderr); exit(2)
}
let app = URL(fileURLWithPath: CommandLine.arguments[1])
let cliURL = URL(fileURLWithPath: CommandLine.arguments[2])
let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
try fm.createDirectory(at: output, withIntermediateDirectories: true)
let deadline = ProcessInfo.processInfo.systemUptime + 120
let originalFront = NSWorkspace.shared.frontmostApplication
let trusted = AXIsProcessTrusted()
var environment = ProcessInfo.processInfo.environment
var commands = [[String: Any]](), cases = [[String: Any]]()
var ipcPaths = [String]()
var report: [String: Any] = [
    "source_sha": environment["BERN_SOURCE_SHA"] ?? "unknown",
    "harness_sha": environment["GITHUB_SHA"] ?? "unknown",
    "variant": environment["FILM_VARIANT"] ?? "unknown",
    "appearance_profile": "normal",
    "os": ProcessInfo.processInfo.operatingSystemVersionString,
    "accessibility_trusted": trusted, "screen_recording_preflight": CGPreflightScreenCaptureAccess(),
    "scope": "Light only; three fresh processes, exact app. AX frames are global screen points. No draft/target/nearest introspection; visible labels do not prove a binding write.",
    "sampling_scope": "First second after Film select CLI launch, including mounting latency; actual AX-walk timestamps, no assumed sampling frequency.",
    "system_preferences": ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
        "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
        "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
    "displays": NSScreen.screens.map { ["frame_points": NSStringFromRect($0.frame), "scale": $0.backingScaleFactor] },
]
func now() -> Double { ProcessInfo.processInfo.systemUptime }
func save() throws {
    report["commands"] = commands; report["cases"] = cases
    report["ipc_directories"] = ipcPaths
    try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        .write(to: output.appendingPathComponent("result.json"), options: .atomic)
}
func pause(_ duration: Double) throws {
    guard now() < deadline else { throw Failure(description: "Observer exceeded 120 seconds") }
    RunLoop.current.run(until: Date().addingTimeInterval(duration))
}
func handle(_ name: String) throws -> FileHandle {
    let url = output.appendingPathComponent(name)
    guard fm.createFile(atPath: url.path, contents: nil) else { throw Failure(description: "Cannot create log") }
    return try FileHandle(forWritingTo: url)
}
func cli(_ args: [String], _ session: String? = nil, allowFailure: Bool = false,
         observe: (() -> Void)? = nil) throws -> Any? {
    let stem = String(format: "%03d", commands.count + 1)
    let out = try handle(stem + "-stdout.json"), err = try handle(stem + "-stderr.txt")
    defer { out.closeFile(); err.closeFile() }
    let p = Process(); p.executableURL = cliURL
    p.arguments = (session.map { ["--session", $0] } ?? []) + args
    p.environment = environment; p.standardOutput = out; p.standardError = err
    let start = now(); try p.run()
    while p.isRunning || (observe != nil && now() - start < 1) {
        if now() - start >= 8 || now() >= deadline {
            if p.isRunning { kill(p.processIdentifier, SIGKILL) }
            throw Failure(description: "CLI exceeded its 8 second limit")
        }
        if now() - start < 1 { observe?() }
        try pause(0.03)
    }
    commands.append(["arguments": p.arguments ?? [], "start_uptime": start, "end_uptime": now(),
        "status": p.terminationStatus, "stdout": stem + "-stdout.json", "stderr": stem + "-stderr.txt"])
    guard p.terminationStatus == 0 else {
        if allowFailure { return nil }; throw Failure(description: "CLI failed: \(args)")
    }
    let data = try Data(contentsOf: output.appendingPathComponent(stem + "-stdout.json"))
    return data.isEmpty ? nil : try JSONSerialization.jsonObject(with: data, options: .fragmentsAllowed)
}
func target(_ session: String, suffix: String) throws -> String {
    let rows = try cli(["ui", "inspect"], session) as? [[String: Any]] ?? []
    let matches = rows.filter { ($0["target"] as? String)?.hasSuffix(suffix) == true && $0["enabled"] as? Bool == true }
    guard matches.count == 1, let value = matches[0]["target"] as? String else {
        throw Failure(description: "Expected one enabled control ending in \(suffix)")
    }
    return value
}
func window(_ pid: pid_t) throws -> [String: Any] {
    let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    let matches = rows.filter {
        ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid &&
        ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 &&
        (($0[kCGWindowBounds as String] as? [String: NSNumber])?["Width"]?.doubleValue ?? 0) > 120
    }
    guard matches.count == 1 else { throw Failure(description: "Expected exactly one visible app window") }
    return matches[0]
}
func image(_ pid: pid_t) throws -> CGImage {
    let info = try window(pid)
    guard let id = info[kCGWindowNumber as String] as? NSNumber,
          let img = CGWindowListCreateImage(.null, .optionIncludingWindow, id.uint32Value, [.boundsIgnoreFraming, .bestResolution]) else {
        throw Failure(description: "WindowServer capture unavailable")
    }
    return img
}
func stable(_ pid: pid_t, name: String) throws -> [String: Any] {
    var previous: Data?, same = 0, count = 0
    let start = now()
    while now() - start < 8 {
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
            throw Failure(description: "Gallery is not active at capture time")
        }
        let img = try image(pid)
        guard let bytes = img.dataProvider?.data else { throw Failure(description: "Missing raw capture buffer") }
        let data = bytes as Data; same = data == previous ? same + 1 : 0; previous = data; count += 1
        if same >= 4 {
            let info = try window(pid), bounds = info[kCGWindowBounds as String] as? [String: NSNumber] ?? [:]
            guard bounds["Width"]?.doubleValue == 920, bounds["Height"]?.doubleValue == 668 else {
                throw Failure(description: "Outer window is not 920 x 668 points")
            }
            let url = output.appendingPathComponent(name + ".png")
            guard let dest = CGImageDestinationCreateWithURL(url as CFURL, "public.png" as CFString, 1, nil) else {
                throw Failure(description: "Cannot create PNG")
            }
            CGImageDestinationAddImage(dest, img, nil)
            guard CGImageDestinationFinalize(dest) else { throw Failure(description: "Cannot save PNG") }
            return ["png": url.lastPathComponent, "elapsed_seconds": now() - start, "samples": count,
                "equal_comparisons": same, "bounds_points": bounds, "pixels": [img.width, img.height]]
        }
        try pause(0.1)
    }
    throw Failure(description: "Window did not become pixel-stable within 8 seconds")
}
func attribute(_ element: AXUIElement, _ key: CFString) -> CFTypeRef? {
    var value: CFTypeRef?; return AXUIElementCopyAttributeValue(element, key, &value) == .success ? value : nil
}
func axSample(_ root: AXUIElement) -> [String: Any] {
    let start = now()
    guard trusted else { return ["start_uptime": start, "missing": "AXIsProcessTrusted=false; no permission request"] }
    var queue = [root], index = 0, rows = [[String: Any]]()
    let names: Set<String> = ["Gingham", "Tartan", "Madras", "Glen", "Houndstooth", "Windowpane"]
    while index < queue.count && index < 512 && now() - start < 0.12 {
        let e = queue[index]; index += 1
        AXUIElementSetMessagingTimeout(e, 0.04)
        let role = attribute(e, kAXRoleAttribute as CFString) as? String ?? "unknown"
        var text = "", textAttribute = "missing"
        for key in [kAXValueAttribute, kAXTitleAttribute, kAXDescriptionAttribute] {
            if let value = attribute(e, key as CFString) as? String, !value.isEmpty {
                text = value; textAttribute = key; break
            }
        }
        if role == (kAXScrollAreaRole as String) || role == (kAXSplitGroupRole as String) || names.contains(text) {
            var row: [String: Any] = ["role": role, "text": text, "text_attribute": textAttribute]
            var p = CGPoint.zero, s = CGSize.zero
            if let value = attribute(e, kAXPositionAttribute as CFString), CFGetTypeID(value) == AXValueGetTypeID(),
               AXValueGetValue(value as! AXValue, .cgPoint, &p),
               let size = attribute(e, kAXSizeAttribute as CFString), CFGetTypeID(size) == AXValueGetTypeID(),
               AXValueGetValue(size as! AXValue, .cgSize, &s) {
                row["frame"] = ["x": p.x, "y": p.y, "width": s.width, "height": s.height]
            } else { row["frame_missing"] = true }
            rows.append(row)
        }
        queue.append(contentsOf: attribute(e, kAXChildrenAttribute as CFString) as? [AXUIElement] ?? [])
    }
    return ["start_uptime": start, "end_uptime": now(), "elements": rows, "visited": index,
        "truncated": index < queue.count, "matching_elements_missing": rows.isEmpty,
        "scroll_area_count": rows.filter { $0["role"] as? String == kAXScrollAreaRole as String }.count,
        "pattern_label_count": rows.filter { names.contains($0["text"] as? String ?? "") }.count]
}
func stop(_ p: Process) {
    guard p.isRunning else { return }
    NSRunningApplication(processIdentifier: p.processIdentifier)?.terminate()
    let end = now() + 2
    while p.isRunning && now() < end { RunLoop.current.run(until: Date().addingTimeInterval(0.03)) }
    if p.isRunning { kill(p.processIdentifier, SIGKILL) }
}
do {
    guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 14, CGPreflightScreenCaptureAccess() else {
        throw Failure(description: "Requires macOS14 and existing Screen Recording access; no TCC changes")
    }
    guard !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
          !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
          !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast else {
        throw Failure(description: "Effective accessibility preferences do not match normal profile; observer does not change preferences")
    }
    defer {
        if NSWorkspace.shared.frontmostApplication?.processIdentifier != originalFront?.processIdentifier {
            originalFront?.activate(options: [])
        }
    }
    for scenario in ["immediate", "wait", "direct"] {
        let ipc = URL(fileURLWithPath: "/tmp/bern-film-\(getpid())-\(scenario)", isDirectory: true)
        // The transport appends /bern-<16hex>/<14hex>.sock (42 bytes), capped at 100.
        guard ipc.path.utf8.count + 42 <= 100 else { throw Failure(description: "IPC socket path exceeds transport limit") }
        try fm.createDirectory(at: ipc, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        ipcPaths.append(ipc.path); try save()
        environment["BERN_IPC_DIR"] = ipc.path; environment["BERN_APPEARANCE"] = "light"
        environment.removeValue(forKey: "BERN_SNAPSHOT_DIR")
        let p = Process(); p.executableURL = app.appendingPathComponent("Contents/MacOS/Gallery")
        p.arguments = ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]; p.environment = environment
        let log = try handle(scenario + "-application.log"); p.standardOutput = log; p.standardError = log
        try p.run()
        defer { stop(p); log.closeFile(); try? fm.removeItem(at: ipc) }
        var session: String?
        let ready = now() + 15
        while session == nil && p.isRunning && now() < ready {
            let entries = try cli(["sessions"], allowFailure: true) as? [[String: Any]] ?? []
            if entries.count == 1 { session = entries[0]["session_id"] as? String }
            if session == nil { try pause(0.1) }
        }
        guard let id = session else { throw Failure(description: "No unique UI session") }
        NSRunningApplication(processIdentifier: p.processIdentifier)?.activate(options: [.activateAllWindows])
        _ = try cli(["ui", "set-language", "--language", "en"], id)
        _ = try cli(["ui", "activate", "--target", target(id, suffix: ".light")], id)
        let state = try cli(["state"]) as? [String: Any] ?? [:]
        guard (state["values"] as? [String: Any])?["appearance"] as? String == "Light" else {
            throw Failure(description: "Gallery did not commit light appearance")
        }
        let windows = try cli(["window", "list"], id) as? [[String: Any]] ?? []
        guard windows.count == 1, let win = windows[0]["window"] as? String else { throw Failure(description: "No unique main window") }
        _ = try cli(["window", "resize", "--window", win, "--width", "920", "--height", "668"], id)
        let pages = try target(id, suffix: ".pages"), details = try target(id, suffix: ".show_details")
        let root = AXUIElementCreateApplication(p.processIdentifier); AXUIElementSetMessagingTimeout(root, 0.04)
        var entry: [String: Any] = ["scenario": scenario, "pid": p.processIdentifier, "session": id, "ipc_dir": ipc.path,
            "patterns": try stable(p.processIdentifier, name: scenario + "-patterns")]
        if scenario != "direct" {
            _ = try cli(["ui", "set-bool", "--target", details, "--value", "true"], id)
            entry["inspector"] = try stable(p.processIdentifier, name: scenario + "-inspector")
            entry["inspector_ax"] = axSample(root)
            _ = try cli(["ui", "set-bool", "--target", details, "--value", "false"], id)
            entry["close_return_uptime"] = now()
            if scenario == "wait" { entry["closed"] = try stable(p.processIdentifier, name: scenario + "-closed") }
        }
        var samples = [[String: Any]](); entry["select_start_uptime"] = now()
        _ = try cli(["ui", "select", "--target", pages, "--option", "Film"], id, observe: { samples.append(axSample(root)) })
        entry["first_second_ax"] = samples
        cases.append(entry); try save()
        entry["film"] = try stable(p.processIdentifier, name: scenario + "-film")
        entry["settled_ax"] = axSample(root)
        entry["controls"] = try cli(["ui", "inspect"], id) ?? NSNull()
        cases[cases.count - 1] = entry; try save()
    }
    report["success"] = true; try save()
} catch {
    report["success"] = false; report["failure"] = String(describing: error); try? save()
    fputs("Film probe failed: \(error)\n", stderr); exit(1)
}
