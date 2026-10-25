#!/usr/bin/env python3
"""Patch exact e48 generated Frame Row after generation, before product target.plan."""
import difflib
import hashlib
import json
import sys
from pathlib import Path

STYLE_SHA = "3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89"
STYLE_BYTES = 210785
GENERATED_SHA = "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653"
GENERATED_BYTES = 81110
HELPER_SHA = "680fbf705238a12c734d9b7c21a33b4911f077f16ae8fd7146d19a31d827bdbf"
ROW_START = b"struct BernRow: Layout {\n"
ROW_END = b"\nstruct BernFlow: Layout {"
FRAME_START = b"/// Generated from the `frame` component.\n"
FRAME_END = b"/// Generated from the `card` component.\n"
FRAME_CALL = b"                        BernRow(alignment: .center, spacing: 12.0) {\n"
FRAME_TAGGED = b"                        BernRow(alignment: .center, spacing: 12.0, diagnosticID: \"gallery.frame.controls\") {\n"
DELIMITER = b"\n// Diagnostic Frame Row ledger; original layout queries and arithmetic retained.\n"

# Exact single-row substitutions. No Rust/product generator code is touched here.
EDITS = [
    (b"    var spacing: CGFloat? = nil\n", b"    var spacing: CGFloat? = nil\n    var diagnosticID: String? = nil\n"),
    (b"    private func widths(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews) -> [CGFloat] {\n",
     b"    private func widths(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews, ledger: BernFrameRowLedgerPlacement? = nil) -> [CGFloat] {\n"),
    (b"                return Item(ideal: 0, least: 0, most: .infinity, grows: true, spacer: true)\n",
     b"                ledger?.raw(least: nil, ideal: nil, most: nil, queried: false)\n                return Item(ideal: 0, least: 0, most: .infinity, grows: true, spacer: true)\n"),
    (b"            return Item(ideal: ideal, least: min(least, ideal), most: max(most, ideal), grows: most > ideal + 0.5, spacer: false)\n",
     b"            ledger?.raw(least: least, ideal: ideal, most: most, queried: true)\n            return Item(ideal: ideal, least: min(least, ideal), most: max(most, ideal), grows: most > ideal + 0.5, spacer: false)\n"),
    (b"        guard let width else { return items.map(\\.ideal) }\n",
     b"        ledger?.normalized(items.map { ($0.least, $0.ideal, $0.most, $0.grows, $0.spacer) })\n        guard let width else { return items.map(\\.ideal) }\n"),
    (b"    private func arrange(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews)\n",
     b"    private func arrange(_ width: CGFloat?, _ height: CGFloat?, _ subviews: Subviews, ledger: BernFrameRowLedgerPlacement? = nil)\n"),
    (b"        let offered = widths(width, height, subviews)\n",
     b"        let offered = widths(width, height, subviews, ledger: ledger)\n"),
    (b"                guides.append(0)\n                continue\n",
     b"                guides.append(0)\n                ledger?.dimension(ordinal: extents.count - 1, queried: false, height: nil, guide: nil)\n                continue\n"),
    (b"            guides.append(guide)\n",
     b"            guides.append(guide)\n            ledger?.dimension(ordinal: extents.count - 1, queried: true, height: dimensions.height, guide: guide)\n"),
    (b"        let layout = arrange(bounds.width, proposal.height, subviews)\n",
     b"        let bernRowLedger = BernFrameRowLedger.shared.begin(id: diagnosticID, bounds: bounds, proposal: proposal, count: subviews.count)\n        let layout = arrange(bounds.width, proposal.height, subviews, ledger: bernRowLedger)\n"),
    (b"            x += layout.extents[index] + (index < gaps.count ? gaps[index] : 0)\n",
     b"            bernRowLedger?.placed(ordinal: index, x: x, spacer: spacer)\n            x += layout.extents[index] + (index < gaps.count ? gaps[index] : 0)\n"),
    (b"        }\n    }\n}\n",
     b"        }\n        BernFrameRowLedger.shared.finish(bernRowLedger, size: layout.size, widths: layout.widths, tops: layout.tops, extents: layout.extents, gaps: gaps, finalX: x)\n    }\n}\n"),
]


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def candidate(style, generated, helper):
    require(len(style) == STYLE_BYTES and sha(style) == STYLE_SHA, "exact e48 Style required")
    require(len(generated) == GENERATED_BYTES and sha(generated) == GENERATED_SHA, "exact actual e48 Gallery generated source required")
    require(sha(helper) == HELPER_SHA, "frozen RowLedger helper required")
    require(style.count(ROW_START) == 1 and style.count(ROW_END) == 1, "BernRow boundary must locate once")
    start = style.index(ROW_START)
    end = style.index(ROW_END, start)
    original_row = style[start:end]
    changed_row = original_row
    for index, (before, after) in enumerate(EDITS):
        require(changed_row.count(before) == 1, "row anchor must locate once: " + str(index))
        changed_row = changed_row.replace(before, after, 1)
    restored = changed_row
    for before, after in reversed(EDITS):
        require(restored.count(after) == 1, "reverse row anchor must locate once")
        restored = restored.replace(after, before, 1)
    require(restored == original_row, "row insertion removal must restore original bytes")
    for query in [b"subview.sizeThatFits(", b"subview.dimensions(in:", b"subviews[index].place("]:
        require(changed_row.count(query) == original_row.count(query), "layout measurement/place call count changed")
    for statement in [b"let least = subview.sizeThatFits", b"let ideal = subview.sizeThatFits", b"let most = subview.sizeThatFits",
                      b"let dimensions = subview.dimensions", b"subviews[index].place(", b"x += layout.extents[index]"]:
        require(changed_row.count(statement) == original_row.count(statement), "original queried statement changed")
    require(generated.count(FRAME_START) == 1 and generated.count(FRAME_END) == 1, "actual Frame boundary must locate once")
    frame_start = generated.index(FRAME_START)
    frame_end = generated.index(FRAME_END, frame_start)
    frame = generated[frame_start:frame_end]
    require(frame.count(FRAME_CALL) == 1, "actual Frame Row call must locate once")
    tagged_frame = frame.replace(FRAME_CALL, FRAME_TAGGED, 1)
    changed_generated = generated[:frame_start] + tagged_frame + generated[frame_end:]
    require(changed_generated.replace(FRAME_TAGGED, FRAME_CALL, 1) == generated, "removing one Frame tag must restore actual source")
    changed_style = style[:start] + changed_row + style[end:] + DELIMITER + helper
    restored_style = changed_style[:-len(DELIMITER + helper)].replace(changed_row, original_row, 1)
    require(restored_style == style, "removing ledger edits/helper must restore exact original Style")
    proof = {
        "source_sha": "e48fff46b3a92a28465ad74295bd273a9d69af7d",
        "style": {"before_bytes": len(style), "before_sha256": sha(style), "after_bytes": len(changed_style), "after_sha256": sha(changed_style)},
        "generated": {"before_bytes": len(generated), "before_sha256": sha(generated), "after_bytes": len(changed_generated), "after_sha256": sha(changed_generated)},
        "helper": {"path": "RowLedger.swift", "bytes": len(helper), "sha256": sha(helper)},
        "scope": "one Frame BernRow optional diagnosticID; original Row queries/algorithm retained with memory snapshots; post-place arm/encode/write; appended helper",
        "frame_original_start_line": generated[:frame_start].count(b"\n") + 1,
        "frame_row_original_line": generated[:frame_start + frame.index(FRAME_CALL)].count(b"\n") + 1,
        "row_original_start_line": style[:start].count(b"\n") + 1,
        "row_edit_count": len(EDITS), "frame_tag_count": 1,
        "inverse_exact_original_style": restored_style == style,
        "inverse_exact_original_row": restored == original_row,
        "inverse_exact_original_generated": changed_generated.replace(FRAME_TAGGED, FRAME_CALL, 1) == generated,
        "original_layout_query_counts": {"sizeThatFits": original_row.count(b"subview.sizeThatFits("), "dimensions": original_row.count(b"subview.dimensions(in:"), "place": original_row.count(b"subviews[index].place(")},
        "original_measurement_and_place_calls_unchanged": True,
        "arm_protocol": {"environment": "BERN_FRAME_ROW_LEDGER_OUTPUT_DIR", "file": "frame-row-ledger.arm.json", "schema": "bern_frame_row_arm_v1", "stage": "frame-closed-light", "required": ["schema", "pid", "stage", "token"]},
        "output_name": "frame-row-ledger-<pid>.json", "file_byte_limit": 65536, "complete_placement_limit": 64,
        "success_scope": "patch construction only; not compile/runtime/visual acceptance"
    }
    return changed_style, changed_generated, proof


def regular(path):
    require(path.is_file() and not path.is_symlink(), "regular source file required: " + str(path))
    return path.read_bytes()


def main():
    require(len(sys.argv) == 3, "usage: patch.py GENERATED_OUTPUT_ROOT FRESH_EVIDENCE_DIR")
    root = Path(sys.argv[1]).resolve(strict=True)
    evidence = Path(sys.argv[2]).resolve()
    require(not evidence.exists(), "fresh evidence directory required")
    require(root != evidence and root not in evidence.parents, "evidence must be outside generated output")
    source = root / "Sources"
    require(source.resolve(strict=True) == source and source.is_dir(), "regular Sources directory required")
    style_path, generated_path = source / "BernStyle.swift", source / "BernGenerated.swift"
    style, generated = regular(style_path), regular(generated_path)
    helper = regular(Path(__file__).with_name("RowLedger.swift"))
    changed_style, changed_generated, proof = candidate(style, generated, helper)
    evidence.mkdir(parents=True)
    for name, before, after in [("BernStyle", style, changed_style), ("BernGenerated", generated, changed_generated)]:
        difference = "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                            fromfile="a/Sources/" + name + ".swift", tofile="b/Sources/" + name + ".swift"))
        (evidence / (name + ".row-ledger.patch")).write_text(difference)
    (evidence / "patch-proof.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    style_path.write_bytes(changed_style)
    generated_path.write_bytes(changed_generated)
    require(regular(style_path) == changed_style and regular(generated_path) == changed_generated, "patched files readback mismatch")
    proof["written_style_sha256"] = sha(regular(style_path))
    proof["written_generated_sha256"] = sha(regular(generated_path))
    (evidence / "patch-proof.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
