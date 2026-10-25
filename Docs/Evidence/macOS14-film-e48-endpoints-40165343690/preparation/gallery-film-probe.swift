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
let expectedOS = Int(environment["BERN_FILM_EXPECTED_OS"] ?? "14") ?? 0
let requestedScenario = environment["BERN_FILM_SCENARIO"] ?? "all"
let observation = environment["BERN_FILM_OBSERVATION"] ?? "active"
let followup = environment["BERN_FILM_FOLLOWUP"] ?? "none"
let scenarios = requestedScenario == "all" ? ["immediate", "wait", "direct"] : [requestedScenario]
var commands = [[String: Any]](), cases = [[String: Any]](), activationRequests = [[String: Any]]()
var inactiveCaptureSamples = [[String: Any]]()
var ipcPaths = [String]()
var report: [String: Any] = [
    "source_sha": environment["BERN_SOURCE_SHA"] ?? "unknown",
    "harness_sha": environment["GITHUB_SHA"] ?? "unknown",
    "variant": environment["FILM_VARIANT"] ?? "unknown",
    "expected_os_major": expectedOS, "requested_scenario": requestedScenario,
    "observation_mode": observation, "followup_sequence": followup,
    "observation_contract": observation == "inactive13"
        ? "Internal diagnostic only: no activate/focus-restore requests; own window must remain visible with alpha>=0.99, inactive, stable raw buffers and bounds. Not active visual acceptance."
        : "Original active visual capture contract.",
    "appearance_profile": "normal",
    "os": ProcessInfo.processInfo.operatingSystemVersionString,
    "accessibility_trusted": trusted, "screen_recording_preflight": CGPreflightScreenCaptureAccess(),
    "scope": "Light only; each selected scenario uses a fresh process, exact app. AX frames are global screen points. No draft/target/nearest introspection; visible labels do not prove a binding write.",
    "sampling_scope": "First second after Film select CLI launch, including mounting latency; actual AX-walk timestamps, no assumed sampling frequency.",
    "system_preferences": ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
        "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
        "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
    "displays": NSScreen.screens.map { ["frame_points": NSStringFromRect($0.frame), "scale": $0.backingScaleFactor] },
]
func now() -> Double { ProcessInfo.processInfo.systemUptime }
func frontState(_ ownPID: pid_t) -> [String: Any] {
    let front = NSWorkspace.shared.frontmostApplication
    return ["uptime": now(), "own_pid": ownPID,
        "front_pid": front.map { $0.processIdentifier as Any } ?? NSNull(),
        "front_bundle": front?.bundleIdentifier as Any? ?? NSNull()]
}
func save() throws {
    report["commands"] = commands; report["cases"] = cases
    report["activation_requests"] = activationRequests
    report["inactive_capture_samples"] = inactiveCaptureSamples
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
         until cutoff: Double? = nil, observe: (() -> Void)? = nil) throws -> Any? {
    let stem = String(format: "%03d", commands.count + 1)
    let out = try handle(stem + "-stdout.json"), err = try handle(stem + "-stderr.txt")
    defer { out.closeFile(); err.closeFile() }
    let p = Process(); p.executableURL = cliURL
    p.arguments = (session.map { ["--session", $0] } ?? []) + args
    p.environment = environment; p.standardOutput = out; p.standardError = err
    let start = now(), callDeadline = min(deadline, min(cutoff ?? deadline, now() + 8)); try p.run()
    while p.isRunning || (observe != nil && now() - start < 1) {
        if now() >= callDeadline {
            if p.isRunning { kill(p.processIdentifier, SIGKILL); p.waitUntilExit() }
            commands.append(["arguments": p.arguments ?? [], "start_uptime": start, "end_uptime": now(),
                "deadline_uptime": callDeadline, "timeout": true, "stdout": stem + "-stdout.json", "stderr": stem + "-stderr.txt"])
            try save()
            throw Failure(description: "CLI exceeded its bounded deadline")
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
func stable(_ pid: pid_t, name: String, expectedWidth: Double = 920) throws -> [String: Any] {
    var previous: Data?, same = 0, count = 0
    var previousInactiveGeometry: [Double]?
    let start = now()
    while now() - start < 8 {
        var inactiveGeometry: [Double]?
        if observation == "inactive13" {
            let info = try window(pid), front = frontState(pid)
            let bounds = info[kCGWindowBounds as String] as? [String: NSNumber] ?? [:]
            let alpha = (info[kCGWindowAlpha as String] as? NSNumber)?.doubleValue
            inactiveCaptureSamples.append(["capture": name, "front": front,
                "own_window": info, "sample": count])
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier != pid,
                  (info[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true,
                  let alpha, alpha >= 0.99,
                  let id = info[kCGWindowNumber as String] as? NSNumber,
                  let x = bounds["X"], let y = bounds["Y"],
                  let width = bounds["Width"], let height = bounds["Height"] else {
                throw Failure(description: "Inactive13 requires an inactive, on-screen own window with alpha>=0.99 and complete geometry")
            }
            inactiveGeometry = [id.doubleValue, x.doubleValue, y.doubleValue,
                width.doubleValue, height.doubleValue, alpha]
        } else if NSWorkspace.shared.frontmostApplication?.processIdentifier != pid {
            report["capture_focus_failure"] = ["capture": name, "actual": frontState(pid)]
            try save()
            throw Failure(description: "Gallery is not active at capture time")
        }
        let img = try image(pid)
        guard let bytes = img.dataProvider?.data else { throw Failure(description: "Missing raw capture buffer") }
        let data = bytes as Data
        same = data == previous && inactiveGeometry == previousInactiveGeometry ? same + 1 : 0
        previous = data; previousInactiveGeometry = inactiveGeometry; count += 1
        if same >= 4 {
            let info = try window(pid), bounds = info[kCGWindowBounds as String] as? [String: NSNumber] ?? [:]
            guard bounds["Width"]?.doubleValue == expectedWidth, bounds["Height"]?.doubleValue == 668 else {
                throw Failure(description: "Outer window is not \(expectedWidth) x 668 points")
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
func axSample(_ root: AXUIElement, timeBudget: Double = 0.12) -> [String: Any] {
    let start = now()
    guard trusted else { return ["start_uptime": start, "missing": "AXIsProcessTrusted=false; no permission request"] }
    var queue = [root], index = 0, rows = [[String: Any]]()
    let names: Set<String> = ["Gingham", "Tartan", "Madras", "Glen", "Houndstooth", "Windowpane"]
    while index < queue.count && index < 512 && now() - start < timeBudget {
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
    guard [13, 14].contains(expectedOS), ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,
          ["all", "immediate", "wait", "direct"].contains(requestedScenario),
          observation == "active" || observation == "inactive13" && expectedOS == 13,
          followup == "none" || followup == "last-resize" && requestedScenario == "direct",
          CGPreflightScreenCaptureAccess() else {
        throw Failure(description: "Requires the explicitly selected macOS13/14, valid scenario and existing Screen Recording access; no TCC changes")
    }
    guard !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
          !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
          !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast else {
        throw Failure(description: "Effective accessibility preferences do not match normal profile; observer does not change preferences")
    }
    for scenario in scenarios {
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
        defer {
            let ownWasFront = NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier
            stop(p); log.closeFile(); try? fm.removeItem(at: ipc)
            if observation == "active", ownWasFront, NSWorkspace.shared.frontmostApplication?.processIdentifier != originalFront?.processIdentifier {
                originalFront?.activate(options: [])
            }
        }
        var session: String?
        let ready = now() + 15
        while session == nil && p.isRunning && now() < ready {
            let entries = try cli(["sessions"], allowFailure: true, until: ready) as? [[String: Any]] ?? []
            if entries.count == 1 { session = entries[0]["session_id"] as? String }
            if session == nil { try pause(0.1) }
        }
        guard let id = session else { throw Failure(description: "No unique UI session") }
        // The transport session can precede SwiftUI's first native window.
        // Keep the original absolute startup deadline; do not inspect controls
        // or request foreground before both registries contain the own window.
        var startupSamples = [[String: Any]](), startupReady = false
        while p.isRunning && now() < ready {
            let listed = try cli(["window", "list"], id, allowFailure: true, until: ready) as? [[String: Any]] ?? []
            let native = try? window(p.processIdentifier)
            let alpha = (native?[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0
            startupSamples.append(["uptime": now(), "windows": listed, "own_native_window": native as Any? ?? NSNull(), "own_native_window_alpha": alpha])
            var startup = report["startup_readiness"] as? [[String: Any]] ?? []
            let sample: [String: Any] = ["scenario": scenario, "pid": p.processIdentifier,
                "deadline_uptime": ready, "samples": startupSamples]
            if startup.last?["pid"] as? Int32 == p.processIdentifier { startup[startup.count - 1] = sample } else { startup.append(sample) }
            report["startup_readiness"] = startup; try save()
            if now() < ready, listed.contains(where: { $0["kind"] as? String == "main" }), native != nil, alpha >= 0.99 {
                startupReady = true; break
            }
            try pause(min(0.08, max(0, ready - now())))
        }
        guard startupReady else { throw Failure(description: "Startup did not register a main window and visible owned CG window within the original 15 second deadline") }
        if observation == "active" {
            let beforeActivation = frontState(p.processIdentifier)
            let activationOptions: NSApplication.ActivationOptions = expectedOS == 13
                ? [.activateAllWindows, .activateIgnoringOtherApps] : [.activateAllWindows]
            let accepted = NSRunningApplication(processIdentifier: p.processIdentifier)?.activate(options: activationOptions) ?? false
            var activationSamples = [frontState(p.processIdentifier)]
            let activationDeadline = min(deadline, now() + 2)
            while NSWorkspace.shared.frontmostApplication?.processIdentifier != p.processIdentifier, now() < activationDeadline {
                try pause(0.05); activationSamples.append(frontState(p.processIdentifier))
            }
            activationRequests.append(["scenario": scenario, "pid": p.processIdentifier,
                "before": beforeActivation, "accepted": accepted,
                "options": expectedOS == 13 ? ["activateAllWindows", "activateIgnoringOtherApps"] : ["activateAllWindows"],
                "samples": activationSamples, "after": frontState(p.processIdentifier)])
        }
        try save()
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
        entry["settled_ax"] = axSample(root, timeBudget: 2)
        entry["controls"] = try cli(["ui", "inspect"], id) ?? NSNull()
        if let directory = environment["BERN_SCROLL_TRACE_DIR"] {
            let trace = URL(fileURLWithPath: directory).appendingPathComponent("scroll-\(p.processIdentifier).json")
            let stopAt = min(deadline, (entry["select_start_uptime"] as? Double ?? now()) + 4)
            while !fm.fileExists(atPath: trace.path), now() < stopAt { try pause(0.05) }
            guard fm.fileExists(atPath: trace.path),
                  let record = try JSONSerialization.jsonObject(with: Data(contentsOf: trace)) as? [String: Any],
                  (record["pid"] as? NSNumber)?.int32Value == p.processIdentifier else {
                throw Failure(description: "Own diagnostic trace did not flush within the bounded wait")
            }
            entry["internal_trace"] = trace.lastPathComponent
            entry["film_after_trace"] = try stable(p.processIdentifier, name: scenario + "-film-after-trace")
        }
        cases[cases.count - 1] = entry; try save()
        if followup == "last-resize" {
            // Only the explicit direct sequence continues after the original
            // first-entry capture/trace. These are real existing bindings.
            var stages = [[String: Any]]()
            for (stage, suffix, width) in [("last", ".to_last", 920), ("first", ".to_first", 920),
                                          ("last-again", ".to_last", 920), ("resize-wide", "", 1020),
                                          ("resize-restore", "", 920)] {
                let started = now()
                if suffix.isEmpty {
                    _ = try cli(["window", "resize", "--window", win, "--width", String(width), "--height", "668"], id)
                } else {
                    _ = try cli(["ui", "activate", "--target", target(id, suffix: suffix)], id)
                }
                let shot = try stable(p.processIdentifier, name: scenario + "-" + stage, expectedWidth: Double(width))
                stages.append(["stage": stage, "action_start_uptime": started, "capture": shot,
                    "ax": axSample(root, timeBudget: 2), "controls": try cli(["ui", "inspect"], id) ?? NSNull(),
                    "windows": try cli(["window", "list"], id) ?? NSNull(),
                    "scope": "Post-initial CLI binding/resize and real stable WindowServer buffer; not physical input or an internal followup trace."])
                entry["followup_stages"] = stages; cases[cases.count - 1] = entry; try save()
            }
        }
    }
    report["success"] = true; try save()
} catch {
    report["success"] = false; report["failure"] = String(describing: error); try? save()
    fputs("Film probe failed: \(error)\n", stderr); exit(1)
}
