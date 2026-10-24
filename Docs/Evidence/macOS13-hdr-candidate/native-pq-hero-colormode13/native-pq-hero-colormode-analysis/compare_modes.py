#!/usr/bin/env python3
"""Offline default/extendedLinear delta, retaining actual ROI geometry and pixels."""
from __future__ import annotations

import argparse
import hashlib
import importlib.util
import io
import json
from pathlib import Path

from PIL import Image, ImageChops, ImageCms, ImageStat, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("frozen_endpoint_analyzer", HERE / "analyze.py")
frozen = importlib.util.module_from_spec(spec)
spec.loader.exec_module(frozen)


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(path):
    return json.loads(path.read_text())


def load(path, mode):
    analysis = read(path)
    report_path = Path(analysis["input_report"])
    frozen.require(sha(report_path) == analysis["input_report_sha256"], "Original report hash mismatch")
    report = read(report_path)
    frozen.require(report["success"] is True and report["completed_phases"] == 2, "Unsuccessful endpoint run")
    frozen.require(report["hero_color_mode_selected"] == mode and
                   report["hero_color_mode_assignment_requested"] is (mode != "default"), "Unexpected colorMode metadata")
    frozen.require(analysis["analyzer_sha256"] == sha(HERE / "analyze.py") and
                   analysis["atlas_spec_sha256"] == sha(HERE / "atlas-rois.json"), "Frozen input mismatch")
    frozen.require(analysis["versions"] == {"pillow": pillow_version, "littlecms": ImageCms.core.littlecms_version}, "Imaging version mismatch")
    captures = {}
    for capture in report["captures"]:
        phase = capture["phase"]
        original = next(c for c in analysis["captures"] if c["phase"] == phase)
        png = report_path.parent / capture["png"]
        frozen.require(sha(png) == capture["png_sha256"] == original["png_sha256"], "Original PNG hash mismatch")
        with Image.open(png) as opened:
            opened.load()
            raw = opened.convert("RGB")
            icc = opened.info["icc_profile"]
            normalized = ImageCms.profileToProfile(raw, ImageCms.ImageCmsProfile(io.BytesIO(icc)),
                ImageCms.createProfile("sRGB"), renderingIntent=0, outputMode="RGB", flags=0)
        panes = {}
        for name in frozen.NAMES:
            box = frozen.rect_box(capture["rois"][name]["screenshot_pixels"], phase + "/" + name)
            panes[name] = {"raw_profile_rgb": raw.crop(box), "icc_to_srgb": normalized.crop(box)}
            for domain, image in panes[name].items():
                key = "raw_profile_rgb_sha256" if domain == "raw_profile_rgb" else "icc_to_srgb_rgb_sha256"
                frozen.require(hashlib.sha256(image.tobytes()).hexdigest() == original["rois"][name][key], "Crop differs from retained analysis")
        captures[phase] = {"runtime": capture, "panes": panes}
    frozen.require(set(captures) == set(frozen.PHASES), "Unexpected phases")
    return analysis, report, captures


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("default", type=Path)
    parser.add_argument("extended", type=Path)
    parser.add_argument("default_vs14", type=Path)
    parser.add_argument("extended_vs14", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    frozen.require(HERE in output.parents and not output.exists(), "Output must be fresh and inside this workspace")
    default, dr, dc = load(args.default, "default")
    extended, er, ec = load(args.extended, "extendedLinear")
    default14, extended14 = read(args.default_vs14), read(args.extended_vs14)
    frozen.require(default14["hosts"]["13"]["analysis_sha256"] == sha(args.default) and
                   extended14["hosts"]["13"]["analysis_sha256"] == sha(args.extended) and
                   default14["hosts"]["14"]["analysis_sha256"] == extended14["hosts"]["14"]["analysis_sha256"],
                   "Cross-host analysis inputs mismatch")
    rows, geometry = [], []
    for phase in frozen.PHASES:
        a, b = dc[phase]["runtime"], ec[phase]["runtime"]
        geometry.append({"phase": phase,
            "window_geometry_exact": all(a[k] == b[k] for k in ("capture_size", "root_bounds", "window_bounds", "window_frame")),
            "default_window_geometry": {k: a[k] for k in ("capture_size", "root_bounds", "window_bounds", "window_frame")},
            "extended_window_geometry": {k: b[k] for k in ("capture_size", "root_bounds", "window_bounds", "window_frame")}})
        for name in frozen.NAMES:
            rows.append({"phase": phase, "roi": name, "roi_geometry_exact": a["rois"][name] == b["rois"][name],
                "default_roi_geometry": a["rois"][name], "extended_roi_geometry": b["rois"][name],
                "domains": {domain: frozen.rgb_metrics(ec[phase]["panes"][name][domain], dc[phase]["panes"][name][domain], ImageChops, ImageStat)
                            for domain in ("raw_profile_rgb", "icc_to_srgb")}})
    residuals, representatives = [], []
    for old, new in zip(default14["comparisons"], extended14["comparisons"]):
        frozen.require((old["phase"], old["source"]) == (new["phase"], new["source"]), "Residual row mismatch")
        key = "residual_13_minus_14_patch_mean_difference"
        residuals.append({"phase": old["phase"], "source": old["source"], "default": old[key], "extendedLinear": new[key],
            "extended_minus_default_mean_absolute_codes": new[key]["mean_absolute_codes"] - old[key]["mean_absolute_codes"],
            "extended_minus_default_max_absolute_codes": new[key]["max_absolute_codes"] - old[key]["max_absolute_codes"]})
        for name in ("cool812", "red812", "white203"):
            x, y = old["patches"][name], new["patches"][name]
            frozen.require(x["hosts"]["14"] == y["hosts"]["14"], "14 reference values changed")
            representatives.append({"phase": old["phase"], "source": old["source"], "patch": name,
                "13_default": x["hosts"]["13"], "13_extendedLinear": y["hosts"]["13"], "14_reference": x["hosts"]["14"],
                "default_residual_13_minus_14": x["residual_13_minus_14"], "extended_residual_13_minus_14": y["residual_13_minus_14"]})
    result = {"analysis_complete": True, "script_sha256": sha(Path(__file__)),
        "inputs": {key: {"path": str(getattr(args, key).resolve()), "sha256": sha(getattr(args, key))}
                   for key in ("default", "extended", "default_vs14", "extended_vs14")},
        "mode_metadata": {name: {k: r[k] for k in ("hero_color_mode_environment", "hero_color_mode_selected", "hero_color_mode_assignment_requested")}
                          for name, r in (("default", dr), ("extendedLinear", er))},
        "all_roi_geometry_exact": all(row["roi_geometry_exact"] for row in rows),
        "all_window_geometry_exact": all(row["window_geometry_exact"] for row in geometry),
        "window_geometry": geometry, "default_to_extended_roi_pixels": rows,
        "crosshost_H_minus_B_residual_comparison": residuals, "representative_normalized_patch_means": representatives,
        "units": "Encoded 8-bit sRGB codes /255; RGB means and patch residuals are not linear light or nits.",
        "limitations": ["No fit, resampling, threshold or automatic equivalence judgment. Comparisons refer to retained endpoint PNGs only.",
                        "Body/oracle pixel and geometry preservation do not validate full flight lifecycle, animation, routing or a physical panel.",
                        "Actual14 reference uses the earlier baseline binary; this colorMode diagnostic is not a same-binary cross-host experiment."]}
    output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"analysis_complete": True, "all_roi_geometry_exact": result["all_roi_geometry_exact"],
        "all_window_geometry_exact": result["all_window_geometry_exact"], "pixel_summaries":
        [{"phase": row["phase"], "roi": row["roi"], "domains": row["domains"]} for row in rows]}, indent=2))


if __name__ == "__main__":
    main()
