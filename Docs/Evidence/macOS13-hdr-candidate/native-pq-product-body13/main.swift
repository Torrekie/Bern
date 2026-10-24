// Prepared actual-product body/lifecycle diagnostic. Never activate the app.
// ProductBodyProbe NAMED_PQ_ATLAS CUSTOM_CICP_PQ_ATLAS OUTPUT_DIRECTORY
import AppKit
import SwiftUI
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

private struct Failure:Error {let message:String}
private func hash(_ data:Data)->String {SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined()}
private func rect(_ r:CGRect)->[String:Double] {["x":r.minX,"y":r.minY,"width":r.width,"height":r.height]}
private struct Frames:PreferenceKey {
    static var defaultValue:[String:CGRect]=[:]
    static func reduce(value:inout [String:CGRect],nextValue:()->[String:CGRect]){value.merge(nextValue(),uniquingKeysWith:{$1})}
}
@MainActor private final class State:ObservableObject {
    @Published var intent=BernImageDynamicRange.standard
    var frames:[String:CGRect]=[:]
}
private struct Content:View {
    let namedURL:String,customURL:String,oracle:CGImage
    @ObservedObject var state:State
    var body:some View {
        HStack(spacing:16) {
            item("product-named") {BernImage(url:namedURL,label:nil,width:320,height:180,fit:.fill,rendering:.original,dynamicRange:state.intent)}
            item("product-custom") {BernImage(url:customURL,label:nil,width:320,height:180,fit:.fill,rendering:.original,dynamicRange:state.intent)}
            item("oracle-native-named") {Image(decorative:oracle,scale:1).renderingMode(.original).resizable().frame(width:320,height:180)}
        }.padding(16).frame(width:1024,height:240,alignment:.topLeading)
            .coordinateSpace(name:"product-content").onPreferenceChange(Frames.self){state.frames=$0}.environment(\.colorScheme,.light)
    }
    private func item<V:View>(_ name:String,@ViewBuilder picture:()->V)->some View {
        VStack(spacing:6) {Text(name).font(.caption);picture().background(GeometryReader {g in
            Color.clear.preference(key:Frames.self,value:[name:g.frame(in:.named("product-content"))])
        })}
    }
}
private final class NonKeyWindow:NSWindow {override var canBecomeKey:Bool {false};override var canBecomeMain:Bool {false}}
private func canonical(_ image:CGImage)throws->Data {
    var bytes=[UInt8](repeating:0,count:image.width*image.height*4)
    try bytes.withUnsafeMutableBytes {b in
        guard let c=CGContext(data:b.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else {throw Failure(message:"Cannot canonicalize own capture")}
        c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    };return Data(bytes)
}
private func savePNG(_ image:CGImage,_ url:URL)throws {
    guard let d=CGImageDestinationCreateWithURL(url as CFURL,UTType.png.identifier as CFString,1,nil) else {throw Failure(message:"Cannot createPNG")}
    CGImageDestinationAddImage(d,image,nil);guard CGImageDestinationFinalize(d) else {throw Failure(message:"Cannot finishPNG")}
}
@MainActor private func metalTree(_ view:NSView)->[MTKView] {
    var result:[MTKView]=[]
    func visit(_ v:NSView){if let m=v as? MTKView {result.append(m)};v.subviews.forEach(visit)}
    visit(view);return result
}
@MainActor private func metalInfo(_ v:MTKView)->[String:Any] {
    let layer=v.layer as? CAMetalLayer
    return ["id":String(describing:ObjectIdentifier(v)),"class":NSStringFromClass(type(of:v)),"attached_to_window":v.window != nil,
        "has_superview":v.superview != nil,"frame":rect(v.frame),"bounds":rect(v.bounds),"visible_rect":rect(v.visibleRect),
        "wants_edr":layer?.wantsExtendedDynamicRangeContent ?? false,"is_paused":v.isPaused,
        "drawable_size":[v.drawableSize.width,v.drawableSize.height],"color_space":layer?.colorspace?.name as String? ?? "nil"]
}
@MainActor private func ledger(_ urls:[URL])throws->[String:Any] {
    var result:[String:Any]=[:]
    for url in urls {
        guard let p=BernPictures.shared.cached(url.absoluteString),let data=p.image.dataProvider?.data,let icc=p.image.colorSpace?.copyICCData() else {throw Failure(message:"Actual product cache missing decoded source")}
        let derived=p.legacyStandardPQImage
        var item:[String:Any]=[:]
        item["image_id"]=String(describing:ObjectIdentifier(p.image))
        item["original_provider_sha256"]=hash(data as Data)
        item["original_icc_sha256"]=hash(icc as Data)
        item["file_sha256"]=hash(try Data(contentsOf:url))
        item["orientation"]=String(describing:p.orientation);item["ratio"]=p.ratio
        item["original_size"]=[p.image.width,p.image.height]
        item["original_bitmap_info"]=p.image.bitmapInfo.rawValue;item["original_alpha_info"]=p.image.alphaInfo.rawValue
        item["original_space_name"]=p.image.colorSpace?.name as String? ?? "unnamed"
        item["original_uses_2100_tf"]=p.image.colorSpace.map{CGColorSpaceUsesITUR_2100TF($0)} ?? false
        item["legacy_hdr_space_name"]=p.legacyHDRColorSpace?.name as String? ?? "nil"
        item["derived_is_pq_based"]=derived?.colorSpace.map{CGColorSpaceIsPQBased($0)} ?? false
        if let average=BernPictures.shared.averages[url.absoluteString] {item["cached_average_rgb"]=average}
        else {item["cached_average_rgb"]=NSNull()}
        item["derived_id"]=derived.map{String(describing:ObjectIdentifier($0))} ?? "nil"
        item["derived_provider_sha256"]=derived?.dataProvider?.data.map{hash($0 as Data)} ?? "nil"
        item["derived_icc_sha256"]=derived?.colorSpace?.copyICCData().map{hash($0 as Data)} ?? "nil"
        result[url.lastPathComponent]=item
    };return result
}
@main private enum Main {
    @MainActor static func main(){exit(run())}
    @MainActor private static func run()->Int32 {
        guard CommandLine.arguments.count==4 else {return 2}
        let urls=CommandLine.arguments[1...2].map{URL(fileURLWithPath:$0)},output=URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
        let front=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window:NSWindow?,host:NSHostingView<Content>?,began:Date?,watchdog:DispatchSourceTimer?
        // Retain only the two observed High views until their detached state is
        // measured. This makes wantsEDR=false observable before deallocation.
        var heldHigh:[MTKView]=[],trajectory:[[String:Any]]=[],captures:[[String:Any]]=[],phases:[[String:Any]]=[]
        var report:[String:Any]=["success":false,"product_commit":"9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0","scope":"Actual product BernImage/url cache/Legacy renderer slice, Standard->High->Standard on13. Two product columns plus native namedPQ oracle. Identityhero stub excludeshero. High checks lifecycle only, not colors.","activation_calls":0,"collection_seconds":7.2,"process_watchdog_seconds":7.9,"image_equality_collection_gate":false,"high_headroom_readiness_gate":false,"retained_high_views":"Held only for detach/wantsEDR observation, then released; no source renderer instrumentation."]
        defer {
            report["retained_high_final_state_before_cleanup"]=heldHigh.map(metalInfo)
            let live=host.map(metalTree) ?? []
            report["live_metal_count_before_cleanup"]=live.count
            // Emergency cleanup only touches this fixture's own surfaces after
            // recording failure/success; it cannot hide a teardown observation.
            for m in live+heldHigh {if let l=m.layer as? CAMetalLayer {l.wantsExtendedDynamicRangeContent=false};m.isPaused=true;m.releaseDrawables()}
            host?.removeFromSuperview();window?.contentView=nil;window?.orderOut(nil);window?.close();watchdog?.cancel();heldHigh.removeAll()
            if let began {report["window_seconds"]=Date().timeIntervalSince(began)}
            report["trajectory"]=trajectory;report["captures"]=captures;report["phases"]=phases
            report["frontmost_before"]=front;report["frontmost_after"]=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["os"]=ProcessInfo.processInfo.operatingSystemVersionString
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            guard ProcessInfo.processInfo.operatingSystemVersion.majorVersion==13,CGPreflightScreenCaptureAccess() else {throw Failure(message:"Actual13 and existing screen capture permission required")}
            guard !NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,!NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,!NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast else {throw Failure(message:"Normal appearance flags required; no prefs changed")}
            let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
            var preloadDone=false,preloadOK=false
            Task { @MainActor in
                let first=await BernPictures.shared.load(urls[0].absoluteString),second=await BernPictures.shared.load(urls[1].absoluteString)
                preloadOK=first != nil && second != nil;preloadDone=true
            }
            let preloadDeadline=Date(timeIntervalSinceNow:10)
            while !preloadDone && Date()<preloadDeadline {RunLoop.main.run(until:Date(timeIntervalSinceNow:0.02))}
            guard preloadDone,preloadOK,let named=BernPictures.shared.cached(urls[0].absoluteString) else {throw Failure(message:"Actual BernPictures.load(fileURL) preload did not finish")}
            let initialLedger=try ledger(urls);report["cache_before"]=initialLedger
            let state=State(),h=NSHostingView(rootView:Content(namedURL:urls[0].absoluteString,customURL:urls[1].absoluteString,oracle:named.image,state:state));host=h
            let w=NonKeyWindow(contentRect:CGRect(x:100,y:100,width:1024,height:240),styleMask:[.titled],backing:.buffered,defer:false);window=w
            w.isReleasedWhenClosed=false;w.isRestorable=false;w.title="Bern actual product PQ lifecycle D3E0";w.contentView=h
            let timer=DispatchSource.makeTimerSource(queue:.global(qos:.userInitiated));watchdog=timer
            timer.setEventHandler {try? Data("Own product fixture7.9second watchdog; incomplete evidence.\n".utf8).write(to:output.appendingPathComponent("hard-deadline.txt"));_exit(124)}
            began=Date();timer.schedule(deadline:.now()+7.9);timer.resume();w.orderFrontRegardless()
            let initialFrame=w.frame,deadline=Date(timeIntervalSinceNow:7.2),names=["standard-initial","high-lifecycle","standard-returned"]
            var phase=0,readyCaptures=0,phaseBegan=Date()
            while Date()<deadline && phase<3 {
                h.layoutSubtreeIfNeeded();h.displayIfNeeded();RunLoop.main.run(until:Date(timeIntervalSinceNow:0.1))
                guard let screen=w.screen else {throw Failure(message:"No own screen")}
                let current=screen.maximumExtendedDynamicRangeColorComponentValue,potential=screen.maximumPotentialExtendedDynamicRangeColorComponentValue
                let live=metalTree(h),onScreen=((CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first?[kCGWindowIsOnscreen as String] as? Bool)==true
                if phase==1 && live.count==2 && heldHigh.isEmpty {heldHigh=live}
                let heldStopped=heldHigh.allSatisfy{$0.window==nil && ($0.layer as? CAMetalLayer)?.wantsExtendedDynamicRangeContent==false}
                let lifecycleReady=phase==1 ? (live.count==2 && live.allSatisfy{($0.layer as? CAMetalLayer)?.wantsExtendedDynamicRangeContent==(potential>1)} && Date().timeIntervalSince(phaseBegan)>=0.3):(live.isEmpty && current<=1.001 && (phase==0 || heldHigh.count==2 && heldStopped))
                trajectory.append(["phase":names[phase],"elapsed_seconds":Date().timeIntervalSince(began!),"current_headroom":current,"potential_headroom":potential,"live_metal_count":live.count,"live_metal":live.map(metalInfo),"held_high":heldHigh.map(metalInfo),"lifecycle_ready":lifecycleReady,"window_frame":rect(w.frame),"host_bounds":rect(h.bounds),"key":w.isKeyWindow,"active":app.isActive,"visible":w.isVisible,"onscreen":onScreen,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
                guard w.isVisible,onScreen,!w.isKeyWindow,!app.isActive,w.frame==initialFrame,NSWorkspace.shared.frontmostApplication?.processIdentifier==front else {throw Failure(message:"Own fixed-frame/nonkey/foreground contract failed; see trajectory")}
                guard lifecycleReady,state.frames.count==3 else {readyCaptures=0;continue}
                guard let shot=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming) else {throw Failure(message:"Own real WindowServer capture unavailable")}
                let filename="\(names[phase])-\(captures.count).png";try savePNG(shot,output.appendingPathComponent(filename))
                var rois:[String:Any]=[:]
                for (name,f) in state.frames {
                    guard f.width==320,f.height==180 else {throw Failure(message:"Actual BernImage public frame changed")}
                    let local=h.isFlipped ? f:CGRect(x:f.minX,y:h.bounds.height-f.maxY,width:f.width,height:f.height)
                    let win=h.convert(local,to:nil),top=CGRect(x:win.minX,y:w.frame.height-win.maxY,width:win.width,height:win.height)
                    let r=CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height)
                    guard let image=shot.cropping(to:r.integral) else {throw Failure(message:"ROI crop failed")}
                    rois[name]=["host_top_left_points":rect(f),"screenshot_pixels":rect(r),"rgba8_srgb_sha256":hash(try canonical(image))]
                }
                let oracle=(rois["oracle-native-named"] as? [String:Any])?["rgba8_srgb_sha256"] as? String
                let named=(rois["product-named"] as? [String:Any])?["rgba8_srgb_sha256"] as? String
                let custom=(rois["product-custom"] as? [String:Any])?["rgba8_srgb_sha256"] as? String
                captures.append(["phase":names[phase],"png":filename,"png_sha256":hash(try Data(contentsOf:output.appendingPathComponent(filename))),"rois":rois,"capture_size":[shot.width,shot.height],"capture_icc_sha256":shot.colorSpace?.copyICCData().map{hash($0 as Data)} ?? "absent","current_headroom":current,"potential_headroom":potential,"live_metal_count":live.count,"standard_matches_native_oracle":phase==1 ? NSNull():(oracle != nil && named==oracle && custom==oracle) as Any,"key":w.isKeyWindow,"active":app.isActive,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,"elapsed_seconds":Date().timeIntervalSince(began!)])
                readyCaptures+=1
                if readyCaptures>=2 {
                    let cache=try ledger(urls),unchanged=NSDictionary(dictionary:cache).isEqual(to:initialLedger)
                    phases.append(["phase":names[phase],"live_metal_count":live.count,"live_metal":live.map(metalInfo),"held_high":heldHigh.map(metalInfo),"current_headroom":current,"potential_headroom":potential,"cache_unchanged":unchanged,"cache":cache,"capture_indices":Array((captures.count-2)..<captures.count)])
                    guard unchanged else {throw Failure(message:"Actual cache/image/provider/ICC identity changed")}
                    phase+=1;readyCaptures=0;phaseBegan=Date()
                    if phase<3 {state.intent=phase==1 ? .high:.standard}
                }
            }
            report["completed_phases"]=phase
            guard phase==3 else {throw Failure(message:"7.2second collection deadline; lifecycle partial")}
            var standardAcrossPhases:[String:Bool]=[:]
            for name in ["product-named","product-custom","oracle-native-named"] {
                let hashes=captures.filter{($0["phase"] as? String) != "high-lifecycle"}.compactMap{capture in
                    ((capture["rois"] as? [String:Any])?[name] as? [String:Any])?["rgba8_srgb_sha256"] as? String
                }
                standardAcrossPhases[name]=hashes.count==4 && Set(hashes).count==1
            }
            report["standard_before_after_equal"]=standardAcrossPhases
            guard captures.filter({($0["phase"] as? String) != "high-lifecycle"}).allSatisfy({$0["standard_matches_native_oracle"] as? Bool==true}) else {throw Failure(message:"Actual product Standard ROI differs from native oracle; all captures retained")}
            guard standardAcrossPhases.values.allSatisfy({$0}) else {throw Failure(message:"Standard before/after ROI changed; all captures retained")}
            guard !app.isActive,!w.isKeyWindow,NSWorkspace.shared.frontmostApplication?.processIdentifier==front else {throw Failure(message:"Foreground changed after captures")}
            report["cache_after"]=try ledger(urls);report["success"]=true;return 0
        } catch {report["error"]=String(describing:error);FileHandle.standardError.write(Data("Actual product fixture incomplete: \(error)\n".utf8));return 1}
    }
}
