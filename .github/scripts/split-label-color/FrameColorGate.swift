// External exact-byte PNG comparison; no image resampling or color conversion.
import Foundation
import CoreGraphics
import ImageIO
import CryptoKit

struct GateFailure: Error { let message: String }
func need(_ value: Bool, _ message: String) throws { if !value { throw GateFailure(message:message) } }
func digest(_ data: Data) -> String { SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined() }
func object(_ url: URL) throws -> [String:Any] { guard let value = try JSONSerialization.jsonObject(with:Data(contentsOf:url)) as? [String:Any] else { throw GateFailure(message:"Expected report object") }; return value }
struct Raster {
    let image: CGImage
    let bytes: Data
    let icc: Data
    var descriptor: [String:Int] { ["width":image.width,"height":image.height,"bits_per_component":image.bitsPerComponent,"bits_per_pixel":image.bitsPerPixel,"bytes_per_row":image.bytesPerRow,"bitmap_info":Int(image.bitmapInfo.rawValue),"alpha_info":Int(image.alphaInfo.rawValue)] }
    init(_ url: URL) throws {
        guard let source = CGImageSourceCreateWithURL(url as CFURL,nil), let image = CGImageSourceCreateImageAtIndex(source,0,nil), let provider = image.dataProvider, let bytes = provider.data, let icc = image.colorSpace?.copyICCData() else { throw GateFailure(message:"Missing decoded PNG pixels/ICC") }
        try need(image.bitsPerComponent == 8 && [24,32].contains(image.bitsPerPixel),"Expected native byte-component PNG")
        self.image = image; self.bytes = bytes as Data; self.icc = icc as Data
        try need(self.bytes.count >= image.bytesPerRow*image.height,"Short pixel provider")
    }
}
func differences(_ a: Raster, _ b: Raster, _ roi: [Int]) -> [String:Any] {
    let stride = a.image.bitsPerPixel/8
    var changed = 0, minX = Int.max, minY = Int.max, maxX = -1, maxY = -1
    a.bytes.withUnsafeBytes { ap in b.bytes.withUnsafeBytes { bp in
        let aa = ap.bindMemory(to:UInt8.self), bb = bp.bindMemory(to:UInt8.self)
        for y in roi[1]..<roi[3] { for x in roi[0]..<roi[2] {
            let offset = y*a.image.bytesPerRow+x*stride
            if (0..<stride).contains(where:{ aa[offset+$0] != bb[offset+$0] }) {
                changed += 1; minX = min(minX,x); minY = min(minY,y); maxX = max(maxX,x); maxY = max(maxY,y)
            }
        } }
    } }
    return ["equal":changed == 0,"changed_pixels":changed,"roi_half_open_pixels":roi,"changed_bbox_half_open_pixels":changed == 0 ? NSNull() : [minX,minY,maxX+1,maxY+1] as Any,"comparison":"All decoded active pixel bytes including stored alpha; row padding excluded; no color conversion"]
}
func validSHA(_ value: String?) -> Bool {
    value?.range(of:"^[0-9a-f]{64}$",options:.regularExpression) != nil
}
guard CommandLine.arguments.count == 5 else { fputs("usage: FrameColorGate CONTROL_REPORT CANDIDATE_REPORT BUILD_MANIFEST FRESH_PAIR_JSON\n",stderr); exit(2) }
let aURL = URL(fileURLWithPath:CommandLine.arguments[1]), bURL = URL(fileURLWithPath:CommandLine.arguments[2])
let manifestURL = URL(fileURLWithPath:CommandLine.arguments[3]), out = URL(fileURLWithPath:CommandLine.arguments[4])
let baselineSHA = "e48fff46b3a92a28465ad74295bd273a9d69af7d", candidateSHA = "ce462b3ef5d11b72d51ddf9158940d686bc7707a"
let originalGUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c", originalCLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
var result: [String:Any] = ["kind":"split_label_color14_no_effect","success":false,"scope":"Selected-label color candidate effect on same-CI macOS14 closed Frame detail only; whole-window differences separate; not full UI or cross-OS equivalence"]
var status: Int32 = 1
do {
    try need(!FileManager.default.fileExists(atPath:out.path),"Fresh gate result required")
    let a = try object(aURL), b = try object(bURL), manifest = try object(manifestURL)
    guard let runID = ProcessInfo.processInfo.environment["GITHUB_RUN_ID"], runID.range(of:"^[0-9]+$",options:.regularExpression) != nil,
          let harness = ProcessInfo.processInfo.environment["GITHUB_SHA"], harness.range(of:"^[0-9a-f]{40}$",options:.regularExpression) != nil else { throw GateFailure(message:"Current CI run/harness identity required") }
    try need(manifest["schema"] as? String == "bern_split_label_color_build_v1" && manifest["success"] as? Bool == true,"Unsuccessful/wrong build manifest")
    try need(manifest["source_sha"] as? String == candidateSHA && manifest["baseline_sha"] as? String == baselineSHA,"Build source mismatch")
    try need(manifest["run_id"] as? String == runID && manifest["harness_sha"] as? String == harness,"Build does not belong to current CI run/harness")
    guard let binaries = manifest["binaries"] as? [String:Any], let gui = binaries["Gallery.app/Contents/MacOS/Gallery"] as? [String:Any], let cli = binaries["bin/gallery"] as? [String:Any],
          let helpers = manifest["helpers"] as? [String:Any], let collector = helpers["FrameColorCapture"] as? [String:Any], let gate = helpers["FrameColorGate"] as? [String:Any] else { throw GateFailure(message:"Missing product/helper build records") }
    for entry in [gui,cli,collector,gate] {
        try need(validSHA(entry["sha256"] as? String) && (entry["bytes"] as? Int ?? 0) > 0,"Invalid built binary hash/length")
    }
    try need(validSHA(collector["source_sha256"] as? String) && validSHA(gate["source_sha256"] as? String),"Missing helper source hashes")
    guard let gateExecutable = Bundle.main.executableURL else { throw GateFailure(message:"Gate executable identity unavailable") }
    let actualGate = try Data(contentsOf:gateExecutable.resolvingSymlinksInPath())
    try need(gate["sha256"] as? String == digest(actualGate) && gate["bytes"] as? Int == actualGate.count,"Actual gate executable differs from build manifest")
    try need(a["source_sha"] as? String == baselineSHA && b["source_sha"] as? String == candidateSHA,"Wrong control/candidate source")
    try need(a["app_executable_sha256"] as? String == originalGUI && a["cli_sha256"] as? String == originalCLI,"Original delivered binary identity mismatch")
    try need(b["app_executable_sha256"] as? String == gui["sha256"] as? String && b["cli_sha256"] as? String == cli["sha256"] as? String,"Candidate binary does not match build manifest")
    try need(a["label"] as? String == "control" && b["label"] as? String == "candidate","Wrong acquisition labels")
    var captures: [[String:Any]] = []
    for report in [a,b] {
        try need(report["success"] as? Bool == true && report["closed_only"] as? Bool == true && report["app_still_running_after_cleanup"] as? Bool == false,"Collector/cleanup failed")
        try need(report["expected_os"] as? Int == 14 && (report["os"] as? String)?.range(of:"^Version 14\\.",options:.regularExpression) != nil,"Actual reported OS must be macOS14")
        try need(report["deadline_seconds"] as? Int == 75,"Collector deadline changed")
        try need(report["ci_run_id"] as? String == runID && report["harness_sha"] as? String == harness,"Acquisition is not current CI run/harness")
        try need(report["collector_executable_sha256"] as? String == collector["sha256"] as? String,"Acquisition collector binary differs from build manifest")
        try need(report["heartbeat_ci_only"] as? Bool == true && report["heartbeat_mode"] as? String == "ci-own-active" && report["local_events_requested"] as? String == "","Expected original CI heartbeat mode")
        try need(report["accessibility_trusted"] as? Bool == true && report["screen_recording"] as? Bool == true && report["post_event_access"] as? Bool == true,"Missing original access preflight")
        guard let normal = report["system_preferences"] as? [String:Any] else { throw GateFailure(message:"Missing normal profile") }
        try need(["reduce_motion","reduce_transparency","increase_contrast"].allSatisfy { normal[$0] as? Bool == false },"Normal motion/transparency/contrast profile required")
        try need(report["row_ledger_enabled"] as? Bool == false && !report.keys.contains(where: { $0.hasPrefix("row_ledger") && $0 != "row_ledger_enabled" }),"Color acquisition forbids row ledger metadata")
        guard let items = report["captures"] as? [[String:Any]], items.count == 1, let capture = items.first else { throw GateFailure(message:"Expected one closed capture") }
        try need(capture["png"] as? String == "frame-closed-light.png" && (capture["stable_equal_comparisons"] as? Int ?? 0) >= 4 && (capture["samples"] as? Int ?? 0) >= 5,"Stable closed capture required")
        guard let ids = capture["window_ids"] as? [Int], ids.count == 1, ids[0] > 0 else { throw GateFailure(message:"Unique closed own window capture required") }
        guard let context = report["final_context"] as? [String:Any] else { throw GateFailure(message:"Missing Frame context") }
        try need(context["caption"] as? Bool == true && context["appearance"] as? String == "Light" && context["volume"] as? String == "closed" && context["video"] as? String == "Paused0" && context["frame_appearance"] as? String == "dark from exact generated source","Frame context differs")
        guard let app = report["app"] as? String, let source = report["source_url"] as? String, let sourceURL = URL(string:source) else { throw GateFailure(message:"Missing source-bound media") }
        let bundled = URL(fileURLWithPath:app).appendingPathComponent("Contents/Resources/media/tides.mp4")
        try need(sourceURL.resolvingSymlinksInPath() == bundled.resolvingSymlinksInPath(),"Clip is not bound to supplied app asset")
        try need(report["bundled_tides_sha256"] as? String == "145a1b5e572bd3ce16207e2b341c0eecb04b4d1e765bf72f5fe3809a24f34957","Original media asset hash differs")
        captures.append(capture)
    }
    try need(a["os"] as? String == b["os"] as? String,"Control/candidate runtime OS differs")
    let aPNG = aURL.deletingLastPathComponent().appendingPathComponent("frame-closed-light.png"), bPNG = bURL.deletingLastPathComponent().appendingPathComponent("frame-closed-light.png")
    let aSHA = digest(try Data(contentsOf:aPNG)), bSHA = digest(try Data(contentsOf:bPNG))
    try need(captures[0]["png_sha256"] as? String == aSHA && captures[1]["png_sha256"] as? String == bSHA,"Actual PNG does not match its capture report")
    result["control_png_sha256"] = aSHA; result["candidate_png_sha256"] = bSHA
    let ar = try Raster(aPNG), br = try Raster(bPNG)
    try need(ar.descriptor == br.descriptor && ar.icc == br.icc,"Decoded PNG layout or ICC differs")
    try need(captures[0]["icc_sha256"] as? String == digest(ar.icc) && captures[1]["icc_sha256"] as? String == digest(br.icc),"Decoded ICC does not match its capture report")
    try need(captures[0]["width"] as? Int == ar.image.width && captures[0]["height"] as? Int == ar.image.height && captures[1]["width"] as? Int == br.image.width && captures[1]["height"] as? Int == br.image.height,"Actual PNG dimensions differ from reports")
    guard let canvas = captures[0]["canvas_screen_top_left_points"] as? [String:Double], let other = captures[1]["canvas_screen_top_left_points"] as? [String:Double], canvas == other else { throw GateFailure(message:"Canvas differs") }
    try need(canvas.values.allSatisfy { $0.isFinite } && canvas["width"] == 920 && canvas["height"] == 668,"Expected finite 920x668 outer window")
    let sx = Double(ar.image.width)/920, sy = Double(ar.image.height)/668
    try need(sx == sy && [1.0,2.0].contains(sx),"Unexpected pixel scale")
    let whole = differences(ar,br,[0,0,ar.image.width,ar.image.height])
    // Frozen historical detail boundary, before observing this new pair.
    let roi = [211,52,920,668].map { Int(Double($0)*sx) }
    let frame = differences(ar,br,roi)
    result["decoded_layout"] = ar.descriptor; result["icc_sha256"] = digest(ar.icc)
    result["whole_window"] = whole; result["frame_detail"] = frame; result["scale"] = sx
    result["frame_roi_points"] = [211,52,920,668]
    result["control_report_sha256"] = digest(try Data(contentsOf:aURL)); result["candidate_report_sha256"] = digest(try Data(contentsOf:bURL))
    result["build_manifest_sha256"] = digest(try Data(contentsOf:manifestURL))
    result["ci_run_id"] = runID; result["harness_sha"] = harness
    result["collector_executable_sha256"] = collector["sha256"]; result["gate_executable_sha256"] = digest(actualGate)
    try need(frame["equal"] as? Bool == true,"Candidate changed macOS14 Frame detail pixels")
    result["success"] = true; status = 0
} catch { result["failure"] = String(describing:error) }
if !FileManager.default.fileExists(atPath:out.path) {
    do { try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]).write(to:out,options:.withoutOverwriting) }
    catch { fputs("Pixel gate result write failed: \(error)\n",stderr); exit(1) }
}
exit(status)
