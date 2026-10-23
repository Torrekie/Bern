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
    fputs("usage: macos14-reference.swift APP CLI OUTPUT\n", stderr)
    exit(2)
}
let appURL = URL(fileURLWithPath: CommandLine.arguments[1])
let product = appURL.deletingPathExtension().lastPathComponent
let cliURL = URL(fileURLWithPath: CommandLine.arguments[2])
let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
try files.createDirectory(at: output, withIntermediateDirectories: true)
let timeLimit: TimeInterval = 160
let deadline = Date().addingTimeInterval(timeLimit)
var report: [String: Any] = [
    "source_sha": ProcessInfo.processInfo.environment["BERN_SOURCE_SHA"] ?? "ffbdbdf3d41bb6492a8b13d3fa6182ee636606ee",
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
func stop(_ process: Process) {
    guard process.isRunning else { return }
    NSRunningApplication(processIdentifier: process.processIdentifier)?.terminate()
    let end = Date().addingTimeInterval(2)
    while process.isRunning && Date() < end {
        RunLoop.current.run(until: Date().addingTimeInterval(0.025))
        Thread.sleep(forTimeInterval: 0.01)
    }
    if process.isRunning { kill(process.processIdentifier, SIGKILL) }
}
func cli(_ arguments: [String], session: String? = nil, allowFailure: Bool = false) throws -> Any? {
    sequence += 1
    let stem = String(format: "%03d", sequence)
    let stdoutName = "\(stem)-stdout.json", stderrName = "\(stem)-stderr.txt"
    let stdout = try logHandle(stdoutName), error = try logHandle(stderrName)
    defer { stdout.closeFile(); error.closeFile() }
    let process = Process(); process.executableURL = cliURL
    process.arguments = (session.map { ["--session", $0] } ?? []) + arguments
    process.environment = environment; process.standardOutput = stdout; process.standardError = error
    try process.run()
    let end = min(Date().addingTimeInterval(8), deadline)
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
    let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    var largest: [String: Any]?
    var largestArea = 0.0
    for info in rows {
        guard let owner = info[kCGWindowOwnerPID as String] as? NSNumber,
              owner.int32Value == pid else { continue }
        guard let layer = info[kCGWindowLayer as String] as? NSNumber,
              layer.intValue == 0 else { continue }
        guard let bounds = info[kCGWindowBounds as String] as? [String: NSNumber],
              let width = bounds["Width"]?.doubleValue,
              let height = bounds["Height"]?.doubleValue,
              width > 120, height > 120 else { continue }
        let area = width * height
        if area > largestArea {
            largest = info
            largestArea = area
        }
    }
    return largest
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

func motion(_ name: String, process: Process, change: () throws -> Void) throws {
    guard let info = visibleWindow(process.processIdentifier),
          let number = info[kCGWindowNumber as String] as? NSNumber else {
        throw Failure(description: "No window for transition capture")
    }
    // Keep the WindowServer sampling canvas stable while an inspector resizes the window.
    let canvas = CGDisplayBounds(CGMainDisplayID())
    let path = output.appendingPathComponent(name + ".gif")
    let count = 16
    guard let destination = CGImageDestinationCreateWithURL(path as CFURL, "com.compuserve.gif" as CFString, count, nil) else {
        throw Failure(description: "Cannot create transition image")
    }
    CGImageDestinationSetProperties(destination, [kCGImagePropertyGIFDictionary: [kCGImagePropertyGIFLoopCount: 0]] as CFDictionary)
    let start = ProcessInfo.processInfo.systemUptime
    var times = [Double]()
    for index in 0..<count {
        if index == 1 { try change() }
        guard process.isRunning, let image = CGWindowListCreateImage(canvas, .optionIncludingWindow, CGWindowID(number.uint32Value), [.boundsIgnoreFraming, .bestResolution]) else {
            throw Failure(description: "Transition capture failed")
        }
        times.append(ProcessInfo.processInfo.systemUptime - start)
        CGImageDestinationAddImage(destination, image, [kCGImagePropertyGIFDictionary: [kCGImagePropertyGIFDelayTime: 0.05]] as CFDictionary)
        try pause(0.05)
    }
    guard CGImageDestinationFinalize(destination) else { throw Failure(description: "Cannot save transition image") }
    var recordings = report["motion"] as? [[String: Any]] ?? []
    recordings.append(["file": path.lastPathComponent, "frame_times_seconds": times,
                       "canvas_points": NSStringFromRect(canvas),
                       "scope": "WindowServer frames; GIF is for motion, original PNGs are the color reference"])
    report["motion"] = recordings
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

    try selectPage("Media", session: session)
    let playable: (String) -> Bool = { value in
        ["Ready ", "Playing ", "Paused ", "Buffering "].contains { value.hasPrefix($0) }
    }
    _ = try waitForValue(session, suffix: ".featured", role: "video", description: "Initial featured clip is playable", matching: playable)
    try pause(0.3)
    try capture("video-ready-light", process: process, session: session)
    let damaged = try control(inspect(session), suffix: ".damaged", role: "button")
    _ = try cli(["ui", "activate", "--target", damaged["target"] as! String], session: session)
    _ = try waitForValue(session, suffix: ".featured", role: "video", description: "Damaged clip reaches failed state") {
        $0.hasPrefix("Failed ")
    }
    try pause(0.3)
    try capture("video-failed-light", process: process, session: session)
    let pattern = try control(inspect(session), suffix: ".pattern", role: "button")
    _ = try cli(["ui", "activate", "--target", pattern["target"] as! String], session: session)
    _ = try waitForValue(session, suffix: ".featured", role: "video", description: "Featured clip recovers after replacing damaged source", matching: playable)
    try pause(0.3)
    try capture("video-recovered-light", process: process, session: session)
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
    guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 14 else {
        throw Failure(description: "Reference capture must run on macOS 14")
    }
    let permission = CGPreflightScreenCaptureAccess()
    report["screen_recording_preflight"] = permission
    try save()
    guard permission else {
        throw Failure(description: "CGPreflightScreenCaptureAccess=false: runner Screen Recording permission unavailable; no TCC changes or screenshot fallback")
    }
    for appearance in ["light", "dark"] {
        let ipc = URL(fileURLWithPath: "/tmp/bern-reference-\(getpid())-\(appearance)", isDirectory: true)
        try files.createDirectory(at: ipc, withIntermediateDirectories: true, attributes: [.posixPermissions: 0o700])
        environment["BERN_IPC_DIR"] = ipc.path; environment["BERN_APPEARANCE"] = appearance
        environment.removeValue(forKey: "BERN_SNAPSHOT_DIR")
        let process = Process(); process.executableURL = appURL.appendingPathComponent("Contents/MacOS/" + product)
        process.arguments = ["-AppleLanguages", "(en)", "-AppleLocale", "en_US"]
        process.environment = environment
        let appLog = try logHandle("\(appearance)-application.log")
        process.standardOutput = appLog; process.standardError = appLog
        try process.run()
        defer { stop(process); appLog.closeFile(); try? files.removeItem(at: ipc) }
        let ready = Date().addingTimeInterval(18)
        var session: String?
        while session == nil && Date() < ready && process.isRunning {
            if let entries = try cli(["sessions"], allowFailure: true) as? [[String: Any]], entries.count == 1 {
                session = entries[0]["session_id"] as? String
            }
            try pause(0.15)
        }
        guard let session = session else { throw Failure(description: "Application did not register exactly one UI session") }
        NSRunningApplication(processIdentifier: process.processIdentifier)?.activate(options: [.activateAllWindows, .activateIgnoringOtherApps])
        _ = try cli(["ui", "set-language", "--language", "en"], session: session)
        let listed = try cli(["window", "list"], session: session) as? [[String: Any]] ?? []
        let main = listed.filter { $0["kind"] as? String == "main" }
        guard main.count == 1, let identifier = main[0]["window"] as? String else {
            throw Failure(description: "window.list did not identify exactly one main window")
        }
        _ = try cli(["window", "resize", "--window", identifier, "--width", "920", "--height", "668"], session: session)
        let sidebar = try control(inspect(session), suffix: ".pages", role: "sidebar")
        if product == "Gallery" {
            try pause(0.8)
            try capture("gallery-patterns-\(appearance)", process: process, session: session)
            let toggle = try control(inspect(session), suffix: ".show_details", role: "switch")
            try motion("gallery-inspector-\(appearance)", process: process) {
                _ = try cli(["ui", "set-bool", "--target", toggle["target"] as! String, "--value", "true"], session: session)
            }
            try capture("gallery-inspector-\(appearance)", process: process, session: session)
            _ = try cli(["ui", "set-bool", "--target", toggle["target"] as! String, "--value", "false"], session: session)
            _ = try cli(["ui", "select", "--target", sidebar["target"] as! String, "--option", "Film"], session: session)
            try pause(1)
            try capture("gallery-film-\(appearance)", process: process, session: session)
            let last = try control(inspect(session), suffix: ".to_last", role: "button")
            try motion("gallery-scroll-last-\(appearance)", process: process) {
                _ = try cli(["ui", "activate", "--target", last["target"] as! String], session: session)
            }
            try capture("gallery-film-last-\(appearance)", process: process, session: session)
            continue
        }
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
    report["success"] = true
    try save()
} catch {
    report["success"] = false; report["failure"] = String(describing: error)
    try? save()
    fputs("reference capture failed: \(error)\n", stderr)
    exit(1)
}
