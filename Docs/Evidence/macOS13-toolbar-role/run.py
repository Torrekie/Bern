#!/usr/bin/env python3
"""Only three independent, hidden Scene fixtures. Never activate the fixture."""
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import time

root = Path(__file__).resolve().parent
stamp = f"r{os.getpid()}t{time.time_ns()}"
rows, cleanup = [], []
try:
    for key in ("automatic", "split-editor", "detail-editor"):
        bundle_id = f"dev.codex.bern-toolbar-role.{key}.{stamp}"
        bundle = root / "bundles" / f"{key}.app"
        binary = bundle / "Contents" / "MacOS" / "ToolbarProbe"
        binary.parent.mkdir(parents=True)
        os.link(root / "ToolbarProbe", binary)
        with (bundle / "Contents" / "Info.plist").open("wb") as f:
            plistlib.dump({"CFBundleExecutable": "ToolbarProbe", "CFBundleIdentifier": bundle_id,
                "CFBundleName": "Toolbar Role Probe", "CFBundlePackageType": "APPL",
                "CFBundleVersion": "1", "CFBundleShortVersionString": "1.0",
                "LSMinimumSystemVersion": "13.0", "NSPrincipalClass": "NSApplication",
                "LSUIElement": True}, f)
        started = time.monotonic()
        try:
            p = subprocess.run([str(binary), key], text=True, capture_output=True, timeout=12)
            (root / f"{key}.stderr").write_text(p.stderr)
            d = json.loads(p.stdout)
            d["wall_seconds"] = time.monotonic() - started
            (root / f"{key}.json").write_text(json.dumps(d, indent=2) + "\n")
            assert p.returncode == 0, d
            assert len(d["samples"]) == 3, d
            assert all(not s["visible"] and not s["key"] for s in d["samples"]), d
            assert all(s["frontmost_pid"] == d["frontmost_pid_before"] for s in d["samples"]), d
            assert d["frontmost_pid_before_restore"] == d["frontmost_pid_before"] == d["frontmost_pid_after"], d
            s = d["samples"][-1]
            toggle = next(i for i in s["toolbar_items"] if i["identifier"] == "com.apple.SwiftUI.navigationSplitView.toggleSidebar")
            graphics = next((n for n in toggle.get("descendants", []) if n["class"] == "SwiftUI._NSGraphicsView"), None)
            split = next(v for v in s["split_views"] if v["vertical"] and len(v["arranged"]) == 2)
            rows.append({"mode": key, "bundle_identifier": bundle_id, "wall_seconds": d["wall_seconds"],
                "sidebar_width": split["arranged"][0]["width"], "toolbar_style": s["toolbar_style"],
                "toggle_item": toggle.get("frame_window"), "toggle_graphics": graphics,
                "native_window_title": s["title"], "title_fields": s["title_fields"],
                "visible_title_present": any(not t["hidden"] for t in s["title_fields"]),
                "three_samples_equal": d["samples"][0] == d["samples"][1] == s,
                "all_invisible_nonkey": True, "foreground_unchanged": True})
        finally:
            # The unique domains are owned by this invocation; no global/user domain is touched.
            deleted = subprocess.run(["defaults", "delete", bundle_id], capture_output=True, text=True)
            paths = [Path.home()/"Library"/"Preferences"/(bundle_id+".plist"),
                     Path.home()/"Library"/"Saved Application State"/(bundle_id+".savedState")]
            paths += list((Path.home()/"Library"/"Preferences"/"ByHost").glob(bundle_id+".*.plist"))
            for path in paths:
                if path.is_dir(): shutil.rmtree(path)
                elif path.exists(): path.unlink()
            cleanup.append({"bundle_identifier": bundle_id, "defaults_delete_status": deleted.returncode,
                "exact_paths_absent": all(not path.exists() for path in paths)})
            shutil.rmtree(bundle)
finally:
    (root/"report.json").write_text(json.dumps({"scope": "Hidden real SwiftUI App/Window Scene; fixed Buttons title, sidebar search, default automatic toolbar placement; no native toolbar mutation or activation.",
        "runtime": "macOS13.7.8", "compiler": "Swift5.9.2/SDK14.2 target13", "rows": rows, "cleanup": cleanup}, indent=2)+"\n")
print(json.dumps(rows, indent=2))
