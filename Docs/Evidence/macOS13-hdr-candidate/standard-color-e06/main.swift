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
enum BernImageDynamicRange: Equatable, Sendable {
    case standard, high
}

#if os(macOS)
/// Requesting HDR depends on potential capability, while drawing HDR depends
/// on the current headroom. Keeping those decisions separate lets a High image
/// request EDR when the screen initially reports 1, without oscillating when
/// brightness temporarily leaves no headroom.
private struct BernLegacyImageDisplay {
    let requestsEDR: Bool
    let rendersHDR: Bool

    init(_ intent: BernImageDynamicRange, potential: CGFloat, current: CGFloat) {
        requestsEDR = intent == .high && potential > 1
        rendersHDR = requestsEDR && current > 1
    }
}

@MainActor
private enum BernLegacyImagePixels {
    static let standardSpace = CGColorSpace(name: CGColorSpace.sRGB)!

    static func input(_ picture: BernImage.Picture, standard: Bool) -> CIImage {
        var options: [CIImageOption: Any] = [.toneMapHDRtoSDR: standard]
        if let space = picture.legacyHDRColorSpace { options[.colorSpace] = space }
        let exif: Int32 = switch picture.orientation {
        case .up: 1
        case .upMirrored: 2
        case .down: 3
        case .downMirrored: 4
        case .leftMirrored: 5
        case .right: 6
        case .rightMirrored: 7
        case .left: 8
        @unknown default: 1
        }
        return CIImage(cgImage: picture.image, options: options).oriented(forExifOrientation: exif)
    }

    static func sized(_ image: CIImage, to size: CGSize) -> CIImage? {
        guard image.extent.width > 0, image.extent.height > 0, size.width > 0, size.height > 0 else { return nil }
        return image.transformed(by: CGAffineTransform(translationX: -image.extent.minX, y: -image.extent.minY))
            .transformed(by: CGAffineTransform(scaleX: size.width / image.extent.width, y: size.height / image.extent.height))
    }

    static func standard(_ picture: BernImage.Picture, size: CGSize, context: CIContext) -> CGImage? {
        guard let image = sized(input(picture, standard: true), to: size) else { return nil }
        // An SDR destination is essential: merely inspecting an extended-linear
        // float intermediate does not exercise the system's SDR conversion.
        return context.createCGImage(image, from: image.extent, format: .RGBA8, colorSpace: standardSpace)
    }
}

/// Ventura needs a native surface to request EDR. Both display paths retain
/// the original resource and ICC; only the Core Image input interpretation is
/// canonicalized when the source's complete standard CICP tag proves equivalence.
private struct BernLegacyEDRImage: NSViewRepresentable {
    let picture: BernImage.Picture
    let dynamicRange: BernImageDynamicRange

    @MainActor private static let device = MTLCreateSystemDefaultDevice()
    @MainActor private static let queue = device?.makeCommandQueue()

    func makeNSView(context: Context) -> NSView {
        if let device = Self.device, let queue = Self.queue { return BernEDRImageView(device: device, queue: queue) }
        // Software/Metal-unavailable Macs still get the system SDR tone map.
        return BernSDRImageView(frame: .zero)
    }

    func updateNSView(_ view: NSView, context: Context) {
        if let view = view as? BernEDRImageView { view.show(picture, dynamicRange: dynamicRange) }
        else if let view = view as? BernSDRImageView { view.show(picture) }
    }

    static func dismantleNSView(_ view: NSView, coordinator: ()) {
        if let view = view as? BernEDRImageView { view.stop() }
        else if let view = view as? BernSDRImageView { view.stop() }
    }
}

@MainActor
private final class BernEDRImageView: MTKView {
    private let imageContext: CIContext
    private let commands: any MTLCommandQueue
    private var picture: BernImage.Picture?
    private var dynamicRange = BernImageDynamicRange.high
    private var standardImage: CGImage?
    private var standardSize = CGSize.zero

    init(device: any MTLDevice, queue: any MTLCommandQueue) {
        commands = queue
        imageContext = CIContext(mtlDevice: device, options: [.cacheIntermediates: false])
        super.init(frame: .zero, device: device)
        colorPixelFormat = .rgba16Float
        framebufferOnly = false
        isPaused = true
        enableSetNeedsDisplay = true
        clearColor = MTLClearColorMake(0, 0, 0, 0)
        (layer as? CAMetalLayer)?.isOpaque = false
    }

    @available(*, unavailable)
    required init(coder: NSCoder) { fatalError("Bern image views are created programmatically") }

    deinit { NotificationCenter.default.removeObserver(self) }
    override var acceptsFirstResponder: Bool { false }
    override var isOpaque: Bool { false }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }

    func show(_ next: BernImage.Picture, dynamicRange: BernImageDynamicRange) {
        let changed = picture?.image !== next.image || picture?.orientation != next.orientation
        guard changed || self.dynamicRange != dynamicRange else { return }
        if changed { standardImage = nil; standardSize = .zero }
        picture = next
        self.dynamicRange = dynamicRange
        refreshDisplay()
    }

    override func viewDidMoveToWindow() {
        super.viewDidMoveToWindow()
        let center = NotificationCenter.default
        center.removeObserver(self, name: NSApplication.didChangeScreenParametersNotification, object: nil)
        center.removeObserver(self, name: NSWindow.didChangeScreenNotification, object: nil)
        if let window {
            center.addObserver(self, selector: #selector(screenParametersChanged(_:)), name: NSApplication.didChangeScreenParametersNotification, object: nil)
            center.addObserver(self, selector: #selector(screenParametersChanged(_:)), name: NSWindow.didChangeScreenNotification, object: window)
        }
        refreshDisplay()
    }

    override func viewDidChangeBackingProperties() {
        super.viewDidChangeBackingProperties()
        // This callback covers both backing scale and window colour-space
        // changes. The cached SDR image is resolution dependent.
        standardImage = nil
        standardSize = .zero
        refreshDisplay()
    }

    override func layout() { super.layout(); needsDisplay = true }

    private var display: BernLegacyImageDisplay {
        guard picture != nil else { return BernLegacyImageDisplay(.standard, potential: 1, current: 1) }
        return BernLegacyImageDisplay(dynamicRange,
            potential: window?.screen?.maximumPotentialExtendedDynamicRangeColorComponentValue ?? 1,
            current: window?.screen?.maximumExtendedDynamicRangeColorComponentValue ?? 1)
    }

    @objc private func screenParametersChanged(_ notification: Notification) {
        if notification.name == NSWindow.didChangeScreenNotification {
            standardImage = nil
            standardSize = .zero
        }
        // NSScreen documents this notification for actual headroom changes;
        // no undocumented KVO contract or continuous frame timer is required.
        refreshDisplay()
    }

    private func refreshDisplay() {
        if let surface = layer as? CAMetalLayer, surface.wantsExtendedDynamicRangeContent != display.requestsEDR {
            surface.wantsExtendedDynamicRangeContent = display.requestsEDR
        }
        needsDisplay = true
    }

    override func draw(_ dirtyRect: NSRect) {
        guard let picture, let surface = layer as? CAMetalLayer else { return }
        let hdr = display.rendersHDR
        let space = hdr ? picture.legacyHDRColorSpace : BernLegacyImagePixels.standardSpace
        guard let space else { return }
        // Configure the interpretation before acquiring this frame's drawable.
        if surface.colorspace != space { surface.colorspace = space }
        guard let drawable = currentDrawable, let command = commands.makeCommandBuffer() else { return }
        let size = CGSize(width: CGFloat(drawable.texture.width), height: CGFloat(drawable.texture.height))
        let image: CIImage
        if hdr {
            // Keep HDR pixels unclamped. Ventura's Metal layer does not
            // reproduce macOS 14's ISO HDR global tone mapper; CA may clip
            // values above the current display headroom. No guessed mastering
            // metadata or reference-white scale is substituted here.
            guard let sized = BernLegacyImagePixels.sized(BernLegacyImagePixels.input(picture, standard: false), to: size) else { return }
            image = sized
        } else {
            if standardImage == nil || standardSize != size {
                standardImage = BernLegacyImagePixels.standard(picture, size: size, context: imageContext)
                standardSize = size
            }
            guard let standardImage else { return }
            image = CIImage(cgImage: standardImage)
        }
        let destination = CIRenderDestination(mtlTexture: drawable.texture, commandBuffer: command)
        destination.colorSpace = space
        destination.isFlipped = true
        do {
            _ = try imageContext.startTask(toRender: image, to: destination)
            command.present(drawable)
            command.commit()
        } catch {
            NSLog("Bern HDR image rendering failed: %@", String(describing: error))
        }
    }

    func stop() {
        NotificationCenter.default.removeObserver(self)
        (layer as? CAMetalLayer)?.wantsExtendedDynamicRangeContent = false
        picture = nil
        standardImage = nil
        isPaused = true
        releaseDrawables()
    }
}

/// This path is also usable without a Metal device. NSImageView supplies the
/// standard native image surface; Core Image supplies only the SDR pixels.
@MainActor
private final class BernSDRImageView: NSImageView {
    private let imageContext = CIContext(options: [.cacheIntermediates: false, .useSoftwareRenderer: true])
    private var picture: BernImage.Picture?
    private var renderedSize = CGSize.zero

    override init(frame: NSRect) {
        super.init(frame: frame)
        imageScaling = .scaleAxesIndependently
        imageFrameStyle = .none
    }
    @available(*, unavailable)
    required init?(coder: NSCoder) { fatalError("Bern image views are created programmatically") }
    override var acceptsFirstResponder: Bool { false }
    override func hitTest(_ point: NSPoint) -> NSView? { nil }

    func show(_ next: BernImage.Picture) {
        guard picture?.image !== next.image || picture?.orientation != next.orientation else { return }
        picture = next
        renderedSize = .zero
        needsLayout = true
    }
    override func layout() { super.layout(); render() }
    override func viewDidChangeBackingProperties() { super.viewDidChangeBackingProperties(); renderedSize = .zero; needsLayout = true }

    private func render() {
        guard let picture else { return }
        let scale = window?.backingScaleFactor ?? 1
        let size = CGSize(width: max(1, (bounds.width * scale).rounded()), height: max(1, (bounds.height * scale).rounded()))
        guard bounds.width > 0, bounds.height > 0, renderedSize != size,
              let converted = BernLegacyImagePixels.standard(picture, size: size, context: imageContext)
        else { return }
        renderedSize = size
        image = NSImage(cgImage: converted, size: bounds.size)
    }

    func stop() {
        picture = nil
        image = nil
        renderedSize = .zero
    }
}
#endif

private func digest(_ data: Data) -> String { SHA256.hash(data:data).map { String(format:"%02x",$0) }.joined() }
private func rect(_ r: CGRect) -> [String:Double] { ["x":r.minX,"y":r.minY,"width":r.width,"height":r.height] }
private struct Frames: PreferenceKey {
    static var defaultValue: [String:CGRect] = [:]
    static func reduce(value: inout [String:CGRect], nextValue:()->[String:CGRect]) { value.merge(nextValue(),uniquingKeysWith:{$1}) }
}
@MainActor private final class State { var frames: [String:CGRect] = [:] }
private let labels = ["product-standard-ffb","product-standard-named","native-swiftui-named"]
private struct Content: View {
    let pictures: [BernImage.Picture]
    let receive: ([String:CGRect])->Void
    @ViewBuilder private func image(_ index: Int) -> some View {
        if index < 2 { BernLegacyEDRImage(picture:pictures[index],dynamicRange:.standard) }
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
@main private enum Main {
    @MainActor static func main() { exit(run()) }
    @MainActor static func run()->Int32 {
        guard CommandLine.arguments.count==4 else {return 2}
        let output=URL(fileURLWithPath:CommandLine.arguments[3],isDirectory:true)
        let before=NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window:NSWindow?,host:NSHostingView<Content>?
        var report:[String:Any]=["success":false,"scope":"Current product macOS13 Standard helper for two same-code PQ atlas files vs native macOS13 SwiftUI namedPQ Image; no product edits, no High or macOS14 equivalence","runtime_sha256":"1ec700f09c9b2488f0253beed0b2134e08b651bd5c6936f0e8e70abad454ac0f","product_commit":"e06e080665a0c774843762ca132edf31bcb82d77","os":ProcessInfo.processInfo.operatingSystemVersionString]
        var windowBegan:Date?
        defer {
            var metalCount=0,softwareCount=0
            func stop(_ view:NSView) {
                if let v=view as? BernEDRImageView {v.stop();metalCount+=1}
                if let v=view as? BernSDRImageView {v.stop();softwareCount+=1}
                view.subviews.forEach(stop)
            }
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
            let pictures=try urls.map {try BernImage.load($0)}
            report["sources"]=zip(urls,pictures).map {url,p in ["file":url.lastPathComponent,"file_sha256":digest(try! Data(contentsOf:url)),"decoded_color":color(p.image),"normalized_space":p.legacyHDRColorSpace?.name as String? ?? "nil","width":p.image.width,"height":p.image.height,"bits_per_component":p.image.bitsPerComponent,"bitmap_info":p.image.bitmapInfo.rawValue,"provider_sha256":digest(p.image.dataProvider!.data! as Data)] as [String:Any]}
            let app=NSApplication.shared;app.setActivationPolicy(.accessory);app.appearance=NSAppearance(named:.aqua);app.finishLaunching()
            let state=State(),h=NSHostingView(rootView:Content(pictures:pictures,receive:{state.frames=$0}));host=h
            let w=NonKeyWindow(contentRect:CGRect(x:100,y:100,width:1024,height:240),styleMask:[.titled],backing:.buffered,defer:false)
            window=w;w.isReleasedWhenClosed=false;w.isRestorable=false;w.title="Bern Standard color CICP probe 41B6";w.contentView=h
            windowBegan=Date();w.orderBack(nil)
            let deadline=Date(timeIntervalSinceNow:8)
            var hashes:[String]=[],captures:[[String:Any]]=[],last:CGImage?
            while Date()<deadline {
                h.layoutSubtreeIfNeeded();RunLoop.main.run(until:Date(timeIntervalSinceNow:0.16))
                guard state.frames.count==3,let screen=w.screen else{continue}
                guard w.isVisible,!w.isKeyWindow,!app.isActive,
                      let info=(CGWindowListCopyWindowInfo(.optionIncludingWindow,CGWindowID(w.windowNumber)) as? [[String:Any]])?.first,info[kCGWindowIsOnscreen as String] as? Bool==true,
                      let shot=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(w.windowNumber),.boundsIgnoreFraming) else {throw Failure(message:"Nonkey real WindowServer capture failed")}
                let hash=digest(try canonical(shot))
                if hashes.last != hash {hashes=[];captures=[]}
                hashes.append(hash);last=shot
                captures.append(["rgba8_srgb_sha256":hash,"current_headroom":screen.maximumExtendedDynamicRangeColorComponentValue,"potential_headroom":screen.maximumPotentialExtendedDynamicRangeColorComponentValue,"active":app.isActive,"key":w.isKeyWindow,"frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0])
                if hashes.count>=4 {break}
            }
            guard hashes.count>=4,let shot=last else{throw Failure(message:"8-second deadline without four stable buffers")}
            var frames:[String:Any]=[:]
            for (name,f) in state.frames {
                guard f.width==320,f.height==180 else{throw Failure(message:"Image geometry mismatch")}
                let local=h.isFlipped ? f : CGRect(x:f.minX,y:h.bounds.height-f.maxY,width:f.width,height:f.height)
                let win=h.convert(local,to:nil),top=CGRect(x:win.minX,y:w.frame.height-win.maxY,width:win.width,height:win.height)
                frames[name]=["host_top_left_points":rect(f),"screenshot_pixels":rect(CGRect(x:top.minX*CGFloat(shot.width)/w.frame.width,y:top.minY*CGFloat(shot.height)/w.frame.height,width:top.width*CGFloat(shot.width)/w.frame.width,height:top.height*CGFloat(shot.height)/w.frame.height))]
            }
            var edr:[Bool]=[]
            func inspect(_ v:NSView) {if let m=v as? BernEDRImageView {edr.append((m.layer as? CAMetalLayer)?.wantsExtendedDynamicRangeContent ?? true)};v.subviews.forEach(inspect)}
            inspect(h)
            guard edr.count==2,edr.allSatisfy({!$0}) else{throw Failure(message:"Product Standard requested EDR or missing actual Metal helper")}
            let dest=CGImageDestinationCreateWithURL(output.appendingPathComponent("capture.png") as CFURL,UTType.png.identifier as CFString,1,nil)!
            CGImageDestinationAddImage(dest,shot,nil);guard CGImageDestinationFinalize(dest) else{throw Failure(message:"Cannot write capture")}
            guard NSWorkspace.shared.frontmostApplication?.processIdentifier==before else{throw Failure(message:"Foreground changed; no activation attempted")}
            report["frames"]=frames;report["captures"]=captures;report["stable_buffer_count"]=hashes.count;report["png_size"]=[shot.width,shot.height];report["png_color"]=color(shot);report["product_edr_requests"]=edr;report["capture_png_sha256"]=digest(try Data(contentsOf:output.appendingPathComponent("capture.png")));report["success"]=true
            return 0
        } catch {report["error"]=String(describing:error);fputs("Standard color fixture failed: \(error)\n",stderr);return 1}
    }
}
