// A bounded external observer of the supplied, separately built application.
// No source injection, TCC changes, offscreen rendering or screenshot fallback.
import AppKit
import ApplicationServices
import CoreGraphics
import Darwin
import Foundation
import ImageIO

struct Failure: Error, CustomStringConvertible { let description: String }
let files = FileManager.default
guard CommandLine.arguments.count == 4 else {
    fputs("usage: picture-local13-collector APP CLI OUTPUT\n", stderr)
    exit(2)
}
let appURL = URL(fileURLWithPath: CommandLine.arguments[1]).resolvingSymlinksInPath()
let product = appURL.deletingPathExtension().lastPathComponent
let cliURL = URL(fileURLWithPath: CommandLine.arguments[2]).resolvingSymlinksInPath()
let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
guard !files.fileExists(atPath: output.path) else {
    fputs("Output must be fresh and nonexistent\n", stderr); exit(2)
}
try files.createDirectory(at: output, withIntermediateDirectories: true)
let originalFront = NSWorkspace.shared.frontmostApplication
var cleanupOK = true
func appIdentity(_ app: NSRunningApplication) -> [String: Any] {
    ["pid": app.processIdentifier, "bundle_id": app.bundleIdentifier ?? "",
     "executable_path": app.executableURL?.resolvingSymlinksInPath().path ?? "",
     "launch_date": app.launchDate.map { $0.timeIntervalSince1970 as Any } ?? NSNull()]
}
func sameIdentity(_ app: NSRunningApplication, _ row: [String: Any]) -> Bool {
    guard !app.isTerminated, let pid = row["pid"] as? NSNumber,
          let launch = row["launch_date"] as? NSNumber, let actual = app.launchDate else { return false }
    return app.processIdentifier == pid.int32Value && app.bundleIdentifier == (row["bundle_id"] as? String) &&
        app.executableURL?.resolvingSymlinksInPath().path == (row["executable_path"] as? String) &&
        abs(actual.timeIntervalSince1970 - launch.doubleValue) < 0.001
}
func writeIdentity(_ row: [String: Any], _ name: String) throws {
    try JSONSerialization.data(withJSONObject: row, options: [.prettyPrinted, .sortedKeys])
        .write(to: output.appendingPathComponent(name), options: .atomic)
}
func writeOwnership(_ process: Process) throws {
    var row: [String: Any] = ["pid": process.processIdentifier,
        "bundle_id": Bundle(url: appURL)?.bundleIdentifier ?? "",
        "executable_path": appURL.appendingPathComponent("Contents/MacOS/Showcase").path,
        "launch_date": NSNull()]
    if let running = NSRunningApplication(processIdentifier: process.processIdentifier),
       running.bundleIdentifier == (row["bundle_id"] as? String),
       running.executableURL?.resolvingSymlinksInPath().path == (row["executable_path"] as? String) {
        row = appIdentity(running)
    }
    row["collector_pid"] = getpid()
    try writeIdentity(row, "ownership.json")
}
let timeLimit: TimeInterval = 160
let deadline = Date().addingTimeInterval(timeLimit)
var report: [String: Any] = [
    "source_sha": ProcessInfo.processInfo.environment["BERN_SOURCE_SHA"] ?? "unknown",
    "application": product,
    "harness_sha": ProcessInfo.processInfo.environment["GITHUB_SHA"] ?? "unknown",
    "os": ProcessInfo.processInfo.operatingSystemVersionString,
    "capture": "CGWindowListCreateImage / WindowServer",
    "interaction_scope": "Generated CLI bindings. Motion files record programmatic transitions; mouse/keyboard paths and transition equivalence are not asserted",
    "requested_outer_size_points": ["width": 920, "height": 668],
    "geometry_scope": "Outer frame normalized through window.resize; CLI does not expose the content rect, and PNGs include system window chrome",
    "commands": [[String: Any]](), "windows": [[String: Any]](),
    "checks": [[String: Any]](),
]
var commands = [[String: Any]]()
var windows = [[String: Any]]()
var checks = [[String: Any]]()
var environment = ProcessInfo.processInfo.environment
var sequence = 0
report["accessibility_trusted"] = AXIsProcessTrusted()
report["post_event_access"] = CGPreflightPostEventAccess()
report["displays"] = NSScreen.screens.map { screen -> [String: Any] in
    ["frame_points": NSStringFromRect(screen.frame), "scale": screen.backingScaleFactor,
     "color_space": screen.colorSpace?.localizedName ?? "unknown"]
}
report["system_preferences"] = [
    "reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
    "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
    "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast,
    "accent": UserDefaults.standard.persistentDomain(forName: UserDefaults.globalDomain)?["AppleAccentColor"] ?? "default",
]

func save() throws {
    report["commands"] = commands; report["windows"] = windows; report["checks"] = checks
    let data = try JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
    try data.write(to: output.appendingPathComponent("result.json"), options: .atomic)
}
func pause(_ seconds: TimeInterval) throws {
    let end = Date().addingTimeInterval(seconds)
    while Date() < end {
        guard Date() < deadline else { throw Failure(description: "Capture exceeded its \(Int(timeLimit)) second limit") }
        RunLoop.current.run(until: Date().addingTimeInterval(0.025))
        Thread.sleep(forTimeInterval: 0.01)
    }
}
func logHandle(_ name: String) throws -> FileHandle {
    let path = output.appendingPathComponent(name)
    guard files.createFile(atPath: path.path, contents: nil) else { throw Failure(description: "Cannot create \(name)") }
    return try FileHandle(forWritingTo: path)
}
// The helper restores the original live instance BEFORE stopping the exact private app.
func stop(_ process: Process) {
    guard let helper = environment["BERN_PICTURE_FOCUS_GUARD"] else { cleanupOK = false; return }
    let p = Process(); p.executableURL = URL(fileURLWithPath: helper)
    p.arguments = ["cleanup", appURL.path, output.appendingPathComponent("original-front.json").path,
                   output.appendingPathComponent("ownership.json").path]
    do {
        let log = try logHandle("cleanup-helper.json"); defer { log.closeFile() }
        p.standardOutput = log; p.standardError = log
        try p.run()
        let end = Date().addingTimeInterval(7)
        while p.isRunning && Date() < end { RunLoop.current.run(until: Date().addingTimeInterval(0.02)) }
        if p.isRunning { kill(p.processIdentifier, SIGKILL); cleanupOK = false }
        else { cleanupOK = p.terminationStatus == 0 && !process.isRunning }
        report["cleanup"] = ["helper_status": p.isRunning ? -1 : p.terminationStatus,
            "own_pid": process.processIdentifier, "own_process_still_running": process.isRunning,
            "success": cleanupOK, "receipt": "cleanup-helper.json"]
    } catch { cleanupOK = false; report["cleanup_error"] = String(describing: error) }
}

func cli(_ arguments: [String], session: String? = nil, allowFailure: Bool = false, until cutoff: Date? = nil) throws -> Any? {
    sequence += 1
    let stem = String(format: "%03d", sequence)
    let stdoutName = "\(stem)-stdout.json", stderrName = "\(stem)-stderr.txt"
    let stdout = try logHandle(stdoutName), error = try logHandle(stderrName)
    defer { stdout.closeFile(); error.closeFile() }
    let process = Process(); process.executableURL = cliURL
    process.arguments = (session.map { ["--session", $0] } ?? []) + arguments
    process.environment = environment; process.standardOutput = stdout; process.standardError = error
    try process.run()
    defer { if process.isRunning { kill(process.processIdentifier, SIGKILL) } }
    let end = min(Date().addingTimeInterval(8), min(cutoff ?? deadline, deadline))
    while process.isRunning && Date() < end { try pause(0.03) }
    if process.isRunning { kill(process.processIdentifier, SIGKILL); throw Failure(description: "CLI timed out: \(arguments)") }
    commands.append(["arguments": process.arguments ?? [], "status": process.terminationStatus,
                     "appearance": environment["BERN_APPEARANCE"] ?? "unknown",
                     "stdout": stdoutName, "stderr": stderrName])
    try save()
    guard process.terminationStatus == 0 else {
        if allowFailure { return nil }
        throw Failure(description: "CLI failed: \(arguments); see \(stderrName)")
    }
    let data = try Data(contentsOf: output.appendingPathComponent(stdoutName))
    return data.isEmpty ? nil : try JSONSerialization.jsonObject(with: data, options: [.fragmentsAllowed])
}
func inspect(_ session: String) throws -> [[String: Any]] {
    guard let rows = try cli(["ui", "inspect"], session: session) as? [[String: Any]] else {
        throw Failure(description: "ui.inspect did not return its control array")
    }
    return rows
}
func control(_ rows: [[String: Any]], suffix: String, role: String) throws -> [String: Any] {
    let matches = rows.filter { ($0["target"] as? String)?.hasSuffix(suffix) == true && $0["role"] as? String == role }
    guard matches.count == 1, matches[0]["enabled"] as? Bool == true else {
        throw Failure(description: "Expected one enabled \(role) ending in \(suffix); found \(matches.count)")
    }
    return matches[0]
}
func waitForValue(_ session: String, suffix: String, role: String, description: String,
                  matching: (String) -> Bool) throws -> [String: Any] {
    let end = min(Date().addingTimeInterval(8), deadline)
    var last = "not mounted"
    repeat {
        let rows = try inspect(session)
        let matches = rows.filter { ($0["target"] as? String)?.hasSuffix(suffix) == true && $0["role"] as? String == role }
        guard matches.count <= 1 else { throw Failure(description: "Ambiguous \(role) ending in \(suffix)") }
        if let row = matches.first {
            last = row["value"] as? String ?? "nil"
            if row["enabled"] as? Bool == true, matching(last) {
                checks.append(["check": description, "target": row["target"] ?? "", "observed_value": last,
                               "appearance": environment["BERN_APPEARANCE"] ?? "unknown", "passed": true])
                try save()
                return row
            }
        }
        try pause(0.12)
    } while Date() < end
    throw Failure(description: "Timed out waiting for \(description): \(last)")
}
func queryVersion(_ row: [String: Any]) throws -> UInt64 {
    let words = (row["value"] as? String ?? "").split(separator: " ")
    guard words.count >= 2, words[1].first == "v", let version = UInt64(words[1].dropFirst()) else {
        throw Failure(description: "Query summary lacks its documented request version: \(row)")
    }
    return version
}
func selectPage(_ page: String, session: String) throws {
    let sidebar = try control(inspect(session), suffix: ".pages", role: "sidebar")
    _ = try cli(["ui", "select", "--target", sidebar["target"] as! String, "--option", page], session: session)
    _ = try waitForValue(session, suffix: ".pages", role: "sidebar", description: "Selected \(page)") { $0 == page }
}
func editSearch(_ value: String, session: String) throws {
    let search = try control(inspect(session), suffix: ".sidebar_search", role: "search")
    _ = try cli(["ui", "edit", "--target", search["target"] as! String, "--value", value], session: session)
    _ = try waitForValue(session, suffix: ".sidebar_search", role: "search", description: "Search draft committed") { $0 == value }
}
func imageInputs() throws {
    var assets = [[String: Any]]()
    for name in ["images/landscape.jpg", "images/bern.png", "images/hdr-gainmap.jpg", "images/hdr-pq.png"] {
        let url = appURL.appendingPathComponent("Contents/Resources").appendingPathComponent(name)
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil), image.width > 0, image.height > 0 else {
            throw Failure(description: "Bundled image cannot be decoded: \(name)")
        }
        assets.append(["resource": name, "pixel_width": image.width, "pixel_height": image.height,
                       "color_space": image.colorSpace?.name as String? ?? "unknown"])
    }
    report["image_assets"] = assets
    report["image_verification_scope"] = "Inputs decode with ImageIO; the Layout PNG requires visual comparison for image presence, fit, clipping and color. No HDR luminance or EDR equivalence is asserted."
    checks.append(["check": "Four bundled image inputs decode", "passed": true])
    try save()
}
func visibleWindow(_ pid: pid_t) -> [String: Any]? {
    let all = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    let own = all.filter { row in
        guard (row[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid,
              (row[kCGWindowLayer as String] as? NSNumber)?.intValue == 0,
              (row[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true,
              ((row[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99,
              let bounds = row[kCGWindowBounds as String] as? [String: NSNumber] else { return false }
        return (bounds["Width"]?.doubleValue ?? 0) > 120 && (bounds["Height"]?.doubleValue ?? 0) > 120
    }
    return own.count == 1 ? own[0] : nil
}

func capture(_ name: String, process: Process, session: String) throws {
    guard process.isRunning, let info = visibleWindow(process.processIdentifier),
          let number = info[kCGWindowNumber as String] as? NSNumber else {
        throw Failure(description: "The application has no visible, normal-level window")
    }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == process.processIdentifier else {
        throw Failure(description: "The reference application is not active at capture time")
    }
    let bounds = info[kCGWindowBounds as String] as? [String: NSNumber] ?? [:]
    if product == "Showcase" {
        guard abs((bounds["Width"]?.doubleValue ?? 0) - 920) <= 1,
              abs((bounds["Height"]?.doubleValue ?? 0) - 668) <= 1 else {
            throw Failure(description: "WindowServer frame differs from the requested 920 x 668 point outer size")
        }
    }
    let permission = CGPreflightScreenCaptureAccess()
    report["screen_recording_preflight"] = permission
    try save()
    guard permission else {
        throw Failure(description: "Screen Recording permission unavailable; no TCC changes or offscreen fallback were attempted")
    }
    guard let image = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(number.uint32Value), [.boundsIgnoreFraming, .bestResolution]) else {
        throw Failure(description: "WindowServer could not capture window \(number)")
    }
    let target = output.appendingPathComponent(name + ".png")
    guard let destination = CGImageDestinationCreateWithURL(target as CFURL, "public.png" as CFString, 1, nil) else {
        throw Failure(description: "Cannot create PNG destination")
    }
    CGImageDestinationAddImage(destination, image, nil)
    guard CGImageDestinationFinalize(destination) else { throw Failure(description: "Cannot write PNG") }
    windows.append(["png": target.lastPathComponent, "pid": process.processIdentifier,
                    "window_number": number, "title": info[kCGWindowName as String] ?? "",
                    "bounds_points": info[kCGWindowBounds as String] ?? [:],
                    "pixel_width": image.width, "pixel_height": image.height,
                    "color_space": image.colorSpace?.name as String? ?? "unknown",
                    "session_windows": try cli(["window", "list"], session: session) ?? NSNull()])
    try save()
}

func showcaseSlices(process: Process, session: String) throws {
    report["showcase_extra_slices"] = "Light appearance only; main window at 920 x 668 outer points. Screenshots are evidence for comparison, not an automatic visual-equivalence verdict."

    for page in ["Text", "Buttons", "Inputs"] {
        try selectPage(page, session: session)
        try pause(0.3)
        try capture(page.lowercased() + "-light", process: process, session: session)
    }

    // Editing before mounting Library guarantees that the first answer has
    // no previous rows. Editing an already-ready Query deliberately retains
    // those rows with an error banner instead of the full unavailable view.
    try selectPage("Text", session: session)
    try editSearch("!", session: session)
    try selectPage("Library", session: session)
    let failed = try waitForValue(session, suffix: ".library_results", role: "query",
                                 description: "Initial query failed without previous results") {
        $0.hasPrefix("failed v") && $0.contains(" invalid_search:")
            && $0.range(of: #"\([0-9]+\)$"#, options: .regularExpression) == nil
    }
    try pause(0.3)
    try capture("query-failed-light", process: process, session: session)
    let failedVersion = try queryVersion(failed)
    // The documented Query control invokes the same retry operation as its
    // visible Retry button; this does not claim a mouse-click acceptance test.
    _ = try cli(["ui", "activate", "--target", failed["target"] as! String], session: session)
    _ = try waitForValue(session, suffix: ".library_results", role: "query", description: "Retry issued a new failing request") {
        guard $0.hasPrefix("failed v"), $0.contains(" invalid_search:"),
              let version = try? queryVersion(["value": $0]) else { return false }
        return version > failedVersion
    }

    try editSearch("zzzzzz", session: session)
    _ = try waitForValue(session, suffix: ".library_results", role: "query", description: "Query returned zero results") {
        $0.hasPrefix("ready v") && $0.hasSuffix(" (0)")
    }
    try pause(0.3)
    try capture("query-empty-light", process: process, session: session)
    try editSearch("", session: session)
    _ = try waitForValue(session, suffix: ".library_results", role: "query", description: "Query recovered with results") {
        $0.hasPrefix("ready v") && $0.range(of: #" \([1-9][0-9]*\)$"#, options: .regularExpression) != nil
    }
    let links = try inspect(session).filter { $0["role"] as? String == "link" && ($0["target"] as? String)?.contains(".item_link") == true }
    guard !links.isEmpty else { throw Failure(description: "Recovered query has no mounted library links") }
    try pause(0.3)
    try capture("query-recovered-light", process: process, session: session)

    try selectPage("Layout", session: session)
    try imageInputs()
    try pause(0.8)
    try capture("images-layout-light", process: process, session: session)


}

do {
    try save()
    if let profile = environment["BERN_REFERENCE_PROFILE"] {
        let reduced = profile == "reduced"
        guard ["normal", "reduced"].contains(profile),
              NSWorkspace.shared.accessibilityDisplayShouldReduceMotion == reduced,
              NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency == reduced else {
            throw Failure(description: "Effective accessibility preferences do not match requested profile \(profile)")
        }
        report["appearance_profile"] = profile
    }
    guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 13,
          !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
          !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
          !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast else {
        throw Failure(description: "Requires macOS13 and existing normal profile; preferences are never written")
    }
    guard product == "Showcase", let bundleID = Bundle(url: appURL)?.bundleIdentifier,
          bundleID.hasPrefix("dev.bern."), bundleID != "dev.bern.showcase",
          !NSWorkspace.shared.runningApplications.contains(where: { $0.bundleIdentifier == bundleID }),
          let originalFront, let frontPath = environment["BERN_PICTURE_WATCHDOG_FRONT"],
          let expectedFront = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: frontPath))) as? [String: Any],
          sameIdentity(originalFront, expectedFront), environment["BERN_PICTURE_FOCUS_GUARD"] != nil else {
        throw Failure(description: "Requires private nonrunning Showcase and matching watchdog original-front receipt")
    }
    try writeIdentity(appIdentity(originalFront), "original-front.json")
    report["original_front"] = appIdentity(originalFront)
    report["private_bundle_id"] = bundleID
    let permission = CGPreflightScreenCaptureAccess()
    report["screen_recording_preflight"] = permission
    try save()
    guard permission else {
        throw Failure(description: "CGPreflightScreenCaptureAccess=false: runner Screen Recording permission unavailable; no TCC changes or screenshot fallback")
    }
    for appearance in ["light"] {
        let ipc = URL(fileURLWithPath: "/tmp/bern-reference-\(getpid())-\(appearance)", isDirectory: true)
        try files.createDirectory(at: ipc, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        environment["BERN_IPC_DIR"] = ipc.path; environment["BERN_APPEARANCE"] = appearance
        environment.removeValue(forKey: "BERN_SNAPSHOT_DIR")
        let process = Process(); process.executableURL = appURL.appendingPathComponent("Contents/MacOS/" + product)
        process.arguments = ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        process.environment = environment
        let appLog = try logHandle("\(appearance)-application.log")
        process.standardOutput = appLog; process.standardError = appLog
        let launchStart = Date()
        try process.run()
        defer {
            stop(process); appLog.closeFile()
            do { try files.removeItem(at: ipc) }
            catch { cleanupOK = false; report["ipc_cleanup_error"] = String(describing: error) }
        }
        try writeOwnership(process)
        let ready = min(deadline, launchStart.addingTimeInterval(18))
        var session: String?, startupReady = false
        var startupSamples = [[String: Any]]()
        while !startupReady && Date() < ready && process.isRunning {
            if session == nil {
                let entries = try cli(["sessions"], allowFailure: true, until: ready) as? [[String: Any]] ?? []
                guard entries.count <= 1 else { throw Failure(description: "Ambiguous private IPC session") }
                session = entries.first?["session_id"] as? String
            }
            if let id = session {
                let listed = try cli(["window", "list"], session: id, allowFailure: true, until: ready) as? [[String: Any]] ?? []
                let main = listed.filter { $0["kind"] as? String == "main" }
                let native = visibleWindow(process.processIdentifier)
                startupSamples.append(["session": id, "registered_windows": listed, "own_pid": process.processIdentifier,
                    "own_visible_window": native as Any? ?? NSNull()])
                startupReady = main.count == 1 && native != nil && Date() < ready
            }
            if !startupReady { try pause(0.15) }
        }
        report["startup_readiness"] = startupSamples; try save()
        guard startupReady, let session else { throw Failure(description: "Private session + main + unique own visible window not ready in18s") }
        try writeOwnership(process)
        let accepted = NSRunningApplication(processIdentifier: process.processIdentifier)?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps]) ?? false
        let activationEnd = min(deadline, Date().addingTimeInterval(2))
        while NSWorkspace.shared.frontmostApplication?.processIdentifier != process.processIdentifier && Date() < activationEnd { try pause(0.03) }
        report["activation_accepted"] = accepted
        guard NSWorkspace.shared.frontmostApplication?.processIdentifier == process.processIdentifier else {
            throw Failure(description: "Own app activation failed")
        }
        _ = try cli(["ui", "set-language", "--language", "en"], session: session)
        let listed = try cli(["window", "list"], session: session) as? [[String: Any]] ?? []
        let main = listed.filter { $0["kind"] as? String == "main" }
        guard main.count == 1, let identifier = main[0]["window"] as? String else {
            throw Failure(description: "window.list did not identify exactly one main window")
        }
        _ = try cli(["window", "resize", "--window", identifier, "--width", "920", "--height", "668"], session: session)
        let sidebar = try control(inspect(session), suffix: ".pages", role: "sidebar")
        _ = try cli(["ui", "select", "--target", sidebar["target"] as! String, "--option", "Controls"], session: session)
        try pause(0.8)
        let before = try inspect(session)
        let toggle = try control(before, suffix: ".notifications", role: "switch")
        let volume = try control(before, suffix: ".volume", role: "slider")
        try capture("controls-\(appearance)", process: process, session: session)
        if appearance == "light" {
            _ = try cli(["ui", "set-bool", "--target", toggle["target"] as! String, "--value", "false"], session: session)
            _ = try cli(["ui", "set-number", "--target", volume["target"] as! String, "--value", "73"], session: session)
            let committed = Date().addingTimeInterval(5)
            var value: Double?
            repeat {
                let state = try cli(["state"]) as? [String: Any]
                value = ((state?["values"] as? [String: Any])?["volume"] as? NSNumber)?.doubleValue
                if value != 73 { try pause(0.1) }
            } while value != 73 && Date() < committed
            let after = try inspect(session)
            guard try control(after, suffix: ".notifications", role: "switch")["value"] as? String == "false", value == 73 else {
                throw Failure(description: "Switch draft or engine volume did not commit through the UI bindings")
            }
            try pause(0.4)
            try capture("controls-light-after-commit", process: process, session: session)
            try showcaseSlices(process: process, session: session)
        }
    }
    guard cleanupOK else { throw Failure(description: "Focus/owned-process cleanup incomplete; watchdog receipt required") }
    report["success"] = true
    try save()
} catch {
    report["success"] = false; report["failure"] = String(describing: error)
    try? save()
    fputs("reference capture failed: \(error)\n", stderr)
    exit(1)
}
