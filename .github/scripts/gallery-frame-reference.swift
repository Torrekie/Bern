// External observer only. APP CLI OUTPUT EXPECTED_OS LABEL SOURCE_SHA; no app injection or TCC changes.
// Heartbeats are CI-only, process-targeted mouseMoved events, not physical mouse acceptance.
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
let originalFront = NSWorkspace.shared.frontmostApplication?.processIdentifier
let ciHeartbeat = ProcessInfo.processInfo.environment["GITHUB_ACTIONS"] == "true" && ProcessInfo.processInfo.environment["CI"] == "true"
var env = ProcessInfo.processInfo.environment, process: Process?, timer: Timer?, heartbeatError: String?, mainID: CGWindowID = 0
var session = "", specs = [[String:Any]](), commands = [[String:Any]](), stages = [[String:Any]](), captures = [[String:Any]](), events = [[String:Any]]()
var volumeTarget = "", clipTarget = "", sliderTarget = "", playerID = "", sourceURL = "", sourceVersion: Int64?
var report: [String:Any] = ["schema":1,"success":false,"label":CommandLine.arguments[5],"source_sha":CommandLine.arguments[6],
    "harness_sha":env["GITHUB_SHA"] ?? "local","expected_os":expectedOS,"os":ProcessInfo.processInfo.operatingSystemVersionString,
    "app":appURL.path,"interaction_scope":"Generated CLI and AXPress; CI own-PID mouseMoved keeps Frame awake. No physical input claim.",
    "heartbeat_ci_only":ciHeartbeat,"frontmost_before":originalFront ?? 0,"accessibility_trusted":AXIsProcessTrusted(),
    "screen_recording":CGPreflightScreenCaptureAccess(),"post_event_access":CGPreflightPostEventAccess(),
    "system_preferences":["reduce_motion":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,"reduce_transparency":NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,"increase_contrast":NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast],
    "displays":NSScreen.screens.map { ["frame_points":rect($0.frame),"scale":$0.backingScaleFactor,"color_space":$0.colorSpace?.localizedName ?? "unknown"] as [String:Any] },
    "geometry_scope":"Public AX roles/frames and WindowServer windows; AX does not identify the Cocoa view class."]
try fm.createDirectory(at:output,withIntermediateDirectories:true)
let ipc = URL(fileURLWithPath:"/tmp/bern-frame-\(getpid())-\(UUID().uuidString)",isDirectory:true)
func save() throws {
    report["commands"] = commands; report["stages"] = stages; report["captures"] = captures; report["heartbeat_events"] = events
    try JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"),options:.atomic)
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
func controls(until stopAt: Date? = nil) throws -> [[String:Any]] { try command("ui.inspect",scoped:true,until:stopAt) as? [[String:Any]] ?? [] }
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
    guard ciHeartbeat, heartbeatError == nil, let p = process, p.isRunning else { return }
    guard NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier,
          let w = ownWindows().first(where:{ windowID($0) == mainID }) else { heartbeatError = "Own target lost foreground/window; heartbeat stopped"; return }
    let r = bounds(w), point = CGPoint(x:r.midX,y:r.midY)
    guard let e = CGEvent(mouseEventSource:nil,mouseType:.mouseMoved,mouseCursorPosition:point,mouseButton:.left) else { heartbeatError = "Cannot create own-PID heartbeat"; return }
    // Public fields (10.7+) associate the mouse event with this known main window.
    // Delivery is still unproven until Frame remains mounted beyond idle_after.
    e.setIntegerValueField(.mouseEventWindowUnderMousePointer,value:Int64(mainID))
    e.setIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent,value:Int64(mainID))
    e.setIntegerValueField(.eventTargetUnixProcessID,value:Int64(p.processIdentifier))
    e.postToPid(p.processIdentifier)
    events.append(["elapsed":Date().timeIntervalSince(began),"pid":p.processIdentifier,"window_id":mainID,"window_fields":[e.getIntegerValueField(.mouseEventWindowUnderMousePointer),e.getIntegerValueField(.mouseEventWindowUnderMousePointerThatCanHandleThisEvent)],"window_bounds_points":rect(r),"point_screen_top_left":[point.x,point.y]])
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
func axFind(_ id: String, role: String? = nil) throws -> AXUIElement {
    guard let p = process else { throw Failure(description:"No target") }
    var queue = [AXUIElementCreateApplication(p.processIdentifier)], seen = Set<CFHashCode>(), found = [AXUIElement](), index = 0
    while index < queue.count && index < 4000 {
        let e = queue[index]; index += 1; if !seen.insert(CFHash(e)).inserted { continue }
        if attribute(e,kAXIdentifierAttribute) as? String == id && (role == nil || attribute(e,kAXRoleAttribute) as? String == role) { found.append(e) }
        queue += attribute(e,kAXChildrenAttribute) as? [AXUIElement] ?? []; queue += attribute(e,kAXWindowsAttribute) as? [AXUIElement] ?? []
    }
    try require(index < 4000 && found.count == 1,"Missing/ambiguous AX identifier \(id) role \(role ?? "any")"); return found[0]
}
func geometry(_ id: String, role: String? = nil) throws -> [String:Any] {
    let e = try axFind(id,role:role), r = try axFrame(e), main = try bounds(mainWindow()); var actions: CFArray?
    _ = AXUIElementCopyActionNames(e,&actions)
    return ["target":id,"role":attribute(e,kAXRoleAttribute) as? String ?? "","subrole":attribute(e,kAXSubroleAttribute) as? String ?? "",
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
    var previous = "", equal = 0, samples = 0; let end = min(deadline,Date().addingTimeInterval(8))
    let expectedBounds = Dictionary(uniqueKeysWithValues:ownWindows().filter { ids.contains(windowID($0)) }.map { (windowID($0),bounds($0)) })
    while Date() < end {
        try healthy(); let visible = ownWindows(); try require(ids.allSatisfy { id in visible.contains { windowID($0) == id && bounds($0) == expectedBounds[id] } },"Selected capture window disappeared or moved")
        if !ids.allSatisfy({ id in visible.contains { windowID($0) == id && (($0[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 } }) { try pause(0.05); continue }
        guard let image = CGImage(windowListFromArrayScreenBounds:canvas,windowArray:ids.map { NSNumber(value:$0) } as CFArray,imageOption:[.boundsIgnoreFraming,.bestResolution]) else { throw Failure(description:"WindowServer capture failed") }
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
                "stable_equal_comparisons":equal,"samples":samples]); try save(); return
        }; try pause(0.1)
    }; throw Failure(description:"WindowServer pixels did not settle: \(name)")
}
func run() -> Int32 {
defer {
    timer?.invalidate()
    let ownWasFront = process != nil && NSWorkspace.shared.frontmostApplication?.processIdentifier == process?.processIdentifier
    if let p = process, p.isRunning { NSRunningApplication(processIdentifier:p.processIdentifier)?.terminate(); let end = Date().addingTimeInterval(2)
        while p.isRunning && Date() < end { RunLoop.current.run(until:Date().addingTimeInterval(0.02)) }; if p.isRunning { kill(p.processIdentifier,SIGKILL) } }
    if ownWasFront, let original = originalFront, NSWorkspace.shared.frontmostApplication?.processIdentifier != original { NSRunningApplication(processIdentifier:original)?.activate(options:[]) }
    try? fm.removeItem(at:ipc); report["elapsed_seconds"] = Date().timeIntervalSince(began); report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0; try? save()
}
do {
    try save(); try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")
    try require(AXIsProcessTrusted() && CGPreflightScreenCaptureAccess() && CGPreflightPostEventAccess(),"AX/Screen Recording/PostEvent access unavailable; no privacy changes attempted")
    try require(!NSWorkspace.shared.accessibilityDisplayShouldReduceMotion && !NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency && !NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast,"Expected ordinary motion/transparency/contrast profile")
    try require(appURL.lastPathComponent == "Gallery.app" && fm.isExecutableFile(atPath:cliURL.path),"Expected supplied Gallery application and CLI")
    try fm.createDirectory(at:ipc,withIntermediateDirectories:false,attributes:[.posixPermissions:0o700]); env["BERN_IPC_DIR"] = ipc.path; env["BERN_APPEARANCE"] = "light"
    for key in ["BERN_SNAPSHOT_DIR","BERN_MOTION"] { env.removeValue(forKey:key) }
    let p = Process(); p.executableURL = appURL.appendingPathComponent("Contents/MacOS/Gallery"); p.arguments = ["-AppleLanguages","(en)","-AppleLocale","en_US"]; p.environment = env
    let log = output.appendingPathComponent("application.log"); _ = fm.createFile(atPath:log.path,contents:nil); let handle = try FileHandle(forWritingTo:log); defer { handle.closeFile() }
    p.standardOutput = handle; p.standardError = handle; try p.run(); process = p
    let ready = Date().addingTimeInterval(18)
    repeat { if let s = try cli(["sessions"],allowFailure:true) as? [[String:Any]], s.count == 1 { session = s[0]["session_id"] as? String ?? "" }; if session.isEmpty { try pause(0.1,active:false) } } while session.isEmpty && Date() < ready
    try require(!session.isEmpty,"Expected one UI session"); NSRunningApplication(processIdentifier:p.processIdentifier)?.activate(options:[.activateAllWindows,.activateIgnoringOtherApps])
    for _ in 0..<40 { if NSWorkspace.shared.frontmostApplication?.processIdentifier == p.processIdentifier, let w = ownWindows().filter({ ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 && bounds($0).width > 500 }).first { mainID = windowID(w); break }; try pause(0.05,active:false) }
    try require(mainID != 0,"No frontmost Gallery main window"); heartbeat(); timer = Timer.scheduledTimer(withTimeInterval:0.5,repeats:true) { _ in heartbeat() }
    guard let catalog = try cli(["catalog"]) as? [String:Any] else { throw Failure(description:"Invalid command catalog") }
    specs = (catalog["session_commands"] as? [[String:Any]] ?? []) + (catalog["media_commands"] as? [[String:Any]] ?? [])
    _ = try command("ui.set_language",["language":"en"],scoped:true); let light = try control(controls(),".light","button")
    _ = try command("ui.activate",["target":light["target"] as! String],scoped:true)
    let listed = try command("window.list",scoped:true) as? [[String:Any]] ?? [], mains = listed.filter { $0["kind"] as? String == "main" }
    try require(mains.count == 1,"Expected one main session window"); let main = mains[0]["window"] as! String
    _ = try command("window.resize",["window":main,"width":"920","height":"668"],scoped:true)
    let display = CGDisplayBounds(CGMainDisplayID()); _ = try command("window.move",["window":main,"x":String(display.midX-460),"y":String(display.midY-334)],scoped:true)
    let pages = try control(controls(),".pages","sidebar"); _ = try command("ui.select",["target":pages["target"] as! String,"option":"Frame"],scoped:true)
    let mounted = Date().addingTimeInterval(3)
    repeat { let rows = try controls(); if let v = try? control(rows,".volume","popover_button"), let c = try? control(rows,".clip","video") { volumeTarget = v["target"] as! String; clipTarget = c["target"] as! String; break }; try pause(0.05) } while Date() < mounted
    try require(!volumeTarget.isEmpty,"Frame volume did not mount; input heartbeat did not wake it")
    guard let values = (try cli(["state"]) as? [String:Any])?["values"] as? [String:Any], let source = (values["clip"] as? [String:Any])?["url"] as? String else { throw Failure(description:"Missing engine clip source") }
    sourceURL = source; try require(values["appearance"] as? String == "Light","Appearance did not commit")
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
    let button = try axFind(volumeTarget,role:kAXButtonRole); try require(AXUIElementPerformAction(button,kAXPressAction as CFString) == .success,"AXPress failed")
    let opening = Date().addingTimeInterval(3)
    while true { let rows = try controls(); if let v = try? control(rows,".volume","popover_button"), v["value"] as? String == "open", let s = try? control(rows,".volume_level","slider") { sliderTarget = s["target"] as! String; break }; try require(Date() < opening,"Popover content did not mount"); try pause(0.05) }
    var popup: [String:Any]?, lastRect = CGRect.null, sameRect = 0; let visible = Date().addingTimeInterval(3)
    repeat {
        let sliderFrame = try axFrame(axFind(sliderTarget,role:kAXSliderRole)), candidates = ownWindows().filter { windowID($0) != mainID && bounds($0).insetBy(dx:-1,dy:-1).contains(sliderFrame) && (($0[kCGWindowAlpha as String] as? NSNumber)?.doubleValue ?? 0) >= 0.99 }
        try require(candidates.count <= 1,"Ambiguous popover window"); if let w = candidates.first { let r = bounds(w); sameRect = r == lastRect ? sameRect+1 : 0; lastRect = r; if sameRect >= 3 { popup = w; break } }; try pause(0.1)
    } while Date() < visible
    guard let popup = popup else { throw Failure(description:"No stable separate onscreen popover contains the real slider") }; let popupID = windowID(popup), popupRect = bounds(popup)
    let orderedIDs = ownWindows().map(windowID).filter { $0 == mainID || $0 == popupID }
    try capture("frame-open-light",ids:orderedIDs,canvas:outer.union(popupRect),open:true)
    try capture("volume-popover-light",ids:[popupID],canvas:popupRect,open:true)
    try require(AXUIElementPerformAction(try axFind(volumeTarget,role:kAXButtonRole),kAXPressAction as CFString) == .success,"Closing AXPress failed")
    let closing = Date().addingTimeInterval(3)
    while true { let rows = try controls(), v = try control(rows,".volume","popover_button"), popupDrawn = ownWindows().contains { windowID($0) == popupID }
        if v["value"] as? String == "closed" && !rows.contains(where:{ $0["target"] as? String == sliderTarget }) && !popupDrawn { break }; try require(Date() < closing,"Popover still draws or its controls remain mounted"); try pause(0.05) }
    try frameStage("dismissed",open:false); report["success"] = true; try save()
} catch { report["failure"] = String(describing:error); try? save(); fputs("Frame reference failed: \(error)\n",stderr); return 1 }
return 0
}
exit(run())
