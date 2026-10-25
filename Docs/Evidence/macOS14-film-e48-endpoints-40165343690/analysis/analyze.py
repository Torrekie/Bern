#!/usr/bin/env python3
"""Read-only fixed e48 Film actual14 export; no artifact code execution."""
import argparse
import hashlib
import json
import math
from pathlib import Path

from PIL import Image, __version__ as pillow_version

SOURCE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
HARNESS = "2cff19aad748ac673fefda921b313886bb902e4b"
COLLECTOR = "6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635"
WORKFLOW = "a3fc84219a34af446802b8865837f6efcdf1590b9a5ab647c0dcf2cadd270102"
RESULT = "54b06d51178cf8e57d947c2de193f837b36ab0a52fa0e341357f0d6972cba0bf"
GUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c"
CLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
NAMES = ["Gingham", "Tartan", "Madras", "Glen", "Houndstooth", "Windowpane"]


def digest(data):
    return hashlib.sha256(data).hexdigest()


def export(artifact, preparation, output):
    artifact = artifact.resolve(strict=True)
    preparation = preparation.resolve(strict=True)
    output = output.resolve()
    assert not output.exists()
    assert all(output != p and output not in p.parents and p not in output.parents
               for p in [artifact, preparation])
    output.mkdir(parents=True)
    try:
        paths = sorted(p for p in artifact.rglob("*") if p.is_file())
        inputs = {str(p.relative_to(artifact)): {"bytes": p.stat().st_size,
                  "sha256": digest(p.read_bytes())} for p in paths}
        assert len(inputs) == 83
        assert inputs["result.json"]["sha256"] == RESULT
        assert inputs["gallery-film-probe.swift"]["sha256"] == COLLECTOR
        assert digest((preparation / "gallery-film-probe.swift").read_bytes()) == COLLECTOR
        assert digest((preparation / "macos14-film-probe.yml").read_bytes()) == WORKFLOW
        plan = json.loads((preparation / "plan.json").read_text())
        report = json.loads((artifact / "result.json").read_text())
        download_path = Path(str(artifact) + ".download.json")
        download = json.loads(download_path.read_text())
        assert download["api_digest_verified"] is True
        assert download["outer_zip_digest"] == download["artifact"]["digest"]
        assert download["run_id"] == "40165343690" and download["zip_member_count"] == 83
        assert download["archive_deleted"] is True
        assert report["success"] is True and report["source_sha"] == SOURCE
        assert report["harness_sha"] == HARNESS and report["expected_os_major"] == 14
        assert report["os"] == "Version 14.8.9 (Build 23J631)"
        assert report["variant"] == "port" and report["requested_scenario"] == "direct"
        assert report["followup_sequence"] == "last-resize"
        assert report["observation_mode"] == "active" and report["appearance_profile"] == "normal"
        assert report["system_preferences"] == dict(increase_contrast=False, reduce_motion=False,
                                                     reduce_transparency=False)
        assert report["accessibility_trusted"] is True and report["screen_recording_preflight"] is True
        assert report["displays"] == [{"frame_points": "{{0, 0}, {1920, 1080}}", "scale": 1}]
        assert report["inactive_capture_samples"] == []
        environment = (artifact / "environment.txt").read_text()
        assert "source_sha=" + SOURCE in environment and "observer_sha=" + HARNESS in environment
        assert "build_run=40070407306" in environment and GUI in environment and CLI in environment
        assert "Xcode 15.4" in environment and "Apple Swift version 5.10" in environment
        assert "Target: arm64-apple-macosx14.0" in environment
        build = json.loads((artifact / "build.json").read_text())
        assert build["architecture"] == "arm64" and build["minimum_macos"] == "13.0"
        assert build["app_bundle"] == "Gallery.app" and build["ui"] == "swiftui-modern"
        assert len(report["cases"]) == 1
        case = report["cases"][0]
        assert case["pid"] == 6547 and case["scenario"] == "direct"
        assert "internal_trace" not in case and "film_after_trace" not in case
        assert [s["stage"] for s in case["followup_stages"]] == plan["expected_sequence"][1:]
        ready = report["startup_readiness"]
        assert len(ready) == 1 and ready[0]["pid"] == case["pid"]
        own = ready[0]["samples"][-1]["own_native_window"]
        assert own["kCGWindowOwnerPID"] == case["pid"]
        assert own["kCGWindowIsOnscreen"] is True and own["kCGWindowAlpha"] == 1
        assert len(report["activation_requests"]) == 1
        assert report["activation_requests"][0]["after"]["front_pid"] == case["pid"]
        # Allow the recorded failed sessions startup poll; later commands must succeed.
        assert all(c["status"] == 0 or c["arguments"] == ["sessions"] for c in report["commands"])
        activations = [c["arguments"][-1] for c in report["commands"]
                       if "activate" in c["arguments"] and c["arguments"][-1].startswith("film.")]
        assert activations == ["film.to_last", "film.to_first", "film.to_last"]
        assert not any("set-bool" in c["arguments"] for c in report["commands"])
        stages = [("initial", case["film"], case["settled_ax"], None, case["controls"], None)]
        stages += [(s["stage"], s["capture"], s["ax"], s["action_start_uptime"],
                    s["controls"], s["windows"]) for s in case["followup_stages"]]
        geometry = []
        for index, (name, capture, ax, action, controls, windows) in enumerate(stages):
            bounds = capture["bounds_points"]
            assert [bounds["Width"], bounds["Height"]] == plan["outer_sizes"][index]
            assert capture["pixels"] == [bounds["Width"], bounds["Height"]]
            assert capture["equal_comparisons"] >= 4 and capture["samples"] >= 5
            assert ax["truncated"] is False and ax["matching_elements_missing"] is False
            images = [e for e in ax["elements"] if e["role"] == "AXImage"]
            assert len(images) == 6 and {e["text"] for e in images} == set(NAMES)
            assert all(sum(e["text"] == name for e in images) == 1 for name in NAMES)
            by_name = {e["text"]: e for e in images}
            rows = []
            for label in NAMES:
                element = by_name[label]
                frame = element["frame"]
                assert all(math.isfinite(frame[k]) for k in ["x", "y", "width", "height"])
                relative = [frame["x"] - bounds["X"], frame["y"] - bounds["Y"],
                            frame["width"], frame["height"]]
                rows.append({"label": label, "original_ax_element": element,
                             "relative_to_original_outer_xywh_points": relative})
            maximum = max(e["frame"]["width"] for e in images)
            values = {c["target"]: c for c in controls}
            assert values["main_window.pages"]["value"] == "Film"
            assert values["film.to_first"]["enabled"] is True and values["film.to_last"]["enabled"] is True
            if windows is not None:
                assert len(windows) == 1 and windows[0]["frame"] == {
                    "x": bounds["X"], "y": bounds["Y"], "width": bounds["Width"], "height": bounds["Height"]}
            geometry.append({"stage": name, "original_capture": capture,
                             "original_action_start_uptime": action,
                             "original_terminal_ax": ax, "original_controls": controls,
                             "original_windows": windows, "images": rows,
                             "maximum_width_points": maximum,
                             "maximum_width_labels": [e["text"] for e in images if e["frame"]["width"] == maximum]})
        pngs = {}
        for p in sorted(artifact.glob("*.png")):
            with Image.open(p) as image:
                image.load()
                icc = image.info.get("icc_profile")
                assert isinstance(icc, bytes) and icc
                pngs[p.name] = {**inputs[p.name], "format": image.format, "mode": image.mode,
                               "size_pixels": list(image.size), "icc_bytes": len(icc),
                               "icc_sha256": digest(icc),
                               "decoded_stored_pixel_bytes_sha256": digest(image.tobytes()),
                               "interpretation": "Pillow decoded stored mode; no ICC conversion, ROI, scale change or normalization"}
        assert set(pngs) == {case["patterns"]["png"], *(s[1]["png"] for s in stages)}
        assert len({v["icc_sha256"] for v in pngs.values()}) == 1
        first_last = geometry[1]; repeated_last = geometry[3]
        deltas = []
        for a, b in zip(first_last["images"], repeated_last["images"]):
            deltas.append({"label": a["label"], "last_again_minus_first_last_relative_xywh_points":
                           [y - x for x, y in zip(a["relative_to_original_outer_xywh_points"],
                                                 b["relative_to_original_outer_xywh_points"])]})
        result = {"kind": "exact_e48_actual14_film_followup_offline_reference", "reference_requirements_met": True,
                  "run_id": "40165343690", "source_sha": SOURCE, "harness_sha": HARNESS,
                  "single_process_pid": case["pid"], "raw_report_context": {k: v for k, v in report.items() if k != "cases"},
                  "case_session": case["session"], "initial_patterns_capture": case["patterns"],
                  "original_first_second_ax": case["first_second_ax"], "stages": geometry,
                  "first_last_vs_last_again": {"exact_relative_frames_equal": all(all(v == 0 for v in r["last_again_minus_first_last_relative_xywh_points"]) for r in deltas),
                                               "all_six_deltas": deltas},
                  "pngs": pngs, "artifact_inputs": inputs,
                  "download_receipt": {"path": str(download_path), "sha256": digest(download_path.read_bytes()), "data": download},
                  "source_read_only": True, "software": {"pillow": pillow_version},
                  "limitations": ["AX measured after stable PNG; no simultaneous AX/pixel state claim.",
                                  "All six AXImage frames retained, including off-window coordinates; AXScrollArea is not used as clip.",
                                  "Stable4 compares original full provider buffers; no new geometric tolerance or settled-animation claim.",
                                  "Existing source stops App before attempting front restoration and reports no termination or front-before/after cleanup fields; no strong cleanup claim.",
                                  "CLI First/Last activations are not physical gestures or proof of internal target/binding writes.",
                                  "Exact e48 actual14 reference only; f9 is not substituted, no local13 or cross-OS acceptance/adoption."]}
        (output / "analysis.json").write_text(json.dumps(result, indent=2) + "\n")
        print(json.dumps({"reference_requirements_met": True, "stages": [
            {"stage": s["stage"], "max_width": s["maximum_width_points"], "labels": s["maximum_width_labels"]} for s in geometry],
            "first_last_equals_repeated_last": result["first_last_vs_last_again"]["exact_relative_frames_equal"],
            "png_count": len(pngs)}, indent=2))
    except BaseException as error:
        (output / "failure.json").write_text(json.dumps({"success": False, "error": type(error).__name__ + ": " + str(error)}, indent=2) + "\n")
        raise


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("artifact", type=Path)
    p.add_argument("preparation", type=Path)
    p.add_argument("output", type=Path)
    a = p.parse_args()
    export(a.artifact, a.preparation, a.output)
