// Standalone, fixed-pixel ISO PQ diagnostic. Never linked into Bern.
// HDRToneProbe ORIGINAL_FFB_PQ_PNG OUTPUT_DIRECTORY
import AppKit
import SwiftUI
import ImageIO
import ColorSync
import CryptoKit
import UniformTypeIdentifiers

private struct Failure: Error { let message: String }
private func sha(_ d: Data) -> String { SHA256.hash(data: d).map { String(format: "%02x", $0) }.joined() }
private func rect(_ r: CGRect) -> [String: Double] { ["x":r.minX,"y":r.minY,"width":r.width,"height":r.height] }
private func pq(_ l: Double) -> Double {
    let p = pow(max(0,l)/10000,2610.0/16384)
    return pow((3424.0/4096 + 2413.0/128*p)/(1 + 2392.0/128*p),2523.0/32)
}
private func nits(_ n: Double) -> Double {
    let p = pow(n,32.0/2523)
    return 10000*pow(max(p-3424.0/4096,0)/(2413.0/128-2392.0/128*p),16384.0/2610)
}
private let names = ["white203","white812","red812","green812","blue812","yellow812","warm812","cool812","warm406","pastel812"]
private let levels: [[Double]] = [[203,203,203],[812,812,812],[812,0,0],[0,812,0],[0,0,812],[812,812,0],[812,406,203],[203,406,812],[406,203,101.5],[812,609,406]]
private func writePNG(_ image: CGImage, _ url: URL) throws {
    guard let d = CGImageDestinationCreateWithURL(url as CFURL,UTType.png.identifier as CFString,1,nil) else { throw Failure(message:"Cannot create PNG") }
    CGImageDestinationAddImage(d,image,nil)
    guard CGImageDestinationFinalize(d) else { throw Failure(message:"Cannot finish PNG") }
}
private func colorInfo(_ image: CGImage) -> [String: Any] {
    guard let s = image.colorSpace, let data = s.copyICCData() else { return ["icc_available":false] }
    let icc = data as Data
    let profile = ColorSyncProfileCreate(icc as CFData,nil)!.takeRetainedValue()
    let tag = ColorSyncProfileCopyTag(profile,"cicp" as CFString)?.takeRetainedValue() as Data?
    return ["icc_available":true,"name":s.name as String? ?? "unnamed","icc_sha256":sha(icc),"icc_bytes":icc.count,
            "cicp_hex":tag?.map { String(format:"%02x",$0) }.joined() ?? "absent",
            "uses_2100":CGColorSpaceUsesITUR_2100TF(s),"is_pq":CGColorSpaceIsPQBased(s)]
}
private func rgb16(_ image: CGImage) throws -> Data {
    let order = image.bitmapInfo.intersection(.byteOrderMask), channels = image.bitsPerPixel/16
    guard image.bitsPerComponent == 16, [3,4].contains(channels), [.byteOrder16Big,.byteOrder16Little].contains(order) else { throw Failure(message:"Unexpected decoded 16-bit layout") }
    let first = [CGImageAlphaInfo.first,.premultipliedFirst,.noneSkipFirst].contains(image.alphaInfo) ? 1 : 0
    let bytes = [UInt8](image.dataProvider!.data! as Data); var result = Data(); result.reserveCapacity(image.width*image.height*6)
    for y in 0..<image.height { for x in 0..<image.width { for c in 0..<3 {
        let at = y*image.bytesPerRow+(x*channels+first+c)*2
        result.append(bytes[at+(order == .byteOrder16Big ? 0 : 1)]); result.append(bytes[at+(order == .byteOrder16Big ? 1 : 0)])
    } } }
    return result
}
private struct Atlas {
    let images: [(String,CGImage)]
    let metadata: [[String: Any]]
    init(original: URL, output: URL) throws {
        let originalData = try Data(contentsOf:original)
        guard sha(originalData) == "96f80d2f1c06070dac29e3b7e2924a6aed8e54286bc73921f62cf75420a599ed",
              let input = CGImageSourceCreateWithData(originalData as CFData,nil), let old = CGImageSourceCreateImageAtIndex(input,0,nil),
              let icc = old.colorSpace?.copyICCData(), let custom = CGColorSpace(iccData:icc) else { throw Failure(message:"Original ffb fixture/ICC unavailable") }
        let codes = levels.map { $0.map { UInt16((pq($0)*65535).rounded()) } }
        let ramp = (0..<640).map { UInt16((pq(812*Double($0)/639)*65535).rounded()) }
        var raw = Data(); raw.reserveCapacity(640*360*8)
        for y in 0..<360 { for x in 0..<640 {
            let rgb = y < 240 ? codes[(y/120)*5+x/128] : [UInt16](repeating:ramp[x],count:3)
            for v in rgb+[65535] { raw.append(UInt8(v>>8)); raw.append(UInt8(v&255)) }
        } }
        var images: [(String,CGImage)] = [], metadata: [[String:Any]] = []
        for (name,space) in [("named-pq",CGColorSpace(name:CGColorSpace.itur_2100_PQ)!),("ffb-icc",custom)] {
            let image = CGImage(width:640,height:360,bitsPerComponent:16,bitsPerPixel:64,bytesPerRow:640*8,space:space,
                bitmapInfo:CGBitmapInfo(rawValue:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder16Big.rawValue),
                provider:CGDataProvider(data:raw as CFData)!,decode:nil,shouldInterpolate:true,intent:.defaultIntent)!
            let url = output.appendingPathComponent("source-\(name).png"); try writePNG(image,url)
            let saved = CGImageSourceCreateImageAtIndex(CGImageSourceCreateWithURL(url as CFURL,nil)!,0,nil)!
            guard saved.width == 640, saved.height == 360, try rgb16(saved) == rgb16(image) else { throw Failure(message:"PNG writer changed source codes") }
            images.append((name,image)); metadata.append(["name":name,"png":url.lastPathComponent,"png_sha256":sha(try Data(contentsOf:url)),
                "raw_rgba16be_sha256":sha(raw),"raw_rgb16be_sha256":sha(try rgb16(image)),"color":colorInfo(image),"saved_png_color":colorInfo(saved),
                "decoded_png_bitmap_info":saved.bitmapInfo.rawValue,"decoded_png_bytes_per_row":saved.bytesPerRow])
        }
        self.images = images; self.metadata = metadata
    }
}
private struct Frames: PreferenceKey {
    static var defaultValue: [String:CGRect] = [:]
    static func reduce(value: inout [String:CGRect], nextValue: ()->[String:CGRect]) { value.merge(nextValue(),uniquingKeysWith:{$1}) }
}
@MainActor private final class State { var frames: [String:CGRect] = [:] }
private struct Content: View {
    let atlas: Atlas; let receive: ([String:CGRect])->Void
    @ViewBuilder private func picture(_ image: CGImage) -> some View {
        if #available(macOS 14,*) { Image(decorative:image,scale:1).resizable().allowedDynamicRange(.high) }
        else { Image(decorative:image,scale:1).resizable() }
    }
    var body: some View {
        VStack(alignment:.leading,spacing:8) {
            Text("ISO PQ • explicit absolute-nit samples").font(.headline)
            HStack(spacing:24) { ForEach(atlas.images.indices,id:\.self) { i in
                VStack(spacing:4) { Text(atlas.images[i].0).font(.caption)
                    picture(atlas.images[i].1).frame(width:320,height:180).background(GeometryReader { g in
                        Color.clear.preference(key:Frames.self,value:[atlas.images[i].0:g.frame(in:.named("content"))])
                    })
                }
            } }
        }.padding(16).frame(width:696,height:260,alignment:.topLeading).coordinateSpace(name:"content")
            .onPreferenceChange(Frames.self,perform:receive).environment(\.colorScheme,.light)
    }
}
private final class NonKeyWindow: NSWindow { override var canBecomeKey: Bool { false }; override var canBecomeMain: Bool { false } }
private func pixels(_ image: CGImage) throws -> Data {
    var bytes = [UInt8](repeating:0,count:image.width*image.height*4)
    try bytes.withUnsafeMutableBytes { buffer in
        guard let context = CGContext(data:buffer.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,
            space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else { throw Failure(message:"Cannot canonicalize capture") }
        context.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    }; return Data(bytes)
}
@main private enum Main {
    @MainActor static func main() { exit(run()) }
    @MainActor static func run() -> Int32 {
        guard CommandLine.arguments.count == 3 else { fputs("HDRToneProbe ORIGINAL_PQ_PNG OUTPUT\n",stderr); return 2 }
        let output = URL(fileURLWithPath:CommandLine.arguments[2],isDirectory:true), began = Date()
        let before = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window: NSWindow?, report: [String:Any] = ["success":false,"harness_sha":ProcessInfo.processInfo.environment["BERN_PROBE_SHA"] ?? "local"]
        defer {
            window?.orderOut(nil); window?.close()
            if NSWorkspace.shared.frontmostApplication?.processIdentifier == getpid() { _ = NSRunningApplication(processIdentifier:before)?.activate(options:[]) }
            report["frontmost_pid_before"] = before; report["frontmost_pid_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["elapsed_seconds"] = Date().timeIntervalSince(began)
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            let atlas = try Atlas(original:URL(fileURLWithPath:CommandLine.arguments[1]),output:output)
            let app = NSApplication.shared; app.setActivationPolicy(.accessory); app.appearance = NSAppearance(named:.aqua); app.finishLaunching()
            let state = State(), host = NSHostingView(rootView:Content(atlas:atlas,receive:{ state.frames=$0 }))
            let w = NonKeyWindow(contentRect:CGRect(x:100,y:100,width:696,height:260),styleMask:[.titled],backing:.buffered,defer:false)
            window=w; w.isReleasedWhenClosed=false; w.isRestorable=false; w.title="Bern HDR tone probe"; w.contentView=host; w.orderBack(nil)
            for _ in 0..<30 { host.layoutSubtreeIfNeeded(); RunLoop.main.run(until:Date(timeIntervalSinceNow:0.1)); if state.frames.count == 2 { break } }
            guard state.frames.count == 2 else { throw Failure(message:"Missing image geometry") }
            RunLoop.main.run(until:Date(timeIntervalSinceNow:1))
            var captures: [[String:Any]] = [], hashes: [String] = []
            for frame in 0..<4 {
                guard Date().timeIntervalSince(began)<45, w.isVisible, !w.isKeyWindow,
                      let info = (CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first,
                      info[kCGWindowIsOnscreen as String] as? Bool == true,
                      let shot = CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming), let screen=w.screen else { throw Failure(message:"Real nonkey WindowServer capture unavailable; no offscreen fallback") }
                let filename="capture-\(frame).png"; try writePNG(shot,output.appendingPathComponent(filename)); let digest=sha(try pixels(shot)); hashes.append(digest)
                var rois: [String:Any] = [:]
                for (name,f) in state.frames {
                    guard abs(f.width-320)<0.01, abs(f.height-180)<0.01 else { throw Failure(message:"Unexpected image size") }
                    let local = host.isFlipped ? f : CGRect(x:f.minX,y:host.bounds.height-f.maxY,width:f.width,height:f.height)
                    let win = host.convert(local,to:nil), top = CGRect(x:win.minX,y:w.frame.height-win.maxY,width:win.width,height:win.height)
                    let imagePixels=CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height)
                    func mapped(_ r: CGRect) -> CGRect { CGRect(x:imagePixels.minX+r.minX/640*imagePixels.width,y:imagePixels.minY+r.minY/360*imagePixels.height,width:r.width/640*imagePixels.width,height:r.height/360*imagePixels.height) }
                    func mean(_ r: CGRect) throws -> Double {
                        guard let crop=shot.cropping(to:mapped(r).integral) else { throw Failure(message:"Invalid image ROI") }
                        let data=[UInt8](try pixels(crop)); return Double(data.enumerated().filter{$0.offset%4<3}.reduce(0){$0+Int($1.element)})/Double(crop.width*crop.height*3)
                    }
                    let low=try mean(CGRect(x:4,y:260,width:24,height:80)), high=try mean(CGRect(x:612,y:260,width:24,height:80))
                    guard high>150, high-low>80, shot.colorSpace?.copyICCData() != nil else { throw Failure(message:"Captured image is blank or lacks a color profile") }
                    rois[name] = ["host_top_left_points":rect(f),"window_top_left_points":rect(top),"screenshot_pixels":rect(imagePixels),"ramp_low_high_srgb_mean":[low,high],
                        "patch_sample_pixels":Dictionary(uniqueKeysWithValues:names.enumerated().map { i,n in (n,rect(mapped(CGRect(x:(i%5)*128+8,y:(i/5)*120+8,width:112,height:104)))) })]
                }
                captures.append(["png":filename,"png_sha256":sha(try Data(contentsOf:output.appendingPathComponent(filename))),"rgba8_srgb_sha256":digest,"png_color":colorInfo(shot),
                    "width":shot.width,"height":shot.height,"image_rois":rois,"window_frame":rect(w.frame),"screen_frame":rect(screen.frame),
                    "current_headroom":screen.maximumExtendedDynamicRangeColorComponentValue,"potential_headroom":screen.maximumPotentialExtendedDynamicRangeColorComponentValue,
                    "key":w.isKeyWindow,"active":app.isActive,"window_number":w.windowNumber,"timestamp":Date().timeIntervalSince1970])
                report["captures"]=captures; RunLoop.main.run(until:Date(timeIntervalSinceNow:0.2))
            }
            report.merge(["os":ProcessInfo.processInfo.operatingSystemVersionString,"sources":atlas.metadata,"capture_contract":"Four real WindowServer frames; exact canonical RGBA8 sRGB equality; no offscreen fallback",
                "scope":"SDR output identifies only neutral/color behavior in this display state; not HDR hardware, metadata policy, or a unique algorithm",
                "source_contract":"RGBA16BE BT.2020 PQ, alpha1; explicit BT.2100 inverse EOTF; source PNG RGB codes round-trip unchanged; no ImageIO reference-white conversion",
                "patches":names.enumerated().map { i,n in ["name":n,"source_rect":rect(CGRect(x:(i%5)*128,y:(i/5)*120,width:128,height:120)),"input_nit":levels[i],"pq_u16":levels[i].map{Int((pq($0)*65535).rounded())},"quantized_nit":levels[i].map{nits((pq($0)*65535).rounded()/65535)}] as [String:Any] },
                "ramp":["source_rect":rect(CGRect(x:0,y:240,width:640,height:120)),"nit_formula":"812*x/639, x=0...639; encoded as round(PQ(nit)*65535)"],
                "color_caveat":"BT.2020 saturated patches can exceed output gamut; compare complete color-management pipelines, not scalar curves alone",
                "native_allowed_dynamic_range_high":ProcessInfo.processInfo.isOperatingSystemAtLeast(OperatingSystemVersion(majorVersion:14,minorVersion:0,patchVersion:0))],uniquingKeysWith:{$1})
            guard hashes.count==4, Set(hashes).count==1 else { throw Failure(message:"Four WindowServer buffers did not agree exactly") }
            report["success"]=true; return 0
        } catch { report["error"]=String(describing:error); fputs("HDR tone probe failed: \(error)\n",stderr); return 1 }
    }
}
