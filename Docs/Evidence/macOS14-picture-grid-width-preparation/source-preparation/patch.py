#!/usr/bin/env python3
"""Patch only the exact generated 9dd Style after the frozen 21-point patch."""
import difflib
import hashlib
import json
from pathlib import Path
import sys

STYLE_SHA = "e1cad857ba8d4d6a5ad5155c3d7f30cc44a511b6de8988329aa45392c6cd1c6f"
GENERATED_SHA = "f4cac6965e72f454c257a30420ca5966d2b9afc012d1e9e264c20ed947b706d2"
GENERATED_BYTES = 106494
HELPER_SHA = "027c778fe272cf388e38ea0d2d5cab5089fa1d51b7b50768dca33da67227311b"
ANCHOR = b"struct BernAdaptiveGrid<Content: View>: View {"
BLOCK = b'''        .onGeometryChange(for: CGFloat.self) { $0.size.width } action: { measured in
            guard measured.isFinite, measured != width else { return }
            if width == 0 {
                var transaction = Transaction()
                transaction.disablesAnimations = true
                withTransaction(transaction) { width = measured }
            } else {
                width = measured
            }
        }
'''
INSERT = b'''            let bernGridTraceOldWidth = width
            let bernGridTraceUptime = ProcessInfo.processInfo.systemUptime
            defer {
                BernPictureGridWidthTrace.shared.append(
                    oldWidth: Double(bernGridTraceOldWidth), measured: Double(measured),
                    columns: columns, minimum: Double(minimum),
                    gap: Double(gap), rowGap: Double(rowGap),
                    actionEnteredUptime: bernGridTraceUptime)
            }
'''
DELIMITER = b"\n// Diagnostic width-action trace; original grid statements preserved.\n"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def candidate(original, helper):
    assert sha(original) == STYLE_SHA, "unexpected generated BernStyle.swift"
    assert sha(helper) == HELPER_SHA, "unexpected trace helper"
    assert original.count(ANCHOR) == 1 and original.count(BLOCK) == 1
    start = original.index(ANCHOR)
    action = original.index(BLOCK)
    assert start < action < original.index(b"\n}\n", start)
    line_end = BLOCK.index(b"\n") + 1
    patched_block = BLOCK[:line_end] + INSERT + BLOCK[line_end:]
    changed = original.replace(BLOCK, patched_block, 1)
    assert changed.replace(patched_block, BLOCK, 1) == original
    assert BLOCK[line_end:] in patched_block, "original guard/write block must stay contiguous"
    result = changed + DELIMITER + helper
    assert result[:-len(DELIMITER + helper)].replace(patched_block, BLOCK, 1) == original
    return result, {
        "original_sha256": sha(original), "original_bytes": len(original),
        "patched_sha256": sha(result), "patched_bytes": len(result),
        "helper_sha256": sha(helper), "helper_bytes": len(helper),
        "adaptive_grid_anchor_count": original.count(ANCHOR),
        "action_block_match_count": original.count(BLOCK),
        "original_guard_transaction_write_bytes_unchanged": True,
        "removing_only_insertion_and_appended_helper_restores_original": True,
        "original_action_line": original[:action].count(b"\n") + 1,
    }


def main():
    assert len(sys.argv) == 3, "usage: patch.py OUTPUT_ROOT FRESH_EVIDENCE_DIR"
    root = Path(sys.argv[1]).resolve(strict=True)
    evidence = Path(sys.argv[2]).absolute()
    assert not evidence.exists(), "evidence must be fresh"
    assert root != evidence and root not in evidence.parents, "evidence must be outside output root"
    style = root / "Sources/BernStyle.swift"
    generated = root / "Sources/BernGenerated.swift"
    assert style.resolve(strict=True).parent == (root / "Sources").resolve(strict=True)
    assert generated.resolve(strict=True).parent == style.parent.resolve(strict=True)
    baseline = generated.read_bytes()
    assert len(baseline) == GENERATED_BYTES and sha(baseline) == GENERATED_SHA, "21-point baseline required"
    original = style.read_bytes()
    helper = Path(__file__).with_name("GridWidthTrace.swift").read_bytes()
    changed, proof = candidate(original, helper)
    proof.update({"generated_21point_sha256_before": sha(baseline),
                  "scope": "one action-entry capture/defer plus file-scope logger; original grid body unchanged"})
    difference = "".join(difflib.unified_diff(original.decode().splitlines(True), changed.decode().splitlines(True),
                        fromfile="Sources/BernStyle.swift.original", tofile="Sources/BernStyle.swift.width-trace"))
    evidence.mkdir(parents=True)
    (evidence / "BernStyle.width-trace.patch").write_text(difference)
    (evidence / "patch-proof.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")
    style.write_bytes(changed)
    assert generated.read_bytes() == baseline, "21-point source changed"
    assert style.read_bytes() == changed
    proof["generated_21point_sha256_after"] = sha(generated.read_bytes())
    proof["written_style_sha256"] = sha(style.read_bytes())
    (evidence / "patch-proof.json").write_text(json.dumps(proof, indent=2, sort_keys=True) + "\n")


if __name__ == "__main__":
    main()
