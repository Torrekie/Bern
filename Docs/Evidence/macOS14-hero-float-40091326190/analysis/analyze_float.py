#!/usr/bin/env python3
"""Offline raw RGBA binary16 descriptors; no color conversion or inferred row direction."""
from __future__ import annotations

import argparse
import base64
from collections import Counter
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import sys

HERE = Path(__file__).resolve().parent
MAX_RAW_BYTES = 4 * 1024 * 1024
MAX_REPORT_BYTES = 2 * 1024 * 1024
ATLAS_SPEC_SHA256 = "39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf"
KEYS = ("baseline-body-named", "baseline-body-custom")
PHASES = ("progress-0", "progress-1")
ROI_NAMES = {"body-named", "body-custom", "flight-named", "flight-custom", "oracle-top", "oracle-bottom"}
NORMAL = {"increase_contrast", "reduce_motion", "reduce_transparency"}
FORMAT = {"bits_per_component": 16, "bits_per_pixel": 64, "bitmap_info_raw": 4353, "alpha_info_raw": 1,
          "byte_order_raw": 4096, "pixel_format_raw": 0, "float_components": True}
HALF = struct.Struct("<e")
WORD = struct.Struct("<H")
PIXEL_BITS = struct.Struct("<4H")


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def integer(value, label, minimum=0):
    require(type(value) is int and value >= minimum, "Invalid integer " + label)
    return value


def finite_nonnegative(value, label):
    require(type(value) in (int, float) and math.isfinite(value) and value >= 0, "Invalid monotonic time " + label)
    return value


def load_json(path):
    require(path.stat().st_size <= MAX_REPORT_BYTES, "Report/spec exceeds bounded JSON size")
    return decode_json(path.read_bytes())


def decode_json(data):
    return json.loads(data, parse_constant=lambda v: (_ for _ in ()).throw(ValueError("Nonfinite JSON literal " + v)))


def relative_file(parent, value):
    require(isinstance(value, str), "Record file is not a string")
    path = Path(value)
    require(not path.is_absolute() and value and ".." not in path.parts, "Unsafe fixture-relative file path")
    original = parent / path
    require(not original.is_symlink(), "Symlink raw/PNG input is unsupported")
    resolved = original.resolve()
    require(parent == resolved.parent or parent in resolved.parents, "Input escapes report directory")
    require(resolved.is_file(), "Missing retained input file: " + str(resolved))
    return resolved


def bit_value(bits):
    return HALF.unpack(WORD.pack(bits))[0]


def channel_summary(histogram):
    count = sum(histogram.values())
    finite = [(bit_value(bits), n) for bits, n in histogram.items() if (bits & 0x7c00) != 0x7c00]
    finite_count = sum(n for _, n in finite)
    nan_count = sum(n for bits, n in histogram.items() if (bits & 0x7c00) == 0x7c00 and (bits & 0x03ff))
    bits = sorted(histogram)
    digest = hashlib.sha256()
    for value in bits:
        digest.update(struct.pack("<HI", value, histogram[value]))
    values = [v for v, _ in finite]
    return {
        "sample_count": count,
        "finite_numeric_min": min(values) if values else None,
        "finite_numeric_mean": math.fsum(v * n for v, n in finite) / finite_count if finite_count else None,
        "finite_numeric_max": max(values) if values else None,
        "finite_count": finite_count, "nan_count": nan_count,
        "positive_infinity_count": histogram.get(0x7c00, 0),
        "negative_infinity_count": histogram.get(0xfc00, 0),
        "numeric_less_than_zero_count": sum(n for b, n in histogram.items() if bit_value(b) < 0),
        "numeric_greater_than_one_count": sum(n for b, n in histogram.items() if bit_value(b) > 1),
        "numeric_equal_one_count": histogram.get(0x3c00, 0),
        "positive_zero_bits_count": histogram.get(0x0000, 0),
        "negative_zero_bits_count": histogram.get(0x8000, 0),
        "unique_uint16_bit_pattern_count": len(bits),
        "all_unique_bits_hex_if_at_most_64": [f"0x{b:04x}" for b in bits] if len(bits) <= 64 else None,
        "first_32_sorted_unique_bits_hex": [f"0x{b:04x}" for b in bits[:32]],
        "full_bit_histogram_sha256": digest.hexdigest(),
        "histogram_hash_encoding": "Sorted pairs of uint16LE bits and uint32LE exact count; not a numeric quantization",
    }


def summarize_region(data, width, height, bytes_per_row, box):
    x0, y0, x1, y1 = box
    require(0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height, "Region outside retained pixel rows")
    require(len(data) == bytes_per_row * height and bytes_per_row >= width * 8 and bytes_per_row % 2 == 0,
            "Invalid exact binary length/stride")
    histograms = [Counter() for _ in range(4)]
    view = memoryview(data)
    for y in range(y0, y1):
        start = y * bytes_per_row + x0 * 8
        for pixel in PIXEL_BITS.iter_unpack(view[start:y * bytes_per_row + x1 * 8]):
            for channel, bits in enumerate(pixel):
                histograms[channel][bits] += 1
    count = (x1 - x0) * (y1 - y0)
    return {"raw_storage_box_half_open": list(box), "pixel_count": count,
            "RGBA": {name: channel_summary(hist) for name, hist in zip("RGBA", histograms)},
            "alpha_all_numeric_exactly_one": histograms[3].get(0x3c00, 0) == count,
            "alpha_one_uint16_bits": "0x3c00"}


def mapped_box(rect, size, source_size):
    def exact(value, actual, source):
        require(type(value) is int, "Atlas source rectangle is not integer")
        product = value * actual
        require(product % source == 0, "Fractional atlas boundary; no rounding/resampling allowed")
        return product // source
    x0 = exact(rect["x"], size[0], source_size[0])
    x1 = exact(rect["x"] + rect["width"], size[0], source_size[0])
    y0 = exact(rect["y"], size[1], source_size[1])
    y1 = exact(rect["y"] + rect["height"], size[1], source_size[1])
    return x0, y0, x1, y1


def coordinate_candidates(spec, width, height):
    regions = {p["name"]: p["interior_source_rect"] for p in spec["patches"]}
    regions["gray-ramp"] = spec["ramp"]["interior_source_rect"]
    top = {name: mapped_box(rect, (width, height), spec["source_size"]) for name, rect in regions.items()}
    bottom = {name: (box[0], height - box[3], box[2], height - box[1]) for name, box in top.items()}
    return {"top-down": top, "bottom-up": bottom}


def validate_runtime(report):
    require(report.get("success") is True and report.get("completed_phases") == 2, "Actual endpoint run did not succeed")
    match = re.search(r"(\d+)\.", str(report.get("os", "")))
    require(match and int(match.group(1)) in (13, 14), "Actual OS must identify macOS13/14")
    major = int(match.group(1))
    for key in ("expected_os_major", "actual_os_major"):
        if key in report:
            require(type(report[key]) is int and report[key] == major, "OS contract mismatch")
    require(report.get("cache_unchanged") is True and report["cache_before"] == report["cache_after"], "Cache changed")
    require(type(report.get("activation_calls")) is int and report["activation_calls"] == 0, "Unexpected activation call count")
    require(type(report.get("metal_count_before_cleanup")) is int and report["metal_count_before_cleanup"] == 0, "Unexpected MTKView count")
    require(report.get("image_equality_collection_gate") is False, "Image equality must not select collection success")
    front = integer(report.get("frontmost_before"), "frontmost_before", 1)
    require(report.get("frontmost_after") == front, "Foreground changed")
    for name in ("normal_before", "normal_after"):
        flags = report.get(name)
        require(isinstance(flags, dict) and set(flags) == NORMAL and all(v is False for v in flags.values()), "Normal flags failed")
    captures, samples = report["captures"], report["samples"]
    require(len(captures) == 2 and [c["phase"] for c in captures] == list(PHASES), "Need both original phase captures")
    require(isinstance(samples, list) and 1 <= len(samples) <= 256, "Unexpected sample count")
    owner = integer(captures[0]["owner_pid"], "owner_pid", 1)
    window = integer(captures[0]["window_id"], "window_id", 1)
    for sample in samples + captures:
        require(sample.get("owner_pid") == owner and sample.get("window_id") == window and sample.get("frontmost_pid") == front,
                "Own window/owner/foreground identity changed")
        require(sample.get("key") is False and sample.get("active") is False and
                type(sample.get("live_metal_count")) is int and sample["live_metal_count"] == 0, "Window/MTKView contract failed")
        manager = sample["manager"]
        require(type(manager.get("flight_count")) is int and manager["flight_count"] == 0 and manager.get("timer_exists") is False,
                "Flight/timer contract failed")
    for capture in captures:
        integer(capture["consecutive_equal_buffers"], "stable raw buffers", 5)
        require(set(capture["rois"]) == ROI_NAMES, "Unexpected six-pane geometry")
        for roi in capture["rois"].values():
            points = roi["host_top_left_points"]
            require(points["width"] == 320 and points["height"] == 180, "Actual pane is not320x180pt")
    return major


def validate_record(record, observation, parent):
    require(record["key"] == observation["key"] and record["export_stage"] == "after_existing_window_teardown", "Wrong record identity/stage")
    for field, value in FORMAT.items():
        require(type(record[field]) is type(value) and record[field] == value, "Unsupported raw format field " + field)
    width = integer(record["width"], "width", 1)
    height = integer(record["height"], "height", 1)
    require((width, height) in ((640, 360), (320, 180)), "Unsupported actual snapshot size")
    row = integer(record["bytes_per_row"], "bytes_per_row", width * 8)
    require(row % 2 == 0, "Odd uint16 row stride")
    length = integer(record["byte_count"], "byte_count", 1)
    require(length == row * height and length <= MAX_RAW_BYTES, "Byte count is not exact stride*height or exceeds budget")
    for field in ("width", "height", "bytes_per_row", *FORMAT):
        require(observation.get(field) == record[field] and type(observation.get(field)) is type(record[field]), "Raw/deferred descriptor mismatch " + field)
    require(observation.get("color_space_metadata_stage") == "after_existing_window_teardown", "Color metadata was not deferred")
    require(observation.get("color_space_present") is True and observation.get("icc_present") is True, "Snapshot ICC context is missing")
    profile = base64.b64decode(observation["icc_base64"], validate=True)
    require(0 < len(profile) <= 65536 and len(profile) == observation["icc_byte_count"] and sha(profile) == observation["icc_sha256"], "Snapshot ICC export hash/length mismatch")
    path = relative_file(parent, record["file"])
    require(path.stat().st_size == length and re.fullmatch(r"[0-9a-f]{64}", record["sha256"] or ""), "Raw file size/SHA schema mismatch")
    data = path.read_bytes()
    require(sha(data) == record["sha256"], "Original raw file SHA mismatch")
    return path, data


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("report", type=Path)
    parser.add_argument("--output", type=Path, required=True, help="Fresh child directory of this analyzer workspace")
    parser.add_argument("--row-direction", choices=("unknown", "top-down", "bottom-up"), default="unknown")
    parser.add_argument("--orientation-evidence", type=Path, help="Independent direction evidence; never inferred from these colors")
    args = parser.parse_args()
    destination, report_path = args.output.resolve(), args.report.resolve()
    require(HERE in destination.parents and not destination.exists(), "Output must be a fresh child of this workspace")
    require(report_path.parent != destination and report_path.parent not in destination.parents, "Do not write into the runtime input tree")
    evidence = None
    if args.row_direction != "unknown":
        require(args.orientation_evidence is not None, "Known direction requires independently grounded evidence")
        ep = args.orientation_evidence.resolve()
        require(ep.is_file() and 0 < ep.stat().st_size <= 65536, "Missing or oversized independent direction evidence")
        evidence = {"path": str(ep), "bytes": ep.stat().st_size, "sha256": sha(ep.read_bytes()),
                    "scope": "Caller-supplied independent evidence. Script records provenance and cannot itself establish that evidence's truth."}
    else:
        require(args.orientation_evidence is None, "Unknown direction does not consume a direction-evidence assertion")
    require(report_path.stat().st_size <= MAX_REPORT_BYTES, "Report exceeds bounded JSON size")
    report_bytes = report_path.read_bytes()
    require(len(report_bytes) <= MAX_REPORT_BYTES, "Report grew beyond bounded JSON size")
    report = decode_json(report_bytes)
    major = validate_runtime(report)
    spec_path = HERE / "atlas-rois.json"
    require(sha(spec_path.read_bytes()) == ATLAS_SPEC_SHA256, "Frozen atlas coordinate specification changed")
    spec = load_json(spec_path)
    for source in spec["sources"]:
        item = report["cache_before"][source["png"]]
        require(item["file_sha256"] == source["png_sha256"] and item["orientation"] == "up", "Actual source ledger differs from frozen opaque/up atlas")
    capture = report["snapshot_float_capture"]
    require(capture.get("success") is True and capture.get("error") is None, "Raw float export failed")
    require(capture.get("selected") in ("off", "on"), "Invalid selected raw capture mode")
    require(capture.get("requested") in ((None, "off") if capture["selected"] == "off" else ("on",)), "Mode request/selection mismatch")
    require(integer(capture["primary_observation_count"], "primary count") == 2, "Ambiguous primary snapshot count")
    cleanup_count = integer(capture["cleanup_observation_count"], "cleanup count")
    require(cleanup_count <= 256, "Unbounded cleanup observation count")
    observations = report["snapshot_cgimage_observations"]
    require(len(observations) == 2 and {o["key"] for o in observations} == set(KEYS), "Need two unique actual primary deferred descriptors")
    require(report.get("snapshot_cgimage_observations_scope") == "before_existing_window_teardown", "Wrong primary observer scope")
    records = capture["records"]
    require(isinstance(records, list), "Raw records is not a list")
    if capture["selected"] == "off":
        require(records == [], "Off mode unexpectedly exported raw data")
    else:
        require(len(records) == 2 and [r["key"] for r in records] == list(KEYS), "Need unique named→custom raw records")
    declared_total = sum(integer(r["byte_count"], "declared byte_count", 1) for r in records)
    require(declared_total <= MAX_RAW_BYTES, "Declared total raw export exceeds4MiB before reading payloads")
    require(capture.get("export_stage") == "after_existing_window_teardown" and capture.get("row_direction") == "unverified", "Wrong source export stage/direction contract")
    require(integer(capture.get("maximum_total_raw_bytes"), "source raw budget") == MAX_RAW_BYTES and
            integer(capture.get("total_raw_bytes"), "source raw total") == declared_total,
            "Source raw budget/total does not match records")
    require(capture.get("primary_observation_keys") is not None and len(capture["primary_observation_keys"]) == 2 and
            set(capture["primary_observation_keys"]) == set(KEYS), "Wrong actual primary hook keys")
    require(type(capture.get("provider_copy_calls")) is int and capture["provider_copy_calls"] == len(records), "Wrong source provider-copy count")
    require(type(capture.get("fixture_retained_images_after_export")) is int and capture["fixture_retained_images_after_export"] == 0,
            "Source fixture reports retained images after export")
    require(type(capture.get("retained_primary_peak_count")) is int and capture["retained_primary_peak_count"] == len(records),
            "Source peak-retention count differs from mode")
    frozen_at = finite_nonnegative(capture["primary_frozen_at_uptime_seconds"], "primary frozen")
    released_at = finite_nonnegative(capture["released_at_uptime_seconds"], "released")
    require(released_at >= frozen_at, "Source release time precedes primary freeze")
    finite_nonnegative(capture["export_elapsed_seconds"], "source export elapsed")
    validated, raw_total, paths = [], 0, set()
    for record in records:
        retained_at = finite_nonnegative(record["retained_at_uptime_seconds"], "record retained")
        read_at = finite_nonnegative(record["provider_read_at_uptime_seconds"], "provider read")
        finite_nonnegative(record["export_elapsed_seconds"], "record export elapsed")
        require(retained_at <= frozen_at <= read_at <= released_at, "Source reported retain/freeze/provider/release ordering failed")
        for phase_capture in report["captures"]:
            actual = phase_capture["rois"][record["key"].removeprefix("baseline-")]["screenshot_pixels"]
            require(actual["width"] == record["width"] and actual["height"] == record["height"], "Raw snapshot size differs from actual native body ROI")
        observation = next(o for o in observations if o["key"] == record["key"])
        path, data = validate_record(record, observation, report_path.parent)
        require(path not in paths, "Two raw records alias one file")
        paths.add(path); raw_total += len(data)
        require(raw_total <= MAX_RAW_BYTES, "Total raw export exceeds4MiB budget")
        validated.append((record, observation, path, data))
    # Verify all retained native captures and all raw files before any numeric interpretation.
    pngs = []
    for c in report["captures"]:
        pp = relative_file(report_path.parent, c["png"])
        require(pp.stat().st_size <= 16 * 1024 * 1024 and sha(pp.read_bytes()) == c["png_sha256"], "Retained native PNG hash mismatch")
        pngs.append({"phase": c["phase"], "path": str(pp), "sha256": c["png_sha256"]})
    result = {"analysis_complete": True, "report": str(report_path), "report_sha256": sha(report_bytes),
        "analyzer_sha256": sha(Path(__file__).read_bytes()), "atlas_spec_sha256": sha(spec_path.read_bytes()),
        "actual_os_major": major, "runtime_validation_passed": True,
        "capture_mode": {k: v for k, v in capture.items() if k != "records"},
        "raw_byte_total": raw_total, "raw_byte_budget": MAX_RAW_BYTES, "retained_native_png_hashes": pngs,
        "row_direction": args.row_direction, "independent_orientation_evidence": evidence,
        "semantic_patch_values_emitted": args.row_direction != "unknown" and bool(records), "records": [],
        "context": {k: report[k] for k in ("os", "normal_before", "normal_after", "frontmost_before", "frontmost_after", "cache_unchanged", "window_seconds")},
        "capture_context": [{k: c[k] for k in ("phase", "capture_size", "capture_icc_sha256", "current_headroom", "potential_headroom")} for c in report["captures"]],
        "numeric_policy": "Original uint16LE payloads decoded as IEEE754 binary16, RGBA stored premultiplied-last. No clamp, unpremultiplication, color conversion, normalization, rescale, alignment, nits inference or automatic row flip. Min/mean/max use finite numbers only; NaN/Inf counts are separate; <0/>1 counts include infinities but exclude NaNs.",
        "limitations": ["Both row mappings are candidates until independently grounded. Whole-buffer differences cannot identify a semantic patch cause or bypass sampling/scaled-edge limits.",
            "Descriptor/ICC context and runtime booleans are retained-source claims, not repeated native measurements or a zero-observer-effect guarantee.",
            "No cross-host semantic patch comparison, expected-value fit, image correction or acceptance threshold is performed.",
            "Normal-after/teardown timing follows the preserved driver. Cleanup count is reported separately; raw exports cover only the two primary identities."]}
    for record, observation, path, data in validated:
        width, height, row = record["width"], record["height"], record["bytes_per_row"]
        candidates = coordinate_candidates(spec, width, height)
        padding = b"".join(data[y * row + width * 8:(y + 1) * row] for y in range(height))
        entry = {"raw_record": record, "resolved_file": str(path),
            "snapshot_ICC_context": {k: v for k, v in observation.items() if k != "icc_base64"},
            "whole_active_pixel_buffer": summarize_region(data, width, height, row, (0, 0, width, height)),
            "padding": {"byte_count": len(padding), "sha256": sha(padding), "excluded_from_pixel_channels": True},
            "candidate_coordinate_mappings_only": {name: {"status": "UNRESOLVED_CANDIDATE" if args.row_direction == "unknown" else "CANDIDATE_COORDINATES_ONLY",
                "raw_storage_boxes_half_open": boxes} for name, boxes in candidates.items()}}
        if args.row_direction != "unknown":
            entry["grounded_direction_patch_and_ramp_statistics"] = {name: summarize_region(data, width, height, row, box)
                for name, box in candidates[args.row_direction].items()}
        result["records"].append(entry)
    require(sha(report_path.read_bytes()) == sha(report_bytes), "Original runtime report changed during analysis")
    for record, _, path, _ in validated:
        require(path.stat().st_size == record["byte_count"] and sha(path.read_bytes()) == record["sha256"], "Original raw export changed during analysis")
    encoded_result = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + "\n"
    require(len(encoded_result.encode()) <= 512 * 1024, "Bounded report exceeds512KiB; no per-pixel/histogram dump allowed")
    destination.mkdir()
    (destination / "analysis.json").write_text(encoded_result)
    print(json.dumps({"analysis_complete": True, "selected": capture["selected"], "records": len(records),
        "raw_byte_total": raw_total, "row_direction": args.row_direction,
        "semantic_patch_values_emitted": result["semantic_patch_values_emitted"], "output": str(destination)}, indent=2))


if __name__ == "__main__":
    try:
        main()
    except (ValueError, KeyError, TypeError, OSError, struct.error) as error:
        print("Raw float analysis rejected input: " + str(error), file=sys.stderr)
        sys.exit(1)
