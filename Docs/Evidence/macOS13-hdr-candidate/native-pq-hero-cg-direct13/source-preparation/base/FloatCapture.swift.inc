// Isolated fixture only. Raw provider access is deferred until the original teardown.
private enum FixtureFloatCaptureMode: String {
    case off, on
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_FLOAT_CAPTURE"]
    static let selected = FixtureFloatCaptureMode(rawValue: requested ?? "off")
}

@MainActor private enum FixtureSnapshotFloatCapture {
    private struct Held {
        let key: String
        let image: CGImage
        let retainedAt: TimeInterval
    }
    private static let names = [("baseline-body-named", "snapshot-named.bin"),
                                ("baseline-body-custom", "snapshot-custom.bin")]
    private static let maximumBytes = 4 * 1024 * 1024
    private static var primary = true
    private static var primaryCount = 0
    private static var cleanupCount = 0
    private static var primaryKeys: [String] = []
    private static var held: [Held] = []
    private static var peakRetained = 0
    private static var frozenAt: TimeInterval?
    private static var observationError: String?
    private static var exported: [[String: Any]] = []
    private static var providerCopyCalls = 0
    private(set) static var finalizationFailed = false

    static func observe(_ image: CGImage, key: String) {
        guard primary else { cleanupCount += 1; return }
        primaryCount += 1
        primaryKeys.append(key)
        guard FixtureFloatCaptureMode.selected == .on else { return }
        guard held.count < 2, names.contains(where: { $0.0 == key }),
              !held.contains(where: { $0.key == key }) else {
            observationError = "Unexpected/duplicate primary image; actual count/key retained in report"
            return
        }
        held.append(Held(key: key, image: image, retainedAt: ProcessInfo.processInfo.systemUptime))
        peakRetained = max(peakRetained, held.count)
    }

    static func freezePrimary() {
        primary = false
        frozenAt = ProcessInfo.processInfo.systemUptime
    }

    // Public image drawing semantics only; caller is already post-teardown.
    private static func drawingSemantics(_ image: CGImage, key: String) -> [String: Any] {
        let began = ProcessInfo.processInfo.systemUptime
        var record: [String: Any] = [
            "stage": "after_existing_window_teardown_before_primary_release",
            "success": false, "error": NSNull(),
            "rendering_intent_raw": NSNull(), "is_mask": NSNull(), "should_interpolate": NSNull(),
            "color_space_model_raw": NSNull(), "color_space_components": NSNull(),
            "decode_present": NSNull(), "decode_count": NSNull(),
            "decode_nonfinite_index": NSNull(), "observed_at_uptime_seconds": began
        ]
        var values: [Double] = [], bits: [String] = []
        do {
            // Each of the four image getters is called exactly once for this record.
            let intent = image.renderingIntent
            let mask = image.isMask
            let interpolate = image.shouldInterpolate
            let decode = image.decode
            record["rendering_intent_raw"] = intent.rawValue
            record["is_mask"] = mask; record["should_interpolate"] = interpolate
            record["decode_present"] = decode != nil
            // Original hook appends this primary descriptor before observing the same image.
            let primaryDescriptors = fixtureSnapshotCGImageObservations.prefix(2)
            let matches = primaryDescriptors.filter { $0.scalars["key"] as? String == key }
            guard !mask, primaryDescriptors.count == 2, matches.count == 1,
                  let descriptor = matches.first, let space = descriptor.space else {
                throw FixtureFailure(message: "CGImage semantics requires one existing primary descriptor/key and a nonmask image with a color space")
            }
            let model = space.model, components = space.numberOfComponents
            record["color_space_model_raw"] = model.rawValue
            record["color_space_components"] = components
            guard model == .rgb, components == 3, MemoryLayout<CGFloat>.size == 8,
                  MemoryLayout<CGFloat>.stride == 8, MemoryLayout<Double>.size == 8 else {
                throw FixtureFailure(message: "CGImage semantics requires RGB3 and64bit CGFloat; no decode pointer scan")
            }
            if let decode {
                record["decode_count"] = 6
                for index in 0..<6 {
                    let value = Double(decode[index])
                    let hex = String(value.bitPattern, radix: 16)
                    bits.append("0x" + String(repeating: "0", count: 16 - hex.count) + hex)
                    guard value.isFinite else {
                        record["decode_nonfinite_index"] = index
                        throw FixtureFailure(message: "Nonfinite CGImage decode value; partial finite values/bits retained")
                    }
                    values.append(value) // Preserve the sign of zero; bits are recorded separately.
                }
            } else { record["decode_count"] = 0 }
            record["success"] = true
        } catch { record["error"] = String(describing: error) }
        record["decode_values"] = values; record["decode_value_bits"] = bits
        record["decode_values_read"] = bits.count
        record["observation_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - began
        return record
    }

    private static func export(_ output: URL) throws {
        var layouts: [String: ([String: Any], Int)] = [:]
        var requiredTotal = 0
        // Validate all layouts/budget before the first provider read.
        for entry in held {
            let image = entry.image
            let (tightRow, rowOverflow) = image.width.multipliedReportingOverflow(by: 8)
            let (required, sizeOverflow) = image.bytesPerRow.multipliedReportingOverflow(by: image.height)
            let (sum, totalOverflow) = requiredTotal.addingReportingOverflow(required)
            guard image.width > 0, image.height > 0, image.bitsPerComponent == 16,
                  image.bitsPerPixel == 64, image.bitmapInfo.rawValue == 4353,
                  image.alphaInfo.rawValue == 1, image.byteOrderInfo.rawValue == 4096,
                  image.pixelFormatInfo.rawValue == 0, image.bitmapInfo.contains(.floatComponents),
                  !rowOverflow, !sizeOverflow, !totalOverflow, image.bytesPerRow >= tightRow,
                  required > 0, sum <= maximumBytes else {
                throw FixtureFailure(message: "Unknown snapshot layout or >4MiB raw budget; no conversion/fallback")
            }
            requiredTotal = sum
            layouts[entry.key] = ([
                "key": entry.key, "width": image.width, "height": image.height,
                "bits_per_component": image.bitsPerComponent, "bits_per_pixel": image.bitsPerPixel,
                "bytes_per_row": image.bytesPerRow, "bitmap_info_raw": image.bitmapInfo.rawValue,
                "alpha_info_raw": image.alphaInfo.rawValue, "byte_order_raw": image.byteOrderInfo.rawValue,
                "pixel_format_raw": image.pixelFormatInfo.rawValue,
                "float_components": image.bitmapInfo.contains(.floatComponents),
                "retained_at_uptime_seconds": entry.retainedAt,
                "export_stage": "after_existing_window_teardown"
            ], required)
        }
        for (key, name) in names {
            guard let entry = held.first(where: { $0.key == key }),
                  let (layout, required) = layouts[key] else {
                throw FixtureFailure(message: "Missing primary image/layout; no export fallback")
            }
            let destination = output.appendingPathComponent(name)
            guard !FileManager.default.fileExists(atPath: destination.path) else {
                throw FixtureFailure(message: "Refuse to overwrite existing snapshot dump")
            }
            let began = ProcessInfo.processInfo.systemUptime
            guard let provider = entry.image.dataProvider else {
                throw FixtureFailure(message: "Original snapshot has no provider")
            }
            providerCopyCalls += 1
            guard let source = provider.data else {
                throw FixtureFailure(message: "Original snapshot provider copy failed")
            }
            let data = source as Data
            guard data.count == required else {
                throw FixtureFailure(message: "Provider length differs from rowbytes*height; no conversion/fallback")
            }
            try data.write(to: destination, options: .atomic)
            var record = layout
            record["file"] = name
            record["byte_count"] = data.count
            record["sha256"] = fixtureHash(data)
            record["provider_read_at_uptime_seconds"] = began
            record["export_elapsed_seconds"] = ProcessInfo.processInfo.systemUptime - began
            let semantics = drawingSemantics(entry.image, key: key)
            record["drawing_semantics"] = semantics
            exported.append(record) // Keep raw export and partial semantics even on rejection.
            guard semantics["success"] as? Bool == true else {
                throw FixtureFailure(message: "CGImage drawing semantics rejected: \(semantics["error"] as? String ?? "unknown")")
            }
        }
    }

    static func finish(output: URL, acquisitionSucceeded: Bool) -> [String: Any] {
        let began = ProcessInfo.processInfo.systemUptime
        var problem = observationError
        if FixtureFloatCaptureMode.selected == nil {
            problem = "Invalid BERN_HERO_FLOAT_CAPTURE; off/on required"
        } else if !acquisitionSucceeded {
            problem = "Acquisition incomplete; provider export not attempted"
        } else if primaryCount != 2 || Set(primaryKeys) != Set(names.map { $0.0 }) {
            problem = "Expected exactly two actual primary observations/keys"
        }
        if problem == nil, FixtureFloatCaptureMode.selected == .on {
            if held.count != 2 {
                problem = "Expected two original primary CGImages"
            } else {
                do { try export(output) }
                catch { problem = String(describing: error) }
            }
        }
        // Release this fixture's references on success and every failure; do not claim deallocation.
        held.removeAll()
        let releasedAt = ProcessInfo.processInfo.systemUptime
        finalizationFailed = problem != nil
        return [
            "requested": FixtureFloatCaptureMode.requested.map { $0 as Any } ?? NSNull(),
            "selected": FixtureFloatCaptureMode.selected.map { $0.rawValue as Any } ?? NSNull(),
            "primary_observation_count": primaryCount, "cleanup_observation_count": cleanupCount,
            "primary_observation_keys": primaryKeys,
            "success": problem == nil, "error": problem.map { $0 as Any } ?? NSNull(),
            "records": exported, "provider_copy_calls": providerCopyCalls,
            "retained_primary_peak_count": peakRetained,
            "fixture_retained_images_after_export": held.count,
            "primary_frozen_at_uptime_seconds": frozenAt.map { $0 as Any } ?? NSNull(),
            "released_at_uptime_seconds": releasedAt,
            "export_elapsed_seconds": releasedAt - began,
            "export_stage": "after_existing_window_teardown",
            "maximum_total_raw_bytes": maximumBytes,
            "total_raw_bytes": exported.reduce(0) { $0 + ($1["byte_count"] as? Int ?? 0) },
            "retention_scope": "on: actual renderer-return object until post-teardown export; off: no CGImage retained; cleanup: no CGImage retained",
            "row_direction": "unverified",
            "observer_effect": "Changed object lifetime/provider access requires off/on pixel controls; zero observer effect is not claimed"
        ]
    }
}
