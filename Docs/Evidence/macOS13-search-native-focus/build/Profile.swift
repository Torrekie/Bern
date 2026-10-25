import AppKit
import Foundation
let workspace = NSWorkspace.shared
let flags = ["reduce_motion": workspace.accessibilityDisplayShouldReduceMotion,
             "reduce_transparency": workspace.accessibilityDisplayShouldReduceTransparency,
             "increase_contrast": workspace.accessibilityDisplayShouldIncreaseContrast]
FileHandle.standardOutput.write(try JSONSerialization.data(withJSONObject: flags, options: [.prettyPrinted, .sortedKeys]))
FileHandle.standardOutput.write(Data([10]))
