import AppKit
import SwiftUI
import MetalKit
import CoreImage
import ColorSync
import ImageIO
import UniformTypeIdentifiers
import CryptoKit

private struct Failure: Error { let message: String }
private enum BernImage {
struct Picture: @unchecked Sendable {
        let image: CGImage
        let orientation: SwiftUI.Image.Orientation
        /// Width over height as shown, after the orientation.
        let ratio: CGFloat
        #if os(macOS)
        /// Classified once during decode; the original image and ICC stay intact.
        let legacyHDRColorSpace: CGColorSpace?
        #endif
    }
private nonisolated static func legacyHDRColorSpace(_ image: CGImage) -> CGColorSpace? {
        guard let space = image.colorSpace else { return nil }
        if CGColorSpaceUsesITUR_2100TF(space) { return space }
        if #available(macOS 14, *) { return nil }
        // Ventura can colour-convert a newer ICC's lookup tables without
        // recognizing its HDR transfer-function flag. Read the standard CICP
        // tag through ColorSync instead of inferring HDR from a profile name.
        // ICC.1:2022 cicpType is 12 bytes: type, reserved, then four code points.
        guard space.model == .rgb, let data = space.copyICCData(),
              let profile = ColorSyncProfileCreate(data, nil)?.takeRetainedValue(),
              let tag = ColorSyncProfileCopyTag(profile, "cicp" as CFString)?.takeRetainedValue()
        else { return nil }
        let bytes = [UInt8](tag as Data)
        guard bytes.count == 12,
              bytes[0...3].elementsEqual([0x63, 0x69, 0x63, 0x70]),
              bytes[4...7].allSatisfy({ $0 == 0 }),
              bytes[8] == 9, (bytes[9] == 16 || bytes[9] == 18),
              bytes[10] == 0, bytes[11] == 1
        else { return nil }
        return CGColorSpace(name: bytes[9] == 16 ? CGColorSpace.itur_2100_PQ : CGColorSpace.itur_2100_HLG)
    }
    static func load(_ url: URL) throws -> Picture {
        guard let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let image = CGImageSourceCreateImageAtIndex(source, 0, nil) else { throw Failure(message: "ImageIO decode failed") }
        let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any]
        guard (properties?[kCGImagePropertyOrientation] as? UInt32 ?? 1) == 1 else { throw Failure(message:"Atlas EXIF must be up") }
        return Picture(image:image, orientation:.up, ratio:CGFloat(image.width)/CGFloat(image.height), legacyHDRColorSpace:legacyHDRColorSpace(image))
    }
}
private func digest(_ data: Data) -> String { SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined() }
private func rect(_ r: CGRect) -> [String:Double] { ["x":r.minX,"y":r.minY,"width":r.width,"height":r.height] }
private struct Frames: PreferenceKey {
    static var defaultValue: [String:CGRect] = [:]
    static func reduce(value: inout [String:CGRect], nextValue:()->[String:CGRect]) { value.merge(nextValue(),uniquingKeysWith:{$1}) }
}
@MainActor private final class State { var frames: [String:CGRect] = [:] }
private struct NativeImageView: NSViewRepresentable {
    let image: CGImage
    func makeNSView(context: Context) -> NSImageView {
        let v = NSImageView(frame:.zero); v.imageScaling = .scaleAxesIndependently; v.imageFrameStyle = .none; return v
    }
    func updateNSView(_ view: NSImageView, context: Context) { view.image = NSImage(cgImage:image,size:NSSize(width:320,height:180)) }
    static func dismantleNSView(_ view:NSImageView,coordinator:()) {view.image=nil}
}
private func bitmapSDR(_ image:CGImage) throws -> CGImage {
    guard let c=CGContext(data:nil,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else {throw Failure(message:"Cannot create8bit sRGB context")}
    c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    guard let result=c.makeImage() else {throw Failure(message:"Cannot extract sRGB bitmap")};return result
}
private let labels = ["nsimageview-named","cgcontext8-srgb","native-swiftui-named"]
private struct Content: View {
    let pictures: [BernImage.Picture]
    let bitmap: CGImage
    let receive: ([String:CGRect])->Void
    @ViewBuilder private func image(_ index: Int) -> some View {
        if index == 0 { NativeImageView(image:pictures[1].image) }
        else if index == 1 { SwiftUI.Image(decorative:bitmap,scale:1).resizable() }
        else { SwiftUI.Image(decorative:pictures[1].image,scale:1,orientation:pictures[1].orientation).resizable() }
    }
    var body: some View {
        HStack(spacing:16) {
            ForEach(0..<3,id:\.self) { index in
                VStack(spacing:6) {
                    Text(labels[index]).font(.caption)
                    image(index).frame(width:320,height:180).clipped()
                        .background(GeometryReader { g in Color.clear.preference(key:Frames.self,value:[labels[index]:g.frame(in:.named("content"))]) })
                }
            }
        }
        .padding(16).frame(width:1024,height:240,alignment:.topLeading)
        .coordinateSpace(name:"content").onPreferenceChange(Frames.self,perform:receive)
        .environment(\.colorScheme,.light)
    }
}
private final class NonKeyWindow: NSWindow {
    override var canBecomeKey:Bool {false}
    override var canBecomeMain:Bool {false}
}
private func canonical(_ image:CGImage) throws -> Data {
    var bytes=[UInt8](repeating:0,count:image.width*image.height*4)
    try bytes.withUnsafeMutableBytes { buffer in
        guard let c=CGContext(data:buffer.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else { throw Failure(message:"sRGB capture conversion failed") }
        c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    }
    return Data(bytes)
}
private func color(_ image:CGImage)->[String:Any] {
    guard let space=image.colorSpace else{return [:]}
    var result:[String:Any]=["name":space.name as String? ?? "unnamed","uses_2100":CGColorSpaceUsesITUR_2100TF(space),"is_pq":CGColorSpaceIsPQBased(space)]
    if let icc=space.copyICCData() {
        result["icc_sha256"]=digest(icc as Data)
        if let profile=ColorSyncProfileCreate(icc,nil)?.takeRetainedValue(),let tag=ColorSyncProfileCopyTag(profile,"cicp" as CFString)?.takeRetainedValue() {result["cicp_hex"]=(tag as Data).map{String(format:"%02x",$0)}.joined()}
    }
    return result
}

// Fixture-only EDR request, using prototype Display.refresh's potential-based policy.
// A constant linear2 clear is presented; no tone-mapping formula is used or changed.
@MainActor private final class EDRRequestView: MTKView {
    private let commands:MTLCommandQueue
    private var high=false
    init(requestSurface:Bool) throws {
        guard let device=MTLCreateSystemDefaultDevice(),let queue=device.makeCommandQueue() else{throw Failure(message:"No Metal request surface")}
        commands=queue
        super.init(frame:NSRect(x:4,y:4,width:8,height:8),device:device)
        colorPixelFormat = .rgba16Float;framebufferOnly=true;isPaused=true;enableSetNeedsDisplay=true
        let l=layer as! CAMetalLayer;l.colorspace=CGColorSpace(name:CGColorSpace.extendedLinearITUR_2020);l.isOpaque=true;l.wantsExtendedDynamicRangeContent=false
    }
    required init(coder:NSCoder){fatalError()}
    func request(_ high:Bool) {
        self.high=high
        (layer as! CAMetalLayer).wantsExtendedDynamicRangeContent=high && (window?.screen?.maximumPotentialExtendedDynamicRangeColorComponentValue ?? 1)>1
        needsDisplay=true
    }
    override func draw(_ dirty:NSRect) {
        clearColor=MTLClearColorMake(high ? 2:0,high ? 2:0,high ? 2:0,1)
        guard let pass=currentRenderPassDescriptor,let drawable=currentDrawable,let command=commands.makeCommandBuffer(),let encoder=command.makeRenderCommandEncoder(descriptor:pass) else{return}
        encoder.endEncoding();command.present(drawable);command.commit()
    }
    func stop(){(layer as! CAMetalLayer).wantsExtendedDynamicRangeContent=false;isPaused=true;releaseDrawables();removeFromSuperview()}
}

@main private enum Main {
    @MainActor static func main() { exit(run()) }
    @MainActor static func run()->Int32 {
        guard CommandLine.arguments.count==4 else {return 2}
        let output=URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
        let before=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window:NSWindow?,host:NSHostingView<Content>?
        var requestView:EDRRequestView?
        var report:[String:Any]=["success":false,"scope":"Public native macOS13 NSImageView and native SwiftUI namedPQ under actual current headroom1->potential->1, fixture-only constant linear2 request; no product mapper/High or macOS14 equivalence","os":ProcessInfo.processInfo.operatingSystemVersionString]
        var windowBegan:Date?
        defer {
            var metalCount=0,softwareCount=0
            func stop(_ view:NSView) {
                if let v=view as? NSImageView {v.image=nil;softwareCount+=1}
                view.subviews.forEach(stop)
            }
            requestView?.stop()
            if let host {stop(host)}
            window?.contentView=nil;window?.orderOut(nil);window?.close()
            if let began=windowBegan {report["window_seconds"]=Date().timeIntervalSince(began)}
            report["stopped_metal_views"]=metalCount;report["stopped_software_views"]=softwareCount
            report["frontmost_pid_before"]=before;report["frontmost_pid_after"]=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["activation_calls"]=0
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            let urls=CommandLine.arguments[1...2].map {URL(fileURLWithPath:$0)}
            let loaded=try urls.map {try BernImage.load($0)}
            guard let named=loaded[1].image.copy(colorSpace:CGColorSpace(name:CGColorSpace.itur_2100_PQ)!),named.dataProvider!.data! as Data == loaded[1].image.dataProvider!.data! as Data else{throw Failure(message:"copy(namedPQ) changed decoded bytes")}
            let pictures=[loaded[0],BernImage.Picture(image:named,orientation:.up,ratio:loaded[1].ratio,legacyHDRColorSpace:named.colorSpace)]
            let bitmap=try bitmapSDR(named)
            report["named_pq_copy_provider_bytes_unchanged"]=true
            report["cgcontext_output_color"]=color(bitmap)
            report["cgcontext_bits_per_component"]=bitmap.bitsPerComponent
            report["sources"]=zip(urls,pictures).map {url,p in ["file":url.lastPathComponent,"file_sha256":digest(try! Data(contentsOf:url)),"decoded_color":color(p.image),"normalized_space":p.legacyHDRColorSpace?.name as String? ?? "nil","width":p.image.width,"height":p.image.height,"bits_per_component":p.image.bitsPerComponent,"bitmap_info":p.image.bitmapInfo.rawValue,"provider_sha256":digest(p.image.dataProvider!.data! as Data)] as [String:Any]}
            let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
            let state=State(),h=NSHostingView(rootView:Content(pictures:pictures,bitmap:bitmap,receive:{state.frames=$0}));host=h
            let w=NonKeyWindow(contentRect:CGRect(x:100,y:100,width:1024,height:240),styleMask:[.titled],backing:.buffered,defer:false)
            window=w;w.isReleasedWhenClosed=false;w.isRestorable=false;w.title="Bern native SDR headroom probe 6A93";w.contentView=h
            windowBegan=Date();w.orderBack(nil)
            let edrRequest=try EDRRequestView(requestSurface:true);requestView=edrRequest;h.addSubview(edrRequest);edrRequest.request(false)
            let deadline=Date(timeIntervalSinceNow:7.5)
            let phaseNames=["headroom1-initial","headroom2-requested","headroom1-returned"]
            var phase=0,hashes:[String]=[],captures:[[String:Any]]=[],last:CGImage?,stages:[[String:Any]]=[]
            while Date()<deadline {
                h.layoutSubtreeIfNeeded();RunLoop.main.run(until:Date(timeIntervalSinceNow:0.12))
                guard state.frames.count==3,let screen=w.screen else{continue}
                let current=screen.maximumExtendedDynamicRangeColorComponentValue,potential=screen.maximumPotentialExtendedDynamicRangeColorComponentValue
                let ready=phase==1 ? (potential>1 && current>=potential*0.995) : current<=1.001
                guard ready else{hashes=[];captures=[];continue}
                guard w.isVisible,!w.isKeyWindow,!app.isActive,
                      let info=(CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first,info[kCGWindowIsOnscreen as String] as? Bool==true,
                      let shot=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming) else {throw Failure(message:"Nonkey real WindowServer capture failed")}
                let hash=digest(try canonical(shot))
                if hashes.last != hash {hashes=[];captures=[]}
                hashes.append(hash);last=shot
                captures.append(["rgba8_srgb_sha256":hash,"current_headroom":current,"potential_headroom":potential,"active":app.isActive,"key":w.isKeyWindow,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
                if hashes.count>=2 {
                    let name=phaseNames[phase]+".png"
                    let target=CGImageDestinationCreateWithURL(output.appendingPathComponent(name) as CFURL,UTType.png.identifier as CFString,1,nil)!
                    CGImageDestinationAddImage(target,shot,nil);guard CGImageDestinationFinalize(target) else{throw Failure(message:"Phase PNG failed")}
                    stages.append(["phase":phaseNames[phase],"png":name,"current_headroom":current,"potential_headroom":potential,"capture_buffers":captures,"elapsed_seconds":Date().timeIntervalSince(windowBegan!)])
                    report["stages"]=stages
                    phase+=1
                    if phase==3 {break}
                    edrRequest.request(phase==1);hashes=[];captures=[]
                }
            }
            report["completed_phases"]=phase
            guard phase==3,let shot=last else{throw Failure(message:"7.5-second collection deadline; actual headroom transition incomplete")}
            var frames:[String:Any]=[:]
            for (name,f) in state.frames {
                guard f.width==320,f.height==180 else{throw Failure(message:"Image geometry mismatch")}
                let local=h.isFlipped ? f : CGRect(x:f.minX,y:h.bounds.height-f.maxY,width:f.width,height:f.height)
                let win=h.convert(local,to:nil),top=CGRect(x:win.minX,y:w.frame.height-win.maxY,width:win.width,height:win.height)
                frames[name]=["host_top_left_points":rect(f),"screenshot_pixels":rect(CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height))]
            }
            var edr:[Bool]=[]
            func inspect(_ v:NSView) {if let m=v as? MTKView,m !== requestView {edr.append((m.layer as? CAMetalLayer)?.wantsExtendedDynamicRangeContent ?? true)};v.subviews.forEach(inspect)}
            inspect(h)
            var nativeBounds:[[String:Any]]=[]
            func native(_ v:NSView) {if let n=v as? NSImageView {nativeBounds.append(["bounds":rect(n.bounds),"frame":rect(n.frame),"image_size":n.image.map { ["width":$0.size.width,"height":$0.size.height] } ?? [:]])};v.subviews.forEach(native)}
            native(h)
            guard nativeBounds.count==1,let b=nativeBounds.first?["bounds"] as? [String:Double],b["width"]==320,b["height"]==180 else {throw Failure(message:"NSImageView native bounds mismatch")}
            report["native_nsimageview_geometry"]=nativeBounds
            guard edr.isEmpty else{throw Failure(message:"Unexpected Metal view in public-component fixture")}
            let dest=CGImageDestinationCreateWithURL(output.appendingPathComponent("capture.png") as CFURL,UTType.png.identifier as CFString,1,nil)!
            CGImageDestinationAddImage(dest,shot,nil);guard CGImageDestinationFinalize(dest) else{throw Failure(message:"Cannot write capture")}
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier==before else{throw Failure(message:"Foreground changed; no activation attempted")}
            report["frames"]=frames;report["captures"]=captures;report["stable_buffer_count"]=hashes.count;report["png_size"]=[shot.width,shot.height];report["png_color"]=color(shot);report["product_edr_requests"]=edr;report["capture_png_sha256"]=digest(try Data(contentsOf:output.appendingPathComponent("capture.png")));report["success"]=true
            return 0
        } catch {report["error"]=String(describing:error);fputs("Standard color fixture failed: \(error)\n",stderr);return 1}
    }
}
