import SwiftUI
import Foundation
struct BernRowSpacer: LayoutValueKey { static let defaultValue = false }
struct BernRow: Layout {
    var alignment: VerticalAlignment = .center
    var spacing: CGFloat? = nil
    var diagnosticID: String? = nil

    private struct Item {
        var ideal: CGFloat
        var least: CGFloat
        var most: CGFloat
        var grows: Bool
        var spacer: Bool
    }

    private func gaps(_ subviews: Subviews) -> [CGFloat] {
        guard subviews.count > 1 else { return [] }
        return (0..<(subviews.count - 1)).map { index in
            spacing ?? subviews[index].spacing.distance(to: subviews[index + 1].spacing, along: .horizontal)
        }
    }

    /// The width each item is offered.
    private func widths(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews, ledger: BernFrameRowLedgerPlacement? = nil) -> [CGFloat] {
        let items = subviews.map { subview -> Item in
            // A spacer has no least width, as on the other targets; the
            // system's own is a gap of its idiom (60 points on tvOS), which
            // took the room of the texts beside it in a narrow row.
            if subview[BernRowSpacer.self] {
                ledger?.raw(least: nil, ideal: nil, most: nil, queried: false)
                return Item(ideal: 0, least: 0, most: .infinity, grows: true, spacer: true)
            }
            let least = subview.sizeThatFits(ProposedViewSize(width: 0, height: height)).width
            let ideal = subview.sizeThatFits(ProposedViewSize(width: nil, height: height)).width
            let most = subview.sizeThatFits(ProposedViewSize(width: .infinity, height: height)).width
            ledger?.raw(least: least, ideal: ideal, most: most, queried: true)
            return Item(ideal: ideal, least: min(least, ideal), most: max(most, ideal), grows: most > ideal + 0.5, spacer: false)
        }
        ledger?.normalized(items.map { ($0.least, $0.ideal, $0.most, $0.grows, $0.spacer) })
        guard let width else { return items.map(\.ideal) }
        var offered = items.map { $0.grows ? $0.least : $0.ideal }
        let room = width - gaps(subviews).reduce(0, +)
        let used = offered.reduce(0, +)
        if !width.isFinite {
            return items.map { $0.grows ? $0.most : $0.ideal }
        }
        if used <= room {
            // What is left over goes to the items that grow, as equally as
            // their least and most widths allow.
            var open = items.indices.filter { items[$0].grows }
            var left = room - items.indices.filter { !items[$0].grows }.reduce(0) { $0 + offered[$1] }
            while !open.isEmpty {
                let share = left / CGFloat(open.count)
                if let index = open.first(where: { items[$0].least > share || items[$0].most < share }) {
                    offered[index] = items[index].least > share ? items[index].least : items[index].most
                    left -= offered[index]
                    open.removeAll { $0 == index }
                    continue
                }
                for index in open { offered[index] = share }
                break
            }
        } else {
            // Too narrow: the others shrink by their part of what is
            // missing, weighed by their width, never below their least.
            var missing = used - room
            var open = items.indices.filter { !items[$0].grows && items[$0].ideal > items[$0].least }
            while missing > 0.01, !open.isEmpty {
                let total = open.reduce(0) { $0 + items[$1].ideal }
                guard total > 0 else { break }
                if let index = open.first(where: { offered[$0] - missing * items[$0].ideal / total < items[$0].least }) {
                    missing -= offered[index] - items[index].least
                    offered[index] = items[index].least
                    open.removeAll { $0 == index }
                    continue
                }
                for index in open { offered[index] -= missing * items[index].ideal / total }
                missing = 0
            }
        }
        return offered
    }

    private func arrange(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews, ledger: BernFrameRowLedgerPlacement? = nil)
        -> (size: CGSize, widths: [CGFloat], tops: [CGFloat], extents: [CGFloat])
    {
        let offered = widths(width, height, subviews, ledger: ledger)
        let gaps = gaps(subviews)
        var above: CGFloat = 0, below: CGFloat = 0
        var extents: [CGFloat] = [], guides: [CGFloat] = []
        for (subview, offer) in zip(subviews, offered) {
            if subview[BernRowSpacer.self] {
                extents.append(offer)
                guides.append(0)
                ledger?.dimension(ordinal: extents.count - 1, queried: false, height: nil, guide: nil)
                continue
            }
            let dimensions = subview.dimensions(in: ProposedViewSize(width: offer, height: height))
            let guide = dimensions[alignment]
            above = max(above, guide)
            below = max(below, dimensions.height - guide)
            extents.append(dimensions.width)
            guides.append(guide)
            ledger?.dimension(ordinal: extents.count - 1, queried: true, height: dimensions.height, guide: guide)
        }
        let tops = zip(subviews, guides).map { subview, guide in subview[BernRowSpacer.self] ? 0 : above - guide }
        let length = extents.reduce(0, +) + gaps.reduce(0, +)
        return (CGSize(width: length, height: above + below), offered, tops, extents)
    }

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        arrange(proposal.width, proposal.height, subviews).size
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        let bernRowLedger = BernFrameRowLedger.shared.begin(id: diagnosticID, bounds: bounds, proposal: proposal, count: subviews.count)
        let layout = arrange(bounds.width, proposal.height, subviews, ledger: bernRowLedger)
        let gaps = gaps(subviews)
        var x = bounds.minX
        for index in subviews.indices {
            let spacer = subviews[index][BernRowSpacer.self]
            subviews[index].place(
                at: CGPoint(x: x, y: bounds.minY + layout.tops[index]),
                anchor: .topLeading,
                proposal: ProposedViewSize(width: layout.widths[index], height: spacer ? bounds.height : proposal.height))
            bernRowLedger?.placed(ordinal: index, x: x, spacer: spacer)
            x += layout.extents[index] + (index < gaps.count ? gaps[index] : 0)
        }
        BernFrameRowLedger.shared.finish(bernRowLedger, size: layout.size, widths: layout.widths, tops: layout.tops, extents: layout.extents, gaps: gaps, finalX: x)
    }
}

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
    private var records: [[String: Any]] = []
    private var stopped = false
    private let placementLimit = 64
    private let byteLimit = 64 * 1024
    private let reserveBytes = 512

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

    private func packet(_ placements: [[String: Any]], truncated: Bool, reason: String?) -> [String: Any] {
        var result: [String: Any] = [
            "schema": "bern_frame_row_ledger_v1", "pid": pid, "diagnostic_id": "gallery.frame.controls",
            "stage": stage ?? [:], "placement_limit": placementLimit, "file_byte_limit": byteLimit,
            "truncated": truncated, "end_state": "not_observed", "placements": placements,
            "complete_placement_count": placements.count,
            "point_scope": "arguments requested by existing Layout.place; not native frame or bezel"
        ]
        if let reason { result["truncation_reason"] = reason }
        return result
    }

    private func write(_ data: Data, initial: Bool) throws {
        guard let output else { return }
        try data.write(to: output, options: initial ? [.withoutOverwriting] : [.atomic])
    }

    private func truncate(_ reason: String) throws {
        let data = try JSONSerialization.data(withJSONObject: packet(records, truncated: true, reason: reason), options: [.sortedKeys])
        guard data.count <= byteLimit else { throw NSError(domain: "BernFrameRowLedger", code: 5) }
        try write(data, initial: records.isEmpty)
        stopped = true
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
            guard records.count < placementLimit else { try truncate("placement_limit"); return }
            let count = capture.items.count
            guard !capture.inconsistent, widths.count == count, tops.count == count, extents.count == count,
                  capture.items.allSatisfy({ $0.rawCaptured && $0.normalized != nil && $0.dimensionCaptured && $0.placed }) else {
                try truncate("incomplete_memory_capture"); return
            }
            var ordinals: [[String: Any]] = []
            for index in capture.items.indices {
                let item = capture.items[index]
                guard let normalized = item.normalized else { try truncate("missing_normalized_item"); return }
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
            let record: [String: Any] = [
                "sequence": records.count, "place_entered_uptime_seconds": capture.enteredUptime,
                "place_completed_uptime_seconds": completedUptime, "on_main_thread": Thread.isMainThread,
                "actual_subview_count": count, "ordinals": ordinals,
                "proposal": ["width": scalar(capture.proposal.width), "height": scalar(capture.proposal.height)],
                "bounds": ["x": scalar(capture.bounds.minX), "y": scalar(capture.bounds.minY), "width": scalar(capture.bounds.width), "height": scalar(capture.bounds.height)],
                "row_size": ["width": scalar(size.width), "height": scalar(size.height)],
                "gaps": gaps.map { scalar($0) }, "final_x": scalar(finalX), "anchor": "topLeading"
            ]
            let next = records + [record]
            let data = try JSONSerialization.data(withJSONObject: packet(next, truncated: false, reason: nil), options: [.sortedKeys])
            guard data.count <= byteLimit - reserveBytes else { try truncate("byte_limit"); return }
            try write(data, initial: records.isEmpty)
            records = next
        } catch {
            stopped = true
            // A failed write cannot truthfully update the previous successful file. Make the failure explicit in stderr.
            FileHandle.standardError.write(Data("BERN_FRAME_ROW_LEDGER_IO_ERROR: \(error)\n".utf8))
        }
    }
}
