#!/usr/bin/env python3
"""One independent bit-tuple audit; does not import or run root's pipeline."""
from fractions import Fraction
from pathlib import Path
import datetime
import hashlib
import itertools
import json
import struct

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "review.json"
COMPACT = ROOT / "work/hero-snapshot-float-geometry-compact"
PNG = ROOT / "work/hero-snapshot-float-geometry-png"
BASE = ROOT / "outputs/Bern/Docs/Evidence/macOS14-hero-float-40091326190/same-binary-13-14"
digest = lambda data: hashlib.sha256(data).hexdigest()

def require(value, label):
    if not value:
        raise ValueError(label)

def box_for(rect, width, height, bottom):
    values = [Fraction(rect["x"] * width, 640), Fraction(rect["y"] * height, 360),
              Fraction((rect["x"] + rect["width"]) * width, 640),
              Fraction((rect["y"] + rect["height"]) * height, 360)]
    require(all(v.denominator == 1 for v in values), "fractional coordinate")
    x0, y0, x1, y1 = map(int, values)
    if bottom:
        y0, y1 = height - y1, height - y0
    require(0 <= x0 < x1 <= width and 0 <= y0 < y1 <= height, "box bounds")
    return [x0, y0, x1, y1]

def cut(rows, box):
    x0, y0, x1, y1 = box
    return [row[x0:x1] for row in rows[y0:y1]]

def distinct(region):
    return len(set(itertools.chain.from_iterable(region)))

def evaluate(rows, width, height, bottom, spec, policy):
    flat = []
    for patch in spec["patches"]:
        box = box_for(patch["interior_source_rect"], width, height, bottom)
        count = distinct(cut(rows, box))
        flat.append({"name": patch["name"], "box": box, "distinct_tuples": count, "pass": count == 1})
    bands = []
    for rect in policy["ramp_marker_bands_source_rects"]:
        box = box_for(rect, width, height, bottom)
        region = cut(rows, box)
        equal_rows = all(row == region[0] for row in region)
        bins = []
        for start, end in policy["ramp_bin_x_source_intervals"]:
            br = dict(x=start, y=rect["y"], width=end-start, height=rect["height"])
            bins.append(len(set(cut(rows, box_for(br, width, height, bottom))[0])))
        bands.append({"box": box, "row_count": len(region), "all_rows_equal": equal_rows,
                      "distinct_tuples": distinct(region), "bin_first_row_counts": bins,
                      "marker": equal_rows and all(n >= 2 for n in bins)})
    return {"pass": all(v["pass"] for v in flat) and [b["marker"] for b in bands] == [False, False, True],
            "flat": flat, "bands": bands}

require(not OUT.exists(), "refuse prior review output")
old = (PNG / "structure.py").read_bytes()
new = (COMPACT / "structure.py").read_bytes()
before = b"json.dumps(result,indent=2,sort_keys=True,allow_nan=False)"
after = b"json.dumps(result,separators=(',',':'),sort_keys=True,allow_nan=False)"
require(old.count(before) == 1 and old.replace(before, after) == new, "non-serialization script change")
unchanged = {}
for name in ("policy.json", "atlas-rois.json", "analyze_float.py", "parser-api-notes.md"):
    left = (PNG / name).read_bytes(); right = (COMPACT / name).read_bytes()
    require(left == right, "changed shared input " + name)
    unchanged[name] = digest(right)
policy = json.loads((COMPACT / "policy.json").read_bytes())
spec = json.loads((COMPACT / "atlas-rois.json").read_bytes())
proof_bytes = (COMPACT / "result/geometry.json").read_bytes()
proof = json.loads(proof_bytes)
require(proof.get("complete") is True and proof.get("all4_directions_unique") is True, "root not complete")
records = []
for major in (13, 14):
    report_path = BASE / f"runtime{major}/on/report.json"
    report_bytes = report_path.read_bytes(); report = json.loads(report_bytes)
    for exported in report["snapshot_float_capture"]["records"]:
        width, height, stride = (exported[k] for k in ("width", "height", "bytes_per_row"))
        require(stride == width * 8 and exported["byte_count"] == stride * height, "not tight four-word raster")
        require((exported["bits_per_component"], exported["bits_per_pixel"], exported["bitmap_info_raw"],
                 exported["alpha_info_raw"], exported["byte_order_raw"], exported["pixel_format_raw"],
                 exported["float_components"]) == (16, 64, 4353, 1, 4096, 0, True), "format changed")
        raw_path = report_path.parent / exported["file"]
        blob = raw_path.read_bytes(); actual_sha = digest(blob)
        require(len(blob) == exported["byte_count"] and actual_sha == exported["sha256"], "raw identity")
        require(proof["inputs"][str(raw_path.relative_to(ROOT))]["sha256"] == actual_sha, "root raw identity")
        # Four integer words preserve complete pixel bits; no half-float or RGB values are interpreted.
        pixels = tuple(struct.iter_unpack("<4H", blob))
        rows = [pixels[y*width:(y+1)*width] for y in range(height)]
        root_record = next(r for r in proof["records"] if r["actual_os_major"] == major and r["key"] == exported["key"])
        directions = {}
        for direction, bottom in (("top-down", False), ("bottom-up", True)):
            got = evaluate(rows, width, height, bottom, spec, policy)
            expected = next(c for c in root_record["candidates"] if c["direction"] == direction)
            require(got["pass"] == expected["pass"], "candidate result mismatch")
            for a, b in zip(got["flat"], expected["flat_interiors"]):
                require((a["name"], a["box"], a["distinct_tuples"], a["pass"]) ==
                        (b["source_region_name_as_geometry_label"], b["raw_box_half_open"], b["distinct_complete_pixel_tuples"], b["pass"]), "flat mismatch")
            for a, b in zip(got["bands"], expected["three_fixed_bands"]):
                require((a["box"], a["row_count"], a["all_rows_equal"], a["distinct_tuples"], a["bin_first_row_counts"], a["marker"]) ==
                        (b["raw_box_half_open"], b["row_count"], b["all_rows_bit_identical"], b["whole_band_distinct_complete_tuples"],
                         [v["first_row_distinct_complete_tuples"] for v in b["bins"]], b["ramp_marker_pass"]), "band mismatch")
            directions[direction] = got
        winners = [k for k, v in directions.items() if v["pass"]]
        require(winners == [root_record["selected_direction"]] and len(winners) == 1, "unique direction mismatch")
        records.append({"host": major, "key": exported["key"], "raw_path": str(raw_path.relative_to(ROOT)),
                        "raw_bytes": len(blob), "raw_sha256": actual_sha, "size": [width, height],
                        "report_sha256": digest(report_bytes), "selected_direction": winners[0], "directions": directions})
        del rows, pixels, blob
require(len(records) == 4, "four raw records required")
result = {"complete": True, "all4_unique_top_down": all(r["selected_direction"] == "top-down" for r in records),
          "records": records, "root_geometry": {"path": str((COMPACT / 'result/geometry.json').relative_to(ROOT)),
          "bytes": len(proof_bytes), "sha256": digest(proof_bytes)},
          "serialization_review": {"only_one_json_whitespace_substitution": True, "png_script_sha256": digest(old),
          "compact_script_sha256": digest(new), "unchanged_shared_inputs": unchanged},
          "method": "Independent Fraction coordinates and struct.iter_unpack(<4H) complete-word tuple matrices; no root module import or pipeline execution, no float/color interpretation.",
          "source_PNG_decode_and_original_native_gates": "Not rerun; this independent audit covers raw geometry and compact-only serialization difference.",
          "numeric_or_RGBA_patch_values_emitted": False, "checker_sha256": digest(Path(__file__).read_bytes()),
          "completed_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
require((COMPACT / "result/geometry.json").read_bytes() == proof_bytes, "root proof changed")
OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({"complete": result["complete"], "all4_unique_top_down": result["all4_unique_top_down"],
                  "root_geometry_sha256": digest(proof_bytes), "records": [{"host": r["host"], "key": r["key"],
                  "reverse_flat_counts": [x["distinct_tuples"] for x in r["directions"]["bottom-up"]["flat"]]} for r in records]}, indent=2))
