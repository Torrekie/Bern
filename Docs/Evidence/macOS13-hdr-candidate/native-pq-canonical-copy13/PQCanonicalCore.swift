// Work-only diagnostic. The original CGImage, source file and ICC stay intact.
import Foundation
import CoreGraphics
import ImageIO
import ColorSync
import CryptoKit

struct PQCopyFailure:Error {let message:String}
func pqDigest(_ data:Data)->String {SHA256.hash(data:data).map{String(format:"%02x",$0)}.joined()}

struct PQDecoded {
    let url:URL
    let fileData:Data
    let source:CGImageSource
    let image:CGImage
    let properties:[CFString:Any]
    let exif:UInt32
    let icc:Data
    let provider:Data
    init(_ url:URL)throws {
        self.url=url;let data=try Data(contentsOf:url);fileData=data
        guard let source=CGImageSourceCreateWithData(data as CFData,nil),let image=CGImageSourceCreateImageAtIndex(source,0,nil),
              let icc=image.colorSpace?.copyICCData(),let provider=image.dataProvider?.data else {throw PQCopyFailure(message:"Normal ImageIO decode/ICC/provider unavailable: \(url.lastPathComponent)")}
        self.source=source;self.image=image;self.icc=icc as Data;self.provider=provider as Data
        properties=CGImageSourceCopyPropertiesAtIndex(source,0,nil) as? [CFString:Any] ?? [:]
        exif=(properties[kCGImagePropertyOrientation] as? UInt32) ?? 1
    }
    var ratio:Double {
        let turned=(5...8).contains(exif)
        return Double(turned ? image.height:image.width)/Double(turned ? image.width:image.height)
    }
}

// Operative Runtime helper, including its native recognition and14 availability
// boundary. Derived-copy selection below narrows the accepted protocol to PQ.
func runtimeLegacyHDRSpace(_ image:CGImage)->CGColorSpace? {
    guard let space=image.colorSpace else {return nil}
    if CGColorSpaceUsesITUR_2100TF(space) {return space}
    if #available(macOS 14,*) {return nil}
    guard space.model == .rgb,let data=space.copyICCData(),
          let profile=ColorSyncProfileCreate(data,nil)?.takeRetainedValue(),
          let tag=ColorSyncProfileCopyTag(profile,"cicp" as CFString)?.takeRetainedValue() else {return nil}
    let bytes=[UInt8](tag as Data)
    guard bytes.count==12,bytes[0...3].elementsEqual([0x63,0x69,0x63,0x70]),
          bytes[4...7].allSatisfy({$0==0}),bytes[8]==9,(bytes[9]==16 || bytes[9]==18),bytes[10]==0,bytes[11]==1 else {return nil}
    return CGColorSpace(name:bytes[9]==16 ? CGColorSpace.itur_2100_PQ:CGColorSpace.itur_2100_HLG)
}

func pqLayout(_ image:CGImage)->[String:Any] {
    ["width":image.width,"height":image.height,"bits_per_component":image.bitsPerComponent,"bits_per_pixel":image.bitsPerPixel,
     "bytes_per_row":image.bytesPerRow,"bitmap_info":image.bitmapInfo.rawValue,"alpha_info":image.alphaInfo.rawValue,
     "byte_order":image.bitmapInfo.intersection(.byteOrderMask).rawValue,"should_interpolate":image.shouldInterpolate]
}
func pqColor(_ image:CGImage)->[String:Any] {
    guard let space=image.colorSpace else {return ["present":false]}
    var r:[String:Any]=["present":true,"name":space.name as String? ?? "unnamed","model":space.model.rawValue,
        "uses_2100":CGColorSpaceUsesITUR_2100TF(space),"is_pq":CGColorSpaceIsPQBased(space)]
    if let data=space.copyICCData() {
        r["icc_sha256"]=pqDigest(data as Data);r["icc_bytes"]=(data as Data).count
        if let p=ColorSyncProfileCreate(data,nil)?.takeRetainedValue(),let t=ColorSyncProfileCopyTag(p,"cicp" as CFString)?.takeRetainedValue() {
            r["cicp_hex"]=(t as Data).map{String(format:"%02x",$0)}.joined()
        }
    };return r
}
func samePQLayout(_ a:CGImage,_ b:CGImage)->Bool {
    a.width==b.width && a.height==b.height && a.bitsPerComponent==b.bitsPerComponent && a.bitsPerPixel==b.bitsPerPixel &&
    a.bytesPerRow==b.bytesPerRow && a.bitmapInfo==b.bitmapInfo && a.alphaInfo==b.alphaInfo && a.shouldInterpolate==b.shouldInterpolate
}

struct PQDisplayCopy {
    let original:PQDecoded
    let display:CGImage
    let selection:String
    let validation:[String:Any]
    init(_ original:PQDecoded)throws {
        self.original=original
        guard let sourceSpace=original.image.colorSpace,let selected=runtimeLegacyHDRSpace(original.image),CGColorSpaceIsPQBased(selected) else {
            throw PQCopyFailure(message:"Input not protocol-PQ under Runtime helper; HLG/unknown inputs remain outside this diagnostic")
        }
        let originalColorBefore=pqColor(original.image)
        if CGColorSpaceUsesITUR_2100TF(sourceSpace) {
            // Native namedPQ oracle stays the original CGImage. No gratuitous copy.
            display=original.image;selection="native-pq-original"
        } else {
            // Runtime can select this only after the complete strict CICP guard.
            guard let copy=original.image.copy(colorSpace:selected) else {throw PQCopyFailure(message:"StrictCICP PQ copy(colorSpace:) failed")}
            display=copy;selection="strict-cicp-pq-color-space-copy"
        }
        let provider=display.dataProvider?.data as Data?
        let afterICC=original.image.colorSpace?.copyICCData() as Data?
        let afterProperties=CGImageSourceCopyPropertiesAtIndex(original.source,0,nil) as? [CFString:Any] ?? [:]
        let afterExif=(afterProperties[kCGImagePropertyOrientation] as? UInt32) ?? 1
        let fileUnchanged=try Data(contentsOf:original.url)==original.fileData
        let unchanged=provider==original.provider && samePQLayout(original.image,display) &&
            afterICC==original.icc && afterExif==original.exif && fileUnchanged
        guard unchanged else {throw PQCopyFailure(message:"Derived display copy changed original source/layout/provider/orientation contract")}
        validation=["selection":selection,"source_file":original.url.lastPathComponent,"source_file_sha256":pqDigest(original.fileData),
            "original_color_before":originalColorBefore,"derived_color":pqColor(display),"original_icc_sha256_before":pqDigest(original.icc),
            "original_icc_sha256_after":afterICC.map(pqDigest) ?? "absent","original_file_unchanged":fileUnchanged,
            "original_layout":pqLayout(original.image),"derived_layout":pqLayout(display),"layout_equal":true,"provider_bytes_equal":true,
            "original_provider_sha256":pqDigest(original.provider),"derived_provider_sha256":provider.map(pqDigest) ?? "absent",
            "source_exif_before":original.exif,"source_exif_after":afterExif,"display_exif_carried_separately":original.exif,
            "orientation_not_baked_into_pixels":true,"display_ratio_after_exif":original.ratio]
    }
}

struct PQPair {
    let named:PQDisplayCopy
    let custom:PQDisplayCopy
    let report:[String:Any]
    init(namedURL:URL,customURL:URL)throws {
        named=try PQDisplayCopy(PQDecoded(namedURL));custom=try PQDisplayCopy(PQDecoded(customURL))
        guard named.selection=="native-pq-original" else {throw PQCopyFailure(message:"Oracle source must be natively recognized PQ")}
        let namedBytes=named.original.image.dataProvider?.data as Data?,customBytes=custom.display.dataProvider?.data as Data?
        let sameLayout=samePQLayout(named.original.image,custom.display)
        let sameBytes=namedBytes==customBytes
        guard sameLayout,sameBytes,named.original.exif==custom.original.exif else {throw PQCopyFailure(message:"Custom PQ derived input differs from named oracle raw layout/provider/orientation")}
        report=["success":true,"scope":"Offline normal ImageIO decode, Runtime protocol-PQ classification and color-space-only derived CGImage. Original source/CGImage/ICC retained. No product edit, pixel redraw or image metadata rewrite.",
            "os":ProcessInfo.processInfo.operatingSystemVersionString,"named":named.validation,"custom":custom.validation,
            "derived_custom_vs_named_original_layout_equal":sameLayout,"derived_custom_vs_named_original_provider_bytes_equal":sameBytes,
            "source_orientation_equal":true,"color_formula_changed":false,"hlg_hero_alpha_exif_coverage":"HLG/hero untested. This source pair is opaque EXIFup; metadata preservation checks do not claim other orientations/alpha coverage."]
    }
}
