// Work-only bounded Standard stability test. No Bern product source linked.
// Probe NAMED_PQ_ATLAS ORIGINAL_NEUTRAL_PQ OUTPUT
import AppKit
import SwiftUI
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

private struct Failure:Error {let message:String}
private func sha(_ d:Data)->String {SHA256.hash(data:d).map{String(format:"%02x",$0)}.joined()}
private func rect(_ r:CGRect)->[String:Double] {["x":r.minX,"y":r.minY,"width":r.width,"height":r.height]}
private struct Frames:PreferenceKey {
    static var defaultValue:[String:CGRect]=[:]
    static func reduce(value:inout [String:CGRect],nextValue:()->[String:CGRect]){value.merge(nextValue(),uniquingKeysWith:{$1})}
}
@MainActor private final class Geometry {var frames:[String:CGRect]=[:]}
private struct NativeImage:NSViewRepresentable {
    let image:CGImage
    func makeNSView(context:Context)->NSImageView {let v=NSImageView(frame:.zero);v.imageScaling = .scaleAxesIndependently;v.imageFrameStyle = .none;return v}
    func updateNSView(_ view:NSImageView,context:Context){view.image=NSImage(cgImage:image,size:NSSize(width:320,height:180))}
    static func dismantleNSView(_ view:NSImageView,coordinator:()){view.image=nil}
}
private struct Content:View {
    let image:CGImage,receive:([String:CGRect])->Void
    var body:some View {
        HStack(spacing:16) {
            item("nsimageview-named") {NativeImage(image:image)}
            item("native-swiftui-named") {Image(decorative:image,scale:1).resizable()}
        }.padding(16).frame(width:688,height:240,alignment:.topLeading)
            .coordinateSpace(name:"content").onPreferenceChange(Frames.self,perform:receive).environment(\.colorScheme,.light)
    }
    private func item<V:View>(_ name:String,@ViewBuilder picture:()->V)->some View {
        VStack(spacing:6) {Text(name).font(.caption);picture().frame(width:320,height:180).clipped()
            .background(GeometryReader {g in Color.clear.preference(key:Frames.self,value:[name:g.frame(in:.named("content"))])})}
    }
}
private final class NonKeyWindow:NSWindow {override var canBecomeKey:Bool {false};override var canBecomeMain:Bool {false}}
private func canonical(_ image:CGImage)throws->Data {
    var bytes=[UInt8](repeating:0,count:image.width*image.height*4)
    try bytes.withUnsafeMutableBytes {b in
        guard let c=CGContext(data:b.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else {throw Failure(message:"Canonical sRGB conversion failed")}
        c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    };return Data(bytes)
}
private func writePNG(_ image:CGImage,_ path:URL)throws {
    guard let d=CGImageDestinationCreateWithURL(path as CFURL,UTType.png.identifier as CFString,1,nil) else {throw Failure(message:"PNG destination failed")}
    CGImageDestinationAddImage(d,image,nil);guard CGImageDestinationFinalize(d) else {throw Failure(message:"PNG write failed")}
}
@main private enum Main {
    @MainActor static func main(){exit(run())}
    @MainActor private static func run()->Int32 {
        guard CommandLine.arguments.count==4 else {return 2}
        let source=URL(fileURLWithPath:CommandLine.arguments[1]),neutral=URL(fileURLWithPath:CommandLine.arguments[2]),output=URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
        let before=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window:NSWindow?,host:NSHostingView<Content>?,driver:ToneView?,began:Date?,watchdog:DispatchSourceTimer?
        var trajectory:[[String:Any]]=[],captures:[[String:Any]]=[],phases:[[String:Any]]=[]
        var report:[String:Any]=["success":false,"activation_calls":0,"scope":"Actual13 Standard candidate stability under another visible native linear-EDR driver. Bare NSImageView and bare native SwiftUI Image; no product mapper or14 High acceptance. Screenshot constancy cannot prove physical-panel or hidden native linear-buffer clamping.","collection_limit_seconds":7.2,"watchdog_seconds":7.9,"image_contract":"Same normally decoded namedPQ CGImage, copy(colorSpace:namedPQ) provider bytes unchanged; two320x180pt views. No allowedDynamicRange modifier.","ordering":"Own nonkey window orderFrontRegardless; no activate/makeKey or foreground restoration calls."]
        defer {
            driver?.stop();driver?.removeFromSuperview()
            func releaseNativeImages(_ view:NSView){if let v=view as? NSImageView {v.image=nil};view.subviews.forEach(releaseNativeImages)}
            if let host {releaseNativeImages(host)}
            host?.removeFromSuperview()
            window?.contentView=nil;window?.orderOut(nil);window?.close();watchdog?.cancel()
            if let began {report["window_seconds"]=Date().timeIntervalSince(began)}
            report["trajectory"]=trajectory;report["captures"]=captures;report["phases"]=phases
            report["driver_submissions"]=submissionEvents;report["driver_completed_texture_readbacks"]=textureSamples;report["real_screen_notifications"]=osEvents
            report["frontmost_before"]=before;report["frontmost_after"]=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["os"]=ProcessInfo.processInfo.operatingSystemVersionString
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            guard let input=CGImageSourceCreateWithURL(source as CFURL,nil),let decoded=CGImageSourceCreateImageAtIndex(input,0,nil),decoded.width==640,decoded.height==360,
                  let named=decoded.copy(colorSpace:CGColorSpace(name:CGColorSpace.itur_2100_PQ)!),decoded.dataProvider!.data! as Data == named.dataProvider!.data! as Data else {throw Failure(message:"NamedPQ atlas decode/unchanged-provider contract failed")}
            report["atlas_sha256"]=sha(try Data(contentsOf:source));report["provider_copy_bytes_unchanged"]=true
            let fixture=PQFixture(neutral)
            guard let device=MTLCreateSystemDefaultDevice() else {throw Failure(message:"No Metal device")}
            let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
            let geometry=Geometry(),h=NSHostingView(rootView:Content(image:named,receive:{geometry.frames=$0}));host=h
            let root=ProofRoot(frame:CGRect(x:0,y:0,width:912,height:240));h.frame=CGRect(x:0,y:0,width:688,height:240);root.addSubview(h)
            let d=ToneView(fixture:fixture,name:"Existing192x108HighDriver",frame:CGRect(x:704,y:48,width:192,height:108),device:device);driver=d;root.addSubview(d)
            let label=NSTextField(labelWithString:"Native linear EDR driver");label.frame=CGRect(x:704,y:172,width:192,height:24);root.addSubview(label)
            let w=NonKeyWindow(contentRect:CGRect(x:100,y:100,width:912,height:240),styleMask:[.titled],backing:.buffered,defer:false);window=w
            w.isReleasedWhenClosed=false;w.isRestorable=false;w.title="Bern Standard stability bounded test C1F8";w.contentView=root
            let timer=DispatchSource.makeTimerSource(queue:.global(qos:.userInitiated));watchdog=timer
            timer.setEventHandler {
                try? Data("Own probe process stopped at7.9second watchdog; report may be incomplete.\n".utf8).write(to:output.appendingPathComponent("hard-deadline.txt"))
                _exit(124)
            }
            began=Date();timer.schedule(deadline:.now()+7.9);timer.resume();w.orderFrontRegardless()
            let deadline=Date(timeIntervalSinceNow:7.2),initialFrame=w.frame
            let names=["headroom1-initial","headroom-potential-requested","headroom1-returned"]
            var phase=0,consecutiveReady=0
            prototypeStage=names[0];d.high=false;d.refresh()
            while Date()<deadline && phase<3 {
                h.layoutSubtreeIfNeeded();root.layoutSubtreeIfNeeded();RunLoop.main.run(until:Date(timeIntervalSinceNow:0.08))
                guard let screen=w.screen else {throw Failure(message:"No screen")}
                let current=Double(screen.maximumExtendedDynamicRangeColorComponentValue),potential=Double(screen.maximumPotentialExtendedDynamicRangeColorComponentValue)
                let onScreen=((CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first?[kCGWindowIsOnscreen as String] as? Bool)==true
                let ready=phase==1 ? (potential>1 && current>=potential*0.995):current<=1.001
                trajectory.append(["uptime":ProcessInfo.processInfo.systemUptime,"elapsed_seconds":Date().timeIntervalSince(began!),"phase":names[phase],"current_headroom":current,"potential_headroom":potential,"ready":ready,"requested":d.requested,"driver_draws":d.draws,"completed_readbacks":textureSamples.count,"driver_frame":rect(d.frame),"driver_bounds":rect(d.bounds),"driver_visible_rect":rect(d.visibleRect),"driver_attached_to_own_window":d.window === w,"driver_layer_hidden":d.layer?.isHidden ?? true,"driver_layer_opacity":d.layer?.opacity ?? 0,"drawable_size":[d.drawableSize.width,d.drawableSize.height],"window_frame":rect(w.frame),"host_bounds":rect(h.bounds),"visible":w.isVisible,"key":w.isKeyWindow,"active":app.isActive,"onscreen":onScreen,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
                guard w.isVisible,!w.isKeyWindow,!app.isActive,onScreen,w.frame==initialFrame,NSWorkspace.shared.frontmostApplication?.processIdentifier==before,d.window === w,d.visibleRect.width==192,d.visibleRect.height==108 else {throw Failure(message:"Own visible/nonkey/foreground/fixed-frame contract failed; see last trajectory")}
                guard geometry.frames.count==2,ready else {consecutiveReady=0;continue}
                guard captures.count<12,let shot=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming) else {throw Failure(message:"Own capture unavailable or bounded capture limit")}
                let path="\(names[phase])-\(captures.count).png";try writePNG(shot,output.appendingPathComponent(path))
                var rois:[String:Any]=[:]
                for (name,f) in geometry.frames {
                    guard f.width==320,f.height==180 else {throw Failure(message:"Image public frame changed")}
                    let local=h.isFlipped ? f:CGRect(x:f.minX,y:h.bounds.height-f.maxY,width:f.width,height:f.height)
                    let win=h.convert(local,to:nil),top=CGRect(x:win.minX,y:w.frame.height-win.maxY,width:win.width,height:win.height)
                    let pixels=CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height)
                    guard let crop=shot.cropping(to:pixels.integral) else {throw Failure(message:"ROI crop failed")}
                    rois[name]=["host_top_left_points":rect(f),"screenshot_pixels":rect(pixels),"rgba8_srgb_sha256":sha(try canonical(crop))]
                }
                let afterCurrent=Double(screen.maximumExtendedDynamicRangeColorComponentValue)
                let afterReady=phase==1 ? (potential>1 && afterCurrent>=potential*0.995):afterCurrent<=1.001
                captures.append(["phase":names[phase],"png":path,"png_sha256":sha(try Data(contentsOf:output.appendingPathComponent(path))),"current_headroom_before":current,"current_headroom_after":afterCurrent,"potential_headroom":potential,"headroom_ready_after":afterReady,"rois":rois,"whole_window_rgba8_srgb_sha256":sha(try canonical(shot)),"capture_size":[shot.width,shot.height],"capture_icc_sha256":shot.colorSpace?.copyICCData().map{sha($0 as Data)} ?? "absent","key":w.isKeyWindow,"active":app.isActive,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,"elapsed_seconds":Date().timeIntervalSince(began!)])
                consecutiveReady=afterReady ? consecutiveReady+1:0
                if consecutiveReady>=2 {
                    phases.append(["name":names[phase],"current_headroom":afterCurrent,"potential_headroom":potential,"capture_indices":Array((captures.count-2)..<captures.count),"image_equality_was_not_a_gate":true])
                    phase+=1;consecutiveReady=0
                    if phase<3 {prototypeStage=names[phase];d.high=phase==1;d.refresh()}
                }
            }
            report["completed_phase_count"]=phase
            report["system_preferences_readonly"]=["reduce_motion":NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,"reduce_transparency":NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,"increase_contrast":NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            guard phase==3 else {throw Failure(message:"7.2second collection deadline; partial headroom trajectory retained")}
            report["success"]=true;return 0
        } catch {report["error"]=String(describing:error);FileHandle.standardError.write(Data("Bounded Standard test incomplete: \(error)\n".utf8));return 1}
    }
}
