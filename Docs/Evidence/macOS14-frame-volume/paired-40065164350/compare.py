"""Offline comparison of the paired original PNGs and public AX geometry. No UI interaction."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import numpy as np
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent
NAMES = ["frame-closed-light", "frame-open-light", "volume-popover-light"]
STAGES = [n + "-stable" for n in NAMES] + ["dismissed"]
sha = lambda data: hashlib.sha256(data).hexdigest()

def load(path):
    image = Image.open(path)
    icc = image.info["icc_profile"]
    srgb = ImageCms.profileToProfile(image.convert("RGB"), ImageCms.ImageCmsProfile(BytesIO(icc)),
                                    ImageCms.createProfile("sRGB"), renderingIntent=1, outputMode="RGB")
    return np.array(image.convert("RGBA")), np.array(srgb), icc

def metrics(a, b):
    assert a.shape == b.shape
    delta = np.abs(a.astype(np.int16) - b.astype(np.int16))
    mask = np.any(delta, axis=2)
    ys, xs = np.nonzero(mask)
    return {"equal": not bool(mask.any()), "changed_pixels": int(mask.sum()),
            "changed_fraction": float(mask.mean()), "mean_absolute_channel_error_255": float(delta.mean()),
            "maximum_channel_error_255": int(delta.max()),
            "changed_bbox_pixels": [int(xs.min()), int(ys.min()), int(xs.max()+1), int(ys.max()+1)] if len(xs) else None}

reports = {side: json.loads((ROOT/side/"report.json").read_text()) for side in ["a", "b"]}
result = {"run_id": 40065164350, "scope": "A and B on the same macOS 14 runner, light only, 1 pixel/point; no macOS 13 or physical-input verdict",
          "pixel_method": "Unscaled original RGBA plus ICC-to-sRGB RGB conversion (relative colorimetric); no alignment or exclusion in whole-image results",
          "captures": {}, "geometry": {}, "runtime_checks": {}}
for side, report in reports.items():
    assert report["success"] is True
    assert all(report[k] for k in ["accessibility_trusted", "screen_recording", "post_event_access"])
    for c in report["window_array_checks"]:
        assert c["exact_ids_and_owner"] is True
        assert sorted(c["requested_ids"]) == sorted(d["kCGWindowNumber"] for d in c["descriptions"])
        assert all(d["kCGWindowOwnerPID"] == c["own_pid"] for d in c["descriptions"])
    assert all(e["sent"] and e["window_id"] == e["nsevent_window_number"] == e["roundtrip_nsevent_window_number"] for e in report["heartbeat_events"])
    captures = {c["png"]: c for c in report["captures"]}
    assert [len(captures[n+".png"]["window_ids"]) for n in NAMES] == [1,2,1]
    assert set(captures[NAMES[1]+".png"]["window_ids"]) == set(captures[NAMES[0]+".png"]["window_ids"] + captures[NAMES[2]+".png"]["window_ids"])
    for n in NAMES:
        c = captures[n+".png"]
        assert c["stable_equal_comparisons"] >= 4 and c["samples"] >= 5
        assert sha((ROOT/side/(n+".png")).read_bytes()) == c["png_sha256"]
        _, _, icc = load(ROOT/side/(n+".png")); assert sha(icc) == c["icc_sha256"]
    stable = [s for s in report["stages"] if s["stage"] in STAGES]
    assert len(stable) == 4
    assert all(s["media"]["phase"] == "Paused" and s["media"]["position_ms"] == 0 and s["media"]["source_version"] == 1 for s in stable)
    end = stable[-1]; assert end["stage"] == "dismissed"
    assert not any(c["target"].endswith(".volume_level") for c in end["controls"])
    assert next(c for c in end["controls"] if c["target"] == "frame.volume")["value"] == "closed"
    result["runtime_checks"][side] = {"success": True, "heartbeat_events": len(report["heartbeat_events"]),
        "window_array_roundtrips": len(report["window_array_checks"]), "awake_checks": len([s for s in report["stages"] if s["stage"] == "awake-check"]),
        "ready_then_paused_zero": True, "raw_window_ids_and_owners_verified": True, "open_and_dismissed": True,
        "elapsed_seconds": report["elapsed_seconds"]}
    popup = captures["volume-popover-light.png"]["canvas_screen_top_left_points"]
    main = captures["frame-open-light.png"]["canvas_screen_top_left_points"]
    x,y,w,h = round(popup["x"]-main["x"]),round(popup["y"]-main["y"]),round(popup["width"]),round(popup["height"])
    full,_,_ = load(ROOT/side/"frame-open-light.png"); panel,_,_ = load(ROOT/side/"volume-popover-light.png")
    opaque = panel[:,:,3] == 255; crop = full[y:y+h,x:x+w]
    mismatch = int(np.any(crop[:,:,:3] != panel[:,:,:3],axis=2)[opaque].sum())
    assert opaque.any() and mismatch == 0
    result["runtime_checks"][side]["composite_popup_opaque_pixels"] = int(opaque.sum())
    result["runtime_checks"][side]["composite_popup_mismatched_pixels"] = mismatch

for name in NAMES:
    a, ca, ia = load(ROOT/"a"/(name+".png")); b, cb, ib = load(ROOT/"b"/(name+".png"))
    entry = {"size_pixels": [a.shape[1], a.shape[0]], "identical_icc": ia == ib, "icc_sha256": sha(ia),
             "identical_png_bytes": (ROOT/"a"/(name+".png")).read_bytes() == (ROOT/"b"/(name+".png")).read_bytes(),
             "raw_rgba": metrics(a,b), "icc_converted_srgb": metrics(ca,cb)}
    if name != "volume-popover-light":
        entry["named_roi_pixels"] = {"frame_detail": [211,52,920,668], "video": [251,167,880,521], "sidebar_selected_row": [10,108,200,136]}
        entry["named_roi_srgb"] = {key: metrics(ca[y0:y1,x0:x1], cb[y0:y1,x0:x1]) for key,(x0,y0,x1,y1) in entry["named_roi_pixels"].items()}
    result["captures"][name] = entry

for stage in STAGES:
    a = next(s for s in reports["a"]["stages"] if s["stage"] == stage)
    b = next(s for s in reports["b"]["stages"] if s["stage"] == stage)
    result["geometry"][stage] = {"identical_native_geometry": a["native_geometry"] == b["native_geometry"], "native_geometry": a["native_geometry"]}
assert reports["a"]["bundled_tides_sha256"] == reports["b"]["bundled_tides_sha256"]
result["media_sha256"] = reports["a"]["bundled_tides_sha256"]
focus = {}
for side, report in reports.items():
    observed = []
    for command in report["commands"]:
        if command["arguments"][-2:] == ["window","list"]:
            observed.append({"stdout":command["stdout"],"scope":"Before selecting Frame, not a capture-time firstResponder observation",
                             "windows":json.loads((ROOT/side/command["stdout"]).read_text())})
    focus[side] = observed
result["focus_observation"] = {"capture_frontmost_own_app_enforced": True,"ax_focused_or_first_responder_collected":False,"early_window_list":focus}
result["claims"] = {"macos14_frame_detail_pixels_identical":True,"macos14_isolated_popover_png_identical":True,
                    "all_measured_native_geometry_identical":True,"whole_main_window_pixels_identical":False,
                    "macos13_visual_verified":False,"physical_mouse_or_keyboard_verified":False,"video_playback_or_audio_verified":False,"hdr_verified":False}
result["conclusion"] = "Frame detail/video are pixel-identical in both states; isolated popover PNG bytes and all measured geometry match. Whole main windows differ only in the sidebar Frame row (A gray/B blue). FirstResponder/focus ownership was not observed, so that cause remains unconfirmed."
(ROOT/"comparison.json").write_text(json.dumps(result,indent=2)+"\n")
print(json.dumps({n: {"raw_changed_pixels":d["raw_rgba"]["changed_pixels"], "srgb_changed_pixels":d["icc_converted_srgb"]["changed_pixels"], "png_equal":d["identical_png_bytes"]} for n,d in result["captures"].items()},indent=2))
