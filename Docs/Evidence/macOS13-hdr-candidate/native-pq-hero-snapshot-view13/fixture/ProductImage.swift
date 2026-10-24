// Exact product image/cache slice, with one documented diagnostic compiler condition.
import AppKit
import SwiftUI
import Combine
import MetalKit
import CoreImage
import ColorSync
import ImageIO

enum BernImageFit {
    case contain, cover, fill
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

private extension View {
    @ViewBuilder func bernImageDynamicRange(_ intent: BernImageDynamicRange) -> some View {
        #if os(macOS)
        if #available(macOS 14, *) { allowedDynamicRange(intent == .standard ? .standard : .high) } else { self }
        #else
        allowedDynamicRange(intent == .standard ? .standard : .high)
        #endif
    }
}


/// A picture from a declared resource in Contents/Resources. With one side
/// given, the other follows the picture's aspect ratio. A label makes it an
/// image for assistive technologies; without one it is decorative.
///
/// HDR pictures show in high dynamic range where the display has headroom:
/// a JPEG or HEIC with a gain map decodes to HDR (macOS 15 and iOS 18 and
/// later), a PQ or HLG PNG keeps its range. On macOS 13, explicit Standard PQ
/// uses the native SwiftUI image surface. Other legacy HDR paths use Core
/// Image; High does not reproduce macOS 14's adaptive ISO HDR tone mapper.

struct BernImage: View {
    /// A declared resource, or
    var name: String? = nil
    /// a file or http(s) URL from a `MediaSource`.
    var url: String? = nil
    let label: String?
    let width: CGFloat?
    let height: CGFloat?
    let fit: BernImageFit
    var rendering: SwiftUI.Image.TemplateRenderingMode = .original
    var dynamicRange = BernImageDynamicRange.high
    /// An explicit width/height ratio fills the proposed grid column.
    var aspect: CGFloat? = nil
    var hero: String? = nil
    var heroMotion = BernMotion(period: 0.48, damping: 0.86)
    var heroCorner: CGFloat = 0
    @State private var fetched: Picture?
    #if os(macOS)
    @ObservedObject private var pictures = BernPictures.shared
    #else
    private var pictures: BernPictures { BernPictures.shared }
    #endif

    struct Picture: @unchecked Sendable {
        let image: CGImage
        let orientation: SwiftUI.Image.Orientation
        /// Width over height as shown, after the orientation.
        let ratio: CGFloat
        #if os(macOS)
        /// Classified once during decode; the original image and ICC stay intact.
        let legacyHDRColorSpace: CGColorSpace?
        /// A display-only PQ interpretation for explicit Standard on macOS 13.
        /// The source image remains available to other picture consumers.
        let legacyStandardPQImage: CGImage?
        #endif
    }

    @MainActor private static var loaded: [String: Picture] = [:]

    @MainActor static func picture(_ name: String) -> Picture? {
        if let picture = loaded[name] { return picture }
        guard let url = Bundle.main.resourceURL?.appendingPathComponent(name),
              let source = CGImageSourceCreateWithURL(url as CFURL, nil),
              let picture = decode(source) else { return nil }
        loaded[name] = picture
        return picture
    }

    /// The first picture of `source`, in HDR where the system can show it,
    /// with its EXIF orientation.
    nonisolated static func decode(_ source: CGImageSource) -> Picture? {
        #if compiler(>=6.0)
        var decoded: CGImage?
        // The iOS simulator decodes gain maps to HDR as black, and cannot
        // show HDR anyway; it shows the SDR picture.
        #if !targetEnvironment(simulator)
        if #available(macOS 15, iOS 18, tvOS 18, *) {
            decoded = CGImageSourceCreateImageAtIndex(
                source, 0, [kCGImageSourceDecodeRequest: kCGImageSourceDecodeToHDR] as CFDictionary)
        }
        #endif
        #else
        // Diagnostic SDK14.2 build: the15+ branch above cannot run on13.
        let decoded: CGImage? = nil
        #endif
        guard let image = decoded ?? CGImageSourceCreateImageAtIndex(source, 0, nil) else { return nil }
        // ImageIO leaves the EXIF orientation to the caller.
        let properties = CGImageSourceCopyPropertiesAtIndex(source, 0, nil) as? [CFString: Any]
        let exif = (properties?[kCGImagePropertyOrientation] as? UInt32) ?? 1
        let orientation: SwiftUI.Image.Orientation = switch exif {
            case 2: .upMirrored
            case 3: .down
            case 4: .downMirrored
            case 5: .leftMirrored
            case 6: .right
            case 7: .rightMirrored
            case 8: .left
            default: .up
        }
        let turned = (5...8).contains(exif)
        let w = CGFloat(turned ? image.height : image.width), h = CGFloat(turned ? image.width : image.height)
        let ratio = w > 0 && h > 0 ? w / h : 1
        #if os(macOS)
        let legacySpace = legacyHDRColorSpace(image)
        return Picture(image: image, orientation: orientation, ratio: ratio,
            legacyHDRColorSpace: legacySpace,
            legacyStandardPQImage: legacyStandardPQImage(image, colorSpace: legacySpace))
        #else
        return Picture(image: image, orientation: orientation, ratio: ratio)
        #endif
    }

    #if os(macOS)
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

    private nonisolated static func legacyStandardPQImage(_ image: CGImage, colorSpace: CGColorSpace?) -> CGImage? {
        if #available(macOS 14, *) { return nil }
        guard #available(macOS 13, *), let originalSpace = image.colorSpace,
              let colorSpace, CGColorSpaceIsPQBased(colorSpace) else { return nil }
        if CGColorSpaceUsesITUR_2100TF(originalSpace) { return image }
        // The decoder selected this space only after the complete CICP proof
        // above. Retag a derived image without rewriting or tone-mapping pixels.
        return image.copy(colorSpace: colorSpace)
    }
    #endif

    @ViewBuilder private func standardImage(_ picture: Picture, displayImage: CGImage? = nil) -> some View {
        let image = SwiftUI.Image(decorative: displayImage ?? picture.image, scale: 1, orientation: picture.orientation)
            .renderingMode(rendering)
        switch fit {
        case .contain: image.resizable().aspectRatio(contentMode: .fit)
        case .cover: image.resizable().aspectRatio(contentMode: .fill)
        case .fill: image.resizable()
        }
    }

    var body: some View {
        let picture = name.flatMap(Self.picture) ?? fetched ?? url.flatMap { pictures.cached($0) }
        let ratio = picture?.ratio ?? 1
        let content = Group {
            if let picture {
                #if os(macOS)
                if #available(macOS 14, *) {
                    standardImage(picture)
                } else if dynamicRange == .standard, rendering == .original,
                          let image = picture.legacyStandardPQImage {
                    standardImage(picture, displayImage: image)
                } else if rendering == .original, picture.legacyHDRColorSpace != nil {
                    switch fit {
                    case .contain: BernLegacyEDRImage(picture: picture, dynamicRange: dynamicRange).aspectRatio(picture.ratio, contentMode: .fit)
                    case .cover: BernLegacyEDRImage(picture: picture, dynamicRange: dynamicRange).aspectRatio(picture.ratio, contentMode: .fill)
                    case .fill: BernLegacyEDRImage(picture: picture, dynamicRange: dynamicRange)
                    }
                } else {
                    standardImage(picture)
                }
                #else
                standardImage(picture)
                #endif
            } else {
                Color.clear
            }
        }
        .bernImageDynamicRange(dynamicRange)
        let shown = Group {
            if let aspect {
                Color.clear
                    .aspectRatio(max(0.01, aspect), contentMode: .fit)
                    // The overlay receives the aspect-fitted proposal directly.
                    // Measuring it and feeding that size back adds a geometry
                    // update for every image on every animated grid resize.
                    .overlay { content }
                    .clipped()
                    .frame(width: width, height: height)
            } else {
                content.frame(width: width ?? height.map { $0 * ratio }, height: height ?? width.map { $0 / ratio }).clipped()
            }
        }
        .task(id: url) {
            guard let url else { return }
            fetched = await pictures.load(url)
        }
        .modifier(BernPictureHero(id: hero, picture: picture, fit: fit, corner: heroCorner, motion: heroMotion))
        if let label {
            shown.accessibilityElement().accessibilityLabel(Text(verbatim: label)).accessibilityAddTraits(.isImage)
        } else {
            shown.accessibilityHidden(true)
        }
    }
}

/// Pictures loaded from files and http(s) URLs, kept while the app runs,
/// with the average color of each for fills drawn from a picture.
@MainActor
#if !os(macOS)
@Observable
#endif
final class BernPictures: BernObservableObject {
    static let shared = BernPictures()
    #if !os(macOS)
    @ObservationIgnored
    #endif
    private var pictures: [String: BernImage.Picture] = [:]
    #if !os(macOS)
    @ObservationIgnored
    #endif
    private var loading: [String: Task<BernImage.Picture?, Never>] = [:]
    /// Average colors as 0xRRGGBB, by URL; observed, so fills follow.
    #if os(macOS)
    @Published
    #endif
    private(set) var averages: [String: UInt32] = [:]

    func cached(_ url: String) -> BernImage.Picture? { pictures[url] }

    func load(_ url: String) async -> BernImage.Picture? {
        if let picture = pictures[url] { return picture }
        let task = loading[url] ?? Task.detached(priority: .userInitiated) { () -> BernImage.Picture? in
            guard let location = URL(string: url) else { return nil }
            let data: Data?
            if location.isFileURL {
                data = try? Data(contentsOf: location)
            } else {
                data = try? await URLSession.shared.data(from: location).0
            }
            guard let data, let source = CGImageSourceCreateWithData(data as CFData, nil) else { return nil }
            return BernImage.decode(source)
        }
        loading[url] = task
        let picture = await task.value
        loading[url] = nil
        if let picture {
            pictures[url] = picture
            averages[url] = Self.average(picture.image)
        }
        return picture
    }

    /// The average color of `url`'s picture, loading it when needed.
    func average(_ url: String?) -> BernColor? {
        guard let url else { return nil }
        if let value = averages[url] { return .fixed(light: value, dark: value) }
        if pictures[url] == nil, loading[url] == nil {
            Task { _ = await load(url) }
        }
        return nil
    }

    /// The mean of the picture drawn down to one pixel.
    private static func average(_ image: CGImage) -> UInt32 {
        var pixel = [UInt8](repeating: 0, count: 4)
        guard let context = CGContext(
            data: &pixel, width: 1, height: 1, bitsPerComponent: 8, bytesPerRow: 4,
            space: CGColorSpace(name: CGColorSpace.sRGB)!,
            bitmapInfo: CGImageAlphaInfo.premultipliedLast.rawValue)
        else { return 0x808080 }
        context.interpolationQuality = .medium
        context.draw(image, in: CGRect(x: 0, y: 0, width: 1, height: 1))
        return (UInt32(pixel[0]) << 16) | (UInt32(pixel[1]) << 8) | UInt32(pixel[2])
    }
}
