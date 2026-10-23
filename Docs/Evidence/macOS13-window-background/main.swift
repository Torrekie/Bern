import AppKit
import SwiftUI
import ImageIO
import UniformTypeIdentifiers
import CryptoKit

private struct Failure:Error {let message:String}
private func sha(_ d:Data)->String {SHA256.hash(data:d).map{String(format:"%02x",$0)}.joined()}
private func rect(_ r:CGRect)->[String:Double] {["x":r.minX,"y":r.minY,"width":r.width,"height":r.height]}
private func nscolor(_ c:NSColor)->[String:Double] {
    guard let c=c.usingColorSpace(.sRGB) else{return [:]}
    return ["r":c.redComponent,"g":c.greenComponent,"b":c.blueComponent,"a":c.alphaComponent]
}
// Exact operative branch of BernColor.system("surface.canvas") and
// BernDraw.shape(rect,fill:role,opacity:1), without unused alternatives.
private enum BernColor {case role(String)
    var color:Color {switch self {case .role("surface.canvas"):return Color(nsColor:.windowBackgroundColor);default:return .primary}}
}
private enum BernDraw {
    static func shape(_ context:inout GraphicsContext,_ r:CGRect,fill:BernColor) {
        var layer=context;layer.opacity=1
        layer.fill(Path(r),with:.color(fill.color))
    }
}
private enum Kind:String,CaseIterable {
    case native="native-nsview",color="swiftui-color",canvas="canvas-role",split="split-transparent",filled="split-explicit-role"
}
private struct Content:View {
    let kind:Kind
    var body:some View {group.frame(width:800,height:520).environment(\.colorScheme,.light)}
    @ViewBuilder private var group:some View {
        switch kind {
        case .native:Color.clear
        case .color:Color(nsColor:.windowBackgroundColor)
        case .canvas:
            SwiftUI.Canvas { context,size in BernDraw.shape(&context,CGRect(origin:.zero,size:size),fill:.role("surface.canvas")) }
        case .split,.filled:
            NavigationSplitView {
                List {Text("Sidebar")}.navigationSplitViewColumnWidth(min:180,ideal:210,max:320)
            } detail: {
                if kind == .filled { Color.clear.frame(maxWidth:.infinity,maxHeight:.infinity).background(BernColor.role("surface.canvas").color) }
                else {Color.clear.frame(maxWidth:.infinity,maxHeight:.infinity)}
            }
        }
    }
}
private final class SolidView:NSView {
    override var isFlipped:Bool {true}
    override var isOpaque:Bool {true}
    override func draw(_ dirty:NSRect) {NSColor.windowBackgroundColor.setFill();bounds.fill()}
}
private final class NonKeyWindow:NSWindow {
    override var canBecomeKey:Bool {false}
    override var canBecomeMain:Bool {false}
}
private func canonical(_ image:CGImage)throws->Data {
    var data=[UInt8](repeating:0,count:image.width*image.height*4)
    try data.withUnsafeMutableBytes { buffer in
        guard let c=CGContext(data:buffer.baseAddress,width:image.width,height:image.height,bitsPerComponent:8,bytesPerRow:image.width*4,space:CGColorSpace(name:CGColorSpace.sRGB)!,bitmapInfo:CGImageAlphaInfo.premultipliedLast.rawValue|CGBitmapInfo.byteOrder32Big.rawValue) else{throw Failure(message:"Cannot convert capture")}
        c.draw(image,in:CGRect(x:0,y:0,width:image.width,height:image.height))
    };return Data(data)
}
private func effects(_ root:NSView)->[[String:Any]] {
    var out:[[String:Any]]=[]
    func walk(_ view:NSView,_ path:[String]) {
        let type=NSStringFromClass(type(of:view)),next=path+[type]
        if let e=view as? NSVisualEffectView {
            out.append(["path":next,"frame":rect(e.frame),"bounds":rect(e.bounds),"frame_in_content":rect(root.convert(e.bounds,from:e)),"material":e.material.rawValue,"state":e.state.rawValue,"blending_mode":e.blendingMode.rawValue,"emphasized":e.isEmphasized,"hidden":e.isHiddenOrHasHiddenAncestor,"alpha":e.alphaValue,"allows_vibrancy":e.allowsVibrancy,"is_opaque":e.isOpaque,"effective_appearance":e.effectiveAppearance.name.rawValue])
        }
        for child in view.subviews {walk(child,next)}
    };walk(root,[]);return out
}
@main private enum Main {
    @MainActor static func main(){exit(run())}
    @MainActor private static func run()->Int32 {
        guard CommandLine.arguments.count==2 else{return 2}
        let output=URL(fileURLWithPath:CommandLine.arguments[1],isDirectory:true)
        let before=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window:NSWindow?,began:Date?,stages:[[String:Any]]=[]
        var report:[String:Any]=["success":false,"scope":"Five public-background paths in one own nonkey macOS13 window. No Bern product change, user preferences change, activation, wallpaper or brightness change.","os":ProcessInfo.processInfo.operatingSystemVersionString,"roi_content_top_left_points":rect(CGRect(x:680,y:430,width:40,height:40)),"activation_calls":0]
        defer {
            window?.contentView=nil;window?.orderOut(nil);window?.close()
            report["groups"]=stages;report["frontmost_before"]=before;report["frontmost_after"]=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            if let began {report["window_seconds"]=Date().timeIntervalSince(began)}
            try? JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at:output,withIntermediateDirectories:true)
            let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
            let w=NonKeyWindow(contentRect:CGRect(x:100,y:100,width:800,height:520),styleMask:[.titled],backing:.buffered,defer:false)
            window=w;w.isReleasedWhenClosed=false;w.isRestorable=false;w.title="Bern background paths probe 17D4"
            let first=SolidView(frame:CGRect(x:0,y:0,width:800,height:520));w.contentView=first
            began=Date();w.orderBack(nil)
            let deadline=Date(timeIntervalSinceNow:9)
            let commonFrame=w.frame
            for kind in Kind.allCases {
                let view:NSView
                if kind == .native {view=first}
                else {view=NSHostingView(rootView:Content(kind:kind))}
                view.frame=CGRect(x:0,y:0,width:800,height:520);view.autoresizingMask=[.width,.height]
                w.contentView=view;view.needsDisplay=true
                var equal=0,lastHash:String?,last:CGImage?,buffers:[[String:Any]]=[]
                while Date()<deadline {
                    view.layoutSubtreeIfNeeded();view.displayIfNeeded()
                    RunLoop.main.run(until:Date(timeIntervalSinceNow:0.12))
                    guard w.isVisible,!w.isKeyWindow,!app.isActive,w.frame==commonFrame,NSWorkspace.shared.frontmostApplication?.processIdentifier==before,
                          let info=(CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first,info[kCGWindowIsOnscreen as String] as? Bool==true,
                          let shot=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming) else{throw Failure(message:"Own nonkey capture/frame/foreground contract failed")}
                    let hash=sha(try canonical(shot));equal = hash==lastHash ? equal+1:1;lastHash=hash;last=shot
                    if equal==1 {buffers=[]}
                    buffers.append(["rgba8_srgb_sha256":hash,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0,"key":w.isKeyWindow,"active":app.isActive])
                    if equal>=2 {break}
                }
                guard equal>=2,let shot=last else{throw Failure(message:"Nine-second collection deadline before all groups stabilized")}
                let roi=CGRect(x:680,y:430,width:40,height:40)
                let local=view.isFlipped ? roi:CGRect(x:roi.minX,y:view.bounds.height-roi.maxY,width:roi.width,height:roi.height)
                let native=view.convert(local,to:nil),top=CGRect(x:native.minX,y:w.frame.height-native.maxY,width:native.width,height:native.height)
                let pixels=CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height)
                let target=CGImageDestinationCreateWithURL(output.appendingPathComponent(kind.rawValue+".png") as CFURL,UTType.png.identifier as CFString,1,nil)!
                CGImageDestinationAddImage(target,shot,nil);guard CGImageDestinationFinalize(target) else{throw Failure(message:"PNG write failed")}
                var colors:[String:Any]=[:]
                view.effectiveAppearance.performAsCurrentDrawingAppearance {colors=["semantic_window_background":nscolor(.windowBackgroundColor),"window_background":nscolor(w.backgroundColor)]}
                let icc=shot.colorSpace?.copyICCData() as Data?
                stages.append(["name":kind.rawValue,"png":kind.rawValue+".png","png_sha256":sha(try Data(contentsOf:output.appendingPathComponent(kind.rawValue+".png"))),"capture_size":[shot.width,shot.height],"capture_icc_sha256":icc.map(sha) ?? "absent","capture_icc_bytes":icc?.count ?? 0,"roi_screenshot_pixels":rect(pixels),"content_bounds":rect(view.bounds),"window_frame":rect(w.frame),"window_is_opaque":w.isOpaque,"window_alpha":w.alphaValue,"window_color_space":w.colorSpace?.localizedName ?? "nil","app_appearance":app.appearance?.name.rawValue ?? "nil","window_appearance":w.appearance?.name.rawValue ?? "nil","effective_window_appearance":w.effectiveAppearance.name.rawValue,"effective_view_appearance":view.effectiveAppearance.name.rawValue,"root_view_class":NSStringFromClass(type(of:view)),"root_allows_vibrancy":view.allowsVibrancy,"root_is_opaque":view.isOpaque,"native_effect_views":effects(w.contentView?.superview ?? view),"resolved_srgb":colors,"stable_buffers":buffers,"elapsed_seconds":Date().timeIntervalSince(began!)])
                report["groups"]=stages
            }
            report["system_preferences_readonly"]=["reduce_transparency":NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,"increase_contrast":NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            report["success"]=true;return 0
        } catch {report["error"]=String(describing:error);fputs("Background probe incomplete: \(error)\n",stderr);return 1}
    }
}
