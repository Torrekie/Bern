"""Read frozen capture evidence; write only this derived pixels directory.

Run with Python, Pillow and NumPy. No UI, app/CLI execution, image resampling,
alignment, colour conversion, compilation, network access or raw-file writes.
"""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import platform

import numpy as np
import PIL
from PIL import Image, ImageCms


HERE = Path(__file__).resolve().parent
RAW = HERE.parents[1] / "capture-pair"
STAGES = ["00-buttons.png", "01-text.png", "02-controls.png", "03-buttons.png"]


def sha(data):
    return hashlib.sha256(data).hexdigest()


def inventory():
    return {p.relative_to(RAW).as_posix(): sha(p.read_bytes())
            for p in sorted(RAW.rglob("*")) if p.is_file()}


def check_manifest(current):
    expected = {}
    for line in (RAW / "SHA256SUMS").read_text().splitlines():
        digest, relative = line.split("  ", 1)
        assert relative not in expected
        expected[relative] = digest
    assert set(expected) == set(current) - {"SHA256SUMS"}
    assert all(current[name] == digest for name, digest in expected.items())
    return len(expected)


def png_data(path):
    raw = path.read_bytes()
    with Image.open(BytesIO(raw)) as im:
        im.load()
        assert im.mode == "RGBA"
        arr = np.asarray(im).copy()
        icc = im.info.get("icc_profile", b"")
        exif = im.info.get("exif", b"")
        profile = ImageCms.ImageCmsProfile(BytesIO(icc)) if icc else None
        meta = dict(file_bytes=len(raw), file_sha256=sha(raw), format=im.format,
            mode=im.mode, size_pixels=list(im.size), decoded_rgba_sha256=sha(arr.tobytes()),
            info_keys=sorted(im.info), icc_bytes=len(icc), icc_sha256=sha(icc) if icc else None,
            icc_profile_name=ImageCms.getProfileName(profile).strip() if profile else None,
            icc_profile_description=ImageCms.getProfileDescription(profile).strip() if profile else None,
            exif_bytes=len(exif), exif_sha256=sha(exif) if exif else None,
            alpha_values=np.unique(arr[:, :, 3]).tolist())
    return raw, arr, meta


def compare(a, b):
    assert a.shape == b.shape
    diff = np.abs(a.astype(np.int16) - b.astype(np.int16))
    changed = np.any(diff != 0, axis=2)
    yy, xx = np.where(changed)
    bbox = None if not changed.any() else [int(xx.min()), int(yy.min()), int(xx.max()+1), int(yy.max()+1)]
    return dict(decoded_rgba_equal=not bool(changed.any()), total_pixels=int(changed.size),
        different_pixels=int(changed.sum()), different_pixel_fraction=float(changed.mean()),
        different_rgb_pixels=int(np.any(diff[:, :, :3] != 0, axis=2).sum()),
        different_alpha_pixels=int((diff[:, :, 3] != 0).sum()),
        diff_bbox_pixels_ltrb_exclusive=bbox,
        mae_rgba=float(diff.mean()), mae_rgb=float(diff[:, :, :3].mean()),
        mae_channels_rgba=[float(x) for x in diff.mean(axis=(0, 1))],
        max_channel_difference=int(diff.max()),
        max_difference_channels_rgba=[int(x) for x in diff.max(axis=(0, 1))])


before = inventory()
manifest_count = check_manifest(before)
runtime = {side: json.loads((RAW / side / "runtime/result.json").read_text()) for side in "AB"}
locks = json.loads((RAW / "run-locks.json").read_text())
summary = json.loads((RAW / "summary.json").read_text())
assert summary["success"] is True
report = dict(schema=1, analysis="Four same-host corresponding A/B PNG pairs only",
    raw_root=str(RAW), software=dict(python=platform.python_version(), pillow=PIL.__version__, numpy=np.__version__),
    method=dict(comparison="Direct decoded RGBA channel values and entire PNG bytes",
        channel_range=[0, 255], mae_denominator="All pixels times stated channel count",
        bbox="PNG top-left origin; left/top inclusive, right/bottom exclusive; null when no differing pixel",
        colour_management="No ICC transform applied; embedded ICC blobs are inspected and hashed",
        transformations="No alignment, crop, resampling, compositing or premultiplication"),
    scope="Recorded active macOS13 A/B snapshots only; effective Light appearance was not asserted by the collector. No native-frame, 13-vs14, physical-input or colour-acceptance verdict.",
    raw_integrity=dict(manifest_entries=manifest_count, original_manifest_sha256=before["SHA256SUMS"]),
    source_inputs={key: value for key, value in before.items() if key in {
        "A/runtime/result.json", "B/runtime/result.json", "run-locks.json", "summary.json", "observer.swift", "SHA256SUMS"}
        or key.endswith(".png")},
    capture_context={}, pairs=[])

for side, data in runtime.items():
    assert data["success"] is True and len(data["stages"]) == 4
    report["capture_context"][side] = dict(source_sha=data["source_sha"],
        locked_gui_sha256=locks[side]["gui_sha256"], locked_cli_sha256=locks[side]["cli_sha256"],
        pid=data["pid"], bundle_identifier=data["bundle_identifier"], session=data["session"],
        os=data["os"], expected_os_major=data["expected_os_major"], displays=data["displays"],
        scope=data["scope"], app_environment_overrides=data["app_environment_overrides"],
        accessibility_trusted=data["accessibility_trusted"], screen_recording_preflight=data["screen_recording_preflight"],
        normal_profile_start=data["normal_profile_start"], normal_profile_end=data["normal_profile_end"])

for index, name in enumerate(STAGES):
    loaded = {side: png_data(RAW / side / "runtime" / name) for side in "AB"}
    pair = dict(index=index, png=name,
        png_file_bytes_equal=loaded["A"][0] == loaded["B"][0],
        icc_bytes_equal=loaded["A"][2]["icc_sha256"] == loaded["B"][2]["icc_sha256"],
        metrics=compare(loaded["A"][1], loaded["B"][1]), images={}, captures={})
    for side in "AB":
        stage = runtime[side]["stages"][index]
        capture = stage["capture"]
        assert capture["png"] == name
        bounds = capture["own_window"]["kCGWindowBounds"]
        pair["images"][side] = loaded[side][2]
        pair["captures"][side] = dict(option=stage["option"], expected_window_title=stage["expected_window_title"],
            window_bounds_points=bounds, pixels=capture["pixels"],
            measured_pixel_per_point=[capture["pixels"][0] / bounds["Width"], capture["pixels"][1] / bounds["Height"]],
            own_window=capture["own_window"], sample_count=capture["sample_count"],
            equal_comparisons=capture["equal_comparisons"], color_space_name=capture["color_space_name"],
            start_uptime=capture["start_uptime"], end_uptime=capture["end_uptime"],
            final_sample_image_metadata=capture["samples"][-1]["image_metadata"],
            final_sample_raw_buffer_bytes=capture["samples"][-1]["raw_buffer_bytes"],
            all_samples_geometry_equal=all(s["geometry_equal_during_capture"] for s in capture["samples"]),
            all_samples_own_front=all(s["front_before"]["front_pid"] == runtime[side]["pid"]
                and s["front_after"]["front_pid"] == runtime[side]["pid"] for s in capture["samples"]))
    report["pairs"].append(pair)

after = inventory()
assert before == after, "Frozen raw evidence changed while being read"
check_manifest(after)
report["raw_integrity"].update(all_manifest_entries_matched_before_and_after=True,
    all_raw_file_hashes_and_names_unchanged_during_analysis=True, raw_file_count=len(before))
report["aggregate"] = dict(pair_count=len(report["pairs"]),
    all_png_pairs_byte_identical=all(p["png_file_bytes_equal"] for p in report["pairs"]),
    all_decoded_pairs_pixel_identical=all(p["metrics"]["decoded_rgba_equal"] for p in report["pairs"]),
    all_icc_blobs_same=len({p["images"][s]["icc_sha256"] for p in report["pairs"] for s in "AB"}) == 1)
(HERE / "metrics.json").write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")
print(json.dumps(dict(aggregate=report["aggregate"], raw_integrity=report["raw_integrity"],
    pairs=[dict(png=p["png"], **p["metrics"]) for p in report["pairs"]]), indent=2))
