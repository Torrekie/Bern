import Foundation
import CoreGraphics
import ImageIO
import ColorSync
import CryptoKit
import Darwin

func verify(_ test: @autoclosure () -> Bool, _ message: String = "", line: UInt = #line) {
    guard test() else { fputs("Input verification failed at line \(line): \(message)\n", stderr); exit(2) }
}

// An isolated scalar candidate for this known neutral fixture. LW=1000 is a
// preset supported by the existing A14 ramp, not mastering metadata from PNG.
private let isoDefaultWhite = 203.0
private let candidateMasteringPeak = 1000.0

func pqNits(_ signal: Double) -> Double {
    let m1 = 2610.0 / 16384, m2 = 2523.0 / 32
    let c1 = 3424.0 / 4096, c2 = 2413.0 / 128, c3 = 2392.0 / 128
    let p = pow(max(0, min(1, signal)), 1 / m2)
    return 10000 * pow(max(p - c1, 0) / (c2 - c3 * p), 1 / m1)
}
func pqSignal(_ nits: Double) -> Double {
    let m1 = 2610.0 / 16384, m2 = 2523.0 / 32
    let c1 = 3424.0 / 4096, c2 = 2413.0 / 128, c3 = 2392.0 / 128
    let p = pow(max(0, nits) / 10000, m1)
    return pow((c1 + c2 * p) / (1 + c3 * p), m2)
}

// BT.2408-6 Annex 5, LB=Lmin=0, LW=1000, Lmax=203*Hd.
// Return linear BT.2020 values relative to ISO diffuse white, not target peak.
// No claim is made about source values outside this fixture's <=812.056 nits.
func annex5EDR(_ signal: Double, headroom: Double) -> Double {
    let luminance = pqNits(signal)
    let hd = max(1, headroom)
    if hd >= candidateMasteringPeak / isoDefaultWhite { return luminance / isoDefaultWhite }
    let low = pqSignal(0)
    let span = pqSignal(candidateMasteringPeak) - low
    let x = min(max((signal - low) / span, 0), 1)
    let p = (pqSignal(isoDefaultWhite * hd) - low) / span
    let k = 1.5 * p - 0.5
    let z: Double
    if x < k { z = x }
    else {
        let t = (x - k) / (1 - k)
        z = (2 * t * t * t - 3 * t * t + 1) * k
            + (t * t * t - 2 * t * t + t) * (1 - k)
            + (-2 * t * t * t + 3 * t * t) * p
    }
    // b=0 for Lmin=LB=0, hence u=z.
    return pqNits(z * span + low) / isoDefaultWhite
}

func residentBytes() -> UInt64 {
    var info = mach_task_basic_info()
    var count = mach_msg_type_number_t(MemoryLayout<mach_task_basic_info>.size / MemoryLayout<integer_t>.size)
    let status = withUnsafeMutablePointer(to: &info) {
        $0.withMemoryRebound(to: integer_t.self, capacity: Int(count)) {
            task_info(mach_task_self_, task_flavor_t(MACH_TASK_BASIC_INFO), $0, &count)
        }
    }
    return status == KERN_SUCCESS ? info.resident_size : 0
}

final class PQFixture {
    let original: CGImage
    let width: Int
    let height: Int
    let raw: Data
    let bytesPerRow: Int
    let sourceSHA256: String
    let maxCode: Int
    let bigEndian: Bool
    let linearSpace = CGColorSpace(name: CGColorSpace.extendedLinearITUR_2020)!
    var timings: [[String: Any]] = []
    let sourceNits: [Double]

    init(_ url: URL) {
        let resource = try! Data(contentsOf: url)
        sourceSHA256 = SHA256.hash(data: resource).map { String(format: "%02x", $0) }.joined()
        verify(sourceSHA256 == "96f80d2f1c06070dac29e3b7e2924a6aed8e54286bc73921f62cf75420a599ed", "Only the audited neutral fixture is supported")
        let source = CGImageSourceCreateWithData(resource as CFData, nil)!
        original = CGImageSourceCreateImageAtIndex(source, 0, nil)!
        let space = original.colorSpace!
        let profile = ColorSyncProfileCreate(space.copyICCData()!, nil)!.takeRetainedValue()
        let cicp = ColorSyncProfileCopyTag(profile, "cicp" as CFString)!.takeRetainedValue() as Data
        verify([UInt8](cicp) == [0x63,0x69,0x63,0x70,0,0,0,0,9,16,0,1])
        let named = original.copy(colorSpace: CGColorSpace(name: CGColorSpace.itur_2100_PQ)!)!
        width = named.width; height = named.height; bytesPerRow = named.bytesPerRow
        verify(width == 640 && height == 360 && named.bitsPerComponent == 16 && named.bitsPerPixel == 64)
        let order = named.bitmapInfo.intersection(.byteOrderMask)
        verify(order == .byteOrder16Big || order == .byteOrder16Little, "Explicit decoded 16-bit byte order required")
        let bigEndian = order == .byteOrder16Big
        self.bigEndian = bigEndian
        raw = named.dataProvider!.data! as Data
        verify(raw == original.dataProvider!.data! as Data, "Relabel only; no source pixel conversion")
        let rawBytes = raw, stride = bytesPerRow, pixelWidth = width, pixelHeight = height
        var maximum = 0
        var components: [Double] = []
        rawBytes.withUnsafeBytes { bytes in
            let p = bytes.bindMemory(to: UInt8.self)
            for y in 0..<pixelHeight { for x in 0..<pixelWidth {
                let at = y * stride + x * 8
                let channels = (0..<4).map { i in bigEndian ? Int(p[at+i*2])*256+Int(p[at+i*2+1]) : Int(p[at+i*2+1])*256+Int(p[at+i*2]) }
                verify(channels[3] == 65535, "This proof handles opaque pixels")
                verify(channels[0...2].max()! - channels[0...2].min()! <= 1, "Only neutral fixture; no color-space application claim")
                maximum = max(maximum, channels[0...2].max()!)
                if (x == pixelWidth/4 || x == pixelWidth*3/4) && y == pixelHeight/4 { components.append(pqNits(Double(channels[0])/65535)) }
            } }
        }
        maxCode = maximum
        sourceNits = components
        verify(pqNits(Double(maximum)/65535) < candidateMasteringPeak)
    }

    func image(headroom: Double) -> CGImage {
        let memoryBefore = residentBytes()
        let began = CFAbsoluteTimeGetCurrent()
        var table = [Float](repeating: 0, count: maxCode + 1)
        for code in 0...maxCode { table[code] = Float(annex5EDR(Double(code)/65535, headroom: headroom)) }
        var pixels = [Float](repeating: 1, count: width * height * 4)
        raw.withUnsafeBytes { bytes in
            let p = bytes.bindMemory(to: UInt8.self)
            for y in 0..<height { for x in 0..<width {
                let at = y * bytesPerRow + x * 8, out = (y * width + x) * 4
                for channel in 0..<3 { pixels[out+channel] = table[bigEndian ? Int(p[at+channel*2])*256+Int(p[at+channel*2+1]) : Int(p[at+channel*2+1])*256+Int(p[at+channel*2])] }
            } }
        }
        let data = pixels.withUnsafeBufferPointer { Data(buffer: $0) } as CFData
        let image = CGImage(width: width, height: height, bitsPerComponent: 32, bitsPerPixel: 128,
            bytesPerRow: width * 16, space: linearSpace,
            bitmapInfo: CGBitmapInfo(rawValue: CGImageAlphaInfo.premultipliedLast.rawValue | CGBitmapInfo.floatComponents.rawValue | CGBitmapInfo.byteOrder32Little.rawValue),
            provider: CGDataProvider(data: data)!, decode: nil, shouldInterpolate: false, intent: .defaultIntent)!
        timings.append(["headroom":headroom,"milliseconds":(CFAbsoluteTimeGetCurrent()-began)*1000,"resident_before":memoryBefore,"resident_after":residentBytes(),"float_image_bytes":width*height*16,"lut_bytes":table.count*4])
        return image
    }
}
