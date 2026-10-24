// External, bounded observer of an already-built, isolated Showcase.
// No application injection, native logger, preferences or TCC mutation.
import AppKit
import ApplicationServices
import CoreGraphics
import Darwin
import Foundation
import ImageIO

struct Failure: Error, CustomStringConvertible { let description: String }
let fm = FileManager.default
guard CommandLine.arguments.count == 4 else {
    fputs("usage: showcase-toolbar-probe APP CLI OUTPUT\n", stderr); exit(2)
}
let app = URL(fileURLWithPath: CommandLine.arguments[1]).standardizedFileURL
let cliURL = URL(fileURLWithPath: CommandLine.arguments[2]).standardizedFileURL
let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true).standardizedFileURL
let started = ProcessInfo.processInfo.systemUptime
let deadline = started + 120
let workDeadline = deadline - 5
let originalFront = NSWorkspace.shared.frontmostApplication
let trusted = AXIsProcessTrusted()
var environment = ProcessInfo.processInfo.environment
var commands = [[String: Any]](), stages = [[String: Any]]()
var report: [String: Any] = [
    "source_sha": environment["BERN_SOURCE_SHA"] ?? "unknown",
    "variant": environment["BERN_TOOLBAR_VARIANT"] ?? "unknown",
    "os": ProcessInfo.processInfo.operatingSystemVersionString,
    "expected_os_major": 13, "started_uptime": started,
    "original_front": ["captured_uptime": started,
        "pid": originalFront.map { $0.processIdentifier as Any } ?? NSNull(),
        "bundle": originalFront?.bundleIdentifier as Any? ?? NSNull()],
    "work_deadline_uptime": workDeadline, "deadline_uptime": deadline,
    "app_path": app.path, "cli_path": cliURL.path,
    "accessibility_trusted": trusted,
    "screen_recording_preflight": CGPreflightScreenCaptureAccess(),
    "sequence": ["Buttons", "Text", "Controls", "Buttons"],
    "scope": "Active Showcase; light requested via env, effective appearance not asserted. Intended for same-host A/B geometry only. Programmatic bound sidebar selections, not physical keyboard/mouse/IME. AX frames and focus attributes are external accessibility evidence, not NSView toolbar item frames or a native firstResponder object.",
    "displays": NSScreen.screens.map { ["frame_points": NSStringFromRect($0.frame), "scale": $0.backingScaleFactor] },
    "deadline_scope": "Cooperative 115-second work limit, final 5 seconds reserved for own-process stop and immediate original-front restoration. Synchronous OS calls cannot be preempted by this loop; caller must impose the 120-second process boundary and own-path cleanup fallback.",
]
var appProcess: Process?, applicationLog: FileHandle?, ipc: URL?
var outputReady = false, acquired = false
func now() -> Double { ProcessInfo.processInfo.systemUptime }
func normalProfile() -> [String: Bool] {
    ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
     "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
     "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
}
func frontState(_ ownPID: pid_t) -> [String: Any] {
    let front = NSWorkspace.shared.frontmostApplication
    return ["uptime": now(), "own_pid": ownPID,
            "front_pid": front.map { $0.processIdentifier as Any } ?? NSNull(),
            "front_bundle": front?.bundleIdentifier as Any? ?? NSNull()]
}
func save() throws {
    guard outputReady else { return }
    report["commands"] = commands; report["stages"] = stages
    try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
        .write(to: output.appendingPathComponent("result.json"), options: .atomic)
}
func pause(_ duration: Double, until limit: Double? = nil) throws {
    let end = min(limit ?? workDeadline, workDeadline)
    guard now() < end else { throw Failure(description: "Observer reached its bounded work deadline") }
    RunLoop.current.run(until: Date().addingTimeInterval(min(duration, max(0, end - now()))))
}
func handle(_ name: String) throws -> FileHandle {
    let url = output.appendingPathComponent(name)
    guard !fm.fileExists(atPath: url.path), fm.createFile(atPath: url.path, contents: nil) else {
        throw Failure(description: "Cannot create fresh log \(name)")
    }
    return try FileHandle(forWritingTo: url)
}
func cli(_ args: [String], _ session: String? = nil, allowFailure: Bool = false,
         until cutoff: Double? = nil) throws -> Any? {
    guard now() < workDeadline else { throw Failure(description: "No time remains for CLI") }
    let stem = String(format: "%03d", commands.count + 1)
    let out = try handle(stem + "-stdout.json"), err = try handle(stem + "-stderr.txt")
    defer { out.closeFile(); err.closeFile() }
    let p = Process(); p.executableURL = cliURL
    p.arguments = (session.map { ["--session", $0] } ?? []) + args
    p.environment = environment; p.standardOutput = out; p.standardError = err
    let start = now(), callDeadline = min(workDeadline, min(cutoff ?? workDeadline, now() + 8))
    try p.run()
    while p.isRunning {
        if now() >= callDeadline {
            kill(p.processIdentifier, SIGKILL); p.waitUntilExit()
            commands.append(["arguments": p.arguments ?? [], "start_uptime": start, "end_uptime": now(),
                "deadline_uptime": callDeadline, "timeout": true,
                "stdout": stem + "-stdout.json", "stderr": stem + "-stderr.txt"])
            try save(); throw Failure(description: "CLI exceeded its bounded deadline")
        }
        RunLoop.current.run(until: Date().addingTimeInterval(min(0.03, max(0, callDeadline - now()))))
    }
    commands.append(["arguments": p.arguments ?? [], "start_uptime": start, "end_uptime": now(),
        "deadline_uptime": callDeadline, "status": p.terminationStatus,
        "stdout": stem + "-stdout.json", "stderr": stem + "-stderr.txt"])
    try save()
    guard p.terminationStatus == 0 else {
        if allowFailure { return nil }; throw Failure(description: "CLI failed: \(args)")
    }
    let data = try Data(contentsOf: output.appendingPathComponent(stem + "-stdout.json"))
    return data.isEmpty ? nil : try JSONSerialization.jsonObject(with: data, options: .fragmentsAllowed)
}
func ownedWindows(_ pid: pid_t, onScreenOnly: Bool = false) -> [[String: Any]] {
    let options: CGWindowListOption = onScreenOnly ? [.optionOnScreenOnly, .excludeDesktopElements] : [.optionAll, .excludeDesktopElements]
    let rows = CGWindowListCopyWindowInfo(options, kCGNullWindowID) as? [[String: Any]] ?? []
    return rows.filter { ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid }
}
func window(_ pid: pid_t) throws -> [String: Any] {
    let matches = ownedWindows(pid, onScreenOnly: true).filter {
        ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 &&
        (($0[kCGWindowBounds as String] as? [String: NSNumber])?["Width"]?.doubleValue ?? 0) > 120
    }
    guard matches.count == 1 else { throw Failure(description: "Expected exactly one visible own normal window") }
    return matches[0]
}
func geometry(_ info: [String: Any], pid: pid_t) throws -> [Double] {
    let bounds = info[kCGWindowBounds as String] as? [String: NSNumber] ?? [:]
    guard (info[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid,
          (info[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true,
          let id = info[kCGWindowNumber as String] as? NSNumber,
          let alpha = info[kCGWindowAlpha as String] as? NSNumber, alpha.doubleValue >= 0.99,
          let x = bounds["X"], let y = bounds["Y"], let w = bounds["Width"], let h = bounds["Height"] else {
        throw Failure(description: "Incomplete, transparent or foreign own-window sample")
    }
    return [id.doubleValue, Double(pid), x.doubleValue, y.doubleValue, w.doubleValue, h.doubleValue, alpha.doubleValue]
}
func stable(_ pid: pid_t, name: String) throws -> [String: Any] {
    var previous: Data?, previousGeometry: [Double]?, previousMetadata: [Int]?, previousColorSpace: String?
    var same = 0, count = 0, samples = [[String: Any]]()
    let start = now(), cutoff = min(workDeadline, now() + 8)
    report["capture_in_progress"] = ["name": name, "start_uptime": start, "deadline_uptime": cutoff, "samples": samples]
    try save()
    while now() < cutoff {
        let before = try window(pid), beforeGeometry = try geometry(before, pid: pid)
        let frontBefore = frontState(pid)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid else {
            report["capture_focus_failure"] = ["capture": name, "actual": frontBefore]
            throw Failure(description: "Showcase is not active at capture time")
        }
        let id = (before[kCGWindowNumber as String] as! NSNumber).uint32Value
        guard let img = CGWindowListCreateImage(.null, .optionIncludingWindow, id, [.boundsIgnoreFraming, .bestResolution]),
              let bytes = img.dataProvider?.data else { throw Failure(description: "Own WindowServer raw buffer unavailable") }
        let after = try window(pid), afterGeometry = try geometry(after, pid: pid), frontAfter = frontState(pid)
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == pid,
              afterGeometry[0] == beforeGeometry[0] else { throw Failure(description: "Own active window identity changed during capture") }
        let data = bytes as Data, metadata = [img.width, img.height, img.bytesPerRow, img.bitsPerPixel, img.bitsPerComponent]
        let colorSpace = img.colorSpace?.name.map { $0 as String } ?? "unnamed"
        let geometryEqual = beforeGeometry == afterGeometry
        same = geometryEqual && data == previous && afterGeometry == previousGeometry && metadata == previousMetadata && colorSpace == previousColorSpace ? same + 1 : 0
        previous = data; previousGeometry = afterGeometry; previousMetadata = metadata; previousColorSpace = colorSpace; count += 1
        samples.append(["sample": count, "uptime": now(), "own_window_before": before, "own_window_after": after,
            "front_before": frontBefore, "front_after": frontAfter, "raw_buffer_bytes": data.count,
            "image_metadata": metadata, "color_space_name": colorSpace, "geometry_equal_during_capture": geometryEqual,
            "consecutive_equal_comparisons": same])
        report["capture_in_progress"] = ["name": name, "start_uptime": start, "deadline_uptime": cutoff, "samples": samples]
        if same >= 4 {
            guard afterGeometry[4] == 920, afterGeometry[5] == 668 else {
                throw Failure(description: "Stable outer window is not 920 x 668 points")
            }
            let url = output.appendingPathComponent(name + ".png")
            guard let dest = CGImageDestinationCreateWithURL(url as CFURL, "public.png" as CFString, 1, nil) else {
                throw Failure(description: "Cannot create PNG")
            }
            CGImageDestinationAddImage(dest, img, nil)
            guard CGImageDestinationFinalize(dest), now() < cutoff else {
                throw Failure(description: "PNG failed or capture exceeded its 8-second deadline")
            }
            let result: [String: Any] = ["png": url.lastPathComponent, "start_uptime": start, "end_uptime": now(),
                "deadline_uptime": cutoff, "samples": samples, "sample_count": count, "equal_comparisons": same,
                "own_window": after, "pixels": [img.width, img.height], "color_space_name": colorSpace]
            report.removeValue(forKey: "capture_in_progress")
            return result
        }
        try pause(0.1, until: cutoff)
    }
    throw Failure(description: "Own window did not become pixel-stable within 8 seconds")
}
// Adapted from the Film probe's bounded AX breadth-first walk. Unlike that
// probe, retain every visited node and parent/child index; no role/name filter.
func axSample(_ root: AXUIElement, timeBudget: Double = 2) -> [String: Any] {
    let start = now(), cutoff = min(workDeadline, now() + timeBudget)
    var exhausted = false, queryFailed = false, structuralQueryFailed = false
    func read(_ e: AXUIElement, _ key: String) -> (CFTypeRef?, AXError) {
        guard now() < cutoff else { exhausted = true; return (nil, .cannotComplete) }
        AXUIElementSetMessagingTimeout(e, Float(min(0.04, max(0.001, cutoff - now()))))
        var value: CFTypeRef?
        let error = AXUIElementCopyAttributeValue(e, key as CFString, &value)
        if error != .success && error != .attributeUnsupported && error != .noValue { queryFailed = true }
        return (value, error)
    }
    func descriptor(_ e: AXUIElement) -> [String: Any] {
        var row = [String: Any](), errors = [String: Int32]()
        var position: CFTypeRef?, size: CFTypeRef?
        for name in ["AXRole", "AXSubrole", "AXTitle", "AXDescription", "AXValue", "AXHelp", "AXIdentifier", "AXEnabled", "AXFocused", "AXSelected", "AXPosition", "AXSize"] {
            let (value, error) = read(e, name)
            if error != .success { errors[name] = error.rawValue }
            if name == "AXPosition" { position = value }
            else if name == "AXSize" { size = value }
            else if let value {
                if let text = value as? String { row[name] = text }
                else if let number = value as? NSNumber { row[name] = number }
                else { row[name] = ["unserialized_cf_type_id": CFGetTypeID(value)] }
            }
        }
        var p = CGPoint.zero, s = CGSize.zero
        if let position, CFGetTypeID(position) == AXValueGetTypeID(),
           AXValueGetValue(position as! AXValue, .cgPoint, &p),
           let size, CFGetTypeID(size) == AXValueGetTypeID(), AXValueGetValue(size as! AXValue, .cgSize, &s) {
            row["frame_screen_points"] = ["x": p.x, "y": p.y, "width": s.width, "height": s.height]
        }
        row["attribute_errors"] = errors
        return row
    }
    var focus = [String: Any]()
    for name in ["AXFocusedUIElement", "AXFocusedWindow", "AXMainWindow"] {
        let (value, error) = read(root, name)
        if let value, CFGetTypeID(value) == AXUIElementGetTypeID() { focus[name] = descriptor(value as! AXUIElement) }
        else { focus[name] = ["attribute_error": error.rawValue] }
    }
    var queue = [root], parents: [Int?] = [nil], index = 0, rows = [[String: Any]]()
    while index < queue.count && index < 512 && now() < cutoff && !exhausted {
        let e = queue[index], nodeIndex = index; index += 1
        var row = descriptor(e)
        if row["AXRole"] as? String == nil { structuralQueryFailed = true }
        row["node_index"] = nodeIndex; row["parent_index"] = parents[nodeIndex].map { $0 as Any } ?? NSNull()
        let (value, error) = read(e, "AXChildren")
        if error != .success && error != .attributeUnsupported && error != .noValue { structuralQueryFailed = true }
        var childIndices = [Int]()
        for child in value as? [AXUIElement] ?? [] {
            if let existing = queue.firstIndex(where: { CFEqual($0, child) }) { childIndices.append(existing) }
            else { childIndices.append(queue.count); queue.append(child); parents.append(nodeIndex) }
        }
        row["child_indices"] = childIndices; row["children_attribute_error"] = error.rawValue
        rows.append(row)
    }
    let truncated = index < queue.count || exhausted || now() >= cutoff
    return ["start_uptime": start, "end_uptime": now(), "deadline_uptime": cutoff, "time_budget_seconds": timeBudget,
            "elements": rows, "visited": index, "discovered": queue.count, "node_cap": 512,
            "truncated": truncated, "query_failed": queryFailed, "complete": !truncated && !queryFailed,
            "structural_query_failed": structuralQueryFailed, "tree_complete": !truncated && !structuralQueryFailed,
            "focus_attributes": focus,
            "scope": "All discovered AXChildren nodes and readable AXRole define tree_complete; optional attribute errors remain explicit and keep complete false. AX focused UIElement is not a native firstResponder object."]
}
do {
    guard !fm.fileExists(atPath: output.path) else { throw Failure(description: "Output must be a fresh nonexistent directory") }
    try fm.createDirectory(at: output, withIntermediateDirectories: true); outputReady = true
    report["front_at_preflight_end"] = frontState(0); report["normal_profile_start"] = normalProfile(); try save()
    guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 13, trusted, CGPreflightScreenCaptureAccess(),
          normalProfile().values.allSatisfy({ !$0 }), originalFront != nil else {
        throw Failure(description: "Requires macOS13, existing AX/Screen access, normal accessibility profile and an immediate original front app; no permission or preference changes")
    }
    guard let bundle = Bundle(url: app), let identifier = bundle.bundleIdentifier,
          identifier.hasPrefix("dev.bern.toolbar13."), bundle.object(forInfoDictionaryKey: "CFBundleExecutable") as? String == "Showcase",
          !NSWorkspace.shared.runningApplications.contains(where: { $0.bundleIdentifier == identifier }) else {
        throw Failure(description: "Requires an isolated, nonrunning Showcase identity with owned prefix dev.bern.toolbar13.")
    }
    report["bundle_identifier"] = identifier
    let ipcURL = URL(fileURLWithPath: "/tmp/bern-toolbar-\(getpid())-\(UUID().uuidString.prefix(8))", isDirectory: true)
    guard ipcURL.path.utf8.count + 42 <= 100, !fm.fileExists(atPath: ipcURL.path) else {
        throw Failure(description: "IPC path is not fresh or exceeds transport limit")
    }
    try fm.createDirectory(at: ipcURL, withIntermediateDirectories: false, attributes: [.posixPermissions: 0o700]); ipc = ipcURL
    environment["BERN_IPC_DIR"] = ipcURL.path; environment["BERN_APPEARANCE"] = "light"
    let removedKeys = ["BERN_SNAPSHOT_DIR", "BERN_SCROLL_TRACE_DIR", "BERN_FILM_SCENARIO", "BERN_FILM_FOLLOWUP", "BERN_FILM_OBSERVATION", "BERN_MOTION", "BERN_RENDER", "BERN_DEV_WINDOW_SIGNALS", "DYLD_INSERT_LIBRARIES"]
    for key in removedKeys { environment.removeValue(forKey: key) }
    report["app_environment_overrides"] = ["BERN_APPEARANCE": "light", "removed_keys": removedKeys]
    report["ipc_dir"] = ipcURL.path
    let p = Process(); p.executableURL = app.appendingPathComponent("Contents/MacOS/Showcase")
    p.arguments = ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]; p.environment = environment
    let log = try handle("application.log"); applicationLog = log; p.standardOutput = log; p.standardError = log
    let launchStart = now(); report["app_launch_start_uptime"] = launchStart
    try p.run(); appProcess = p
    report["pid"] = p.processIdentifier; try save()
    let ready = min(workDeadline, launchStart + 15)
    var session: String?
    while session == nil && p.isRunning && now() < ready {
        let entries = try cli(["sessions"], allowFailure: true, until: ready) as? [[String: Any]] ?? []
        if entries.count == 1 { session = entries[0]["session_id"] as? String }
        if session == nil { try pause(0.1, until: ready) }
    }
    guard let id = session else { throw Failure(description: "No unique own transport session") }
    report["session"] = id
    var startupSamples = [[String: Any]](), startupReady = false
    while p.isRunning && now() < ready {
        let listed = try cli(["window", "list"], id, allowFailure: true, until: ready) as? [[String: Any]] ?? []
        let native = try? window(p.processIdentifier)
        let alpha = (native?[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0
        startupSamples.append(["uptime": now(), "windows": listed,
            "all_own_cg_windows": ownedWindows(p.processIdentifier),
            "own_visible_normal_window": native as Any? ?? NSNull(), "own_visible_window_alpha": alpha,
            "front": frontState(p.processIdentifier)])
        report["startup_readiness"] = ["deadline_uptime": ready, "samples": startupSamples]; try save()
        if now() < ready, listed.contains(where: { $0["kind"] as? String == "main" }), native != nil, alpha >= 0.99 {
            startupReady = true; break
        }
        try pause(0.08, until: ready)
    }
    guard startupReady else { throw Failure(description: "Main registry and visible own window did not become ready inside the original 15-second deadline") }
    let beforeActivation = frontState(p.processIdentifier)
    let accepted = NSRunningApplication(processIdentifier: p.processIdentifier)?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps]) ?? false
    let activationDeadline = min(workDeadline, now() + 2)
    var activationSamples = [frontState(p.processIdentifier)]
    while NSWorkspace.shared.frontmostApplication?.processIdentifier != p.processIdentifier, now() < activationDeadline {
        try pause(0.05, until: activationDeadline); activationSamples.append(frontState(p.processIdentifier))
    }
    report["activation"] = ["before": beforeActivation, "accepted": accepted, "samples": activationSamples,
        "options": ["activateAllWindows", "activateIgnoringOtherApps"], "after": frontState(p.processIdentifier)]; try save()
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier else {
        throw Failure(description: "Own Showcase activation did not succeed")
    }
    _ = try cli(["ui", "set-language", "--language", "en"], id)
    let windows = try cli(["window", "list"], id) as? [[String: Any]] ?? []
    guard windows.count == 1, windows[0]["kind"] as? String == "main", let win = windows[0]["window"] as? String else {
        throw Failure(description: "No unique own registered main window")
    }
    report["resize_before"] = ["uptime": now(), "windows": windows, "own_window": try window(p.processIdentifier)]
    _ = try cli(["window", "resize", "--window", win, "--width", "920", "--height", "668"], id)
    report["resize_after_cli_return"] = ["uptime": now(), "own_window": try window(p.processIdentifier)]
    let initialControls = try cli(["ui", "inspect"], id) as? [[String: Any]] ?? []
    report["initial_controls"] = initialControls
    let matches = initialControls.filter { ($0["target"] as? String)?.hasSuffix(".pages") == true && $0["enabled"] as? Bool == true }
    guard matches.count == 1, let pages = matches[0]["target"] as? String else { throw Failure(description: "No unique enabled sidebar pages target") }
    let root = AXUIElementCreateApplication(p.processIdentifier); AXUIElementSetMessagingTimeout(root, 0.04)
    for (index, option) in ["Buttons", "Text", "Controls", "Buttons"].enumerated() {
        var stage: [String: Any] = ["index": index, "option": option, "pid": p.processIdentifier, "session": id,
                                  "select_start_uptime": now(), "front_before": frontState(p.processIdentifier)]
        stages.append(stage); try save()
        _ = try cli(["ui", "select", "--target", pages, "--option", option], id)
        stage["select_return_uptime"] = now(); stages[index] = stage; try save()
        stage["capture"] = try stable(p.processIdentifier, name: String(format: "%02d-", index) + option.lowercased())
        stages[index] = stage; try save()
        let ax = axSample(root, timeBudget: 2); stage["ax"] = ax; stages[index] = stage; try save()
        guard ax["tree_complete"] as? Bool == true else { throw Failure(description: "Final AXChildren/AXRole traversal was incomplete; partial traversal retained") }
        let nodes = ax["elements"] as? [[String: Any]] ?? []
        let mainWindows = nodes.filter { $0["AXRole"] as? String == "AXWindow" && $0["AXIdentifier"] as? String == "main" }
        let toolbars = nodes.filter { $0["AXRole"] as? String == "AXToolbar" }
        let toggles = nodes.filter { $0["AXRole"] as? String == "AXButton" && $0["AXDescription"] as? String == "Toggle Sidebar" }
        func positiveFrame(_ node: [String: Any]) -> Bool {
            guard let f = node["frame_screen_points"] as? [String: CGFloat],
                  ["x", "y", "width", "height"].allSatisfy({ f[$0]?.isFinite == true }),
                  let width = f["width"], let height = f["height"] else { return false }
            return width > 0 && height > 0
        }
        stage["required_geometry"] = ["main_windows": mainWindows, "toolbars": toolbars, "sidebar_toggles": toggles]
        stages[index] = stage; try save()
        let expectedTitle = option == "Controls" ? "Switches & Sliders" : option
        stage["expected_window_title"] = expectedTitle; stages[index] = stage; try save()
        guard mainWindows.count == 1, mainWindows[0]["AXTitle"] as? String == expectedTitle,
              toolbars.count == 1, !toggles.isEmpty,
              (mainWindows + toolbars + toggles).allSatisfy(positiveFrame) else {
            throw Failure(description: "Required main title, toolbar or sidebar-toggle geometry is missing; optional errors retained")
        }
        let controls = try cli(["ui", "inspect"], id) as? [[String: Any]] ?? []
        stage["controls"] = controls; stage["front_after"] = frontState(p.processIdentifier)
        stage["normal_profile"] = normalProfile(); stages[index] = stage; try save()
        guard controls.contains(where: { $0["target"] as? String == pages && $0["value"] as? String == option }),
              normalProfile().values.allSatisfy({ !$0 }), NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier else {
            throw Failure(description: "Sidebar selection, active own front or normal profile changed")
        }
    }
    acquired = true
} catch { report["error"] = String(describing: error) }

// Stop only the Process created here. Do not steal focus back if the user
// has already moved to a different foreground application.
var cleanupOK = true
if let p = appProcess {
    let ownWasFront = NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier
    report["cleanup_front_before_stop"] = frontState(p.processIdentifier)
    if p.isRunning {
        NSRunningApplication(processIdentifier: p.processIdentifier)?.terminate()
        let stopDeadline = min(deadline - 2, now() + 2)
        while p.isRunning && now() < stopDeadline { RunLoop.current.run(until: Date().addingTimeInterval(0.03)) }
        if p.isRunning { kill(p.processIdentifier, SIGKILL) }
        let exitDeadline = min(deadline - 2, now() + 0.5)
        while p.isRunning && now() < exitDeadline { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
    }
    report["own_process_running_after_stop"] = p.isRunning
    if p.isRunning { cleanupOK = false }
    if ownWasFront, let originalFront, !originalFront.isTerminated {
        let needsRestore = NSWorkspace.shared.frontmostApplication?.processIdentifier != originalFront.processIdentifier
        let accepted = !needsRestore || originalFront.activate(options: [])
        let restoreDeadline = min(deadline, now() + 2)
        while NSWorkspace.shared.frontmostApplication?.processIdentifier != originalFront.processIdentifier, now() < restoreDeadline {
            RunLoop.current.run(until: Date().addingTimeInterval(0.03))
        }
        let restored = NSWorkspace.shared.frontmostApplication?.processIdentifier == originalFront.processIdentifier
        report["front_restore"] = ["requested": needsRestore, "eligible": true, "accepted": accepted, "restored": restored, "after": frontState(p.processIdentifier)]
        if !restored { cleanupOK = false }
    } else {
        report["front_restore"] = ["requested": false, "reason": "Own app was not immediately front at cleanup, or original app exited; no override of a changed foreground application.", "after": frontState(p.processIdentifier)]
        if ownWasFront { cleanupOK = false }
    }
}
applicationLog?.closeFile()
if let ipc {
    do { try fm.removeItem(at: ipc); report["ipc_removed"] = !fm.fileExists(atPath: ipc.path) }
    catch { report["ipc_cleanup_error"] = String(describing: error); cleanupOK = false }
}
report["normal_profile_end"] = normalProfile(); report["ended_uptime"] = now()
report["elapsed_seconds"] = now() - started
report["acquisition_complete"] = acquired; report["cleanup_complete"] = cleanupOK
let success = acquired && cleanupOK && now() <= deadline
report["success"] = success
do { try save() } catch { fputs("Cannot save observer result: \(error)\n", stderr); exit(1) }
if !success {
    fputs("Showcase toolbar acquisition failed: \(report["error"] as? String ?? "cleanup or deadline condition"). \(outputReady ? "Partial result retained." : "Output was not created.")\n", stderr)
}
exit(success ? 0 : 1)
