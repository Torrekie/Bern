// One external e48/macOS13 Film direct -> first Last capture. Sources only until root review.
// Own-PID heartbeat is inherited metadata/event delivery, not physical mouse/keyboard acceptance.
import AppKit
import ApplicationServices
import CoreGraphics
import CryptoKit
import Darwin
import Foundation
import ImageIO

struct Failure: Error, CustomStringConvertible { let description: String }
func require(_ condition: Bool, _ message: String) throws { if !condition { throw Failure(description: message) } }
func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func rect(_ r: CGRect) -> [String: Double] { ["x":r.minX,"y":r.minY,"width":r.width,"height":r.height] }
func integer(_ value: Any?) -> Int64? { (value as? String).flatMap(Int64.init) ?? (value as? NSNumber)?.int64Value }
guard CommandLine.arguments.count == 4 else {
    fputs("usage: FilmFirstLast APP CLI OUTPUT\n",stderr); exit(2)
}
let appURL = URL(fileURLWithPath:CommandLine.arguments[1]).standardizedFileURL
let cliURL = URL(fileURLWithPath:CommandLine.arguments[2])
let output = URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
let fm = FileManager.default, began = Date(), deadline = Date().addingTimeInterval(75)
let uptimeDeadline = ProcessInfo.processInfo.systemUptime + 75
let originalApplication = NSWorkspace.shared.frontmostApplication
let originalFront = originalApplication?.processIdentifier
let trusted = AXIsProcessTrusted(), observation = "active", expectedOS = 13
let requestedLocalEvents = ProcessInfo.processInfo.environment["BERN_FRAME_LOCAL_EVENTS"] ?? ""
let sendsHeartbeat = requestedLocalEvents == "own-pid-active13"
var env = ProcessInfo.processInfo.environment, process: Process?, timer: Timer?, heartbeatError: String?, mainID: CGWindowID = 0
let filmObservationDestination = env.removeValue(forKey:"BERN_FILM_LAST_OBSERVER_DESTINATION")
var session = "", commands = [[String:Any]](), stages = [[String:Any]](), events = [[String:Any]](), activationRequests = [[String:Any]]()
var inactiveCaptureSamples = [[String:Any]]()
let ciRunID = env["GITHUB_RUN_ID"] ?? "local"
guard let executableURL = Bundle.main.executableURL else { fputs("Collector executable identity unavailable\n",stderr); exit(1) }
let collectorExecutableSHA256: String
do { collectorExecutableSHA256 = sha(try Data(contentsOf:executableURL.resolvingSymlinksInPath())) }
catch { fputs("Collector executable read failed: \(error)\n",stderr); exit(1) }
var report: [String:Any] = ["schema":1,"kind":"film_first_last13_capture","label":"film-first-last","success":false,
    "source_sha":"e48fff46b3a92a28465ad74295bd273a9d69af7d","expected_os":13,"expected_os_major":13,
    "ci_run_id":ciRunID,"collector_executable_sha256":collectorExecutableSHA256,
    "harness_sha":env["GITHUB_SHA"] ?? "local","os":ProcessInfo.processInfo.operatingSystemVersionString,
    "deadline_seconds":75,"deadline_wall_time":deadline.timeIntervalSince1970,"deadline_uptime_seconds":uptimeDeadline,
    "scenario":"direct","followup_sequence":"first-last-only","observation_mode":"local-own-active13",
    "interaction_scope":"Existing generated CLI only; inherited own-PID active mouseMoved heartbeat. No physical input or internal scroll state claim.",
    "sampling_scope":"Two Film terminal AX walks after stable PNG; no first-second observation loop. AX screen coordinates and capture origin retained separately; not atomic.",
    "heartbeat_ci_only":false,"heartbeat_mode":"local-own-active13","local_events_requested":requestedLocalEvents,
    "frontmost_before":originalFront ?? 0,"accessibility_trusted":trusted,"screen_recording":CGPreflightScreenCaptureAccess(),"post_event_access":CGPreflightPostEventAccess(),
    "system_preferences":["reduce_motion":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,"reduce_transparency":NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,"increase_contrast":NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
    "row_ledger_enabled":false,"scroll_trace_enabled":false,
    "displays":NSScreen.screens.map { ["frame_points":rect($0.frame),"scale":$0.backingScaleFactor,"color_space":$0.colorSpace?.localizedName ?? "unknown"] as [String:Any] }]
try fm.createDirectory(at:output,withIntermediateDirectories:true)
let ipc = URL(fileURLWithPath:"/tmp/bern-frame-\(getpid())-\(UUID().uuidString)",isDirectory:true)
func save() throws {
    report["commands"] = commands; report["stages"] = stages; report["heartbeat_events"] = events; report["activation_requests"] = activationRequests
    try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"),options:.atomic)
}
func now() -> Double { ProcessInfo.processInfo.systemUptime }
func frontState(_ ownPID: pid_t) -> [String: Any] {
    let front = NSWorkspace.shared.frontmostApplication
    return ["uptime": now(), "own_pid": ownPID,
        "front_pid": front.map { $0.processIdentifier as Any } ?? NSNull(),
        "front_bundle": front?.bundleIdentifier as Any? ?? NSNull()]
}
func requestActivation(_ pid: pid_t, options: NSApplication.ActivationOptions, names: [String], reason: String) {
    let before = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
    let accepted = NSRunningApplication(processIdentifier:pid)?.activate(options:options) ?? false
    activationRequests.append(["elapsed":Date().timeIntervalSince(began),"requested_pid":pid,"reason":reason,"options":names,"accepted":accepted,
        "frontmost_before":before,"frontmost_immediately_after":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
    try? save()
}
func healthy(_ active: Bool = true) throws {
    try require(Date() < deadline,"Observer exceeded 75 seconds")
    if let error = heartbeatError { throw Failure(description:error) }
    if let p = process { try require(p.isRunning,"Gallery exited"); if active { try require(NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier,"Target lost foreground; no further events will be sent") } }
}
func pause(_ seconds: Double, active: Bool = true) throws {
    let end = Date().addingTimeInterval(seconds)
    repeat { try healthy(active); RunLoop.current.run(until:Date().addingTimeInterval(0.02)) } while Date() < end
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
    p.environment = env; p.standardOutput = out; p.standardError = err
    let start = now(), callDeadline = min(uptimeDeadline, min(cutoff ?? uptimeDeadline, now() + 8)); try p.run(); defer { if p.isRunning { kill(p.processIdentifier,SIGKILL) } }
    while p.isRunning || (observe != nil && now() - start < 1) {
        if now() >= callDeadline {
            if p.isRunning { kill(p.processIdentifier, SIGKILL); p.waitUntilExit() }
            commands.append(["arguments": p.arguments ?? [], "start_uptime": start, "end_uptime": now(),
                "deadline_uptime": callDeadline, "timeout": true, "stdout": stem + "-stdout.json", "stderr": stem + "-stderr.txt"])
            try save()
            throw Failure(description: "CLI exceeded its bounded deadline")
        }
        if now() - start < 1 { observe?() }
        try pause(0.03,active:process == nil || mainID != 0)
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
func ownWindows() -> [[String:Any]] {
    (CGWindowListCopyWindowInfo([.optionOnScreenOnly,.excludeDesktopElements],kCGNullWindowID) as? [[String:Any]] ?? []).filter {
        ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == process?.processIdentifier && (($0[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) > 0
    }
}
func windowID(_ w: [String:Any]) -> CGWindowID { (w[kCGWindowNumber as String] as? NSNumber)?.uint32Value ?? 0 }
func bounds(_ w: [String:Any]) -> CGRect {
    guard let d = w[kCGWindowBounds as String] as? NSDictionary else { return .zero }; return CGRect(dictionaryRepresentation:d) ?? .zero
}
func heartbeat() {
    guard sendsHeartbeat, heartbeatError == nil, let p = process, p.isRunning else { return }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier,
          let w = ownWindows().first(where:{ windowID($0) == mainID }) else { heartbeatError = "Own target lost foreground/window; heartbeat stopped"; return }
    let r = bounds(w), point = CGPoint(x:r.midX,y:r.midY), local = CGPoint(x:r.width/2,y:r.height/2)
    guard r.width > 0, r.height > 0, (w[kCGWindowIsOnscreen as String] as? NSNumber)?.boolValue == true,
          ((w[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 else { heartbeatError = "Own active main window is not fully visible; heartbeat stopped"; return }
    guard let native = NSEvent.mouseEvent(with:.mouseMoved,location:local,modifierFlags:[],timestamp:ProcessInfo.processInfo.systemUptime,
        windowNumber:Int(mainID),context:nil,eventNumber:0,clickCount:0,pressure:0), let e = native.cgEvent else { heartbeatError = "Cannot construct window-associated NSEvent heartbeat"; return }
    let nativeWindow = native.windowNumber
    e.location = point
    e.setIntegerValueField(.mouseEventWindowUnderMousePointer,value:Int64(mainID))
    e.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent,value:Int64(mainID))
    e.setIntegerValueField(.eventTargetUnixProcessID,value:Int64(p.processIdentifier))
    let roundTripWindow = NSEvent(cgEvent:e)?.windowNumber
    var event: [String:Any] = ["elapsed":Date().timeIntervalSince(began),"pid":p.processIdentifier,"window_id":mainID,"window_fields":[e.getIntegerValueField(.mouseEventWindowUnderMousePointer),e.getIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent)],
        "nsevent_window_number":nativeWindow,"roundtrip_nsevent_window_number":roundTripWindow ?? -1,"window_bounds_points":rect(r),"point_window_local":[local.x,local.y],"point_screen_top_left":[e.location.x,e.location.y],"sent":false]
    guard nativeWindow == Int(mainID), roundTripWindow == Int(mainID) else { events.append(event); heartbeatError = "NSEvent windowNumber was not preserved through CGEvent conversion; heartbeat not sent"; return }
    // Window metadata is only a precondition; delivery must still pass the real idle gate.
    e.postToPid(p.processIdentifier)
    event["sent"] = true; events.append(event)
}

func terminalAX(_ root: AXUIElement, state: String, capture: [String:Any]) throws -> [String:Any] {
    let sample = axSample(root,timeBudget:2)
    report["incomplete_terminal_ax"] = ["state":state,"capture":capture,"ax":sample]
    try require(sample["truncated"] as? Bool == false,"Terminal AX walk truncated")
    let rows = sample["elements"] as? [[String:Any]] ?? []
    let names: Set<String> = ["Gingham","Tartan","Madras","Glen","Houndstooth","Windowpane"]
    let images = rows.filter { $0["role"] as? String == kAXImageRole as String && names.contains($0["text"] as? String ?? "") }
    try require(images.count == 6 && Set(images.compactMap { $0["text"] as? String }) == names,"Terminal AX needs exactly six unique pattern images")
    for image in images {
        guard let f = image["frame"] as? [String:Any], let x = (f["x"] as? NSNumber)?.doubleValue,
              let y = (f["y"] as? NSNumber)?.doubleValue, let w = (f["width"] as? NSNumber)?.doubleValue,
              let h = (f["height"] as? NSNumber)?.doubleValue,
              [x,y,w,h].allSatisfy({ $0.isFinite }), w > 0, h > 0 else { throw Failure(description:"Incomplete/nonfinite terminal image frame") }
    }
    report.removeValue(forKey:"incomplete_terminal_ax")
    return sample
}
func checkedFilmControls() throws -> Any {
    let value = try cli(["ui","inspect"],session) ?? NSNull()
    let rows = value as? [[String:Any]] ?? []
    let pages = rows.filter { ($0["target"] as? String)?.hasSuffix(".pages") == true && $0["enabled"] as? Bool == true }
    try require(pages.count == 1 && pages[0]["value"] as? String == "Film","Film page/context changed")
    return value
}
func run() -> Int32 {
defer {
    timer?.invalidate()
    report["local_cleanup_adapter"] = "kernel_guard_before_stop_v1"
    report["ipc_directory"] = ipc.path
    do {
        if let p = process, p.isRunning {
            guard let guardPath = env["BERN_PICTURE_FOCUS_GUARD"],
                  let frontPath = env["BERN_PICTURE_WATCHDOG_FRONT"] else { throw Failure(description:"Missing independent kernel guard handoff") }
            let outerData = try Data(contentsOf:URL(fileURLWithPath:frontPath))
            guard let captured = originalApplication, !captured.isTerminated,
                  let outer = try JSONSerialization.jsonObject(with:outerData) as? [String:Any],
                  integer(outer["pid"]) == Int64(originalFront ?? 0),
                  integer(outer["pid"]) == Int64(captured.processIdentifier),
                  outer["bundle_id"] as? String == captured.bundleIdentifier,
                  outer["executable_path"] as? String == captured.executableURL?.resolvingSymlinksInPath().path,
                  let kernel = outer["kernel_start"] as? [String:Any],
                  let seconds = integer(kernel["tv_sec"]), seconds > 0,
                  let micros = integer(kernel["tv_usec"]), micros >= 0, micros < 1_000_000 else {
                throw Failure(description:"Captured original application does not match outer strong receipt; no guard cleanup request")
            }
            report["local_original_front_binding"] = ["matched":true,"pid":captured.processIdentifier,
                "outer_front_receipt_sha256":sha(outerData),
                "scope":"Captured NSRunningApplication PID/bundle/path correlated to outer kernel receipt; guard verifies the live kernel identity before any restoration"]
            let owned = output.appendingPathComponent("ownership.json")
            guard let row = try JSONSerialization.jsonObject(with:Data(contentsOf:owned)) as? [String:Any],
                  integer(row["collector_pid"]) == Int64(getpid()), integer(row["pid"]) == Int64(p.processIdentifier),
                  row["executable_path"] as? String == appURL.appendingPathComponent("Contents/MacOS/Gallery").resolvingSymlinksInPath().path,
                  row["bundle_id"] as? String == Bundle(url:appURL)?.bundleIdentifier else { throw Failure(description:"Missing/mismatched outer kernel ownership receipt; own child left for guarded cleanup") }
            let helper = Process(); helper.executableURL = URL(fileURLWithPath:guardPath)
            helper.arguments = ["cleanup",appURL.path,frontPath,owned.path]
            helper.environment = env
            let log = output.appendingPathComponent("cleanup-helper.json"), err = output.appendingPathComponent("cleanup-helper.stderr.txt")
            _ = fm.createFile(atPath:log.path,contents:nil); _ = fm.createFile(atPath:err.path,contents:nil)
            let oh = try FileHandle(forWritingTo:log), eh = try FileHandle(forWritingTo:err)
            defer { oh.closeFile(); eh.closeFile() }
            helper.standardOutput = oh; helper.standardError = eh; try helper.run()
            let until = Date().addingTimeInterval(7)
            while helper.isRunning && Date() < until { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }
            if helper.isRunning { kill(helper.processIdentifier,SIGKILL); throw Failure(description:"Independent kernel guard timed out") }
            guard let receipt = try JSONSerialization.jsonObject(with:Data(contentsOf:log)) as? [String:Any],
                  helper.terminationStatus == 0, receipt["success"] as? Bool == true else { throw Failure(description:"Independent kernel restore-before-stop did not complete") }
            report["kernel_guard_cleanup"] = receipt
            let ended = Date().addingTimeInterval(1)
            while p.isRunning && Date() < ended { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }
        }
    } catch { report["success"] = false; report["cleanup_failure"] = String(describing:error) }
    report["app_still_running_after_cleanup"] = process?.isRunning ?? false
    if process?.isRunning == true { report["success"] = false; report["cleanup_failure"] = report["cleanup_failure"] ?? "Own child still running after guarded cleanup" }
    if let p = process, !p.isRunning { report["app_termination_status"] = p.terminationStatus }
    let guardSucceeded = (report["kernel_guard_cleanup"] as? [String:Any])?["success"] as? Bool == true
    if process == nil || (guardSucceeded && process?.isRunning != true) {
        do {
            if fm.fileExists(atPath:ipc.path) { try fm.removeItem(at:ipc) }
            report["ipc_removed_by_adapter"] = !fm.fileExists(atPath:ipc.path)
        } catch { report["success"] = false; report["ipc_cleanup_failure"] = String(describing:error) }
    } else {
        report["ipc_preserved_for_unverified_cleanup"] = ipc.path
        report["success"] = false
        report["cleanup_failure"] = report["cleanup_failure"] ?? "No successful exact guarded child cleanup receipt; IPC retained"
    }
    report["elapsed_seconds"] = Date().timeIntervalSince(began)
    report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
    do { try save() } catch { report["success"] = false; fputs("Final local report save failed: \(error)\n",stderr) }
}
do {
    try save()
    try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == 13,"macOS13 only")
    try require(env["CI"] != "true" && env["GITHUB_ACTIONS"] != "true" && ciRunID == "local","Local collector cannot impersonate CI")
    try require(env["BERN_SOURCE_SHA"] == "e48fff46b3a92a28465ad74295bd273a9d69af7d","Exact original e48 source handoff required")
    try require(env["BERN_FRAME_ROW_LEDGER_OUTPUT_DIR"] == nil && env["BERN_SCROLL_TRACE_DIR"] == nil,"No row ledger or scroll trace allowed")
    try require(sendsHeartbeat,"Explicit own-pid-active13 required")
    try require(trusted && CGPreflightScreenCaptureAccess() && CGPreflightPostEventAccess(),"Existing AX/Screen Recording/PostEvent access required; no TCC changes")
    try require(!NSWorkspace.shared.accessibilityDisplayShouldReduceMotion && !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency && !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast,"Ordinary profile required")
    try require(appURL.lastPathComponent == "Gallery.app" && fm.isExecutableFile(atPath:cliURL.path),"Supplied Gallery and CLI required")
    guard let guardPath = env["BERN_PICTURE_FOCUS_GUARD"], fm.isExecutableFile(atPath:guardPath),
          let frontPath = env["BERN_PICTURE_WATCHDOG_FRONT"], fm.fileExists(atPath:frontPath) else { throw Failure(description:"Outer kernel guard/front handoff required before UI") }
    try fm.createDirectory(at:ipc,withIntermediateDirectories:false,attributes:[.posixPermissions:0o700]); env["BERN_IPC_DIR"] = ipc.path; env["BERN_APPEARANCE"] = "light"
    for key in ["BERN_SNAPSHOT_DIR","BERN_MOTION"] { env.removeValue(forKey:key) }
    report["app_executable_sha256"] = sha(try Data(contentsOf:appURL.appendingPathComponent("Contents/MacOS/Gallery")))
    report["cli_sha256"] = sha(try Data(contentsOf:cliURL))
    var appEnvironment = env
    appEnvironment["BERN_FILM_LAST_OBSERVATION_FILE"] = filmObservationDestination
    let p = Process(); p.executableURL = appURL.appendingPathComponent("Contents/MacOS/Gallery"); p.arguments = ["-AppleLanguages","(en)","-AppleLocale","en_US"]; p.environment = appEnvironment
    let log = output.appendingPathComponent("application.log"); _ = fm.createFile(atPath:log.path,contents:nil); let logHandle = try FileHandle(forWritingTo:log); defer { logHandle.closeFile() }
    p.standardOutput = logHandle; p.standardError = logHandle; try p.run(); process = p
    let ready = min(uptimeDeadline,now()+18)
    repeat { if let s = try cli(["sessions"],allowFailure:true,until:ready) as? [[String:Any]], s.count == 1 { session = s[0]["session_id"] as? String ?? "" }; if session.isEmpty { try pause(0.1,active:false) } } while session.isEmpty && p.isRunning && now() < ready
    try require(!session.isEmpty,"Expected one UI session")
    var startup = [[String:Any]](), startupID: CGWindowID = 0
    while p.isRunning && now() < ready {
        let rows = try cli(["window","list"],session,allowFailure:true,until:ready) as? [[String:Any]] ?? []
        let mains = rows.filter { $0["kind"] as? String == "main" }
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        startup.append(["elapsed":Date().timeIntervalSince(began),"deadline_uptime":ready,"pid":p.processIdentifier,"windows":rows,"native_candidates":native])
        report["startup_readiness"] = startup; try save()
        if now() < ready, mains.count == 1, native.count == 1, ((native[0][kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 { startupID = windowID(native[0]); break }
        try pause(min(0.08,max(0,ready-now())),active:false)
    }
    try require(startupID != 0,"Startup main registry/unique visible own CG window unavailable within18s; CLI cap8s")
    requestActivation(p.processIdentifier,options:[.activateAllWindows,.activateIgnoringOtherApps],names:["activateAllWindows","activateIgnoringOtherApps"],reason:"own-gallery-after-startup-ready")
    for _ in 0..<40 {
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier, native.count == 1, windowID(native[0]) == startupID { mainID = startupID; break }
        try pause(0.05,active:false)
    }
    try require(mainID != 0,"No frontmost Gallery main window matching the startup window"); heartbeat(); timer = Timer.scheduledTimer(withTimeInterval:0.5,repeats:true) { _ in heartbeat() }
    _ = try cli(["ui","set-language","--language","en"],session)
    _ = try cli(["ui","activate","--target",target(session,suffix:".light")],session)
    let state = try cli(["state"]) as? [String:Any] ?? [:]
    try require((state["values"] as? [String:Any])?["appearance"] as? String == "Light","Light appearance did not commit")
    let windows = try cli(["window","list"],session) as? [[String:Any]] ?? []
    try require(windows.count == 1,"No unique main session window")
    guard let main = windows[0]["window"] as? String else { throw Failure(description:"Missing main window ID") }
    _ = try cli(["window","resize","--window",main,"--width","920","--height","668"],session)
    let pages = try target(session,suffix:".pages")
    let root = AXUIElementCreateApplication(p.processIdentifier); AXUIElementSetMessagingTimeout(root,0.04)
    report["setup_patterns"] = try stable(p.processIdentifier,name:"setup-patterns")
    let selected = now()
    _ = try cli(["ui","select","--target",pages,"--option","Film"],session)
    report["select_start_uptime"] = selected; report["select_return_uptime"] = now()
    let initial = try stable(p.processIdentifier,name:"direct-film")
    let initialAX = try terminalAX(root,state:"initial",capture:initial)
    let initialControls = try checkedFilmControls()
    stages.append(["stage":"initial","pid":p.processIdentifier,"session":session,"capture":initial,"ax":initialAX,"controls":initialControls,
        "coordinate_scope":"Raw AX screen points; separate capture bounds_points origin; AX walk follows PNG, not atomic."])
    try save()
    let started = now()
    _ = try cli(["ui","activate","--target",target(session,suffix:".to_last")],session)
    let returned = now()
    let last = try stable(p.processIdentifier,name:"direct-last")
    let lastAX = try terminalAX(root,state:"last",capture:last)
    stages.append(["stage":"last","pid":p.processIdentifier,"session":session,"action_start_uptime":started,"action_return_uptime":returned,
        "capture":last,"ax":lastAX,"controls":try checkedFilmControls(),"windows":try cli(["window","list"],session) ?? NSNull(),
        "coordinate_scope":"Raw AX screen points; separate capture bounds_points origin; AX walk follows PNG, not atomic."])
    report["final_context"] = ["appearance":"Light","page":"Film","requested_action":"first Last only","terminal_states":2]
    report["success"] = true; try save()
} catch { report["failure"] = String(describing:error); try? save(); fputs("Film FirstLast failed: \(error)\n",stderr); return 1 }
return 0
}
let runStatus = run()
exit(runStatus == 0 && report["success"] as? Bool == true && report["app_still_running_after_cleanup"] as? Bool == false ? 0 : 1)
