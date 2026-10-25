from pathlib import Path
import hashlib,difflib,json
root=Path(__file__).resolve().parents[2]
base=root/'outputs/Bern/Docs/Evidence/macOS13-frame-volume/paired-f9-aot/gallery-frame-reference.swift'
out=Path(__file__).resolve().parent
original=base.read_text(); assert hashlib.sha256(original.encode()).hexdigest()=='77e4bb6849ea226cb4bcc4bacac7b08197e8f5a18f4aa991752d81cea44c4db8'
s=original
changes=[]
def replace(a,b):
 global s
 assert s.count(a)==1,a[:120]
 s=s.replace(a,b,1); changes.append({'before_sha256':hashlib.sha256(a.encode()).hexdigest(),'after_sha256':hashlib.sha256(b.encode()).hexdigest()})
replace('let originalFront = NSWorkspace.shared.frontmostApplication?.processIdentifier','let originalApplication = NSWorkspace.shared.frontmostApplication\nlet originalFront = originalApplication?.processIdentifier')
replace('var inspectedControls = [[String:Any]]()',r'''var inspectedControls = [[String:Any]]()
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
}''')
replace('"Generated CLI and AXPress; explicit local13/CI own-active-PID mouseMoved keeps Frame awake. No physical input claim."','"Generated CLI only; explicit local13/CI own-active-PID mouseMoved keeps Frame awake. Closed Frame only; no AXPress or physical input claim."')
replace('"Restore the captured immediate original PID only when own Gallery was still frontmost at teardown"','"Request immediate original live application before stopping own child, only while own Gallery remains frontmost; preserve a changed foreground"')
replace('func capture(_ name: String, ids: [CGWindowID], canvas: CGRect, open: Bool) throws {\n','func capture(_ name: String, ids: [CGWindowID], canvas: CGRect, open: Bool) throws {\n    let captureBeganUptime = ProcessInfo.processInfo.systemUptime\n')
replace('        guard let image = CGImage(windowListFromArrayScreenBounds:canvas,windowArray:windowArray,imageOption:[.boundsIgnoreFraming,.bestResolution]) else { throw Failure(description:"WindowServer capture failed") }','        let sampleBeganUptime = ProcessInfo.processInfo.systemUptime\n        guard let image = CGImage(windowListFromArrayScreenBounds:canvas,windowArray:windowArray,imageOption:[.boundsIgnoreFraming,.bestResolution]) else { throw Failure(description:"WindowServer capture failed") }\n        let sampleAcquiredUptime = ProcessInfo.processInfo.systemUptime')
replace('"stable_equal_comparisons":equal,"samples":samples]','"stable_equal_comparisons":equal,"samples":samples,"capture_begin_uptime_seconds":captureBeganUptime,"sample_begin_uptime_seconds":sampleBeganUptime,"sample_acquired_uptime_seconds":sampleAcquiredUptime]')
old_start=s.index('    if let p = process, p.isRunning { NSRunningApplication(processIdentifier:p.processIdentifier)?.terminate();')
old_end=s.index('    try? fm.removeItem(at:ipc);',old_start)
replace(s[old_start:old_end],r'''    if ownWasFront, let original = originalApplication, !original.isTerminated {
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
''')
replace('    try? fm.removeItem(at:ipc); report["elapsed_seconds"]', '    if process?.isRunning != true { try? fm.removeItem(at:ipc) } else { report["ipc_preserved_for_live_child"] = ipc.path }; report["elapsed_seconds"]')
replace('exit(run())', 'let runStatus = run()\nexit(runStatus == 0 && report["success"] as? Bool == true && report["app_still_running_after_cleanup"] as? Bool == false ? 0 : 1)')
replace('    try save(); try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")','    try save(); try require(CommandLine.arguments[6] == "e48fff46b3a92a28465ad74295bd273a9d69af7d","This collector requires exact e48 source provenance")\n    report["closed_only"] = true\n    try require(ProcessInfo.processInfo.operatingSystemVersion.majorVersion == expectedOS,"Unexpected runtime OS")')
replace('    let p = Process(); p.executableURL = appURL.appendingPathComponent("Contents/MacOS/Gallery");','    report["app_executable_sha256"] = sha(try Data(contentsOf:appURL.appendingPathComponent("Contents/MacOS/Gallery")))\n    report["cli_sha256"] = sha(try Data(contentsOf:cliURL))\n    let p = Process(); p.executableURL = appURL.appendingPathComponent("Contents/MacOS/Gallery");')
replace('    let pages = try control(controls(),".pages","sidebar");','    try armRowLedger()\n    let pages = try control(controls(),".pages","sidebar");')
replace('    sourceURL = source; try require(values["appearance"] as? String == "Light","Appearance did not commit")','    sourceURL = source; try require(values["appearance"] as? String == "Light" && values["caption"] as? Bool == true,"Expected Light window and caption=true")')
start=s.index('    let button = try axFind(volumeTarget,role:kAXButtonRole); try require(AXUIElementPerformAction(button,')
end=s.index('    try frameStage("dismissed",open:false); report["success"] = true; try save()',start)+len('    try frameStage("dismissed",open:false); report["success"] = true; try save()')
replace(s[start:end],r'''    try frameStage("closed-end",open:false)
    guard let final = (try cli(["state"]) as? [String:Any])?["values"] as? [String:Any] else { throw Failure(description:"Missing final engine state") }
    try require(final["appearance"] as? String == "Light" && final["caption"] as? Bool == true,"Frame context changed before completion")
    report["final_context"] = ["appearance":"Light","caption":true,"volume":"closed","video":"Paused0","frame_appearance":"dark from exact generated source"]
    try finishRowLedger(); report["success"] = true; try save()''')
assert 'AXUIElementPerformAction(' not in s and s.count('try capture(')==1
(out/'FrameClosed.swift').write_text(s)
(out/'FrameClosed.patch').write_text(''.join(difflib.unified_diff(original.splitlines(True),s.splitlines(True),fromfile='f9-verified-collector.swift',tofile='FrameClosed.swift')))
(out/'derivation.json').write_text(json.dumps({'original_sha256':hashlib.sha256(original.encode()).hexdigest(),'derived_sha256':hashlib.sha256(s.encode()).hexdigest(),'replace_operations':len(changes),'scope':'Closed-only external collector; original media/awake/rawwindow/ICC/stable4 bodies retained, explicit arm/capture timestamps and restore-before-stop receipt added. No UI execution or compiler run yet.'},indent=2)+'\n')
print('Derived FrameClosed.swift',len(s.encode()),hashlib.sha256(s.encode()).hexdigest())
