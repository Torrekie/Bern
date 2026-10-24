// Separate lightweight offline entry. Does not import AppKit, SwiftUI or MetalKit.
import Foundation
@main private enum Offline {
    static func main() {
        guard CommandLine.arguments.count==4 else {FileHandle.standardError.write(Data("Offline NAMED_PQ_PNG CUSTOM_CICP_PQ_PNG OUTPUT_DIRECTORY\n".utf8));exit(2)}
        let output=URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            let pair=try PQPair(namedURL:URL(fileURLWithPath:CommandLine.arguments[1]),customURL:URL(fileURLWithPath:CommandLine.arguments[2]))
            try JSONSerialization.data(withJSONObject:pair.report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("validation.json"))
        } catch {
            let report:[String:Any]=["success":false,"error":String(describing:error),"scope":"Offline PQ copy diagnostic only"]
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("validation.json"))
            FileHandle.standardError.write(Data("PQ copy validation failed: \(error)\n".utf8));exit(1)
        }
    }
}
