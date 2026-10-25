// External observer only. APP CLI OUTPUT EXPECTED_OS LABEL SOURCE_SHA; no app injection or TCC changes.
// Explicit local13/CI heartbeats are own-active-PID mouseMoved events, not physical mouse acceptance.
import AppKit
import ApplicationServices
import CoreGraphics
import CryptoKit
import Foundation
import ImageIO

struct Failure: Error, CustomStringConvertible { let description: String }
func require(_ condition: Bool, _ message: String) throws { if !condition { throw Failure(description: message) } }
func sha(_ data: Data) -> String { SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined() }
func rect(_ r: CGRect) -> [String: Double] { ["x":r.minX,"y":r.minY,"width":r.width,"height":r.height] }
func integer(_ value: Any?) -> Int64? { (value as? String).flatMap(Int64.init) ?? (value as? NSNumber)?.int64Value }
guard CommandLine.arguments.count == 7, let expectedOS = Int(CommandLine.arguments[4]), [13,14].contains(expectedOS) else {
    fputs("usage: gallery-frame-reference.swift APP CLI OUTPUT EXPECTED_OS LABEL SOURCE_SHA\n", stderr); exit(2)
}
let appURL = URL(fileURLWithPath: CommandLine.arguments[1]).standardizedFileURL
let cliURL = URL(fileURLWithPath: CommandLine.arguments[2]), output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory:true)
let fm = FileManager.default, began = Date(), deadline = Date().addingTimeInterval(75)
let originalApplication = NSWorkspace.shared.frontmostApplication
let originalFront = originalApplication?.processIdentifier
let ciHeartbeat = ProcessInfo.processInfo.environment["GITHUB_ACTIONS"] == "true" && ProcessInfo.processInfo.environment["CI"] == "true"
let requestedLocalEvents = ProcessInfo.processInfo.environment["BERN_FRAME_LOCAL_EVENTS"] ?? ""
let localOwnActive13 = expectedOS == 13 && !ciHeartbeat && requestedLocalEvents == "own-pid-active13"
let sendsHeartbeat = ciHeartbeat || localOwnActive13
var env = ProcessInfo.processInfo.environment, process: Process?, timer: Timer?, heartbeatError: String?, mainID: CGWindowID = 0
var activationRequests = [[String:Any]]()
var session = "", specs = [[String:Any]](), commands = [[String:Any]](), stages = [[String:Any]](), captures = [[String:Any]](), events = [[String:Any]]()
var inspectedControls = [[String:Any]]()
let ledgerPath = ProcessInfo.processInfo.environment["BERN_FRAME_ROW_LEDGER_OUTPUT_DIR"]
var ledgerToken: String?
func ledgerLogHasError() throws -> Bool {
    guard ledgerPath != nil else { return false }
    let file = output.appendingPathComponent("application.log")
    let attributes = try fm.attributesOfItem(atPath:file.path)
    try require(((attributes[.size] as? NSNumber)?.intValue ?? Int.max) <= 262144,"Application log exceeds bounded ledger error check")
    return try Data(contentsOf:file).range(of:Data("BERN_FRAME_ROW_LEDGER_IO_ERROR".utf8)) != nil
}
func armRowLedger() throws {
    guard let path = ledgerPath, let p = process else { return }
    let folder = URL(fileURLWithPath:path,isDirectory:true).standardizedFileURL
    try require(path.hasPrefix("/") && folder.resolvingSymlinksInPath() == folder && folder == output.appendingPathComponent("ledger",isDirectory:true).standardizedFileURL,"Ledger directory must be fresh OUTPUT/ledger")
    try require(try fm.contentsOfDirectory(atPath:folder.path).isEmpty,"Ledger directory must start empty")
    let token = UUID().uuidString
    let packet: [String:Any] = ["schema":"bern_frame_row_arm_v1","pid":p.processIdentifier,"stage":"frame-closed-light","token":token,"armed_uptime_seconds":ProcessInfo.processInfo.systemUptime]
    try JSONSerialization.data(withJSONObject:packet,options:[.sortedKeys]).write(to:folder.appendingPathComponent("frame-row-ledger.arm.json"),options:.withoutOverwriting)
    ledgerToken = token; report["row_ledger_arm"] = packet; try save()
}
func finishRowLedger() throws {
    guard let path = ledgerPath, let token = ledgerToken, let p = process else { report["row_ledger_enabled"] = false; return }
    try require(!(try ledgerLogHasError()),"Ledger reported an I/O error; prior file prefix is not accepted")
    let file = URL(fileURLWithPath:path,isDirectory:true).appendingPathComponent("frame-row-ledger-\(p.processIdentifier).json")
    let attributes = try fm.attributesOfItem(atPath:file.path)
    try require(attributes[.type] as? FileAttributeType == .typeRegular && ((attributes[.size] as? NSNumber)?.intValue ?? Int.max) <= 65536,"Missing regular bounded row ledger")
    let data = try Data(contentsOf:file)
    guard let packet = try JSONSerialization.jsonObject(with:data) as? [String:Any], let rows = packet["placements"] as? [[String:Any]], let stage = packet["stage"] as? [String:Any], let last = rows.last, let capture = captures.last else { throw Failure(description:"Incomplete row ledger") }
    try require(packet["schema"] as? String == "bern_frame_row_ledger_v1" && integer(packet["pid"]) == Int64(p.processIdentifier) && packet["diagnostic_id"] as? String == "gallery.frame.controls","Ledger identity mismatch")
    try require(packet["truncated"] as? Bool == false && packet["end_state"] as? String == "not_observed" && rows.count > 0 && rows.count <= 64 && integer(packet["complete_placement_count"]) == Int64(rows.count),"Missing/truncated row placements")
    try require(stage["token"] as? String == token && stage["stage"] as? String == "frame-closed-light" && integer(stage["pid"]) == Int64(p.processIdentifier),"Ledger arm mismatch")
    guard let arm = report["row_ledger_arm"] as? [String:Any], let armed = arm["armed_uptime_seconds"] as? Double, let imageBegan = capture["sample_begin_uptime_seconds"] as? Double, let completed = last["place_completed_uptime_seconds"] as? Double else { throw Failure(description:"Missing ledger/capture uptime") }
    try require(rows.allSatisfy { ($0["place_entered_uptime_seconds"] as? Double ?? -.infinity) >= armed && $0["on_main_thread"] as? Bool == true } && completed <= imageBegan,"Ledger does not precede actual stable image sample")
    report["row_ledger_enabled"] = true
    report["row_ledger"] = ["file":file.lastPathComponent,"sha256":sha(data),"bytes":data.count,"token":token,"complete_placement_count":rows.count,"last_complete_uptime_seconds":completed,"stable_image_sample_begin_uptime_seconds":imageBegan,"end_state":"not_observed","scope":"complete original placements preceding the stable image; not a presentation synchronization fence"]
    try save()
}
var volumeTarget = "", clipTarget = "", sliderTarget = "", playerID = "", sourceURL = "", sourceVersion: Int64?
var report: [String:Any] = ["schema":1,"success":false,"label":CommandLine.arguments[5],"source_sha":CommandLine.arguments[6],
    "harness_sha":env["GITHUB_SHA"] ?? "local","expected_os":expectedOS,"os":ProcessInfo.processInfo.operatingSystemVersionString,
    "deadline_seconds":75,"deadline_wall_time":deadline.timeIntervalSince1970,"frontmost_restore_rule":"Request immediate original live application before stopping own child, only while own Gallery remains frontmost; preserve a changed foreground",
    "app":appURL.path,"interaction_scope":"Generated CLI only; explicit local13/CI own-active-PID mouseMoved keeps Frame awake. Closed Frame only; no AXPress or physical input claim.",
    "heartbeat_ci_only":ciHeartbeat,"heartbeat_mode":sendsHeartbeat ? (localOwnActive13 ? "local-own-active13" : "ci-own-active") : "disabled","local_events_requested":requestedLocalEvents,"frontmost_before":originalFront ?? 0,"accessibility_trusted":AXIsProcessTrusted(),
    "screen_recording":CGPreflightScreenCaptureAccess(),"post_event_access":CGPreflightPostEventAccess(),
    "system_preferences":["reduce_motion":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,"reduce_transparency":NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,"increase_contrast":NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
    "displays":NSScreen.screens.map { ["frame_points":rect($0.frame),"scale":$0.backingScaleFactor,"color_space":$0.colorSpace?.localizedName ?? "unknown"] as [String:Any] },
    "geometry_scope":"Public AX roles/frames and WindowServer windows; AX does not identify the Cocoa view class."]
try fm.createDirectory(at:output,withIntermediateDirectories:true)
let ipc = URL(fileURLWithPath:"/tmp/bern-frame-\(getpid())-\(UUID().uuidString)",isDirectory:true)
func save() throws {
    report["commands"] = commands; report["stages"] = stages; report["captures"] = captures; report["heartbeat_events"] = events; report["activation_requests"] = activationRequests
    try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"),options:.atomic)
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
func cli(_ words: [String], session scoped: Bool = false, allowFailure: Bool = false, until stopAt: Date? = nil) throws -> Any {
    let stem = String(format:"%03d",commands.count+1), out = output.appendingPathComponent(stem+"-stdout.json"), err = output.appendingPathComponent(stem+"-stderr.txt")
    _ = fm.createFile(atPath:out.path,contents:nil); _ = fm.createFile(atPath:err.path,contents:nil)
    let oh = try FileHandle(forWritingTo:out), eh = try FileHandle(forWritingTo:err); defer { oh.closeFile(); eh.closeFile() }
    let p = Process(); p.executableURL = cliURL; p.arguments = (scoped ? ["--session",session] : []) + words; p.environment = env
    p.standardOutput = oh; p.standardError = eh; try p.run(); defer { if p.isRunning { kill(p.processIdentifier,SIGKILL) } }; let end = min(min(deadline,Date().addingTimeInterval(8)),stopAt ?? deadline)
    while p.isRunning && Date() < end { try pause(0.02,active:process == nil || mainID != 0) }
    if p.isRunning { kill(p.processIdentifier,SIGKILL); throw Failure(description:"CLI timeout: \(words)") }
    commands.append(["arguments":p.arguments ?? [],"status":p.terminationStatus,"stdout":out.lastPathComponent,"stderr":err.lastPathComponent]); try save()
    if p.terminationStatus != 0 { if allowFailure { return NSNull() }; throw Failure(description:"CLI failed: \(words); see \(err.lastPathComponent)") }
    let data = try Data(contentsOf:out); return data.isEmpty ? NSNull() : try JSONSerialization.jsonObject(with:data,options:.fragmentsAllowed)
}
func command(_ id: String, _ params: [String:String] = [:], scoped: Bool = false, until stopAt: Date? = nil) throws -> Any {
    let found = specs.filter { $0["id"] as? String == id }; try require(found.count == 1,"Missing/ambiguous catalog command \(id)")
    let spec = found[0], names = (spec["params"] as? [[String:Any]] ?? []).compactMap { $0["name"] as? String }
    guard let words = (spec["external"] as? [String:Any])?["cli"] as? [String] else { throw Failure(description:"Missing CLI catalog words for \(id)") }
    try require(Set(names) == Set(params.keys),"Catalog parameters differ for \(id)")
    return try cli(words + names.flatMap { ["--"+$0.replacingOccurrences(of:"_",with:"-"),params[$0]!] },session:scoped,until:stopAt)
}
func controls(until stopAt: Date? = nil) throws -> [[String:Any]] { inspectedControls = try command("ui.inspect",scoped:true,until:stopAt) as? [[String:Any]] ?? []; return inspectedControls }
func control(_ rows: [[String:Any]], _ suffix: String, _ role: String) throws -> [String:Any] {
    let found = rows.filter { ($0["target"] as? String)?.hasSuffix(suffix) == true && $0["role"] as? String == role }
    try require(found.count == 1 && found.first?["enabled"] as? Bool == true,"Expected one enabled \(role) \(suffix)"); return found[0]
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
func mainWindow() throws -> [String:Any] {
    guard let w = ownWindows().first(where:{ windowID($0) == mainID }) else { throw Failure(description:"Main window is not onscreen") }; return w
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
func attribute(_ e: AXUIElement, _ key: String) -> CFTypeRef? {
    var value: CFTypeRef?; return AXUIElementCopyAttributeValue(e,key as CFString,&value) == .success ? value : nil
}
func axFrame(_ e: AXUIElement) throws -> CGRect {
    guard let p = attribute(e,kAXPositionAttribute), let s = attribute(e,kAXSizeAttribute), CFGetTypeID(p) == AXValueGetTypeID(), CFGetTypeID(s) == AXValueGetTypeID() else { throw Failure(description:"Missing AX geometry") }
    var point = CGPoint.zero, size = CGSize.zero
    try require(AXValueGetValue(p as! AXValue,.cgPoint,&point) && AXValueGetValue(s as! AXValue,.cgSize,&size),"Invalid AX geometry")
    try require(size.width > 0 && size.height > 0,"Empty AX frame"); return CGRect(origin:point,size:size)
}
func axFailure(_ id: String, role: String?, found: Int, visited: Int, queued: Int, hashes: Int) throws {
    guard let p = process else { return }; let root = AXUIElementCreateApplication(p.processIdentifier), end = min(deadline,Date().addingTimeInterval(12))
    let timeoutCode = AXUIElementSetMessagingTimeout(root,0.25).rawValue
    func read(_ e: AXUIElement, _ key: String, _ codes: inout [String:Int32]) -> CFTypeRef? {
        var value: CFTypeRef?; let code = AXUIElementCopyAttributeValue(e,key as CFString,&value); codes[key] = code.rawValue; return code == .success ? value : nil
    }
    func summary(_ e: AXUIElement) -> ([String:Any],[AXUIElement],[AXUIElement],AXUIElement?) {
        var pid: pid_t = 0; let pidCode = AXUIElementGetPid(e,&pid).rawValue
        var node: [String:Any] = ["pid":pid,"pid_code":pidCode], codes = [String:Int32]()
        guard pidCode == 0 && pid == p.processIdentifier else { node["skipped_other_process"] = true; return (node,[],[],nil) }
        for key in [kAXRoleAttribute,kAXSubroleAttribute,kAXIdentifierAttribute,kAXTitleAttribute,kAXDescriptionAttribute] {
            node[key] = (read(e,key,&codes) as? String).map { String($0.prefix(240)) } ?? ""
        }
        let pos = read(e,kAXPositionAttribute,&codes), size = read(e,kAXSizeAttribute,&codes); var point = CGPoint.zero, dimensions = CGSize.zero
        if let pos = pos, let size = size, CFGetTypeID(pos) == AXValueGetTypeID(), CFGetTypeID(size) == AXValueGetTypeID(),
           AXValueGetValue(pos as! AXValue,.cgPoint,&point), AXValueGetValue(size as! AXValue,.cgSize,&dimensions) { node["frame_screen_top_left_points"] = rect(CGRect(origin:point,size:dimensions)) }
        var actions: CFArray?; codes["AXActionNames"] = AXUIElementCopyActionNames(e,&actions).rawValue; node["actions"] = actions as? [String] ?? []
        let children = read(e,kAXChildrenAttribute,&codes) as? [AXUIElement] ?? [], windows = read(e,kAXWindowsAttribute,&codes) as? [AXUIElement] ?? []
        let rawParent = read(e,kAXParentAttribute,&codes), parent = rawParent.flatMap { CFGetTypeID($0) == AXUIElementGetTypeID() ? ($0 as! AXUIElement) : nil }
        node["return_codes"] = codes; node["children_count"] = children.count; node["windows_count"] = windows.count
        return (node,children,windows,parent)
    }
    // This failure-only walk uses CFEqual identities: equal hash values need not identify equal AX objects.
    var queue = [root], index = 0, elements = [AXUIElement](), nodes = [[String:Any]](), childEdges = [[AXUIElement]](), windowEdges = [[AXUIElement]]()
    var matching = [[String:Any]](), collisions = 0, hashBuckets = [CFHashCode:[AXUIElement]](), queueClipped = false
    while index < queue.count && index < 4000 && nodes.count < 512 && Date() < end {
        let e = queue[index]; index += 1; if elements.contains(where:{ CFEqual($0,e) }) { continue }
        let hash = CFHash(e); if let bucket = hashBuckets[hash], bucket.contains(where:{ !CFEqual($0,e) }) { collisions += 1 }; hashBuckets[hash,default:[]].append(e)
        let (details,children,windows,parent) = summary(e); var node = details; node["index"] = nodes.count; node["elapsed"] = Date().timeIntervalSince(began)
        elements.append(e); childEdges.append(children); windowEdges.append(windows)
        if node[kAXIdentifierAttribute] as? String == id {
            var ancestors = [[String:Any]](), current = parent, lineage = [e]
            for _ in 0..<4 {
                guard let a = current, !lineage.contains(where:{ CFEqual($0,a) }), Date() < end else { break }; lineage.append(a)
                let (detail,_,_,next) = summary(a); ancestors.append(detail); current = next
            }
            var target = node, related = [[String:Any]](); target["ancestors"] = ancestors
            for child in children.prefix(32) { if Date() >= end { break }; related.append(summary(child).0); if related.count % 4 == 0 { RunLoop.current.run(until:Date().addingTimeInterval(0.001)) } }
            target["related_children"] = related; target["related_children_truncated"] = children.count > related.count; matching.append(target)
        }
        nodes.append(node); let additions = Array((children+windows).prefix(max(0,4000-queue.count)))
        if additions.count < children.count+windows.count { queueClipped = true }; queue += additions
        if nodes.count % 8 == 0 { RunLoop.current.run(until:Date().addingTimeInterval(0.001)) }
    }
    for i in nodes.indices {
        nodes[i]["children_indices"] = childEdges[i].map { child in elements.firstIndex(where:{ CFEqual($0,child) }) ?? -1 }
        nodes[i]["windows_indices"] = windowEdges[i].map { child in elements.firstIndex(where:{ CFEqual($0,child) }) ?? -1 }
    }
    report["ax_failure"] = ["target":id,"required_role":role ?? "any","found_count":found,"original_visited":visited,"original_queued":queued,"original_unique_hashes":hashes,"original_truncated":visited >= 4000,
        "timeout_set_code":timeoutCode,"diagnostic_visited":index,"diagnostic_nodes":nodes.count,"diagnostic_truncated":queueClipped || index < queue.count,"diagnostic_limits":["nodes":512,"queue":4000,"seconds":12],"hash_collisions_observed":collisions,"matching_identifier_nodes":matching,"tree":nodes]
    try save()
}
func scopedFrameAX(_ id: String, role: String?) throws -> AXUIElement? {
    guard let p = process, !volumeTarget.isEmpty, !clipTarget.isEmpty,
          (id == volumeTarget && role == kAXButtonRole) || (id == clipTarget && role == nil) || (!sliderTarget.isEmpty && id == sliderTarget && role == kAXSliderRole) else { return nil }
    let volume = try control(inspectedControls,".volume","popover_button"), clip = try control(inspectedControls,".clip","video"), page = try control(inspectedControls,".pages","sidebar")
    try require(volume["target"] as? String == volumeTarget && clip["target"] as? String == clipTarget && page["value"] as? String == "Frame","Frame registry identity changed during AX selection")
    guard let volumeLabel = volume["label"] as? String, !volumeLabel.isEmpty, let clipLabel = clip["label"] as? String, !clipLabel.isEmpty else { throw Failure(description:"Frame CLI labels unavailable") }
    func owned(_ e: AXUIElement) -> Bool { var pid: pid_t = 0; return AXUIElementGetPid(e,&pid) == .success && pid == p.processIdentifier }
    func parent(_ e: AXUIElement) -> AXUIElement? { guard let value = attribute(e,kAXParentAttribute), CFGetTypeID(value) == AXUIElementGetTypeID() else { return nil }; return (value as! AXUIElement) }
    func near(_ a: CGRect, _ b: CGRect) -> Bool { abs(a.minX-b.minX)<=1 && abs(a.minY-b.minY)<=1 && abs(a.width-b.width)<=1 && abs(a.height-b.height)<=1 }
    func label(_ e: AXUIElement, _ text: String) -> Bool { attribute(e,kAXDescriptionAttribute) as? String == text || attribute(e,kAXTitleAttribute) as? String == text }
    func actions(_ e: AXUIElement) -> [String] { var value: CFArray?; return AXUIElementCopyActionNames(e,&value) == .success ? value as? [String] ?? [] : [] }
    func walk(_ window: AXUIElement) throws -> [AXUIElement] {
        var queue = [window], index = 0, seen = [AXUIElement](); let end = min(deadline,Date().addingTimeInterval(8))
        while index < queue.count && index < 4000 && seen.count < 512 && Date() < end {
            let e = queue[index]; index += 1; if !owned(e) || seen.contains(where:{ CFEqual($0,e) }) { continue }; seen.append(e)
            queue += attribute(e,kAXChildrenAttribute) as? [AXUIElement] ?? []
            if seen.count % 8 == 0 { RunLoop.current.run(until:Date().addingTimeInterval(0.001)); try healthy() }
        }
        try require(index == queue.count,"Scoped own-window AX walk incomplete"); return seen
    }
    func describe(_ e: AXUIElement) throws -> [String:Any] { ["identifier":attribute(e,kAXIdentifierAttribute) as? String ?? "","role":attribute(e,kAXRoleAttribute) as? String ?? "","description":attribute(e,kAXDescriptionAttribute) as? String ?? "","title":attribute(e,kAXTitleAttribute) as? String ?? "","actions":actions(e),"frame_screen_top_left_points":rect(try axFrame(e))] }
    func selected(_ e: AXUIElement, _ scope: [String:Any]) throws -> AXUIElement {
        var log = report["ax_selector_trace"] as? [[String:Any]] ?? []; log.append(["elapsed":Date().timeIntervalSince(began),"requested_cli_target":id,"method":"scoped_frame_label","native":try describe(e),"scope":scope]); report["ax_selector_trace"] = log; try save(); return e
    }
    let windows = (attribute(AXUIElementCreateApplication(p.processIdentifier),kAXWindowsAttribute) as? [AXUIElement] ?? []).filter { owned($0) && attribute($0,kAXRoleAttribute) as? String == kAXWindowRole }
    let mainBounds = try bounds(mainWindow()), mains = windows.filter { (try? axFrame($0)).map { near($0,mainBounds) } ?? false }
    try require(mains.count == 1,"Cannot match one AXWindow to the own CG main window"); let main = mains[0]
    if id == sliderTarget {
        let row = try control(inspectedControls,".volume_level","slider")
        guard volume["value"] as? String == "open", row["target"] as? String == sliderTarget, let text = row["label"] as? String, !text.isEmpty else { throw Failure(description:"Popup slider CLI identity/label unavailable") }
        var matches = [(AXUIElement,AXUIElement,[String:Any])]()
        for window in windows where !CFEqual(window,main) {
            guard let r = try? axFrame(window) else { continue }
            let cg = ownWindows().filter { windowID($0) != mainID && near(bounds($0),r) && (($0[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 }
            guard cg.count == 1 else { continue }
            for e in try walk(window) where attribute(e,kAXRoleAttribute) as? String == kAXSliderRole && label(e,text) {
                if let f = try? axFrame(e), r.insetBy(dx:-1,dy:-1).contains(f) { matches.append((e,window,cg[0])) }
            }
        }
        try require(matches.count == 1,"Missing/ambiguous labelled AXSlider in a separate owned popup window")
        let m = matches[0]; return try selected(m.0,["relationship":"unique slider inside a separate own popup AX/CG window","popup_window_id":windowID(m.2),"popup_window":try describe(m.1),"cli_label":text])
    }
    let tree = try walk(main), clips = tree.filter { attribute($0,kAXRoleAttribute) as? String == kAXUnknownRole && label($0,clipLabel) }
    let buttons = tree.filter { attribute($0,kAXRoleAttribute) as? String == kAXButtonRole && label($0,volumeLabel) && actions($0).contains(kAXPressAction) }
    var pairs = [(AXUIElement,AXUIElement,AXUIElement)]()
    for c in clips { for v in buttons {
        guard let cp = parent(c), let vp = parent(v), owned(cp), CFEqual(cp,vp), attribute(cp,kAXRoleAttribute) as? String == kAXGroupRole,
              let groupFrame = try? axFrame(cp), let cf = try? axFrame(c), let vf = try? axFrame(v), mainBounds.insetBy(dx:-1,dy:-1).contains(groupFrame), groupFrame.insetBy(dx:-1,dy:-1).contains(cf), groupFrame.insetBy(dx:-1,dy:-1).contains(vf) else { continue }
        pairs.append((c,v,cp))
    } }
    try require(pairs.count == 1,"Missing/ambiguous same-parent Frame Clip AXUnknown and Volume AXButton")
    let pair = pairs[0]; return try selected(id == clipTarget ? pair.0 : pair.1,["relationship":"Clip and Volume share one content AXGroup","main_window_id":mainID,"main_window":try describe(main),"parent":try describe(pair.2),"clip":try describe(pair.0),"volume":try describe(pair.1),"cli_labels":[clipLabel,volumeLabel]])
}
func axFind(_ id: String, role: String? = nil) throws -> AXUIElement {
    guard let p = process else { throw Failure(description:"No target") }
    var queue = [AXUIElementCreateApplication(p.processIdentifier)], seen = Set<CFHashCode>(), found = [AXUIElement](), index = 0
    while index < queue.count && index < 4000 {
        let e = queue[index]; index += 1; if !seen.insert(CFHash(e)).inserted { continue }
        if attribute(e,kAXIdentifierAttribute) as? String == id && (role == nil || attribute(e,kAXRoleAttribute) as? String == role) { found.append(e) }
        queue += attribute(e,kAXChildrenAttribute) as? [AXUIElement] ?? []; queue += attribute(e,kAXWindowsAttribute) as? [AXUIElement] ?? []
    }
    if index < 4000 && found.isEmpty {
        do { if let selected = try scopedFrameAX(id,role:role) { return selected } }
        catch { report["ax_scope_failure"] = String(describing:error) }
    }
    if index >= 4000 || found.count != 1 { try axFailure(id,role:role,found:found.count,visited:index,queued:queue.count,hashes:seen.count) }
    try require(index < 4000 && found.count == 1,"Missing/ambiguous AX identifier \(id) role \(role ?? "any"); found=\(found.count), visited=\(index)"); return found[0]
}
func geometry(_ id: String, role: String? = nil) throws -> [String:Any] {
    let e = try axFind(id,role:role), r = try axFrame(e), main = try bounds(mainWindow()); var actions: CFArray?
    _ = AXUIElementCopyActionNames(e,&actions)
    return ["target":id,"actual_ax_identifier":attribute(e,kAXIdentifierAttribute) as? String ?? "","role":attribute(e,kAXRoleAttribute) as? String ?? "","subrole":attribute(e,kAXSubroleAttribute) as? String ?? "",
            "screen_top_left_points":rect(r),"relative_to_main_outer_points":rect(r.offsetBy(dx:-main.minX,dy:-main.minY)),"actions":actions as? [String] ?? [],"enabled":attribute(e,kAXEnabledAttribute) as? Bool ?? false]
}
func player() throws -> [String:Any] {
    guard let state = try command("media.state",["player_id":playerID]) as? [String:Any] else { throw Failure(description:"Invalid media.state") }
    try require(state["player_id"] as? String == playerID && (state["source"] as? [String:Any])?["url"] as? String == sourceURL,"Player/source changed")
    try require(sourceVersion == nil || integer(state["source_version"]) == sourceVersion,"Source version changed")
    try require(state["error"] is NSNull && (state["request"] as? [String:Any])?["status"] as? String != "Failed","Media reported a failure"); return state
}
func frameStage(_ name: String, open: Bool, paused: Bool = true) throws {
    try healthy(); let rows = try controls(), volume = try control(rows,".volume","popover_button"), clip = try control(rows,".clip","video")
    try require(volume["target"] as? String == volumeTarget && clip["target"] as? String == clipTarget,"Frame identity changed")
    try require(volume["value"] as? String == (open ? "open" : "closed"),"Unexpected popover state at \(name)")
    let state = try player(); if paused { try require(state["phase"] as? String == "Paused" && integer(state["position_ms"]) == 0,"Video is not paused at zero at \(name)") }
    var native = [try geometry(volumeTarget,role:kAXButtonRole),try geometry(clipTarget)]
    if open { let slider = try control(rows,".volume_level","slider"); sliderTarget = slider["target"] as! String; native.append(try geometry(sliderTarget,role:kAXSliderRole)) }
    stages.append(["stage":name,"elapsed":Date().timeIntervalSince(began),"controls":rows,"media":state,"native_geometry":native,"own_windows":ownWindows()]); try save()
}
func capture(_ name: String, ids: [CGWindowID], canvas: CGRect, open: Bool) throws {
    let captureBeganUptime = ProcessInfo.processInfo.systemUptime
    var previous = "", equal = 0, samples = 0; let end = min(deadline,Date().addingTimeInterval(8))
    let expectedBounds = Dictionary(uniqueKeysWithValues:ownWindows().filter { ids.contains(windowID($0)) }.map { (windowID($0),bounds($0)) })
    guard let owner = process?.processIdentifier, let windowArray = CFArrayCreateMutable(kCFAllocatorDefault,0,nil) else { throw Failure(description:"Cannot allocate own window-ID array") }
    try require(Set(ids).count == ids.count && !ids.isEmpty && !ids.contains(0),"Invalid capture window IDs")
    // This API family requires raw CGWindowID slots, not NSNumber object pointers.
    for id in ids { CFArrayAppendValue(windowArray,UnsafeRawPointer(bitPattern:UInt(id))) }
    while Date() < end {
        try healthy(); let visible = ownWindows(); try require(ids.allSatisfy { id in visible.contains { windowID($0) == id && bounds($0) == expectedBounds[id] } },"Selected capture window disappeared or moved")
        if !ids.allSatisfy({ id in visible.contains { windowID($0) == id && (($0[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 } }) { try pause(0.05); continue }
        let descriptions = CGWindowListCreateDescriptionFromArray(windowArray) as? [[String:Any]] ?? [], describedIDs = descriptions.map(windowID)
        let exact = descriptions.count == ids.count && Set(describedIDs) == Set(ids) && descriptions.allSatisfy { ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == owner }
        var checks = report["window_array_checks"] as? [[String:Any]] ?? []
        checks.append(["capture":name,"elapsed":Date().timeIntervalSince(began),"encoding":"raw CGWindowID pointer slots; CFArray callbacks=nil","requested_ids":ids,"described_ids":describedIDs,"descriptions":descriptions,"own_pid":owner,"exact_ids_and_owner":exact]); report["window_array_checks"] = checks; try save()
        try require(exact,"Raw CGWindowID array did not round-trip exact IDs and own PID")
        let sampleBeganUptime = ProcessInfo.processInfo.systemUptime
        guard let image = CGImage(windowListFromArrayScreenBounds:canvas,windowArray:windowArray,imageOption:[.boundsIgnoreFraming,.bestResolution]) else { throw Failure(description:"WindowServer capture failed") }
        let sampleAcquiredUptime = ProcessInfo.processInfo.systemUptime
        var rgba = [UInt8](repeating:0,count:image.width*image.height*4)
        let ok = rgba.withUnsafeMutableBytes { b -> Bool in
            guard let c = CGContext(data:b.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else { return false }
            c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height)); return true
        }
        try require(ok && stride(from:3,to:rgba.count,by:4).contains(where:{ rgba[$0] > 0 }),"Capture is empty/transparent")
        guard let icc = image.colorSpace?.copyICCData() else { throw Failure(description:"WindowServer image lacks ICC profile") }
        let hash = sha(Data(rgba)); equal = hash == previous ? equal+1 : 0; previous = hash; samples += 1
        if equal >= 4 {
            try frameStage(name+"-stable",open:open); let path = output.appendingPathComponent(name+".png")
            guard let d = CGImageDestinationCreateWithURL(path as CFURL,"public.png" as CFString,1,nil) else { throw Failure(description:"Cannot create PNG") }
            CGImageDestinationAddImage(d,image,nil); try require(CGImageDestinationFinalize(d),"Cannot save PNG")
            guard let png = CGImageSourceCreateWithURL(path as CFURL,nil), let embedded = CGImageSourceCreateImageAtIndex(png,0,nil)?.colorSpace?.copyICCData() else { throw Failure(description:"PNG lost its ICC profile") }
            try require(sha(embedded as Data) == sha(icc as Data),"PNG ICC differs from captured image")
            captures.append(["png":path.lastPathComponent,"window_ids":ids,"canvas_screen_top_left_points":rect(canvas),"width":image.width,"height":image.height,
                "pixels_per_point":[Double(image.width)/canvas.width,Double(image.height)/canvas.height],"color_space":image.colorSpace?.name as String? ?? "unnamed",
                "rgba8_srgb_sha256":hash,"png_sha256":sha(try Data(contentsOf:path)),"icc_sha256":sha(icc as Data),
                "stable_equal_comparisons":equal,"samples":samples,"capture_begin_uptime_seconds":captureBeganUptime,"sample_begin_uptime_seconds":sampleBeganUptime,"sample_acquired_uptime_seconds":sampleAcquiredUptime]); try save(); return
        }; try pause(0.1)
    }; throw Failure(description:"WindowServer pixels did not settle: \(name)")
}
func run() -> Int32 {
defer {
    timer?.invalidate()
    let ownWasFront = process != nil && NSWorkspace.shared.frontmostApplication?.processIdentifier == process?.processIdentifier
    if ownWasFront, let original = originalApplication, !original.isTerminated {
        requestActivation(original.processIdentifier,options:[],names:[],reason:"restore-immediate-original-before-own-child-stop")
        let end = Date().addingTimeInterval(1)
        while NSWorkspace.shared.frontmostApplication?.processIdentifier == process?.processIdentifier && Date() < end { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }
    }
    let restoreFailed = ownWasFront && originalApplication != nil && NSWorkspace.shared.frontmostApplication?.processIdentifier == process?.processIdentifier
    if restoreFailed { report["cleanup_failure"] = "Original foreground could not be restored before own child stop; child left for explicit guarded cleanup"; report["success"] = false }
    if !restoreFailed, let p = process, p.isRunning {
        NSRunningApplication(processIdentifier:p.processIdentifier)?.terminate(); let end = Date().addingTimeInterval(2)
        while p.isRunning && Date() < end { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }; if p.isRunning { kill(p.processIdentifier,SIGKILL) }
        let killed = Date().addingTimeInterval(1); while p.isRunning && Date() < killed { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }
    }
    report["app_still_running_after_cleanup"] = process?.isRunning ?? false
    if process?.isRunning == true { report["success"] = false; report["cleanup_failure"] = report["cleanup_failure"] ?? "Own child still running after cleanup" }
    do { if try ledgerLogHasError() { report["success"] = false; report["ledger_io_error_seen_after_cleanup"] = true } }
    catch { report["success"] = false; report["ledger_log_error_after_cleanup"] = String(describing:error) }
    if let p = process, !p.isRunning { report["app_termination_status"] = p.terminationStatus }
    if process?.isRunning != true { try? fm.removeItem(at:ipc) } else { report["ipc_preserved_for_live_child"] = ipc.path }; report["elapsed_seconds"] = Date().timeIntervalSince(began); report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0; try? save()
}
do {
    try save(); try require(CommandLine.arguments[6] == "e48fff46b3a92a28465ad74295bd273a9d69af7d","This collector requires exact e48 source provenance")
    report["closed_only"] = true
    try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")
    try require(requestedLocalEvents.isEmpty || localOwnActive13,"Local events require explicit own-pid-active13 on macOS13 outside CI")
    try require(sendsHeartbeat,"Requires CI mode or explicit local13 own-PID active mode; no CI impersonation")
    try require(AXIsProcessTrusted() && CGPreflightScreenCaptureAccess() && CGPreflightPostEventAccess(),"AX/Screen Recording/PostEvent access unavailable; no privacy changes attempted")
    try require(!NSWorkspace.shared.accessibilityDisplayShouldReduceMotion && !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency && !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast,"Expected ordinary motion/transparency/contrast profile")
    try require(appURL.lastPathComponent == "Gallery.app" && fm.isExecutableFile(atPath:cliURL.path),"Expected supplied Gallery application and CLI")
    try fm.createDirectory(at:ipc,withIntermediateDirectories:false,attributes:[.posixPermissions:0o700]); env["BERN_IPC_DIR"] = ipc.path; env["BERN_APPEARANCE"] = "light"
    for key in ["BERN_SNAPSHOT_DIR","BERN_MOTION"] { env.removeValue(forKey:key) }
    report["app_executable_sha256"] = sha(try Data(contentsOf:appURL.appendingPathComponent("Contents/MacOS/Gallery")))
    report["cli_sha256"] = sha(try Data(contentsOf:cliURL))
    let p = Process(); p.executableURL = appURL.appendingPathComponent("Contents/MacOS/Gallery"); p.arguments = ["-AppleLanguages","(en)","-AppleLocale","en_US"]; p.environment = env
    let log = output.appendingPathComponent("application.log"); _ = fm.createFile(atPath:log.path,contents:nil); let handle = try FileHandle(forWritingTo:log); defer { handle.closeFile() }
    p.standardOutput = handle; p.standardError = handle; try p.run(); process = p
    let ready = min(deadline,Date().addingTimeInterval(18))
    repeat { if let s = try cli(["sessions"],allowFailure:true,until:ready) as? [[String:Any]], s.count == 1 { session = s[0]["session_id"] as? String ?? "" }; if session.isEmpty { try pause(0.1,active:false) } } while session.isEmpty && p.isRunning && Date() < ready
    try require(!session.isEmpty,"Expected one UI session")
    // Session transport is not UI readiness. No foreground request or control
    // inspection occurs before one main registry row and one visible own CG window.
    var startup = [[String:Any]](), startupID: CGWindowID = 0
    while p.isRunning && Date() < ready {
        let rows = try cli(["window","list"],session:true,allowFailure:true,until:ready) as? [[String:Any]] ?? []
        let mains = rows.filter { $0["kind"] as? String == "main" }
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        startup.append(["elapsed":Date().timeIntervalSince(began),"deadline":ready.timeIntervalSince1970,"pid":p.processIdentifier,"windows":rows,"native_candidates":native])
        report["startup_readiness"] = startup; try save()
        if Date() < ready, mains.count == 1, native.count == 1, ((native[0][kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 { startupID = windowID(native[0]); break }
        try pause(min(0.08,max(0,ready.timeIntervalSinceNow)),active:false)
    }
    try require(startupID != 0,"Startup main registry and unique visible own CG window were not ready within18 seconds (individual CLI cap8 seconds)")
    requestActivation(p.processIdentifier,options:[.activateAllWindows,.activateIgnoringOtherApps],names:["activateAllWindows","activateIgnoringOtherApps"],reason:"own-gallery-after-startup-ready")
    for _ in 0..<40 {
        let native = ownWindows().filter { ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 && bounds($0).height > 0 }
        if NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier, native.count == 1, windowID(native[0]) == startupID { mainID = startupID; break }
        try pause(0.05,active:false)
    }
    try require(mainID != 0,"No frontmost Gallery main window matching the startup window"); heartbeat(); timer = Timer.scheduledTimer(withTimeInterval:0.5,repeats:true) { _ in heartbeat() }
    guard let catalog = try cli(["catalog"]) as? [String:Any] else { throw Failure(description:"Invalid command catalog") }
    specs = (catalog["session_commands"] as? [[String:Any]] ?? []) + (catalog["media_commands"] as? [[String:Any]] ?? [])
    _ = try command("ui.set_language",["language":"en"],scoped:true); let light = try control(controls(),".light","button")
    _ = try command("ui.activate",["target":light["target"] as! String],scoped:true)
    let listed = try command("window.list",scoped:true) as? [[String:Any]] ?? [], mains = listed.filter { $0["kind"] as? String == "main" }
    try require(mains.count == 1,"Expected one main session window"); let main = mains[0]["window"] as! String
    _ = try command("window.resize",["window":main,"width":"920","height":"668"],scoped:true)
    let display = CGDisplayBounds(CGMainDisplayID()); _ = try command("window.move",["window":main,"x":String(display.midX-460),"y":String(display.midY-334)],scoped:true)
    try armRowLedger()
    let pages = try control(controls(),".pages","sidebar"); _ = try command("ui.select",["target":pages["target"] as! String,"option":"Frame"],scoped:true)
    let mounted = Date().addingTimeInterval(3)
    repeat { let rows = try controls(); if let v = try? control(rows,".volume","popover_button"), let c = try? control(rows,".clip","video") { volumeTarget = v["target"] as! String; clipTarget = c["target"] as! String; break }; try pause(0.05) } while Date() < mounted
    try require(!volumeTarget.isEmpty,"Frame volume did not mount; input heartbeat did not wake it")
    guard let values = (try cli(["state"]) as? [String:Any])?["values"] as? [String:Any], let source = (values["clip"] as? [String:Any])?["url"] as? String else { throw Failure(description:"Missing engine clip source") }
    sourceURL = source; try require(values["appearance"] as? String == "Light" && values["caption"] as? Bool == true,"Expected Light window and caption=true")
    // BernVideo's source-bound identity is window.id + "/" + target in both locked builds.
    // Its asynchronous .task can create/bind the player after control.onAppear registers the UI.
    let expectedPlayer = main+"/"+clipTarget, discoveryEnd = min(deadline,Date().addingTimeInterval(8))
    repeat {
        let rows = try controls(until:discoveryEnd), volume = try control(rows,".volume","popover_button"), clip = try control(rows,".clip","video")
        try require(volume["target"] as? String == volumeTarget && clip["target"] as? String == clipTarget && volume["value"] as? String == "closed","Frame unmounted or changed while waiting for its player")
        let players = try command("media.players",until:discoveryEnd) as? [[String:Any]] ?? [], matched = players.filter { $0["player_id"] as? String == expectedPlayer && $0["owner"] as? String == main && $0["source_bound"] as? Bool == true && ($0["source"] as? [String:Any])?["url"] as? String == source }
        stages.append(["stage":"player-discovery","elapsed":Date().timeIntervalSince(began),"expected_player_id":expectedPlayer,"volume":volume,"matching_players":matched.count]); try save()
        try require(matched.count <= 1,"Ambiguous Frame player"); try require(Date() < discoveryEnd,"Frame player did not finish binding within 8 seconds")
        if let found = matched.first { playerID = found["player_id"] as! String; sourceVersion = integer(found["source_version"]); break }
        try pause(min(0.1,discoveryEnd.timeIntervalSinceNow))
    } while Date() < discoveryEnd
    try require(!playerID.isEmpty,"Frame player did not finish binding within 8 seconds")
    try require(sourceVersion != nil,"Invalid media source_version")
    let videoReady = Date().addingTimeInterval(8)
    while try player()["phase"] as? String != "Ready" { try require(Date() < videoReady,"Clip never reached Ready"); try pause(0.1) }
    stages.append(["stage":"video-ready","media":try player()]); _ = try command("media.play",["player_id":playerID]); _ = try command("media.pause",["player_id":playerID]); _ = try command("media.seek",["player_id":playerID,"position_ms":"0"])
    let paused = Date().addingTimeInterval(5)
    while true { let s = try player(); if s["phase"] as? String == "Paused" && integer(s["position_ms"]) == 0 { break }; try require(Date() < paused,"Video never paused at zero"); try pause(0.1) }
    // More than idle_after proves that CLI operations alone did not keep the Frame controls alive.
    let awake = Date().addingTimeInterval(3.2); repeat { try frameStage("awake-check",open:false); try pause(0.4) } while Date() < awake
    let outer = try bounds(mainWindow()); try require(abs(outer.width-920) <= 1 && abs(outer.height-668) <= 1,"Unexpected main outer geometry")
    report["display_bounds_points"] = rect(display); report["source_url"] = source; report["player_id"] = playerID
    let bundled = appURL.appendingPathComponent("Contents/Resources/media/tides.mp4")
    try require(URL(string:source)?.resolvingSymlinksInPath() == bundled.resolvingSymlinksInPath(),"Frame is not using the supplied bundled clip")
    report["bundled_tides_sha256"] = sha(try Data(contentsOf:bundled))
    try capture("frame-closed-light",ids:[mainID],canvas:outer,open:false)
    try frameStage("closed-end",open:false)
    guard let final = (try cli(["state"]) as? [String:Any])?["values"] as? [String:Any] else { throw Failure(description:"Missing final engine state") }
    try require(final["appearance"] as? String == "Light" && final["caption"] as? Bool == true,"Frame context changed before completion")
    report["final_context"] = ["appearance":"Light","caption":true,"volume":"closed","video":"Paused0","frame_appearance":"dark from exact generated source"]
    try finishRowLedger(); report["success"] = true; try save()
} catch { report["failure"] = String(describing:error); try? save(); fputs("Frame reference failed: \(error)\n",stderr); return 1 }
return 0
}
let runStatus = run()
exit(runStatus == 0 && report["success"] as? Bool == true && report["app_still_running_after_cleanup"] as? Bool == false ? 0 : 1)
