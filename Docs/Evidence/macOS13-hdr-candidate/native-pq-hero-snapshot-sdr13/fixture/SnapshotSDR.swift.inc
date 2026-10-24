// Isolated fixed-endpoint Standard-display recipe; never changes the original raw capture.
import CoreImage

private enum FixtureSnapshotSDRMode: String {
    case `default`, bakedNamed = "baked-named"
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_SNAPSHOT_SDR"]
    static let selected = FixtureSnapshotSDRMode(rawValue: requested ?? "default")
}

@MainActor private enum FixtureSnapshotSDR {
    private static var primary = true
    private static var context: CIContext?
    private static var derived: CGImage?
    private static var inputID: ObjectIdentifier?
    private static weak var displayImage: NSImage?
    private static var record: [String: Any] = [:]
    private static var phaseChecks: [[String: Any]] = []
    private static var problem: String?
    private static var conversions = 0, contextCreates = 0, cacheHits = 0, cleanupPasses = 0
    private(set) static var finalizationFailed = false

    static func pixels(_ image: CGImage, key: String, size: CGSize) -> CGImage? {
        // Default does not create CI objects, inspect image properties, or bind a display image.
        guard FixtureSnapshotSDRMode.selected == .bakedNamed else { return image }
        guard primary else { cleanupPasses += 1; return image }
        guard key == "baseline-body-named" else { return image }
        guard problem == nil else { return nil }
        let started = ProcessInfo.processInfo.systemUptime
        do {
            if let derived {
                guard inputID == ObjectIdentifier(image) else { throw FixtureFailure(message: "Named SDR cache input identity changed") }
                cacheHits += 1; return derived
            }
            let matches = fixtureSnapshotCGImageObservations.filter { $0.scalars["key"] as? String == key }
            guard size == CGSize(width: 320, height: 180), matches.count == 1,
                  let descriptor = matches.first, let space = descriptor.space,
                  space.model == .rgb, space.numberOfComponents == 3,
                  let width = descriptor.scalars["width"] as? Int,
                  let height = descriptor.scalars["height"] as? Int,
                  (width == 320 || width == 640), height == width * 9 / 16,
                  let rowBytes = descriptor.scalars["bytes_per_row"] as? Int, rowBytes >= width * 8,
                  descriptor.scalars["bits_per_component"] as? Int == 16,
                  descriptor.scalars["bits_per_pixel"] as? Int == 64,
                  descriptor.scalars["bitmap_info_raw"] as? UInt32 == 4353,
                  descriptor.scalars["alpha_info_raw"] as? UInt32 == 1,
                  descriptor.scalars["byte_order_raw"] as? UInt32 == 4096,
                  descriptor.scalars["pixel_format_raw"] as? UInt32 == 0,
                  descriptor.scalars["float_components"] as? Bool == true else {
                throw FixtureFailure(message: "Unknown named snapshot layout/extent; no SDR fallback")
            }
            let extent = CGRect(x: 0, y: 0, width: width, height: height)
            record = ["key": key, "input_object_id": String(describing: ObjectIdentifier(image)),
                      "input_layout": descriptor.scalars, "input_extent": fixtureRect(extent),
                      "logical_size": [size.width, size.height], "requested_tone_map_hdr_to_sdr": true,
                      "actual_tone_mapping_applied": "unknown", "input_color_space_override": false,
                      "requested_output_format": "RGBA8", "requested_output_color_space": "sRGB",
                      "deferred": false, "conversion_started_uptime_seconds": started]
            let input = CIImage(cgImage: image, options: [.toneMapHDRtoSDR: true])
            guard input.extent == extent, let destination = CGColorSpace(name: CGColorSpace.sRGB) else {
                throw FixtureFailure(message: "CI input extent or sRGB destination unavailable")
            }
            let renderer = CIContext(options: nil); context = renderer; contextCreates += 1
            guard let result = renderer.createCGImage(input, from: extent, format: .RGBA8,
                                                       colorSpace: destination, deferred: false),
                  result.width == width, result.height == height,
                  result.bitsPerComponent == 8, result.bitsPerPixel == 32,
                  !result.bitmapInfo.contains(.floatComponents), result.bytesPerRow >= width * 4 else {
                throw FixtureFailure(message: "CI RGBA8 exact-extent conversion failed; no fallback")
            }
            inputID = ObjectIdentifier(image); derived = result; conversions += 1
            record["output_object_id"] = String(describing: ObjectIdentifier(result))
            record["conversion_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - started
            return result
        } catch { problem = String(describing: error); return nil }
    }

    static func bindDisplay(_ image: NSImage, key: String) -> Bool {
        guard FixtureSnapshotSDRMode.selected == .bakedNamed, primary,
              key == "baseline-body-named" else { return true }
        guard problem == nil, derived != nil, displayImage == nil,
              image.size == CGSize(width: 320, height: 180) else {
            problem = problem ?? "Named derived NSImage binding failed"; return false
        }
        displayImage = image
        record["derived_display_nsimage_id"] = String(describing: ObjectIdentifier(image))
        return true
    }

    static func check(_ flights: [BernHeroFlightView], stage: String, phase: Int) throws {
        if let problem { throw FixtureFailure(message: problem) }
        guard FixtureSnapshotSDRMode.selected == .bakedNamed else { return }
        guard flights.count == 2, let image = displayImage, let named = flights.first,
              derived != nil, conversions == 1, contextCreates == 1,
              named.from === image, named.to === image, image.size == CGSize(width: 320, height: 180),
              named.bounds.size == image.size, named.corner == 0 else {
            problem = "Named derived display identity/geometry changed"; throw FixtureFailure(message: problem!)
        }
        phaseChecks.append(["stage": stage, "phase": phase, "uptime_seconds": ProcessInfo.processInfo.systemUptime,
                            "display_nsimage_id": String(describing: ObjectIdentifier(image)),
                            "derived_cgimage_id": String(describing: ObjectIdentifier(derived!)),
                            "same_from_to_display_image": true])
    }

    static func freezePrimary() { primary = false }

    static func finish(acquisitionSucceeded: Bool) -> [String: Any] {
        // All PNGs and original window teardown already completed. No provider is read.
        if let image = derived {
            let scalars: [String: Any] = ["width": image.width, "height": image.height,
                "bits_per_component": image.bitsPerComponent, "bits_per_pixel": image.bitsPerPixel,
                "bytes_per_row": image.bytesPerRow, "bitmap_info_raw": image.bitmapInfo.rawValue,
                "alpha_info_raw": image.alphaInfo.rawValue, "byte_order_raw": image.byteOrderInfo.rawValue,
                "pixel_format_raw": image.pixelFormatInfo.rawValue,
                "float_components": image.bitmapInfo.contains(.floatComponents)]
            record["output_metadata"] = FixtureSnapshotCGImageDescriptor(scalars: scalars, space: image.colorSpace).metadata()
        }
        if problem == nil, FixtureSnapshotSDRMode.selected == nil { problem = "Invalid snapshot SDR mode" }
        if problem == nil, !acquisitionSucceeded { problem = "Native acquisition incomplete" }
        if problem == nil, FixtureSnapshotSDRMode.selected == .bakedNamed,
           (conversions != 1 || contextCreates != 1 || phaseChecks.filter({ $0["stage"] as? String == "after_png" }).count != 2) {
            problem = "Incomplete one-cache/two-phase SDR display recipe"
        }
        derived = nil; context = nil; inputID = nil; displayImage = nil
        finalizationFailed = problem != nil
        return ["requested": FixtureSnapshotSDRMode.requested.map { $0 as Any } ?? NSNull(),
                "selected": FixtureSnapshotSDRMode.selected.map { $0.rawValue as Any } ?? NSNull(),
                "success": !finalizationFailed, "error": problem.map { $0 as Any } ?? NSNull(),
                "primary_frozen": !primary, "conversion_count": conversions,
                "context_create_count": contextCreates, "cache_hit_count": cacheHits,
                "cleanup_passthrough_count": cleanupPasses, "records": record.isEmpty ? [] : [record],
                "phase_checks": phaseChecks, "metadata_stage": "after_existing_window_teardown",
                "helper_references_cleared": derived == nil && context == nil && displayImage == nil,
                "release_scope": "Only helper-owned derived/context and weak display reference; no deallocation claim"]
    }
}
