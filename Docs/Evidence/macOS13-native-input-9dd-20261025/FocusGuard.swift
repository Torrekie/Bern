// Public NSRunningApplication focus/owned-process cleanup; no cursor or TCC calls.
import AppKit
import Darwin
import Foundation

struct GuardFailure: Error, CustomStringConvertible { let description: String }
func require(_ condition: Bool, _ text: String) throws {
    if !condition { throw GuardFailure(description: text) }
}
// Public Darwin kernel process start timeval; launchDate remains diagnostic-only.
func kernelStart(_ pid: pid_t) -> [String: UInt64]? {
    guard pid > 0 else { return nil }
    var info = proc_bsdinfo()
    let size = MemoryLayout<proc_bsdinfo>.stride
    let result = proc_pidinfo(pid, PROC_PIDTBSDINFO, 0, &info, Int32(size))
    guard result == Int32(size), info.pbi_pid == UInt32(pid),
          info.pbi_start_tvsec > 0, info.pbi_start_tvusec < 1_000_000 else { return nil }
    return ["tv_sec": info.pbi_start_tvsec, "tv_usec": info.pbi_start_tvusec]
}
func sameKernelStart(_ pid: pid_t, _ row: [String: Any]) -> Bool {
    guard let expected = row["kernel_start"] as? [String: Any],
          let seconds = expected["tv_sec"] as? NSNumber,
          let micros = expected["tv_usec"] as? NSNumber,
          let actual = kernelStart(pid) else { return false }
    return seconds.uint64Value == actual["tv_sec"] && micros.uint64Value == actual["tv_usec"]
}
func identity(_ app: NSRunningApplication) -> [String: Any] {
    ["pid": app.processIdentifier, "bundle_id": app.bundleIdentifier ?? "",
     "executable_path": app.executableURL?.resolvingSymlinksInPath().path ?? "",
     "launch_date": app.launchDate.map { $0.timeIntervalSince1970 as Any } ?? NSNull(),
     "kernel_start": kernelStart(app.processIdentifier).map { $0 as Any } ?? NSNull()]
}
func same(_ app: NSRunningApplication, _ row: [String: Any]) -> Bool {
    guard !app.isTerminated, let pid = row["pid"] as? NSNumber,
          sameKernelStart(app.processIdentifier, row) else { return false }
    return app.processIdentifier == pid.int32Value &&
        app.bundleIdentifier == (row["bundle_id"] as? String) &&
        app.executableURL?.resolvingSymlinksInPath().path == (row["executable_path"] as? String)
}
func read(_ path: String) throws -> [String: Any] {
    guard let result = try JSONSerialization.jsonObject(with: Data(contentsOf: URL(fileURLWithPath: path))) as? [String: Any] else {
        throw GuardFailure(description: "Expected an identity JSON object")
    }
    return result
}
func pause(_ until: Date) { RunLoop.current.run(until: min(until, Date().addingTimeInterval(0.02))) }
var result: [String: Any] = ["success": false]
do {
    let args = CommandLine.arguments
    try require(args.count == 3 || args.count == 5, "usage: FocusGuard inspect APP | cleanup APP ORIGINAL_JSON OWN_JSON")
    try require(["inspect", "cleanup"].contains(args[1]), "Unknown operation")
    let appURL = URL(fileURLWithPath: args[2]).resolvingSymlinksInPath()
    guard let bundle = Bundle(url: appURL), let bundleID = bundle.bundleIdentifier else {
        throw GuardFailure(description: "No application bundle identity")
    }
    try require(bundleID.hasPrefix("dev.bern.native13.input.") && bundleID != "dev.bern.gallery", "A root-prepared private Showcase identity is required")
    try require(bundle.object(forInfoDictionaryKey: "CFBundleExecutable") as? String == "Showcase", "Expected Showcase executable")
    let executable = appURL.appendingPathComponent("Contents/MacOS/Showcase").resolvingSymlinksInPath().path
    let matches = NSWorkspace.shared.runningApplications.filter { $0.bundleIdentifier == bundleID }
    try require(matches.count <= 1, "Ambiguous private bundle identity; no action")
    if let own = matches.first {
        try require(own.executableURL?.resolvingSymlinksInPath().path == executable, "Private identity has a different executable; no action")
    }
    result["private_bundle_id"] = bundleID; result["executable_path"] = executable
    result["own"] = matches.first.map { identity($0) as Any } ?? NSNull()
    result["front"] = NSWorkspace.shared.frontmostApplication.map { identity($0) as Any } ?? NSNull()
    if args[1] == "inspect" {
        try require(args.count == 3, "inspect takes APP only")
        result["success"] = true
    } else {
        try require(args.count == 5, "cleanup requires both identity receipts")
        let original = try read(args[3]), expected = try read(args[4])
        if let own = matches.first {
            try require(same(own, expected), "Own PID/bundle/path/kernel start changed; no action")
            var restored = true
            if NSWorkspace.shared.frontmostApplication?.processIdentifier == own.processIdentifier {
                let originalPID = (original["pid"] as? NSNumber)?.int32Value ?? 0
                if let target = NSRunningApplication(processIdentifier: originalPID), same(target, original) {
                    // Recheck immediately before the single activation request.
                    if NSWorkspace.shared.frontmostApplication?.processIdentifier == own.processIdentifier {
                        let accepted = target.activate(options: [.activateIgnoringOtherApps])
                        let end = Date().addingTimeInterval(2)
                        while Date() < end,
                              NSWorkspace.shared.frontmostApplication?.processIdentifier == own.processIdentifier { pause(end) }
                        restored = NSWorkspace.shared.frontmostApplication?.processIdentifier == target.processIdentifier
                        result["front_restore"] = ["requested": true, "accepted": accepted, "restored": restored]
                    } else {
                        result["front_restore"] = ["requested": false, "reason": "Foreground changed before restore; preserved"]
                    }
                } else {
                    restored = false
                    result["front_restore"] = ["requested": false, "restored": false, "reason": "Original foreground instance no longer matches"]
                }
            } else {
                result["front_restore"] = ["requested": false, "reason": "Own app is not foreground; preserved user choice"]
            }
            result["front_after_restore_before_stop"] = NSWorkspace.shared.frontmostApplication.map { identity($0) as Any } ?? NSNull()
            try require(restored || NSWorkspace.shared.frontmostApplication?.processIdentifier != own.processIdentifier,
                        "Original foreground was not restored and own app is still foreground; refusing stop")
            // Only after the conditional restore attempt, stop this exact instance.
            if let current = NSRunningApplication(processIdentifier: own.processIdentifier), same(current, expected) {
                result["terminate_accepted"] = current.terminate()
                let end = Date().addingTimeInterval(1)
                while !current.isTerminated && Date() < end { pause(end) }
                if let live = NSRunningApplication(processIdentifier: own.processIdentifier), same(live, expected) {
                    result["sigkill_result"] = kill(live.processIdentifier, SIGKILL)
                    let final = Date().addingTimeInterval(0.5)
                    while !live.isTerminated && Date() < final { pause(final) }
                }
            }
            let stillOwn = NSRunningApplication(processIdentifier: own.processIdentifier).map { same($0, expected) } ?? false
            result["own_instance_still_running"] = stillOwn
            result["success"] = restored && !stillOwn
        } else {
            result["front_restore"] = ["requested": false, "reason": "Private app is no longer running"]
            result["success"] = true
        }
    }
} catch { result["error"] = String(describing: error) }
result["front_after"] = NSWorkspace.shared.frontmostApplication.map { identity($0) as Any } ?? NSNull()
let data = try JSONSerialization.data(withJSONObject: result, options: [.prettyPrinted, .sortedKeys])
FileHandle.standardOutput.write(data); FileHandle.standardOutput.write(Data([10]))
exit(result["success"] as? Bool == true ? 0 : 1)
