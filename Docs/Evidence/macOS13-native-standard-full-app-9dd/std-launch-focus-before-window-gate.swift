import AppKit
if CommandLine.arguments.count == 1 {
    print(NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0)
} else if CommandLine.arguments.count == 2, let pid = Int32(CommandLine.arguments[1]) {
    guard let application = NSRunningApplication(processIdentifier: pid), application.activate(options: [.activateIgnoringOtherApps]) else { exit(1) }
} else { exit(2) }
