
// Fixture-only, process-cached, scalar observation after PNGs/final guards.
// No contents/presentation/provider reads, layout/display, or layer/view setters.
private enum FixtureBackingMode {
    static let requested = ProcessInfo.processInfo.environment["BERN_HERO_LAYER_OBSERVE"]
    static let selected: String? = {
        guard let value = requested else { return "off" }
        return ["off", "on"].contains(value) ? value : nil
    }()
}
extension BernWindowImageHeroes {
    // Read the overlay already prepared by fixtureSnapshot; never prepare it here.
    fileprivate var fixtureExistingOverlay: NSView { overlay }
}
@MainActor private enum FixtureBackingObservation {
    static func initial() -> [String: Any] {
        ["requested": FixtureBackingMode.requested.map { $0 as Any } ?? NSNull(),
         "selected": FixtureBackingMode.selected.map { $0 as Any } ?? NSNull(),
         "stage": "post_png_post_final_guards_pre_teardown", "success": false,
         "error": NSNull(), "records": [], "root": NSNull(), "overlay": NSNull()]
    }
    private static func node(_ view: NSView) -> [String: Any] {
        // Each optional layer getter is performed once, only in selected=on.
        let wantsLayer = view.wantsLayer
        let layer = view.layer
        var layerRecord: [String: Any] = ["present": layer != nil]
        if let layer = layer {
            let delegate = layer.delegate
            layerRecord["object_id"] = String(describing: ObjectIdentifier(layer))
            layerRecord["class"] = NSStringFromClass(type(of: layer))
            layerRecord["contents_format"] = layer.contentsFormat.rawValue
            layerRecord["contents_scale"] = layer.contentsScale
            layerRecord["delegate_class"] = delegate.map { NSStringFromClass(type(of: $0)) as Any } ?? NSNull()
            layerRecord["delegate_is_view"] = (delegate as AnyObject?) === view
        }
        return ["object_id": String(describing: ObjectIdentifier(view)),
                "class": NSStringFromClass(type(of: view)),
                "window_number": view.window.map { $0.windowNumber as Any } ?? NSNull(),
                "frame": fixtureRect(view.frame), "bounds": fixtureRect(view.bounds),
                "is_flipped": view.isFlipped, "wants_layer": wantsLayer,
                "wants_update_layer": view.wantsUpdateLayer,
                "can_draw_subviews_into_layer": view.canDrawSubviewsIntoLayer,
                "layer_contents_redraw_policy": view.layerContentsRedrawPolicy.rawValue,
                "layer_contents_placement": view.layerContentsPlacement.rawValue,
                "layer": layerRecord]
    }
    private static func tree(_ view: NSView) throws -> [String: Any] {
        let first = node(view)
        var ancestors: [[String: Any]] = []
        var parent = view.superview
        var seen = Set<ObjectIdentifier>([ObjectIdentifier(view)])
        while let current = parent {
            guard ancestors.count < 16, seen.insert(ObjectIdentifier(current)).inserted else {
                throw FixtureFailure(message: "Backing observer ancestor bound/cycle; incomplete metadata")
            }
            ancestors.append(node(current)); parent = current.superview
        }
        return ["view": first, "ancestors": ancestors, "ancestor_chain_complete": true]
    }
    static func finish(_ flights: [BernHeroFlightView], root: NSView,
                       manager: BernWindowImageHeroes, window: NSWindow) throws -> [String: Any] {
        var report = initial()
        guard let mode = FixtureBackingMode.selected else {
            throw FixtureFailure(message: "Invalid BERN_HERO_LAYER_OBSERVE")
        }
        // Off does not query a new view/layer/ancestor property.
        guard mode == "on" else { report["success"] = true; return report }
        let overlay = manager.fixtureExistingOverlay
        let expectedParent = window.contentView?.superview ?? window.contentView
        guard flights.count == 2, root.window === window, overlay.window === window,
              expectedParent != nil, overlay.superview === expectedParent,
              flights.allSatisfy({ $0.window === window && $0.superview === root &&
                  $0.bounds.size == CGSize(width: 320, height: 180) }) else {
            throw FixtureFailure(message: "Backing observer expected two root flights/root/existing actual overlay in same window")
        }
        var records: [[String: Any]] = []
        for (i, flight) in flights.enumerated() {
            var record = try tree(flight)
            record["role"] = i == 0 ? "flight-named" : "flight-custom"
            record["parent_is_fixture_root"] = true
            record["rect_in_fixture_root"] = fixtureRect(flight.convert(flight.bounds, to: root))
            records.append(record)
        }
        report["records"] = records; report["root"] = try tree(root)
        report["overlay"] = try tree(overlay)
        report["overlay_parent_is_window_content_superview_or_content"] = true
        report["expected_window_number"] = window.windowNumber
        report["success"] = true
        return report
    }
}

// Fixture-only entry point, appended in this file to preserve product access control.
import MetalKit
import ImageIO
import UniformTypeIdentifiers
import CryptoKit
import Darwin

private struct FixtureFailure: Error { let message: String }
private func fixtureHash(_ data: Data) -> String {
    SHA256.hash(data: data).map { String(format: "%02x", $0) }.joined()
}
// Fixture-only observer: hold scalar descriptors and a color-space reference, never an image.
// ICC export/classification happens only after all PNGs and existing window teardown.
@MainActor private struct FixtureSnapshotCGImageDescriptor {
    let scalars: [String: Any]
    let space: CGColorSpace?
    func metadata() -> [String: Any] {
        var record = scalars
        record["color_space_metadata_stage"] = "after_existing_window_teardown"
        for field in ["color_space_name", "color_space_model_raw", "color_space_components",
                      "icc_present", "icc_byte_count", "icc_sha256", "icc_base64",
                      "icc_base64_omitted_reason", "wide_gamut_rgb",
                      "uses_extended_range", "uses_itur2100_tf", "is_pq_based", "is_hlg_based"] {
            record[field] = NSNull()
        }
        if let space {
            if let name = space.name { record["color_space_name"] = name as String }
            record["color_space_model_raw"] = space.model.rawValue
            record["color_space_components"] = space.numberOfComponents
            record["wide_gamut_rgb"] = space.isWideGamutRGB
            record["uses_extended_range"] = CGColorSpaceUsesExtendedRange(space)
            record["uses_itur2100_tf"] = CGColorSpaceUsesITUR_2100TF(space)
            record["is_pq_based"] = CGColorSpaceIsPQBased(space)
            record["is_hlg_based"] = CGColorSpaceIsHLGBased(space)
            if let profile = space.copyICCData() {
                let data = profile as Data
                record["icc_present"] = true
                record["icc_byte_count"] = data.count
                record["icc_sha256"] = fixtureHash(data)
                if data.count <= 65_536 {
                    record["icc_base64"] = data.base64EncodedString()
                } else {
                    record["icc_base64_omitted_reason"] = "profile_exceeds_65536_bytes"
                }
            } else {
                record["icc_present"] = false
                record["icc_byte_count"] = 0
                record["icc_base64_omitted_reason"] = "no_icc_profile"
            }
        }
        return record
    }
}
@MainActor private var fixtureSnapshotCGImageObservations: [FixtureSnapshotCGImageDescriptor] = []
@MainActor private func fixtureObserveSnapshotCGImage(_ image: CGImage, key: String) {
    var record: [String: Any] = [:]
    record["key"] = key
    record["observation_site"] = "snapshot_descriptors_before_NSImage_color_metadata_after_window_teardown"
    record["width"] = image.width
    record["height"] = image.height
    record["bits_per_component"] = image.bitsPerComponent
    record["bits_per_pixel"] = image.bitsPerPixel
    record["bytes_per_row"] = image.bytesPerRow
    record["bitmap_info_raw"] = image.bitmapInfo.rawValue
    record["alpha_info_raw"] = image.alphaInfo.rawValue
    record["float_components"] = image.bitmapInfo.contains(.floatComponents)
    record["byte_order_raw"] = image.byteOrderInfo.rawValue
    record["pixel_format_raw"] = image.pixelFormatInfo.rawValue
    let space = image.colorSpace
    record["color_space_present"] = space != nil
    fixtureSnapshotCGImageObservations.append(FixtureSnapshotCGImageDescriptor(scalars: record, space: space))
    FixtureSnapshotFloatCapture.observe(image, key: key)
}
private func fixtureRect(_ r: CGRect) -> [String: Double] {
    ["x": r.minX, "y": r.minY, "width": r.width, "height": r.height]
}
private func fixtureSavePNG(_ image: CGImage, _ url: URL) throws {
    guard let d = CGImageDestinationCreateWithURL(url as CFURL, UTType.png.identifier as CFString, 1, nil) else {
        throw FixtureFailure(message: "PNG destination unavailable")
    }
    CGImageDestinationAddImage(d, image, nil)
    guard CGImageDestinationFinalize(d) else { throw FixtureFailure(message: "PNG finalize failed") }
}
@MainActor private func fixtureLedger(_ urls: [URL]) throws -> [String: Any] {
    var result: [String: Any] = [:]
    for url in urls {
        guard let p = BernPictures.shared.cached(url.absoluteString),
              let bytes = p.image.dataProvider?.data, let icc = p.image.colorSpace?.copyICCData() else {
            throw FixtureFailure(message: "Product cache/provider/ICC missing")
        }
        let d = p.legacyStandardPQImage
        var item: [String: Any] = [:]
        item["image_id"] = String(describing: ObjectIdentifier(p.image))
        item["original_provider_sha256"] = fixtureHash(bytes as Data)
        item["original_icc_sha256"] = fixtureHash(icc as Data)
        item["file_sha256"] = fixtureHash(try Data(contentsOf: url))
        item["orientation"] = String(describing: p.orientation); item["ratio"] = p.ratio
        item["original_size"] = [p.image.width, p.image.height]
        item["original_bitmap_info"] = p.image.bitmapInfo.rawValue
        item["original_alpha_info"] = p.image.alphaInfo.rawValue
        item["original_space_name"] = p.image.colorSpace?.name as String? ?? "unnamed"
        item["original_uses_2100_tf"] = p.image.colorSpace.map { CGColorSpaceUsesITUR_2100TF($0) } ?? false
        item["legacy_hdr_space_name"] = p.legacyHDRColorSpace?.name as String? ?? "nil"
        item["derived_is_pq_based"] = d?.colorSpace.map { CGColorSpaceIsPQBased($0) } ?? false
        item["cached_average_rgb"] = BernPictures.shared.averages[url.absoluteString].map { $0 as Any } ?? NSNull()
        item["derived_id"] = d.map { String(describing: ObjectIdentifier($0)) } ?? "nil"
        item["derived_provider_sha256"] = d?.dataProvider?.data.map { fixtureHash($0 as Data) } ?? "nil"
        item["derived_icc_sha256"] = d?.colorSpace?.copyICCData().map { fixtureHash($0 as Data) } ?? "nil"
        result[url.lastPathComponent] = item
    }
    return result
}
private final class FixtureWindow: NSWindow {
    override var canBecomeKey: Bool { false }
    override var canBecomeMain: Bool { false }
}
private final class FixtureRoot: NSView {
    override var isFlipped: Bool { true }
    override var isOpaque: Bool { true }
    override func draw(_ dirtyRect: NSRect) { NSColor.white.setFill(); dirtyRect.fill() }
}
extension BernWindowImageHeroes {
    fileprivate func fixtureSnapshot(_ anchor: BernPictureHeroAnchor) -> BernHeroPicture? {
        guard prepareOverlay() else { return nil }
        return anchor.snapshot(in: overlay)
    }
    fileprivate var fixtureState: [String: Any] {
        ["entries": entries.mapValues { $0.compactMap { $0.anchor?.key } },
         "flight_count": flights.count, "timer_exists": timer != nil,
         "overlay_frame": fixtureRect(overlay.frame), "overlay_bounds": fixtureRect(overlay.bounds),
         "overlay_attached": overlay.window != nil]
    }
}
@MainActor private func fixtureDescendants(_ view: NSView) -> [NSView] {
    [view] + view.subviews.flatMap { fixtureDescendants($0) }
}
@MainActor private func fixtureMount<V: View>(_ content: V, _ frame: CGRect, _ root: NSView) -> NSView {
    let host = NSHostingView(rootView: content.environment(\.colorScheme, .light))
    host.frame = frame
    root.addSubview(host)
    return host
}
@MainActor private func fixtureImageMetadata(_ p: BernHeroPicture) -> [String: Any] {
    ["rect_in_actual_overlay": fixtureRect(p.rect), "corner": p.corner,
     "nsimage_size": [p.image.size.width, p.image.size.height],
     "representations": p.image.representations.map {
        ["class": NSStringFromClass(type(of: $0)), "pixels_wide": $0.pixelsWide,
         "pixels_high": $0.pixelsHigh, "bits_per_sample": $0.bitsPerSample,
         "has_alpha": $0.hasAlpha, "color_space_name": $0.colorSpaceName.rawValue] as [String: Any]
     },
     "readback_policy": "Public NSImageRep metadata only; no CGImage/TIFF/bitmap recache conversion"]
}
@main private enum HeroBaselineMain {
    @MainActor static func main() {
        let status = run()
        exit(status == 0 && FixtureSnapshotFloatCapture.finalizationFailed ? 1 : status)
    }
    @MainActor private static func run() -> Int32 {
        guard CommandLine.arguments.count == 4 else { return 2 }
        let urls = CommandLine.arguments[1...2].map { URL(fileURLWithPath: $0) }
        let output = URL(fileURLWithPath: CommandLine.arguments[3], isDirectory: true)
        let expectedOS = Int(ProcessInfo.processInfo.environment["BERN_HERO_EXPECT_OS"] ?? "13") ?? -1
        let actualOS = ProcessInfo.processInfo.operatingSystemVersion.majorVersion
        let front = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
        var window: NSWindow?, root: FixtureRoot?, began: Date?, watchdog: DispatchSourceTimer?
        var samples: [[String: Any]] = [], captures: [[String: Any]] = []
        var report: [String: Any] = [
            "success": false, "product_head": "b08db54e01ac2ec54fb84e6f2a70041f1f4c3604",
            "expected_os_major": expectedOS, "actual_os_major": actualOS,
            "scope": "Actual BernImage(hero: unique nonnil keys) body/modifier/anchor/manager/snapshot; actual BernHeroFlightView.draw at fixed progress0/1, same opaque image at both endpoints. Static endpoints only, no actual coordinated flight or lifecycle acceptance.",
            "activation_calls": 0, "collection_seconds": 7.2, "watchdog_seconds": 7.9,
            "image_equality_collection_gate": false,
            "snapshot_cgimage_metadata": "Fixture-only public CGImage scalar descriptors and color-space reference at the actual renderer.cgImage result; classification/ICC hash/bounded profile serialization only after all PNG captures and original window teardown. The v2 metadata observer retains no image; separate opt-in raw capture lifetime/provider reads are reported in snapshot_float_capture. No NSImage recache, conversion or relabel. Not a zero-observer-effect claim."
        ]
        report["backing_observation"] = FixtureBackingObservation.initial()
        defer {
            FixtureSnapshotFloatCapture.freezePrimary()
            let observationsBeforeCleanup = fixtureSnapshotCGImageObservations
            report["snapshot_cgimage_observations_scope"] = "before_existing_window_teardown"
            report["normal_after"] = ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            if let r = root { report["metal_count_before_cleanup"] = fixtureDescendants(r).filter { $0 is MTKView }.count }
            window?.orderOut(nil); window?.contentView = nil; window?.close(); watchdog?.cancel()
            if let began { report["window_seconds"] = Date().timeIntervalSince(began) }
            report["snapshot_cgimage_observations"] = observationsBeforeCleanup.map { $0.metadata() }
            report["snapshot_cgimage_cleanup_observations"] = fixtureSnapshotCGImageObservations.dropFirst(observationsBeforeCleanup.count).map { $0.metadata() }
            report["samples"] = samples; report["captures"] = captures
            report["frontmost_before"] = front
            report["frontmost_after"] = NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString
            let floatCapture = FixtureSnapshotFloatCapture.finish(output: output, acquisitionSucceeded: report["success"] as? Bool == true)
            report["snapshot_float_capture"] = floatCapture
            if floatCapture["success"] as? Bool != true {
                report["success"] = false
                if report["error"] == nil { report["error"] = floatCapture["error"] }
            }
            try? JSONSerialization.data(withJSONObject: report, options: [.prettyPrinted, .sortedKeys])
                .write(to: output.appendingPathComponent("report.json"))
        }
        do {
            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)
            guard FixtureBackingMode.selected != nil else {
                throw FixtureFailure(message: "Invalid BERN_HERO_LAYER_OBSERVE; off/on required before window creation")
            }
            guard FixtureFloatCaptureMode.selected != nil else {
                throw FixtureFailure(message: "Invalid BERN_HERO_FLOAT_CAPTURE; off/on required before window creation")
            }
            guard (expectedOS == 13 || expectedOS == 14), actualOS == expectedOS, CGPreflightScreenCaptureAccess() else {
                throw FixtureFailure(message: "Expected13/14 and existing screen permission required; no prompt")
            }
            func normal() -> [String: Bool] {
                ["reduce_motion": NSWorkspace.shared.accessibilityDisplayShouldReduceMotion,
                 "reduce_transparency": NSWorkspace.shared.accessibilityDisplayShouldReduceTransparency,
                 "increase_contrast": NSWorkspace.shared.accessibilityDisplayShouldIncreaseContrast]
            }
            report["normal_before"] = normal()
            guard normal().values.allSatisfy({ !$0 }) else { throw FixtureFailure(message: "Normal flags required") }
            let app = NSApplication.shared
            app.setActivationPolicy(.accessory); app.appearance = NSAppearance(named: .aqua); app.finishLaunching()
            var loaded = false, loadOK = false
            Task { @MainActor in
                let a = await BernPictures.shared.load(urls[0].absoluteString)
                let b = await BernPictures.shared.load(urls[1].absoluteString)
                loadOK = a != nil && b != nil; loaded = true
            }
            let preloadDeadline = Date(timeIntervalSinceNow: 10)
            while !loaded && Date() < preloadDeadline { RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.02)) }
            guard loaded, loadOK, let named = BernPictures.shared.cached(urls[0].absoluteString) else {
                throw FixtureFailure(message: "Actual cache preload failed")
            }
            let before = try fixtureLedger(urls); report["cache_before"] = before
            let r = FixtureRoot(frame: CGRect(x: 0, y: 0, width: 1024, height: 440)); root = r
            let topY: CGFloat = 24, bottomY: CGFloat = 244
            let xs: [CGFloat] = [16, 352, 688]
            var regions: [String: NSView] = [:]
            for (i, name) in ["body-named", "body-custom"].enumerated() {
                let v = BernImage(url: urls[i].absoluteString, label: nil, width: 320, height: 180,
                                  fit: .fill, rendering: .original, dynamicRange: .standard,
                                  hero: "baseline-\(name)")
                regions[name] = fixtureMount(v, CGRect(x: xs[i], y: topY, width: 320, height: 180), r)
            }
            func oracle(_ y: CGFloat) -> NSView {
                fixtureMount(Image(decorative: named.image, scale: 1).renderingMode(.original)
                    .resizable().frame(width: 320, height: 180),
                    CGRect(x: xs[2], y: y, width: 320, height: 180), r)
            }
            regions["oracle-top"] = oracle(topY); regions["oracle-bottom"] = oracle(bottomY)
            for (i, title) in ["Actual named PQ", "Actual custom cICP PQ", "Native named PQ oracle"].enumerated() {
                for y: CGFloat in [2, 222] {
                    let label = NSTextField(labelWithString: title)
                    label.font = .systemFont(ofSize: 12); label.textColor = .black
                    label.frame = CGRect(x: xs[i], y: y, width: 320, height: 18); r.addSubview(label)
                }
            }
            let w = FixtureWindow(contentRect: CGRect(x: 100, y: 100, width: 1024, height: 440),
                                  styleMask: [.titled], backing: .buffered, defer: false)
            window = w; w.isReleasedWhenClosed = false; w.isRestorable = false
            w.title = "Bern actual PQ hero baseline"; w.contentView = r
            let timer = DispatchSource.makeTimerSource(queue: .global(qos: .userInitiated)); watchdog = timer
            timer.setEventHandler {
                try? Data("Own hero fixture7.9second watchdog; incomplete evidence.\n".utf8)
                    .write(to: output.appendingPathComponent("hard-deadline.txt"))
                _exit(124)
            }
            began = Date(); timer.schedule(deadline: .now() + 7.9); timer.resume(); w.orderFrontRegardless()
            let initialFrame = w.frame, deadline = Date(timeIntervalSinceNow: 7.2)
            let manager = BernWindowImageHeroes.forWindow(w)
            var flights: [BernHeroFlightView] = [], phase = 0, identical = 0, previousHash = ""
            var phaseBegan = Date(), snapshotTaken = false
            while Date() < deadline && phase < 2 {
                r.layoutSubtreeIfNeeded(); r.displayIfNeeded()
                RunLoop.main.run(until: Date(timeIntervalSinceNow: 0.08))
                let views = fixtureDescendants(r), anchors = views.compactMap { $0 as? BernPictureHeroAnchor }
                let metal = views.filter { $0 is MTKView }.count
                let infos = CGWindowListCopyWindowInfo(.optionIncludingWindow, CGWindowID(w.windowNumber)) as? [[String: Any]] ?? []
                guard let info = infos.first, info[kCGWindowOwnerPID as String] as? pid_t == getpid(),
                      info[kCGWindowNumber as String] as? Int == w.windowNumber,
                      info[kCGWindowIsOnscreen as String] as? Bool == true,
                      w.isVisible, !w.isKeyWindow, !app.isActive, w.frame == initialFrame,
                      NSWorkspace.shared.frontmostApplication?.processIdentifier == front, metal == 0 else {
                    throw FixtureFailure(message: "Own window/foreground/fixed-frame/no-Metal contract failed")
                }
                guard anchors.count == 2, anchors.allSatisfy({ $0.attached && $0.window === w && $0.bounds.size == CGSize(width: 320, height: 180) }) else { continue }
                if !snapshotTaken {
                    var anchorInfo: [[String: Any]] = []
                    for (i, name) in ["body-named", "body-custom"].enumerated() {
                        guard let a = anchors.first(where: { $0.key == "baseline-\(name)" }),
                              let p = manager.fixtureSnapshot(a) else { throw FixtureFailure(message: "Actual anchor snapshot failed") }
                        var metadata = fixtureImageMetadata(p)
                        metadata["key"] = a.key; metadata["attached"] = a.attached
                        metadata["anchor_frame_in_root"] = fixtureRect(a.convert(a.bounds, to: r))
                        metadata["anchor_bounds"] = fixtureRect(a.bounds); metadata["captures_view"] = a.capturesView
                        anchorInfo.append(metadata)
                        let f = BernHeroFlightView(from: p.image, to: p.image)
                        f.corner = p.corner; f.frame = CGRect(x: xs[i], y: bottomY, width: 320, height: 180)
                        r.addSubview(f); flights.append(f); regions[i == 0 ? "flight-named" : "flight-custom"] = f
                    }
                    report["snapshots"] = anchorInfo; snapshotTaken = true; phaseBegan = Date(); continue
                }
                guard (manager.fixtureState["flight_count"] as? Int) == 0,
                      (manager.fixtureState["timer_exists"] as? Bool) == false else {
                    throw FixtureFailure(message: "Unique keys unexpectedly started coordinator flight")
                }
                guard Date().timeIntervalSince(phaseBegan) >= 0.24 else { continue }
                guard let screen = w.screen,
                      let shot = CGWindowListCreateImage(.null, .optionIncludingWindow, CGWindowID(w.windowNumber), .boundsIgnoreFraming),
                      let buffer = shot.dataProvider?.data else { throw FixtureFailure(message: "Own raw window capture unavailable") }
                let rawHash = fixtureHash(buffer as Data)
                identical = rawHash == previousHash ? identical + 1 : 1; previousHash = rawHash
                var rois: [String: Any] = [:]
                for (name, view) in regions {
                    let f = view.convert(view.bounds, to: r)
                    guard f.width == 320, f.height == 180 else { throw FixtureFailure(message: "Public image frame changed") }
                    let win = r.convert(f, to: nil)
                    let top = CGRect(x: win.minX, y: w.frame.height - win.maxY, width: win.width, height: win.height)
                    let pixels = CGRect(x: top.minX * CGFloat(shot.width) / w.frame.width,
                                        y: top.minY * CGFloat(shot.height) / w.frame.height,
                                        width: top.width * CGFloat(shot.width) / w.frame.width,
                                        height: top.height * CGFloat(shot.height) / w.frame.height)
                    rois[name] = ["host_top_left_points": fixtureRect(f), "screenshot_pixels": fixtureRect(pixels)]
                }
                let sample: [String: Any] = [
                    "phase": "progress-\(phase)", "elapsed_seconds": Date().timeIntervalSince(began!),
                    "raw_buffer_sha256": rawHash, "consecutive_equal_buffers": identical,
                    "window_id": w.windowNumber, "owner_pid": getpid(), "window_bounds": info[kCGWindowBounds as String] ?? NSNull(),
                    "window_frame": fixtureRect(w.frame), "root_bounds": fixtureRect(r.bounds),
                    "capture_size": [shot.width, shot.height], "rois": rois,
                    "capture_space_name": shot.colorSpace?.name as String? ?? "unnamed",
                    "capture_icc_sha256": shot.colorSpace?.copyICCData().map { fixtureHash($0 as Data) } ?? "absent",
                    "current_headroom": screen.maximumExtendedDynamicRangeColorComponentValue,
                    "potential_headroom": screen.maximumPotentialExtendedDynamicRangeColorComponentValue,
                    "live_metal_count": metal, "manager": manager.fixtureState,
                    "key": w.isKeyWindow, "active": app.isActive,
                    "frontmost_pid": NSWorkspace.shared.frontmostApplication?.processIdentifier ?? 0
                ]
                samples.append(sample)
                if identical >= 5 {
                    let filename = "progress-\(phase).png", url = output.appendingPathComponent(filename)
                    try fixtureSavePNG(shot, url)
                    var capture = sample; capture["png"] = filename
                    capture["png_sha256"] = fixtureHash(try Data(contentsOf: url)); captures.append(capture)
                    phase += 1; identical = 0; previousHash = ""; phaseBegan = Date()
                    for f in flights { f.progress = CGFloat(phase); f.needsDisplay = true }
                }
            }
            report["completed_phases"] = phase
            guard phase == 2 else { throw FixtureFailure(message: "Collection deadline; incomplete endpoints") }
            let after = try fixtureLedger(urls); report["cache_after"] = after
            let unchanged = NSDictionary(dictionary: after).isEqual(to: before); report["cache_unchanged"] = unchanged
            report["normal_after"] = normal()
            guard unchanged, normal().values.allSatisfy({ !$0 }),
                  NSWorkspace.shared.frontmostApplication?.processIdentifier == front else {
                throw FixtureFailure(message: "Cache/normal/foreground final contract failed")
            }
            report["backing_observation"] = try FixtureBackingObservation.finish(flights, root: r, manager: manager, window: w)
            report["success"] = true; return 0
        } catch {
            var backing = report["backing_observation"] as? [String: Any] ?? FixtureBackingObservation.initial()
            if backing["success"] as? Bool != true { backing["error"] = String(describing: error) }
            report["backing_observation"] = backing
            report["error"] = String(describing: error)
            FileHandle.standardError.write(Data("Hero baseline incomplete: \(error)\n".utf8)); return 1
        }
    }
}
