#!/usr/bin/env python3
"""Tiny synthetic binary16/stride tests only; never a native runtime claim."""
import ast
import hashlib
import importlib.util
import json
from pathlib import Path
import struct

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location("float_analyzer_under_test", HERE / "analyze_float.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def rejected(call):
    try:
        call()
    except ValueError:
        return
    raise AssertionError("Expected explicit rejection")


def main():
    ast.parse((HERE / "analyze_float.py").read_text())
    assert hashlib.sha256((HERE / "atlas-rois.json").read_bytes()).hexdigest() == module.ATLAS_SPEC_SHA256
    assert module.bit_value(0x0001) == 2 ** -24 and module.bit_value(0x8001) == -(2 ** -24)
    assert module.bit_value(0x7bff) == 65504
    # Four artificial RGBA pixels, two rows, distinct NaN payloads and four padding bytes per row.
    row0 = struct.pack("<8H", 0x3c00, 0x4000, 0xbc00, 0x3c00,
                       0x8000, 0x7c00, 0x7e01, 0x3c00) + b"\xff\xff\xaa\xaa"
    row1 = struct.pack("<8H", 0x0000, 0xfc00, 0x3c00, 0x3c00,
                       0xc000, 0x3e00, 0x7fff, 0x3c00) + b"\x00\x7c\x01\x7e"
    data = row0 + row1
    result = module.summarize_region(data, 2, 2, 20, (0, 0, 2, 2))
    r, g, b, a = [result["RGBA"][c] for c in "RGBA"]
    assert r["finite_numeric_min"] == -2 and r["finite_numeric_max"] == 1
    assert r["finite_numeric_mean"] == -0.25 and r["sample_count"] == 4
    assert r["negative_zero_bits_count"] == r["positive_zero_bits_count"] == 1
    assert r["numeric_less_than_zero_count"] == 1
    assert g["positive_infinity_count"] == g["negative_infinity_count"] == 1
    assert g["finite_numeric_mean"] == 1.75 and g["numeric_greater_than_one_count"] == 3
    assert b["nan_count"] == 2 and b["finite_count"] == 2 and b["finite_numeric_mean"] == 0
    assert b["all_unique_bits_hex_if_at_most_64"] == ["0x3c00", "0x7e01", "0x7fff", "0xbc00"]
    assert a["unique_uint16_bit_pattern_count"] == 1 and result["alpha_all_numeric_exactly_one"] is True
    # Padding contains Inf/NaN bit patterns, which must not become active-pixel samples.
    assert sum(result["RGBA"][c]["sample_count"] for c in "RGBA") == 16
    rejected(lambda: module.summarize_region(data[:-1], 2, 2, 20, (0, 0, 2, 2)))
    rejected(lambda: module.summarize_region(data, 2, 2, 15, (0, 0, 2, 2)))
    atlas = module.load_json(HERE / "atlas-rois.json")
    maps640 = module.coordinate_candidates(atlas, 640, 360)
    maps320 = module.coordinate_candidates(atlas, 320, 180)
    assert maps640["top-down"]["white203"] == (8, 8, 120, 112)
    assert maps640["bottom-up"]["white203"] == (8, 248, 120, 352)
    assert maps320["top-down"]["gray-ramp"] == (2, 130, 318, 170)
    assert maps320["bottom-up"]["gray-ramp"] == (2, 10, 318, 50)
    rejected(lambda: module.mapped_box({"x": 1, "y": 0, "width": 1, "height": 1}, (320, 180), [640, 360]))
    rejected(lambda: module.decode_json(b'{"bad":NaN}'))
    wrong_format = {"key": module.KEYS[0], "export_stage": "after_existing_window_teardown", **module.FORMAT}
    wrong_format["bitmap_info_raw"] = 0
    rejected(lambda: module.validate_record(wrong_format, {"key": module.KEYS[0]}, HERE))
    json.dumps(result, allow_nan=False)
    print(json.dumps({"scope": "Synthetic 2x2 binary16 bit-pattern/row-padding and atlas integer-coordinate tests only; no captured report, UI, compiler, CI, native runtime or visual acceptance.",
        "passed": True, "tested": ["RGBA uint16LE channels", "binary16 subnormal/finite extrema", "negative zero distinct bits", "finite mean excludes NaN/Inf explicitly", "NaN payload uniqueness", "Inf and <0/>1 counters", "padding excluded", "truncated/short stride rejected", "top/bottom coordinate candidates", "fractional atlas boundary rejected", "nonfinite JSON literal rejected", "unsupported bitmap layout rejected before file access"],
        "analyzer_sha256": hashlib.sha256((HERE / "analyze_float.py").read_bytes()).hexdigest(),
        "test_source_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()}, indent=2))


if __name__ == "__main__":
    main()
