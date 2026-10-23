import AppKit
import SwiftUI
import Combine
import MetalKit
import CoreImage
import ColorSync
import ImageIO
import UniformTypeIdentifiers
private var fixtureRefreshes = 0
private var fixtureDraws = 0
private var fixtureStops = 0
private var fixtureManualPosting = false
private var fixtureStageName = "high-initial"
private var fixtureNotifications: [[String:Any]] = []
private var fixturePixels: [[String:Any]] = []
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
    nonisolated static func legacyHDRColorSpace(_ image: CGImage) -> CGColorSpace? {
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
        else if let view = view as? BernSDRImageView { view.image = nil }
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
        fixtureNotifications.append(["name":notification.name.rawValue,"manual":fixtureManualPosting,"stage":fixtureStageName,"intent":dynamicRange == .high ? "high":"standard","headroom":window?.screen?.maximumExtendedDynamicRangeColorComponentValue ?? 1,"requests_edr":display.requestsEDR,"renders_hdr":display.rendersHDR])
        if notification.name == NSWindow.didChangeScreenNotification {
            standardImage = nil
            standardSize = .zero
        }
        // NSScreen documents this notification for actual headroom changes;
        // no undocumented KVO contract or continuous frame timer is required.
        refreshDisplay()
    }

    private func refreshDisplay() {
        fixtureRefreshes += 1
        if let surface = layer as? CAMetalLayer, surface.wantsExtendedDynamicRangeContent != display.requestsEDR {
            surface.wantsExtendedDynamicRangeContent = display.requestsEDR
        }
        needsDisplay = true
    }

    override func draw(_ dirtyRect: NSRect) {
        fixtureDraws += 1
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
            // Fixture-only readback verifies the pixels submitted to CA;
            // no readback, counters, or frame timers are added to the product.
            if let readback = device?.makeBuffer(length: 512, options: .storageModeShared),
               let encoder = command.makeBlitCommandEncoder() {
                for (index, x) in [drawable.texture.width / 4, drawable.texture.width * 3 / 4].enumerated() {
                    encoder.copy(from: drawable.texture, sourceSlice: 0, sourceLevel: 0,
                        sourceOrigin: MTLOrigin(x: x, y: drawable.texture.height / 4, z: 0), sourceSize: MTLSize(width: 1, height: 1, depth: 1),
                        to: readback, destinationOffset: index * 256, destinationBytesPerRow: 256, destinationBytesPerImage: 256)
                }
                encoder.endEncoding()
                let stage = fixtureStageName
                let route = hdr ? "HDR" : "SDR"
                let outputSpace = String(describing: space.name)
                let headroom = window?.screen?.maximumExtendedDynamicRangeColorComponentValue ?? 1
                command.addCompletedHandler { _ in
                    let words = readback.contents().assumingMemoryBound(to: UInt16.self)
                    let left = Float(Float16(bitPattern: UInt16(littleEndian: words[0])))
                    let right = Float(Float16(bitPattern: UInt16(littleEndian: words[128])))
                    DispatchQueue.main.async {
                        fixturePixels.append(["stage":stage,"route":route,"output_space":outputSpace,"headroom":headroom,"left":left,"right":right])
                    }
                }
            }
            command.present(drawable)
            command.commit()
        } catch {
            NSLog("Bern HDR image rendering failed: %@", String(describing: error))
        }
    }

    func stop() {
        fixtureStops += 1
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
}
#endif

private extension View {
    @ViewBuilder func bernImageDynamicRange(_ intent: BernImageDynamicRange) -> some View {
        #if os(macOS)
        if #available(macOS 14, *) { allowedDynamicRange(intent == .standard ? .standard : .high) } else { self }
        #else
        allowedDynamicRange(intent == .standard ? .standard : .high)
        #endif
    }
}



private let resource = URL(fileURLWithPath:CommandLine.arguments[1])
private let output = URL(fileURLWithPath:CommandLine.arguments[2],isDirectory:true)
private let source = CGImageSourceCreateWithURL(resource as CFURL,nil)!
private let cg = CGImageSourceCreateImageAtIndex(source,0,nil)!
private let fixturePicture = BernImage.Picture(image:cg,orientation:.up,ratio:CGFloat(cg.width)/CGFloat(cg.height),legacyHDRColorSpace:BernImage.legacyHDRColorSpace(cg))
private struct Frames:PreferenceKey {
    static var defaultValue:[String:CGRect] { [:] }
    static func reduce(value:inout [String:CGRect],nextValue:()->[String:CGRect]) {value.merge(nextValue(),uniquingKeysWith:{_,n in n})}
}
private var frames:[String:CGRect]=[:]
private final class Model:ObservableObject {
    @Published var highIntent=BernImageDynamicRange.high
    @Published var size=CGSize(width:192,height:108)
    @Published var mounted=true
}
private struct SoftwareImage:NSViewRepresentable {
    func makeNSView(context:Context)->BernSDRImageView {BernSDRImageView(frame:.zero)}
    func updateNSView(_ view:BernSDRImageView,context:Context) {view.show(fixturePicture)}
    static func dismantleNSView(_ view:BernSDRImageView,coordinator:()) {view.image=nil}
}
private struct Pane<V:View>:View {
    let name:String
    let picture:V
    let size:CGSize
    var body:some View {
        VStack(spacing:8) {
            picture.frame(width:size.width,height:size.height).clipped()
                .background(GeometryReader {g in Color.clear.preference(key:Frames.self,value:[name:g.frame(in:.named("fixture"))])})
            Text(name).font(.system(size:12))
        }.frame(width:220,height:155,alignment:.top)
    }
}
private struct Fixture:View {
    @ObservedObject var model:Model
    var body:some View {
        Group {
            if model.mounted {
                HStack(spacing:0) {
                    Pane(name:"Standard",picture:BernLegacyEDRImage(picture:fixturePicture,dynamicRange:.standard),size:model.size)
                    Pane(name:"High",picture:BernLegacyEDRImage(picture:fixturePicture,dynamicRange:model.highIntent),size:model.size)
                    Pane(name:"No Metal fallback",picture:SoftwareImage(),size:model.size)
                }
            }
        }.padding(20).frame(width:700,height:200).background(Color.white)
            .environment(\.colorScheme,.light).foregroundColor(.black)
            .coordinateSpace(name:"fixture").onPreferenceChange(Frames.self){frames=$0}
    }
}
func rect(_ r:CGRect)->[String:Double] {["x":r.minX,"y":r.minY,"width":r.width,"height":r.height]}
func all(_ v:NSView)->[NSView] {[v]+v.subviews.flatMap{all($0)}}
private let model=Model()
private let app=NSApplication.shared
private let previous=NSWorkspace.shared.frontmostApplication
app.setActivationPolicy(.regular)
private let window=NSWindow(contentRect:NSRect(x:140,y:140,width:700,height:200),styleMask:[.titled,.closable],backing:.buffered,defer:false)
window.title="Bern adaptive HDR probe 73B8"
window.contentView=NSHostingView(rootView:Fixture(model:model))
window.makeKeyAndOrderFront(nil);app.activate(ignoringOtherApps:true)
private var policyChecks:[[String:Any]]=[]
for intent in [BernImageDynamicRange.standard,.high] {
    for potential:CGFloat in [1,2] {
        for current:CGFloat in [1,2] {
            let plan=BernLegacyImageDisplay(intent,potential:potential,current:current)
            policyChecks.append(["intent":intent == .high ? "high":"standard","potential":potential,"current":current,"requestsEDR":plan.requestsEDR,"rendersHDR":plan.rendersHDR,"pass":plan.requestsEDR == (intent == .high && potential>1) && plan.rendersHDR == (intent == .high && potential>1 && current>1)])
        }
    }
}
private var stage=0
private var stable=0
private var ticks=0
private var last:Data?
private var samples:[[String:Any]]=[]
private var refreshedBefore=0
private var drawsBefore=0
private var restored=false
private let started=Date()
private let names=["high-initial","high-to-standard","standard-to-high","screen-notifications","resized","unmounted"]
func finish(_ failure:String?=nil) {
    var report:[String:Any]=["os":ProcessInfo.processInfo.operatingSystemVersionString,"samples":samples,"policy":policyChecks,"notifications":fixtureNotifications,"submitted_texture_pixels":fixturePixels,"source_uses_2100":CGColorSpaceUsesITUR_2100TF(cg.colorSpace!),"canonical_space":String(describing:fixturePicture.legacyHDRColorSpace?.name),"original_frontmost_pid":previous?.processIdentifier ?? -1,"restore_requested":restored,"restored_frontmost_pid":NSWorkspace.shared.frontmostApplication?.processIdentifier ?? -1,"focus":"Activated only until initial capture, then restored original frontmost; later captures were own inactive window","fixture_instrumentation":"Product helper bodies extracted verbatim plus fixture-only counters/OS-notification logs and 2-pixel GPU blit readback per frame; SoftwareImage forces native no-Metal fallback without replacing the installed GPU","limitations":"No second physical display was available; screen notifications are posted only in this fixture process. WindowServer SDR PNG is not a physical HDR luminance measurement."]
    if let failure {report["failure"]=failure}
    try! JSONSerialization.data(withJSONObject:report,options:[.prettyPrinted,.sortedKeys]).write(to:output.appendingPathComponent("report.json"))
    if !restored,let previous { _=previous.activate(options:[.activateIgnoringOtherApps]) }
    window.close();exit(failure == nil ? 0:1)
}
private let timer=Timer.scheduledTimer(withTimeInterval:0.15,repeats:true) {_ in
    guard Date().timeIntervalSince(started)<20 else {finish("bounded timeout at stage \(stage)");return}
    ticks += 1
    if stage==5 {
        guard ticks>=4 else{return}
        let views=all(window.contentView!)
        samples.append(["stage":names[stage],"metal_views":views.filter{$0 is MTKView}.count,"software_views":views.filter{$0 is BernSDRImageView}.count,"stops":fixtureStops])
        guard fixtureStops>=2,!views.contains(where:{$0 is MTKView || $0 is BernSDRImageView}) else {finish("teardown did not release views");return}
        finish();return
    }
    guard ticks>=3,frames.count==3,let image=CGWindowListCreateImage(.null,.optionIncludingWindow,CGWindowID(window.windowNumber),.boundsIgnoreFraming),let data=image.dataProvider?.data else{return}
    if (data as Data)==last {stable += 1} else {stable=0;last=data as Data}
    guard stable>=4 else{return}
    if stage == 1, window.screen!.maximumExtendedDynamicRangeColorComponentValue > 1, ticks < 60 { return }
    let url=output.appendingPathComponent(names[stage]+".png")
    let destination=CGImageDestinationCreateWithURL(url as CFURL,UTType.png.identifier as CFString,1,nil)!
    CGImageDestinationAddImage(destination,image,nil);CGImageDestinationFinalize(destination)
    let screen=window.screen!
    let views=all(window.contentView!)
    let surfaces=views.compactMap{$0 as? MTKView}.map{v -> [String:Any] in
        let layer=v.layer as! CAMetalLayer
        return ["frame":rect(v.convert(v.bounds,to:nil)),"drawable_size":[v.drawableSize.width,v.drawableSize.height],"requests_edr":layer.wantsExtendedDynamicRangeContent,"output_space":String(describing:layer.colorspace?.name),"pixel_format":v.colorPixelFormat.rawValue]
    }
    samples.append(["stage":names[stage],"headroom":screen.maximumExtendedDynamicRangeColorComponentValue,"potential":screen.maximumPotentialExtendedDynamicRangeColorComponentValue,"frames":Dictionary(uniqueKeysWithValues:frames.map{($0.key,rect($0.value))}),"capture_width":image.width,"capture_height":image.height,"scale":window.backingScaleFactor,"content_height":200,"surfaces":surfaces,"refreshes":fixtureRefreshes,"draws":fixtureDraws,"active":app.isActive,"key":window.isKeyWindow])
    if stage==0,let previous {restored=previous.activate(options:[.activateIgnoringOtherApps])}
    if stage==3 {
        guard fixtureRefreshes>=refreshedBefore+4,fixtureDraws>drawsBefore else {finish("screen event did not redraw");return}
    }
    stage += 1;ticks=0;stable=0;last=nil
    fixtureStageName = names[stage]
    switch stage {
    case 1:model.highIntent = .standard
    case 2:model.highIntent = .high
    case 3:
        refreshedBefore=fixtureRefreshes;drawsBefore=fixtureDraws
        fixtureManualPosting = true
        NotificationCenter.default.post(name:NSApplication.didChangeScreenParametersNotification,object:nil)
        NotificationCenter.default.post(name:NSWindow.didChangeScreenNotification,object:window)
        fixtureManualPosting = false
    case 4:model.size=CGSize(width:208,height:117)
    case 5:model.mounted=false
    default:break
    }
}
app.run()
