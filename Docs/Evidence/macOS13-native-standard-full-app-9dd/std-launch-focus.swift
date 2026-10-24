import AppKit
if CommandLine.arguments.count == 1 {
    print(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0)
} else if CommandLine.arguments.count == 3, CommandLine.arguments[1] == "--windows", let pid = Int32(CommandLine.arguments[2]) {
    let rows = CGWindowListCopyWindowInfo([.optionOnScreenOnly, .excludeDesktopElements], kCGNullWindowID) as? [[String: Any]] ?? []
    let own = rows.filter { ($0[kCGWindowOwnerPID as String] as? NSNumber)?.int32Value == pid && ($0[kCGWindowLayer as String] as? NSNumber)?.intValue == 0 }
    FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: own, options: [.sortedKeys]))
} else if CommandLine.arguments.count == 2, let pid = Int32(CommandLine.arguments[1]) {
    guard let application = NSRunningApplication(processIdentifier: pid), application.activate(options: [.activateIgnoringOtherApps]) else { exit(1) }
} else { exit(2) }
