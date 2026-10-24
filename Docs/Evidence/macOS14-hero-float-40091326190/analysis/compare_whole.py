#!/usr/bin/env python3
"""Compare whole-buffer binary16 distributions only; no orientation/patch alignment."""
import argparse
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
KEYS = ("baseline-body-named", "baseline-body-custom")


def require(value, message):
    if not value:
        raise ValueError(message)


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("analysis13", type=Path)
    parser.add_argument("analysis14", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    require(HERE in output.parents and not output.exists(), "Output must be fresh inside this workspace")
    hosts, inputs = {}, {}
    for major in (13, 14):
        path = getattr(args, f"analysis{major}").resolve()
        a = json.loads(path.read_text())
        require(a["analysis_complete"] is True and a["runtime_validation_passed"] is True and a["actual_os_major"] == major, "Invalid actual host analysis")
        require(a["row_direction"] == "unknown" and a["semantic_patch_values_emitted"] is False and a["capture_mode"]["selected"] == "on", "Need unknown-direction actual on analyses")
        require(a["analyzer_sha256"] == digest(HERE / "analyze_float.py") and a["atlas_spec_sha256"] == digest(HERE / "atlas-rois.json"), "Frozen analyzer/spec mismatch")
        require([r["raw_record"]["key"] for r in a["records"]] == list(KEYS), "Wrong actual raw identities")
        hosts[major] = {r["raw_record"]["key"]: r for r in a["records"]}
        inputs[str(major)] = {"path": str(path), "sha256": digest(path), "report": a["report"], "report_sha256": a["report_sha256"],
            "runtime_context": a["context"], "capture_context": a["capture_context"]}
    comparisons = []
    for key in KEYS:
        a, b = hosts[13][key], hosts[14][key]
        require(a["snapshot_ICC_context"]["icc_sha256"] == b["snapshot_ICC_context"]["icc_sha256"] and
                a["snapshot_ICC_context"]["icc_byte_count"] == b["snapshot_ICC_context"]["icc_byte_count"], "Snapshot ICC differs")
        wa, wb = a["whole_active_pixel_buffer"], b["whole_active_pixel_buffer"]
        n13, n14 = wa["pixel_count"], wb["pixel_count"]
        require(n13 == 4 * n14, "This acquired pair does not have the actual4x pixel-count context")
        channels = {}
        for c in "RGBA":
            x, y = wa["RGBA"][c], wb["RGBA"][c]
            finite = {name: {"13": x[name], "14": y[name], "14_minus_13": None if x[name] is None or y[name] is None else y[name] - x[name]}
                      for name in ("finite_numeric_min", "finite_numeric_mean", "finite_numeric_max")}
            counts = {}
            for name in ("numeric_less_than_zero_count", "numeric_greater_than_one_count", "nan_count", "positive_infinity_count", "negative_infinity_count", "numeric_equal_one_count"):
                counts[name] = {"13": x[name], "14": y[name], "13_fraction": x[name] / n13, "14_fraction": y[name] / n14,
                    "13_minus_4_times_14": x[name] - 4 * y[name]}
            channels[c] = {"finite_statistics": finite, "count_context_only": counts,
                "unique_bits_counts": {"13": x["unique_uint16_bit_pattern_count"], "14": y["unique_uint16_bit_pattern_count"]}}
        comparisons.append({"key": key, "raw13": a["raw_record"], "raw14": b["raw_record"],
            "actual_pixel_counts": {"13": n13, "14": n14}, "sample_count_ratio13_over14": 4,
            "snapshot_ICC_sha256": a["snapshot_ICC_context"]["icc_sha256"],
            "snapshot_ICC_bytes": a["snapshot_ICC_context"]["icc_byte_count"],
            "alpha_all_numeric_exactly_one": {"13": wa["alpha_all_numeric_exactly_one"], "14": wb["alpha_all_numeric_exactly_one"]},
            "channels": channels})
    result = {"analysis_complete": True, "script_sha256": digest(Path(__file__)), "inputs": inputs,
        "scope": "Unlabelled whole-buffer stored RGBA binary16 distributions only. No semantic color-patch values or row direction assignment.",
        "comparisons": comparisons,
        "boundary_observation": "Distinct whole-buffer means/count fractions are present in retained renderer-return raw snapshot storage for these acquired inputs. This observation does not identify a unique OS cause or explain the visible mismatch.",
        "binary_provenance": "Not inferred by this numeric script. Same-distributed-binary interpretation requires the separately retained package hash and actual run receipts.",
        "limitations": ["640x360 versus320x180 are different native sampling grids.4x multiplication is aggregate count context only; no pixels are resampled, aligned, fitted, flipped or compared positionally.",
            "Global distributions are invariant to row reversal but cannot locate semantic patches or eliminate edge/sampling/display/host context differences.",
            "No clamp, color conversion, transfer-function application, unpremultiplication, nits conversion or automatic visual-equivalence threshold."]}
    output.write_text(json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n")
    print(json.dumps({"analysis_complete": True, "output": str(output), "comparisons": len(comparisons),
        "mean14_minus13": {r["key"]: {c: r["channels"][c]["finite_statistics"]["finite_numeric_mean"]["14_minus_13"] for c in "RGBA"} for r in comparisons}}, indent=2))


if __name__ == "__main__":
    main()
