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
guard CommandLine.arguments.count == 4 else { fputs("usage: PixelGate.swift CONTROL_REPORT OBSERVER_REPORT FRESH_PAIR_JSON\n",stderr); exit(2) }
let aURL = URL(fileURLWithPath:CommandLine.arguments[1]), bURL = URL(fileURLWithPath:CommandLine.arguments[2]), out = URL(fileURLWithPath:CommandLine.arguments[3])
var result: [String:Any] = ["success":false,"scope":"Observer effect on exact e48 closed Frame detail only; whole-window differences reported separately; not cross-OS visual equivalence"]
var status: Int32 = 1
do {
    try need(!FileManager.default.fileExists(atPath:out.path),"Fresh gate result required")
    let a = try object(aURL), b = try object(bURL)
    var captures: [[String:Any]] = []
    for report in [a,b] {
        try need(report["success"] as? Bool == true && report["closed_only"] as? Bool == true && report["app_still_running_after_cleanup"] as? Bool == false,"Collector/cleanup failed")
        try need(report["source_sha"] as? String == "e48fff46b3a92a28465ad74295bd273a9d69af7d","Wrong product source")
        guard let items = report["captures"] as? [[String:Any]], items.count == 1, let capture = items.first else { throw GateFailure(message:"Expected one closed capture") }
        try need(capture["png"] as? String == "frame-closed-light.png" && (capture["stable_equal_comparisons"] as? Int ?? 0) >= 4,"Stable closed capture required")
        guard let context = report["final_context"] as? [String:Any] else { throw GateFailure(message:"Missing Frame context") }
        try need(context["caption"] as? Bool == true && context["appearance"] as? String == "Light" && context["volume"] as? String == "closed" && context["video"] as? String == "Paused0","Frame context differs")
        captures.append(capture)
    }
    try need(a["expected_os"] as? Int == b["expected_os"] as? Int && [13,14].contains(a["expected_os"] as? Int ?? 0),"Same target OS pair required")
    try need(a["bundled_tides_sha256"] as? String == b["bundled_tides_sha256"] as? String,"Media content differs")
    try need(a["row_ledger_enabled"] as? Bool == false && b["row_ledger_enabled"] as? Bool == true,"Control must be off and observer on")
    let aPNG = aURL.deletingLastPathComponent().appendingPathComponent("frame-closed-light.png"), bPNG = bURL.deletingLastPathComponent().appendingPathComponent("frame-closed-light.png")
    let aSHA = digest(try Data(contentsOf:aPNG)), bSHA = digest(try Data(contentsOf:bPNG))
    try need(captures[0]["png_sha256"] as? String == aSHA && captures[1]["png_sha256"] as? String == bSHA,"Actual PNG does not match its capture report")
    result["control_png_sha256"] = aSHA; result["observer_png_sha256"] = bSHA
    let ar = try Raster(aPNG), br = try Raster(bPNG)
    try need(ar.descriptor == br.descriptor && ar.icc == br.icc,"Decoded PNG layout or ICC differs")
    try need(captures[0]["icc_sha256"] as? String == digest(ar.icc) && captures[1]["icc_sha256"] as? String == digest(br.icc),"Decoded ICC does not match its capture report")
    guard let canvas = captures[0]["canvas_screen_top_left_points"] as? [String:Double], let other = captures[1]["canvas_screen_top_left_points"] as? [String:Double], canvas == other else { throw GateFailure(message:"Canvas differs") }
    try need(canvas["width"] == 920 && canvas["height"] == 668,"Expected 920x668 outer window")
    let sx = Double(ar.image.width)/920, sy = Double(ar.image.height)/668
    try need(sx == sy && [1.0,2.0].contains(sx),"Unexpected pixel scale")
    let whole = differences(ar,br,[0,0,ar.image.width,ar.image.height])
    // Frozen historical detail boundary, before observing this new pair.
    let roi = [211,52,920,668].map { Int(Double($0)*sx) }
    let frame = differences(ar,br,roi)
    result["decoded_layout"] = ar.descriptor; result["icc_sha256"] = digest(ar.icc)
    result["whole_window"] = whole; result["frame_detail"] = frame; result["scale"] = sx
    result["frame_roi_points"] = [211,52,920,668]
    result["control_report_sha256"] = digest(try Data(contentsOf:aURL)); result["observer_report_sha256"] = digest(try Data(contentsOf:bURL))
    try need(frame["equal"] as? Bool == true,"Observer changed Frame detail pixels")
    result["success"] = true; status = 0
} catch { result["failure"] = String(describing:error) }
if !FileManager.default.fileExists(atPath:out.path) {
    do { try JSONSerialization.data(withJSONObject:result,options:[.prettyPrinted,.sortedKeys]).write(to:out,options:.withoutOverwriting) }
    catch { fputs("Pixel gate result write failed: \(error)\n",stderr); exit(1) }
}
exit(status)
