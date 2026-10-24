#!/usr/bin/env python3
"""Offline same-OS, same-scale actual ROI comparison; no image fitting."""
from __future__ import annotations
import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import re
from PIL import Image, ImageChops, ImageCms, ImageStat, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
module_spec = importlib.util.spec_from_file_location("frozen_endpoint_analyzer", HERE / "analyze.py")
frozen = importlib.util.module_from_spec(module_spec)
module_spec.loader.exec_module(frozen)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(path, major):
    analysis = json.loads(path.read_text())
    report_path = Path(analysis["input_report"])
    frozen.require(sha(report_path) == analysis["input_report_sha256"], "Original report hash differs")
    report = json.loads(report_path.read_text())
    os_match = re.search(r"(\d+)\.", report["os"])
    frozen.require(os_match and int(os_match.group(1)) == major, "Unexpected actual OS")
    frozen.require(report["success"] is True and report["completed_phases"] == 2 and analysis["analysis_complete"] is True, "Incomplete run")
    frozen.require(analysis["analyzer_sha256"] == sha(HERE / "analyze.py") and
                   analysis["atlas_spec_sha256"] == sha(HERE / "atlas-rois.json"), "Frozen analyzer/spec differ")
    frozen.require(analysis["versions"] == {"pillow": pillow_version, "littlecms": ImageCms.core.littlecms_version}, "Imaging versions differ")
    atlas = json.loads((HERE / "atlas-rois.json").read_text())
    captures, context = {}, {}
    for row in analysis["captures"]:
        phase = row["phase"]
        original = next(c for c in report["captures"] if c["phase"] == phase)
        png = report_path.parent / original["png"]
        frozen.require(sha(png) == original["png_sha256"] == row["png_sha256"], "Original PNG hash differs")
        with Image.open(png) as opened:
            opened.load()
            raw = opened.convert("RGB")
            icc = opened.info["icc_profile"]
            normalized = ImageCms.profileToProfile(raw, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                ImageCms.createProfile("sRGB"), renderingIntent=0, outputMode="RGB", flags=0)
        frozen.require(hashlib.sha256(icc).hexdigest() == row["embedded_icc_sha256"], "Embedded ICC differs")
        captures[phase] = {}
        for name in frozen.NAMES:
            box = frozen.rect_box(row["rois"][name]["screenshot_pixels"], phase + "/" + name)
            values = {"raw_profile_rgb": raw.crop(box), "icc_to_srgb": normalized.crop(box)}
            for domain, image in values.items():
                hash_key = "raw_profile_rgb_sha256" if domain == "raw_profile_rgb" else "icc_to_srgb_rgb_sha256"
                frozen.require(hashlib.sha256(image.tobytes()).hexdigest() == row["rois"][name][hash_key], "Retained ROI hash differs")
            captures[phase][name] = {domain: frozen.measure(image, atlas, ImageStat) for domain, image in values.items()}
        context[phase] = {"png_sha256": row["png_sha256"], "embedded_icc_sha256": row["embedded_icc_sha256"],
            "rois": {name: {k: row["rois"][name][k] for k in ("pixel_size", "screenshot_pixels")} for name in frozen.NAMES},
            "runtime_capture": row["runtime_capture"]}
    frozen.require(set(captures) == set(frozen.PHASES), "Unexpected phases")
    return analysis, report, captures, context


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("historical", type=Path)
    parser.add_argument("current", type=Path)
    parser.add_argument("--expected-major", type=int, choices=(13, 14), required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    frozen.require(HERE in output.parents and not output.exists(), "Output must be fresh and inside this workspace")
    old, old_report, old_pixels, old_context = load(args.historical, args.expected_major)
    new, new_report, new_pixels, new_context = load(args.current, args.expected_major)
    comparisons = []
    for phase in frozen.PHASES:
        for name in frozen.NAMES:
            frozen.require(old_context[phase]["rois"][name]["pixel_size"] == new_context[phase]["rois"][name]["pixel_size"], "Same-OS ROI pixel sizes differ; no resize allowed")
            for domain in ("raw_profile_rgb", "icc_to_srgb"):
                comparisons.append({"phase": phase, "roi": name, "domain": domain,
                    "same_roi_screenshot_frame": old_context[phase]["rois"][name] == new_context[phase]["rois"][name],
                    "same_png_embedded_icc": old_context[phase]["embedded_icc_sha256"] == new_context[phase]["embedded_icc_sha256"],
                    "metrics_current_minus_historical": frozen.compare(new_pixels[phase][name][domain], old_pixels[phase][name][domain], ImageChops, ImageStat)})
    result = {"analysis_complete": True, "script_sha256": sha(Path(__file__)), "actual_os_major": args.expected_major,
        "inputs": {label: {"analysis_path": str(path.resolve()), "analysis_sha256": sha(path),
            "runtime_report": analysis["input_report"], "runtime_report_sha256": analysis["input_report_sha256"],
            "actual_os": report["os"], "captures": context}
            for label, path, analysis, report, context in (("historical", args.historical, old, old_report, old_context), ("current", args.current, new, new_report, new_context))},
        "raw_roi_all_exact": all(row["metrics_current_minus_historical"]["rgb_exact"] for row in comparisons if row["domain"] == "raw_profile_rgb"),
        "normalized_roi_all_exact": all(row["metrics_current_minus_historical"]["rgb_exact"] for row in comparisons if row["domain"] == "icc_to_srgb"),
        "comparisons": comparisons,
        "limitations": ["Different acquisition times/processes and potentially different VM/display context; equality or differences do not uniquely establish observer effect, OS, toolchain or display cause.",
            "Same native ROI sizes only, no resampling/registration/fitting or automatic equivalence threshold. All signed patch deltas are current minus historical, encoded RGB code values 0-255.",
            "Whole retained windows may differ outside these six ROIs; this does not assert whole-PNG equality or complete flight lifecycle acceptance."]}
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis_complete": True, "raw_roi_all_exact": result["raw_roi_all_exact"], "normalized_roi_all_exact": result["normalized_roi_all_exact"],
        "roi_metrics": [{"phase": row["phase"], "roi": row["roi"], "domain": row["domain"],
            "mae": row["metrics_current_minus_historical"]["mae_codes"], "max": row["metrics_current_minus_historical"]["max_absolute_delta_codes"],
            "different_rgb_pixels": row["metrics_current_minus_historical"]["different_rgb_pixels"]} for row in comparisons]}, indent=2))


if __name__ == "__main__":
    main()
