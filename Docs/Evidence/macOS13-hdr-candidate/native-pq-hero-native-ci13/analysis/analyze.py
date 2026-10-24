#!/usr/bin/env python3
"""Offline only: compare real hero endpoint WindowServer PNGs using reported ROIs."""
from __future__ import annotations

import argparse
import gzip
import hashlib
import io
import json
import math
from pathlib import Path
import struct
import sys

HERE = Path(__file__).resolve().parent
NAMES = ("body-named", "body-custom", "oracle-top", "flight-named", "flight-custom", "oracle-bottom")
PHASES = ("progress-0", "progress-1")
ORACLES = ("oracle-top", "oracle-bottom")


def sha(data):
    return hashlib.sha256(data).hexdigest()


def load_json(path):
    return json.loads(path.read_text())


def require(condition, message):
    if not condition:
        raise ValueError(message)


def integer(value, label):
    require(isinstance(value, (int, float)) and not isinstance(value, bool) and math.isfinite(value), f"Nonfinite or invalid {label}")
    rounded = round(value)
    require(abs(value - rounded) <= 1e-5, f"Fractional pixel boundary for {label}: {value}; no rounding/fitting is allowed")
    return rounded


def rect_box(rect, label):
    x0 = integer(rect["x"], label + ".x")
    y0 = integer(rect["y"], label + ".y")
    x1 = integer(rect["x"] + rect["width"], label + ".maxX")
    y1 = integer(rect["y"] + rect["height"], label + ".maxY")
    require(x1 > x0 and y1 > y0, f"Empty rectangle: {label}")
    return x0, y0, x1, y1


def mapped_box(rect, size, source_size, label):
    sx, sy = size[0] / source_size[0], size[1] / source_size[1]
    return rect_box(dict(x=rect["x"] * sx, y=rect["y"] * sy,
                         width=rect["width"] * sx, height=rect["height"] * sy), label)


def png_header(data):
    require(data[:8] == b"\x89PNG\r\n\x1a\n" and data[12:16] == b"IHDR", "Input is not an IHDR-first PNG")
    width, height, depth, color_type = struct.unpack(">IIBB", data[16:26])
    require(depth == 8 and color_type in (2, 6), "Only 8-bit RGB/RGBA screenshot PNGs are accepted; no implicit 16-bit conversion")
    return dict(width=width, height=height, bit_depth=depth, color_type=color_type)


def rgb_metrics(left, right, ImageChops, ImageStat):
    require(left.mode == right.mode == "RGB" and left.size == right.size, "RGB comparison needs identical unscaled dimensions")
    diff = ImageChops.difference(left, right)
    stat = ImageStat.Stat(diff)
    channels = diff.split()
    any_channel = ImageChops.lighter(ImageChops.lighter(channels[0], channels[1]), channels[2])
    different = left.width * left.height - any_channel.histogram()[0]
    maxima = [e[1] for e in stat.extrema]
    return dict(rgb_exact=different == 0, different_rgb_pixels=different,
                pixel_count=left.width * left.height,
                channel_mae_codes=list(stat.mean), channel_max_absolute_delta_codes=maxima,
                mae_codes=sum(stat.mean) / 3, max_absolute_delta_codes=max(maxima))


def column_means(image):
    data = memoryview(image.tobytes())
    stride = image.width * 3
    return [[sum(data[x * 3 + c::stride]) / image.height for c in range(3)] for x in range(image.width)]


def measure(image, spec, ImageStat):
    source_size = spec["source_size"]
    require(image.width * source_size[1] == image.height * source_size[0], "ROI distorts the atlas aspect ratio")
    patches = {}
    for patch in spec["patches"]:
        box = mapped_box(patch["interior_source_rect"], image.size, source_size, patch["name"])
        crop = image.crop(box)
        patches[patch["name"]] = dict(image=crop, box=box, mean_rgb=list(ImageStat.Stat(crop).mean))
    ramp_box = mapped_box(spec["ramp"]["interior_source_rect"], image.size, source_size, "gray-ramp")
    ramp = image.crop(ramp_box)
    return dict(image=image, patches=patches, ramp_image=ramp, ramp_box=ramp_box, ramp_columns=column_means(ramp))


def compare(left, right, ImageChops, ImageStat):
    result = rgb_metrics(left["image"], right["image"], ImageChops, ImageStat)
    result["patch_interiors"] = {}
    mean_deltas = []
    for name, a in left["patches"].items():
        b = right["patches"][name]
        delta = [x - y for x, y in zip(a["mean_rgb"], b["mean_rgb"])]
        mean_deltas.append(delta)
        result["patch_interiors"][name] = dict(
            **rgb_metrics(a["image"], b["image"], ImageChops, ImageStat),
            mean_rgb_left=a["mean_rgb"], mean_rgb_right=b["mean_rgb"], mean_rgb_delta_left_minus_right=delta)
    result["patch_mean_rgb_mae_codes"] = sum(abs(v) for row in mean_deltas for v in row) / (len(mean_deltas) * 3)
    result["patch_mean_rgb_max_absolute_delta_codes"] = max(abs(v) for row in mean_deltas for v in row)
    la, ra = left["ramp_columns"], right["ramp_columns"]
    require(len(la) == len(ra), "Gray-ramp column counts differ")
    deltas = [[a - b for a, b in zip(x, y)] for x, y in zip(la, ra)]
    result["gray_ramp"] = dict(
        **rgb_metrics(left["ramp_image"], right["ramp_image"], ImageChops, ImageStat),
        columns=len(deltas), rows=left["ramp_image"].height,
        column_mean_channel_mae_codes=[sum(abs(row[c]) for row in deltas) / len(deltas) for c in range(3)],
        column_mean_channel_max_absolute_delta_codes=[max(abs(row[c]) for row in deltas) for c in range(3)],
        column_mean_rgb_mae_codes=sum(abs(v) for row in deltas for v in row) / (len(deltas) * 3),
        column_mean_rgb_max_absolute_delta_codes=max(abs(v) for row in deltas for v in row))
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path, help="Actual fixture runtime13/report.json; never modified")
    parser.add_argument("--output", type=Path, default=HERE / "baseline-analysis", help="Fresh result directory below this analysis directory")
    args = parser.parse_args()
    from PIL import Image, ImageChops, ImageCms, ImageStat, __version__ as pillow_version

    report_path = args.report.resolve()
    destination = args.output.resolve()
    require(HERE in destination.parents and not destination.exists(), "Output must be a fresh subdirectory of this analysis directory")
    require(report_path.parent != destination and report_path.parent not in destination.parents, "Do not write into the fixture/runtime input tree")
    spec_path = HERE / "atlas-rois.json"
    spec = load_json(spec_path)
    report = load_json(report_path)
    require(report.get("success") is True and report.get("completed_phases") == 2, "Fixture did not complete both endpoints; no successful endpoint analysis is implied")
    require(report.get("cache_unchanged") is True and report["cache_before"] == report["cache_after"], "Recorded source/cache ledger changed")
    for source in spec["sources"]:
        require(report["cache_before"][source["png"]]["file_sha256"] == source["png_sha256"], "Fixture atlas file hash differs from the inspected atlas source")
    captures = report["captures"]
    require(len(captures) == 2 and {c["phase"] for c in captures} == set(PHASES), "Need exactly one actual capture for progress-0 and progress-1")
    data_by_phase, capture_rows, ramps = {}, [], {}
    warnings = []
    for capture in captures:
        phase = capture["phase"]
        relative = Path(capture["png"])
        require(not relative.is_absolute() and ".." not in relative.parts, "PNG must be a fixture-relative path")
        path = (report_path.parent / relative).resolve()
        require(path.is_file(), f"Missing actual PNG: {path}")
        encoded = path.read_bytes()
        require(sha(encoded) == capture["png_sha256"], f"Original PNG hash mismatch: {path}")
        header = png_header(encoded)
        require(capture.get("consecutive_equal_buffers", 0) >= 5, "Runtime did not record five equal raw buffers")
        with Image.open(io.BytesIO(encoded)) as opened:
            opened.load()
            require(opened.mode in ("RGB", "RGBA"), f"Unsupported decoded screenshot mode: {opened.mode}")
            require(list(opened.size) == capture["capture_size"], "Recorded screenshot dimensions differ from original PNG")
            icc = opened.info.get("icc_profile")
            require(isinstance(icc, bytes) and len(icc) > 0, "Screenshot has no embedded ICC; do not guess sRGB")
            raw = opened.convert("RGB")
            alpha = opened.getchannel("A") if opened.mode == "RGBA" else Image.new("L", opened.size, 255)
            normalized = ImageCms.profileToProfile(
                raw, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile("sRGB"),
                renderingIntent=0, outputMode="RGB", flags=0)
            original_mode = opened.mode
        actual_icc = sha(icc)
        recorded_icc = capture.get("capture_icc_sha256")
        if recorded_icc != actual_icc:
            warnings.append(dict(phase=phase, issue="PNG embedded ICC bytes differ from recorded CGColorSpace ICC bytes",
                                 recorded=recorded_icc, embedded_png=actual_icc,
                                 action="Normalization uses actual PNG ICC; no cause or equivalence is inferred"))
        require(set(capture["rois"]) == set(NAMES), "Unexpected six-pane ROI names")
        arrays, row, ramp_phase = {}, dict(phase=phase, png=str(path), png_sha256=sha(encoded), png_header=header,
            original_mode=original_mode, embedded_icc_sha256=actual_icc,
            recorded_capture_icc_sha256=recorded_icc,
            runtime_capture={k: capture[k] for k in ("consecutive_equal_buffers", "raw_buffer_sha256", "window_id", "owner_pid", "window_bounds", "window_frame", "current_headroom", "potential_headroom", "key", "active", "frontmost_pid") if k in capture}, rois={}), {}
        common_size = None
        for name in NAMES:
            entry = capture["rois"][name]
            host = entry["host_top_left_points"]
            require(abs(host["width"] - 320) <= 1e-5 and abs(host["height"] - 180) <= 1e-5, "Runtime pane is not 320x180 points")
            box = rect_box(entry["screenshot_pixels"], phase + "/" + name)
            require(0 <= box[0] < box[2] <= raw.width and 0 <= box[1] < box[3] <= raw.height, "Reported ROI is outside its original PNG")
            raw_crop, normalized_crop = raw.crop(box), normalized.crop(box)
            if common_size is None:
                common_size = raw_crop.size
            require(raw_crop.size == common_size, "Same-phase panes have different pixel dimensions; no resampling allowed")
            alpha_extrema = alpha.crop(box).getextrema()
            require(alpha_extrema == (255, 255), "Only the existing opaque-atlas endpoint scope is supported; alpha compositing is not inferred")
            measurements = {"raw_profile_rgb": measure(raw_crop, spec, ImageStat),
                            "icc_to_srgb": measure(normalized_crop, spec, ImageStat)}
            arrays[name] = measurements
            row["rois"][name] = dict(screenshot_pixels=entry["screenshot_pixels"], pixel_size=list(raw_crop.size),
                alpha_extrema=list(alpha_extrema), raw_profile_rgb_sha256=sha(raw_crop.tobytes()),
                icc_to_srgb_rgb_sha256=sha(normalized_crop.tobytes()),
                patch_boxes_relative_to_roi={n: list(m["box"]) for n, m in measurements["raw_profile_rgb"]["patches"].items()},
                ramp_box_relative_to_roi=list(measurements["raw_profile_rgb"]["ramp_box"]),
                means={domain: {n: p["mean_rgb"] for n, p in value["patches"].items()} for domain, value in measurements.items()})
            ramp_phase[name] = {domain: value["ramp_columns"] for domain, value in measurements.items()}
        data_by_phase[phase] = dict(panes=arrays, icc=actual_icc)
        capture_rows.append(row); ramps[phase] = ramp_phase

    comparisons, primary = [], []
    for phase in PHASES:
        panes = data_by_phase[phase]["panes"]
        pairs = [(name, oracle) for name in NAMES for oracle in ORACLES]
        pairs += [("body-named", "flight-named"), ("body-custom", "flight-custom")]
        for left, right in pairs:
            for domain in ("raw_profile_rgb", "icc_to_srgb"):
                metrics = compare(panes[left][domain], panes[right][domain], ImageChops, ImageStat)
                comparisons.append(dict(kind="same_phase", phase=phase, left=left, right=right, domain=domain,
                                        same_embedded_icc=True, metrics=metrics))
                if (left.startswith("body-") and right == "oracle-top") or (left.startswith("flight-") and right == "oracle-bottom"):
                    primary.append(dict(phase=phase, target=left, oracle=right, domain=domain, rgb_exact=metrics["rgb_exact"]))
    for name in NAMES:
        for domain in ("raw_profile_rgb", "icc_to_srgb"):
            comparisons.append(dict(kind="cross_phase", left_phase=PHASES[0], right_phase=PHASES[1], target=name, domain=domain,
                same_embedded_icc=data_by_phase[PHASES[0]]["icc"] == data_by_phase[PHASES[1]]["icc"],
                metrics=compare(data_by_phase[PHASES[0]]["panes"][name][domain], data_by_phase[PHASES[1]]["panes"][name][domain], ImageChops, ImageStat)))
    result = dict(analysis_complete=True,
        scope="Actual same-window opaque PQ atlas snapshot/draw endpoints, fixed size, progress 0/1 with from==to. Not coordinator flight lifecycle, full Bern application or macOS14 parity.",
        input_report=str(report_path), input_report_sha256=sha(report_path.read_bytes()),
        analyzer_sha256=sha(Path(__file__).read_bytes()), atlas_spec_sha256=sha(spec_path.read_bytes()),
        atlas_source_provenance=spec["provenance"],
        versions=dict(pillow=pillow_version, littlecms=ImageCms.core.littlecms_version),
        normalization="Own embedded PNG ICC -> sRGB, Pillow/LittleCMS perceptual intent 0, flags 0, 8-bit RGB. Raw profile-encoded RGB retained separately; all deltas are encoded code values /255, not linear light or nits.",
        roi_method="Use each recorded screenshot_pixels rectangle; source atlas region boundaries mapped exactly to its actual pixel size. No image rescaling, registration, fitting, threshold alignment or invented ROI.",
        warnings=warnings, captures=capture_rows, primary_comparisons=primary, comparisons=comparisons,
        limitations=["Endpoint draw views use the same NSImage for from/to; endpoints do not validate actual enter/leave, geometry interpolation, hide/restore, retarget/reversal or mid-flight intent changes.",
                     "Five equal buffers, owned WindowServer identity, cache preservation and foreground are recorded runtime claims; this offline script verifies retained PNG hashes/metadata, not missing raw buffers or native runtime objects.",
                     "Only opaque EXIF-up named/custom PQ Standard/original/fill320x180 atlas inputs; no alpha/other EXIF/HLG/High/gainmap/full-app/physical-panel/macOS14 equivalence.",
                     "Image differences are measurements, not analyzer errors; exit 0 never means visual acceptance."])
    destination.mkdir()
    ramp_file = destination / "ramp-column-means.json.gz"
    ramp_file.write_bytes(gzip.compress(json.dumps(ramps, separators=(",", ":"), sort_keys=True).encode(), mtime=0))
    result["ramp_column_means"] = dict(file=ramp_file.name, sha256=sha(ramp_file.read_bytes()), encoding="gzip JSON; every per-ROI raw and ICC-normalized gray-ramp column RGB mean")
    (destination / "analysis.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps(dict(analysis_complete=True, output=str(destination), captures=len(capture_rows), comparisons=len(comparisons),
                         primary_rgb_exact=primary, warnings=warnings), indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, OSError, ImportError) as error:
        print(f"Offline analysis failed: {error}", file=sys.stderr)
        sys.exit(1)
