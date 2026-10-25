import Foundation

// Diagnostic storage only. No Observable state, UI mutation, or layout query.
private final class BernFrameRowLedgerPlacement {
    struct Item {
        var rawCaptured = false
        var rawLeast: CGFloat? = nil
        var rawIdeal: CGFloat? = nil
        var rawMost: CGFloat? = nil
        var rawQueried = false
        var normalized: (CGFloat, CGFloat, CGFloat, Bool, Bool)? = nil
        var dimensionCaptured = false
        var dimensionQueried = false
        var dimensionHeight: CGFloat? = nil
        var guide: CGFloat? = nil
        var placed = false
        var placedX: CGFloat? = nil
        var placeSpacer = false
    }
    let bounds: CGRect
    let proposal: ProposedViewSize
    let enteredUptime = ProcessInfo.processInfo.systemUptime
    var items: [Item]
    private var nextRaw = 0
    var inconsistent = false

    init(bounds: CGRect, proposal: ProposedViewSize, count: Int) {
        self.bounds = bounds
        self.proposal = proposal
        self.items = Array(repeating: Item(), count: count)
    }

    func raw(least: CGFloat?, ideal: CGFloat?, most: CGFloat?, queried: Bool) {
        guard items.indices.contains(nextRaw) else { inconsistent = true; return }
        items[nextRaw].rawCaptured = true
        items[nextRaw].rawLeast = least
        items[nextRaw].rawIdeal = ideal
        items[nextRaw].rawMost = most
        items[nextRaw].rawQueried = queried
        nextRaw += 1
    }

    func normalized(_ values: [(CGFloat, CGFloat, CGFloat, Bool, Bool)]) {
        guard values.count == items.count else { inconsistent = true; return }
        for index in items.indices { items[index].normalized = values[index] }
    }

    func dimension(ordinal: Int, queried: Bool, height: CGFloat?, guide: CGFloat?) {
        guard items.indices.contains(ordinal) else { inconsistent = true; return }
        items[ordinal].dimensionCaptured = true
        items[ordinal].dimensionQueried = queried
        items[ordinal].dimensionHeight = height
        items[ordinal].guide = guide
    }

    func placed(ordinal: Int, x: CGFloat, spacer: Bool) {
        guard items.indices.contains(ordinal) else { inconsistent = true; return }
        items[ordinal].placed = true
        items[ordinal].placedX = x
        items[ordinal].placeSpacer = spacer
    }
}

private final class BernFrameRowLedger: @unchecked Sendable {
    static let shared = BernFrameRowLedger()
    private let lock = NSLock()
    private let path: String?
    private let pid = ProcessInfo.processInfo.processIdentifier
    private var stage: [String: Any]? = nil
    private var output: URL? = nil
    private var latest: [String: Any]? = nil
    private var observedCompleteCount: Int64 = 0
    private var stopped = false
    private let byteLimit = 64 * 1024

    private init() {
        let value = ProcessInfo.processInfo.environment["BERN_FRAME_ROW_LEDGER_OUTPUT_DIR"]
        path = value.flatMap { $0.hasPrefix("/") && !$0.isEmpty ? $0 : nil }
    }

    func begin(id: String?, bounds: CGRect, proposal: ProposedViewSize, count: Int) -> BernFrameRowLedgerPlacement? {
        // Environment inspection and memory only. No filesystem calls before original place completes.
        guard id == "gallery.frame.controls", path != nil else { return nil }
        return BernFrameRowLedgerPlacement(bounds: bounds, proposal: proposal, count: count)
    }

    private func scalar(_ value: CGFloat?) -> Any {
        guard let value else { return ["kind": "nil"] }
        let number = Double(value)
        if number.isFinite { return number }
        let kind = number.isNaN ? "nan" : (number.sign == .minus ? "negative_infinity" : "positive_infinity")
        return ["kind": kind, "bits": String(format: "%016llx", number.bitPattern)]
    }

    private func armAfterPlace() throws -> Bool {
        if stage != nil { return true }
        guard let path else { return false }
        let folder = URL(fileURLWithPath: path, isDirectory: true).standardizedFileURL
        var directory: ObjCBool = false
        guard folder.resolvingSymlinksInPath() == folder,
              FileManager.default.fileExists(atPath: folder.path, isDirectory: &directory), directory.boolValue else {
            throw NSError(domain: "BernFrameRowLedger", code: 1, userInfo: [NSLocalizedDescriptionKey: "output must be existing absolute nonsymlink directory"])
        }
        let arm = folder.appendingPathComponent("frame-row-ledger.arm.json")
        guard FileManager.default.fileExists(atPath: arm.path) else { return false }
        let attributes = try FileManager.default.attributesOfItem(atPath: arm.path)
        guard attributes[.type] as? FileAttributeType == .typeRegular,
              ((attributes[.size] as? NSNumber)?.intValue ?? Int.max) <= 4096 else {
            throw NSError(domain: "BernFrameRowLedger", code: 2, userInfo: [NSLocalizedDescriptionKey: "arm must be regular and at most 4096 bytes"])
        }
        let data = try Data(contentsOf: arm)
        guard let armRecord = try JSONSerialization.jsonObject(with: data) as? [String: Any],
              armRecord["schema"] as? String == "bern_frame_row_arm_v1",
              (armRecord["pid"] as? NSNumber)?.int32Value == pid,
              armRecord["stage"] as? String == "frame-closed-light",
              let token = armRecord["token"] as? String, !token.isEmpty, token.utf8.count <= 128 else {
            throw NSError(domain: "BernFrameRowLedger", code: 3, userInfo: [NSLocalizedDescriptionKey: "invalid stage arm identity"])
        }
        let file = folder.appendingPathComponent("frame-row-ledger-\(pid).json")
        guard !FileManager.default.fileExists(atPath: file.path) else {
            throw NSError(domain: "BernFrameRowLedger", code: 4, userInfo: [NSLocalizedDescriptionKey: "existing ledger refused"])
        }
        stage = ["schema": "bern_frame_row_arm_v1", "pid": pid, "stage": "frame-closed-light", "token": token]
        output = file
        return true
    }

    private func packet(_ record: [String: Any], observed: Int64) -> [String: Any] {
        [
            "schema": "bern_frame_row_latest_v2", "pid": pid, "diagnostic_id": "gallery.frame.controls",
            "stage": stage ?? [:], "retention": "latest1", "retained_limit": 1, "file_byte_limit": byteLimit,
            "end_state": "not_observed", "observed_complete_count": observed,
            "replaced_complete_count": observed - 1, "retained_complete_count": 1, "latest": record,
            "point_scope": "arguments requested by existing Layout.place; not native frame or bezel"
        ]
    }

    private func write(_ data: Data, initial: Bool) throws {
        guard let output else { throw failure("output_not_bound") }
        if initial && FileManager.default.fileExists(atPath: output.path) { throw failure("existing_latest_slot_refused") }
        try data.write(to: output, options: [.atomic])
    }

    private func failure(_ reason: String) -> NSError {
        NSError(domain: "BernFrameRowLedger", code: 5, userInfo: [NSLocalizedDescriptionKey: reason])
    }

    func finish(_ capture: BernFrameRowLedgerPlacement?, size: CGSize, widths: [CGFloat], tops: [CGFloat],
                extents: [CGFloat], gaps: [CGFloat], finalX: CGFloat) {
        // Called only after every original place call AND the original final x advance.
        guard let capture else { return }
        let completedUptime = ProcessInfo.processInfo.systemUptime
        lock.lock(); defer { lock.unlock() }
        guard !stopped else { return }
        do {
            guard try armAfterPlace() else { return }
            let count = capture.items.count
            guard !capture.inconsistent, widths.count == count, tops.count == count, extents.count == count,
                  capture.items.allSatisfy({ $0.rawCaptured && $0.normalized != nil && $0.dimensionCaptured && $0.placed }) else {
                throw failure("incomplete_memory_capture")
            }
            var ordinals: [[String: Any]] = []
            for index in capture.items.indices {
                let item = capture.items[index]
                guard let normalized = item.normalized else { throw failure("missing_normalized_item") }
                ordinals.append([
                    "ordinal": index,
                    "raw_queries_performed": item.rawQueried,
                    "raw_least": scalar(item.rawLeast), "raw_ideal": scalar(item.rawIdeal), "raw_most": scalar(item.rawMost),
                    "least": scalar(normalized.0), "ideal": scalar(normalized.1), "most": scalar(normalized.2),
                    "grows": normalized.3, "widths_spacer": normalized.4,
                    "offered": scalar(widths[index]), "extent": scalar(extents[index]), "top": scalar(tops[index]),
                    "dimensions_queried": item.dimensionQueried, "dimension_height": scalar(item.dimensionHeight), "guide": scalar(item.guide),
                    "point": ["x": scalar(item.placedX), "y": scalar(capture.bounds.minY + tops[index])],
                    "place_spacer": item.placeSpacer,
                    "place_proposal": ["width": scalar(widths[index]), "height": scalar(item.placeSpacer ? capture.bounds.height : capture.proposal.height)]
                ])
            }
            let (nextObserved, overflow) = observedCompleteCount.addingReportingOverflow(1)
            guard !overflow, nextObserved > 0 else { throw failure("observed_complete_count_overflow") }
            observedCompleteCount = nextObserved
            let record: [String: Any] = [
                "sequence": observedCompleteCount - 1, "place_entered_uptime_seconds": capture.enteredUptime,
                "place_completed_uptime_seconds": completedUptime, "on_main_thread": Thread.isMainThread,
                "actual_subview_count": count, "ordinals": ordinals,
                "proposal": ["width": scalar(capture.proposal.width), "height": scalar(capture.proposal.height)],
                "bounds": ["x": scalar(capture.bounds.minX), "y": scalar(capture.bounds.minY), "width": scalar(capture.bounds.width), "height": scalar(capture.bounds.height)],
                "row_size": ["width": scalar(size.width), "height": scalar(size.height)],
                "gaps": gaps.map { scalar($0) }, "final_x": scalar(finalX), "anchor": "topLeading"
            ]
            let data = try JSONSerialization.data(withJSONObject: packet(record, observed: observedCompleteCount), options: [.sortedKeys])
            guard data.count <= byteLimit else { throw failure("single_complete_placement_byte_limit") }
            try write(data, initial: latest == nil)
            latest = record
        } catch {
            stopped = true
            // A failed write cannot truthfully update the previous successful file. Make the failure explicit in stderr.
            FileHandle.standardError.write(Data("BERN_FRAME_ROW_LEDGER_IO_ERROR: \(error)\n".utf8))
        }
    }
}
