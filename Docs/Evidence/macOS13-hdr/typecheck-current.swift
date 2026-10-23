import AppKit
import SwiftUI
import Combine
import MetalKit
import CoreImage
import ColorSync
import ImageIO
import UniformTypeIdentifiers
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
