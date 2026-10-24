#!/usr/bin/env python3
"""Offline per-ROI exactness check: actual default-mode control vs archived macOS13."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import re
import sys

HERE = Path(__file__).resolve().parent
NAMES = ("body-named", "body-custom", "oracle-top", "flight-named", "flight-custom", "oracle-bottom")
PHASES = ("progress-0", "progress-1")


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(analysis_path, report_override):
    analysis_path = analysis_path.resolve()
    analysis = json.loads(analysis_path.read_text())
    report_path = (report_override or Path(analysis["input_report"])).resolve()
    require(sha(report_path) == analysis["input_report_sha256"], "Runtime report hash differs from analysis input")
    runtime = json.loads(report_path.read_text())
    match = re.search(r"(\d+)\.", str(runtime.get("os", "")))
    require(match is not None and int(match.group(1)) == 13, "Both actual runtime OS strings must identify macOS13")
    require(analysis.get("analysis_complete") is True and runtime.get("success") is True and runtime.get("completed_phases") == 2,
            "Both actual endpoint captures and offline analysis must be complete")
    captures = {c["phase"]: c for c in analysis["captures"]}
    require(len(analysis["captures"]) == 2 and set(captures) == set(PHASES), "Need two actual endpoint phases")
    return analysis, captures, runtime, dict(analysis=str(analysis_path), analysis_sha256=sha(analysis_path),
        runtime_report=str(report_path), runtime_report_sha256=sha(report_path), actual_os=runtime["os"],
        color_mode_fields={k: runtime.get(k) for k in ("hero_color_mode_environment", "hero_color_mode_selected", "hero_color_mode_assignment_requested")})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive_analysis", type=Path)
    parser.add_argument("default_analysis", type=Path)
    parser.add_argument("--archive-report", type=Path)
    parser.add_argument("--default-report", type=Path)
    parser.add_argument("--output", type=Path, default=HERE / "default-vs-archive13")
    args = parser.parse_args()
    output = args.output.resolve()
    require(HERE in output.parents and not output.exists(), "Output must be a fresh subdirectory of this analysis workspace")
    old, old_captures, _, old_context = load(args.archive_analysis, args.archive_report)
    new, new_captures, runtime, new_context = load(args.default_analysis, args.default_report)
    require(runtime.get("hero_color_mode_selected") == "default" and runtime.get("hero_color_mode_assignment_requested") is False,
            "Input is not a recorded default control with no requested colorMode setter")
    for key in ("analyzer_sha256", "atlas_spec_sha256", "versions"):
        require(old[key] == new[key], f"Different {key}; use the same frozen local analyzer")
    rows = []
    for phase in PHASES:
        require(set(old_captures[phase]["rois"]) == set(new_captures[phase]["rois"]) == set(NAMES), "Six-pane names differ")
        for name in NAMES:
            a, b = old_captures[phase]["rois"][name], new_captures[phase]["rois"][name]
            same_size = a["pixel_size"] == b["pixel_size"]
            rows.append(dict(phase=phase, roi=name, archive_pixels=a["pixel_size"], default_pixels=b["pixel_size"],
                same_embedded_icc=old_captures[phase]["embedded_icc_sha256"] == new_captures[phase]["embedded_icc_sha256"],
                raw_rgb_exact=same_size and a["raw_profile_rgb_sha256"] == b["raw_profile_rgb_sha256"],
                icc_normalized_rgb_exact=same_size and a["icc_to_srgb_rgb_sha256"] == b["icc_to_srgb_rgb_sha256"],
                archive_raw_rgb_sha256=a["raw_profile_rgb_sha256"], default_raw_rgb_sha256=b["raw_profile_rgb_sha256"],
                archive_icc_normalized_rgb_sha256=a["icc_to_srgb_rgb_sha256"], default_icc_normalized_rgb_sha256=b["icc_to_srgb_rgb_sha256"]))
    result = dict(analysis_complete=True, script_sha256=sha(Path(__file__)), archive=old_context, default_control=new_context,
                  scope="Actual per-ROI decoded RGB hashes from separately completed frozen analyses; no image fitting, resampling or new runtime.",
                  comparisons=rows, raw_roi_all_exact=all(r["raw_rgb_exact"] for r in rows),
                  normalized_roi_all_exact=all(r["icc_normalized_rgb_exact"] for r in rows),
                  limitations=["Color-mode fields record selected/requested configuration; this script does not instrument actual renderer setter calls.",
                               "Exit0 means comparison completed. Pixel inequality is retained as a result, not a script error or automatic acceptance.",
                               "Fixed-size same-image snapshot/draw endpoints do not validate coordinated flight lifecycle or full application UI."])
    output.mkdir()
    (output / "comparison.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({k: result[k] for k in ("analysis_complete", "raw_roi_all_exact", "normalized_roi_all_exact")}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError) as error:
        print(f"Default-control offline comparison failed: {error}", file=sys.stderr)
        sys.exit(1)
