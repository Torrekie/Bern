// Fixture-only public conversion. This is not a general product snapshot renderer.
import CoreImage

private enum FixtureHeroSnapshotBackend: String {
    case imageRenderer = "default"
    case nativeCI
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_SNAPSHOT_BACKEND"]
    static let selected = FixtureHeroSnapshotBackend(rawValue: requested ?? "default")
}

@MainActor private enum FixtureNativeCI {
    private struct Input {
        let label: String
        let permitsNamedOriginal: Bool
    }
    private static var inputs: [ObjectIdentifier: Input] = [:]
    private static var context: CIContext?
    private static var sources: [[String: Any]] = []
    private static var outputs: [[String: Any]] = []
    private(set) static var failure: String?

    static func fail(_ message: String) { failure = message }
    static var report: [String: Any] {
        ["context_created": context != nil, "sources": sources, "outputs": outputs,
         "failure": failure ?? "none",
         "operation": "CIImage explicit source colorSpace -> CIContext.createCGImage RGBAh/extendedSRGB; no filters/exposure/resize/tone curve",
         "scope": "SHA-locked opaque/up 640x360 atlas, fill 320x180pt at2x only; not general orientation/fit/alpha acceptance"]
    }

    private static func metadata(_ image: CGImage) -> [String: Any] {
        ["width": image.width, "height": image.height,
         "bits_per_component": image.bitsPerComponent, "bits_per_pixel": image.bitsPerPixel,
         "bytes_per_row": image.bytesPerRow, "bitmap_info": image.bitmapInfo.rawValue,
         "alpha_info": image.alphaInfo.rawValue,
         "float_components": image.bitmapInfo.contains(.floatComponents)]
    }

    static func prepareInputs(_ urls: [URL]) throws {
        guard FixtureHeroSnapshotBackend.selected == .nativeCI, urls.count == 2, inputs.isEmpty else {
            throw FixtureFailure(message: "nativeCI input registration configuration unsupported")
        }
        let hashes = ["3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b",
                      "fa3fdc43d91518c145c08b01ba6181ec063c68158e57d312a1ff942571c2a12e"]
        for (index, url) in urls.enumerated() {
            guard fixtureHash(try Data(contentsOf: url)) == hashes[index],
                  let picture = BernPictures.shared.cached(url.absoluteString),
                  picture.orientation == .up, picture.image.width == 640, picture.image.height == 360 else {
                throw FixtureFailure(message: "nativeCI requires exact known opaque/up640x360 atlas inputs")
            }
            let display: CGImage
            let choice: String
            if let canonical = picture.legacyStandardPQImage {
                display = canonical; choice = "actual_cached_legacyStandardPQImage"
            } else if index == 0 {
                display = picture.image; choice = "original_named_recognized_PQ"
            } else {
                throw FixtureFailure(message: "nativeCI has no actual cached canonicalPQ or recognized namedPQ source")
            }
            guard display.width == 640, display.height == 360, display.colorSpace != nil else {
                throw FixtureFailure(message: "nativeCI selected display image has no explicit colorSpace or wrong size")
            }
            let input = Input(label: url.lastPathComponent, permitsNamedOriginal: index == 0)
            inputs[ObjectIdentifier(picture.image)] = input
            var entry = metadata(display)
            entry["label"] = input.label; entry["selection"] = choice
            entry["file_sha256"] = hashes[index]
            entry["original_id"] = String(describing: ObjectIdentifier(picture.image))
            entry["display_id"] = String(describing: ObjectIdentifier(display))
            entry["opacity_proof"] = "Exact SHA-locked previously verified fully opaque atlas, not alphaInfo inference"
            sources.append(entry)
        }
    }

    static func pixels(_ picture: BernImage.Picture, fit: BernImageFit,
                       bounds: CGRect, rect: CGRect, scale: CGFloat, corner: CGFloat) -> CGImage? {
        guard case .fill = fit else { fail("nativeCI unsupported fit; fill required"); return nil }
        guard picture.orientation == .up, bounds.size == CGSize(width: 320, height: 180),
              rect.size == bounds.size, scale == 2, corner == 0,
              let input = inputs[ObjectIdentifier(picture.image)] else {
            fail("nativeCI unsupported source/frame/orientation/scale/corner; no fallback"); return nil
        }
        let display: CGImage
        if let canonical = picture.legacyStandardPQImage { display = canonical }
        else if input.permitsNamedOriginal { display = picture.image }
        else { fail("nativeCI missing cached canonicalPQ; no fallback"); return nil }
        guard display.width == 640, display.height == 360, let sourceSpace = display.colorSpace else {
            fail("nativeCI source extent/colorSpace unsupported"); return nil
        }
        guard let destination = CGColorSpace(name: CGColorSpace.extendedSRGB) else {
            fail("nativeCI extendedSRGB unavailable"); return nil
        }
        // Only the selected branch reaches this lazy creation. Default does not.
        if context == nil { context = CIContext() }
        guard let context else { fail("nativeCI context unavailable"); return nil }
        let image = CIImage(cgImage: display, options: [.colorSpace: sourceSpace])
        let extent = CGRect(x: 0, y: 0, width: 640, height: 360)
        guard image.extent == extent,
              let pixels = context.createCGImage(image, from: extent, format: .RGBAh, colorSpace: destination),
              pixels.width == 640, pixels.height == 360 else {
            fail("nativeCI createCGImage failed or changed fixed extent; no fallback"); return nil
        }
        var entry = metadata(pixels)
        entry["source"] = input.label
        entry["input_extent"] = fixtureRect(image.extent)
        entry["destination_color_space_requested"] = "kCGColorSpaceExtendedSRGB (configuration, not observed profile)"
        outputs.append(entry)
        return pixels
    }
}
