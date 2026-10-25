#!/usr/bin/env python3
"""Export exact e48 Gallery Swift source in disposable CI; never run a product plan."""
import argparse
import difflib
import hashlib
import json
import shutil
import subprocess
import sys
from pathlib import Path

SOURCE_SHA = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
CLI = "crates/bern-cli/src/main.rs"
MANIFEST = "examples/gallery/Bern.toml"
GALLERY_UI = "examples/gallery/gallery-ui/src/lib.rs"
TARGET = "macos_modern"
INPUT_PATHS = ["Cargo.toml", "Cargo.lock", "crates", "examples/gallery"]
INPUT_COUNT = 631
CLI_ORIGINAL_SHA256 = "63af68fa7f763b118ca34ed432b0f1b9fdfa2b3190582ebde747135303d0fa64"
MANIFEST_SHA256 = "da3342d31d3cfb92740ab4e2964d08c1b0b8a3a2be84966fad9a1fb2f40d729f"
GALLERY_UI_SHA256 = "9840fcaa199b643842f490e89b071ba7b1c9af76e8857354cc4240100f525f07"
NEEDLE = b"        let plan = match target.plan(&app, &context) {\n"
MARKER = "BERN_FRAME_GENERATE_ONLY: Gallery generated files written; skipped target.plan and product build"
HOOK = ("        if std::env::var_os(\"BERN_DIAGNOSTIC_GENERATE_ONLY\").as_deref()\n"
        "            == Some(std::ffi::OsStr::new(\"1\"))\n"
        "        {\n"
        "            eprintln!(\"" + MARKER + "\");\n"
        "            return ExitCode::SUCCESS;\n"
        "        }\n").encode()
FRAME_COMMENT = b"/// Generated from the `frame` component."
MAX_SOURCE = 1024 * 1024
MAX_JSON = 256 * 1024
MAX_LOG = 128 * 1024


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    raw = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    require(len(raw) <= MAX_JSON, "metadata over cap")
    path.write_bytes(raw)


def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])


def bounded_file(path, cap):
    require(path.is_file() and not path.is_symlink(), "expected regular file: " + str(path))
    require(path.stat().st_size <= cap, "file over cap: " + str(path))
    return path.read_bytes()


def file_meta(path):
    if not path.exists():
        require(not path.is_symlink(), "dangling symlink: " + str(path))
        return {"exists": False}
    require(path.is_file() and not path.is_symlink(), "expected regular file: " + str(path))
    data = path.read_bytes()
    return {"exists": True, "bytes": len(data), "sha256": sha(data)}


def generated_meta(repo):
    base = repo / "target/bern" / TARGET
    return {name: file_meta(base / name) for name in
            ["Sources/BernGenerated.swift", "Sources/BernApp.swift", "build.json"]}


def input_names(repo):
    raw = git(repo, "ls-tree", "-r", "--name-only", "-z", SOURCE_SHA, "--", *INPUT_PATHS)
    names = [name.decode("utf-8") for name in raw.split(b"\0") if name]
    require(len(names) == INPUT_COUNT and len(set(names)) == INPUT_COUNT, "fixed input set changed")
    require(all(name in names for name in [CLI, MANIFEST, GALLERY_UI, "Cargo.lock"]), "required input missing")
    return names


def original_input_rows(repo):
    rows = []
    for name in input_names(repo):
        path = repo / name
        require(path.is_file() and not path.is_symlink(), "input is not regular: " + name)
        data = path.read_bytes()
        require(data == git(repo, "show", SOURCE_SHA + ":" + name), "input mismatch: " + name)
        rows.append({"path": name, "bytes": len(data), "sha256": sha(data)})
    require(next(r["sha256"] for r in rows if r["path"] == MANIFEST) == MANIFEST_SHA256, "Gallery manifest mismatch")
    require(next(r["sha256"] for r in rows if r["path"] == GALLERY_UI) == GALLERY_UI_SHA256, "Gallery UI mismatch")
    return rows


def require_head(repo):
    require(git(repo, "rev-parse", "HEAD").decode().strip() == SOURCE_SHA, "HEAD must be exact e48")


def prepare(repo, out):
    out.mkdir(parents=True, exist_ok=True)
    require({p.name for p in out.iterdir()} <= {"environment.txt"}, "fresh evidence directory required; only environment.txt may preexist")
    if (out / "environment.txt").exists():
        bounded_file(out / "environment.txt", MAX_LOG)
    require(not out.is_relative_to(repo / "target"), "evidence cannot be inside reset target")
    require_head(repo)
    require(not git(repo, "status", "--porcelain", "--untracked-files=no").strip(), "tracked checkout must be clean")
    rows = original_input_rows(repo)
    before = (repo / CLI).read_bytes()
    require(sha(before) == CLI_ORIGINAL_SHA256, "original CLI SHA mismatch")
    require(before.count(NEEDLE) == 1, "target.plan hook must match exactly once")
    require(b"BERN_DIAGNOSTIC_GENERATE_ONLY" not in before and MARKER.encode() not in before, "hook already present")
    after = before.replace(NEEDLE, HOOK + NEEDLE, 1)
    diff = "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                                       fromfile="a/" + CLI, tofile="b/" + CLI)).encode()
    target_root = repo / "target"
    target_output = target_root / "bern" / TARGET
    require(target_root.resolve() == target_root, "target root symlink refused")
    require(target_output.resolve() == target_output, "target output symlink or traversal refused")
    require(not target_output.is_symlink(), "target output symlink refused")
    record = {"source_sha": SOURCE_SHA, "source_tree": git(repo, "rev-parse", "HEAD^{tree}").decode().strip(),
        "manifest": MANIFEST, "target": TARGET, "inputs": rows, "input_count": len(rows),
        "input_scope": "all fixed-revision tracked crates/** and examples/gallery/** plus root Cargo.toml/Cargo.lock; external dependencies not exported",
        "cli_before_sha256": sha(before), "cli_after_expected_sha256": sha(after), "hook_match_count": 1,
        "cached_generated_before_removal": generated_meta(repo),
        "output_reset": "only target/bern/macos_modern removed after recording; Rust build/cache paths retained"}
    write_json(out / "before.json", record)
    (out / "cli-generate-only.patch").write_bytes(diff)
    if target_output.exists():
        require(target_output.is_dir(), "target output must be a directory")
        shutil.rmtree(target_output)
    (repo / CLI).write_bytes(after)
    require(git(repo, "diff", "HEAD", "--name-only").decode().splitlines() == [CLI], "unexpected tracked change")
    require((repo / CLI).read_bytes() == after, "patched CLI readback mismatch")


def bounded_log(out, result):
    path = out / "generate.full.log"
    require(path.is_file() and not path.is_symlink(), "missing regular generate.full.log")
    size = path.stat().st_size
    digest = hashlib.sha256()
    marker_count = 0
    # Streaming digest/count avoids retaining an unbounded compiler log in memory.
    overlap = b""
    needle = MARKER.encode()
    with path.open("rb") as stream:
        while True:
            chunk = stream.read(64 * 1024)
            if not chunk:
                break
            digest.update(chunk)
            combined = overlap + chunk
            marker_count += combined.count(needle)
            overlap = combined[-(len(needle) - 1):]
    omission = b"\n[bounded log: middle omitted]\n"
    with path.open("rb") as stream:
        if size <= MAX_LOG:
            kept = stream.read()
        else:
            budget = MAX_LOG - len(omission)
            first = budget // 2
            kept = stream.read(first)
            stream.seek(-(budget - first), 2)
            kept += omission + stream.read()
    require(len(kept) <= MAX_LOG, "retained log over cap")
    (out / "generate.log").write_bytes(kept)
    result["log"] = {"full_bytes": size, "full_sha256": digest.hexdigest(), "retained_bytes": len(kept),
                     "truncated": size > MAX_LOG, "generate_only_marker_count": marker_count}
    return marker_count


def frame_slice(raw):
    lines = raw.splitlines(keepends=True)
    comments = [(i, line.rstrip(b"\r\n")) for i, line in enumerate(lines)
                if line.startswith(b"/// Generated from the `") and line.rstrip(b"\r\n").endswith(b"` component.")]
    frames = [(i, line) for i, line in comments if line == FRAME_COMMENT]
    require(len(frames) == 1, "actual frame component marker must locate once")
    start, comment = frames[0]
    end = next((i for i, _ in comments if i > start), len(lines))
    sliced = b"".join(lines[start:end])
    require(b"struct AppView_frame: View {" in sliced and b"var body: some View" in sliced, "actual Frame component declaration/body missing")
    # These are actual e48 controls to inspect, not synthetic replacement source.
    for token in [b"BernSplitButton", b"SwiftUI.Slider(value:", b"SwiftUI.Menu {",
                  b'"frame.caption"', b'"frame.caption_size"', b'"frame.caption_sizes"']:
        require(token in sliced, "Frame native-control path missing: " + token.decode())
    begin_byte = sum(map(len, lines[:start]))
    require(raw[begin_byte:begin_byte + len(sliced)] == sliced, "slice must preserve original bytes")
    return sliced, {"component_comment": comment.decode(), "start_line": start + 1, "end_line_inclusive": end,
                    "start_byte": begin_byte, "end_byte_exclusive": begin_byte + len(sliced),
                    "range_policy": "original bytes from frame component comment through before next component comment",
                    "bytes": len(sliced), "sha256": sha(sliced), "path": "Frame.component.swift"}


def collect(repo, out):
    for name in ["after.json", "generate.log", "BernGenerated.swift", "Frame.component.swift", "build.json", "SHA256SUMS"]:
        require(not (out / name).exists() and not (out / name).is_symlink(), "fresh collect required; output already exists: " + name)
    result = {"source_sha": SOURCE_SHA, "manifest": MANIFEST, "target": TARGET, "success": False,
              "product_compile_attempted_by_this_driver": None}
    try:
        marker_count = bounded_log(out, result)
        before = json.loads(bounded_file(out / "before.json", MAX_JSON))
        require(before["source_sha"] == SOURCE_SHA and before["manifest"] == MANIFEST and before["target"] == TARGET, "preparation scope mismatch")
        require_head(repo)
        require(git(repo, "rev-parse", "HEAD^{tree}").decode().strip() == before["source_tree"], "source tree mismatch")
        result["tracked_diff_paths"] = git(repo, "diff", "HEAD", "--name-only").decode().splitlines()
        require(result["tracked_diff_paths"] == [CLI], "only CLI hook may change tracked source")
        patched = (repo / CLI).read_bytes()
        original = git(repo, "show", SOURCE_SHA + ":" + CLI)
        require(sha(original) == CLI_ORIGINAL_SHA256, "fixed CLI object mismatch")
        require(original.count(NEEDLE) == 1 and patched == original.replace(NEEDLE, HOOK + NEEDLE, 1), "CLI hook differs from exact expected patch")
        require(sha(patched) == before["cli_after_expected_sha256"] and patched.count(HOOK) == 1, "patched CLI changed")
        names = input_names(repo)
        require([r["path"] for r in before["inputs"]] == names and before["input_count"] == INPUT_COUNT, "input list differs from locked tree")
        checked = []
        for row in before["inputs"]:
            current = file_meta(repo / row["path"])
            expected = sha(patched) if row["path"] == CLI else row["sha256"]
            expected_size = len(patched) if row["path"] == CLI else row["bytes"]
            require(current.get("sha256") == expected and current.get("bytes") == expected_size, "input changed: " + row["path"])
            checked.append({"path": row["path"], "bytes": current["bytes"], "sha256": current["sha256"]})
        result["inputs_after"] = checked
        result["input_count"] = len(checked)
        rc = int(bounded_file(out / "generate.exit-code.txt", 32).decode().strip())
        result["cargo_exit_code"] = rc
        require(rc == 0 and marker_count == 1, "generate-only must exit 0 and emit exactly one marker")
        result["product_compile_attempted_by_this_driver"] = False
        base = repo / "target/bern" / TARGET
        require(base.resolve() == base and base.is_dir(), "generated output path invalid")
        product_paths = ["Gallery.app/Contents/MacOS", "Gallery.app.dSYM", "bin"]
        result["product_outputs"] = {name: (base / name).exists() for name in product_paths}
        require(not any(result["product_outputs"].values()), "unexpected Gallery product executable")
        require(not (base / "Sources/BernApp.swift").exists(), "unexpected BernApp.swift; inspect rather than relabel")
        raw = bounded_file(base / "Sources/BernGenerated.swift", MAX_SOURCE)
        require(raw.startswith(b"// Generated by Bern from the Rust declarations. Do not edit.\n"), "actual Bern generated header missing")
        result["generated"] = {"path": "BernGenerated.swift", "bytes": len(raw), "sha256": sha(raw)}
        # Preserve the true bounded generated file even if a later semantic guard fails.
        (out / "BernGenerated.swift").write_bytes(raw)
        build_raw = bounded_file(base / "build.json", MAX_JSON)
        result["build_json"] = {"path": "build.json", "bytes": len(build_raw), "sha256": sha(build_raw)}
        (out / "build.json").write_bytes(build_raw)
        result["generated_after"] = generated_meta(repo)
        text = raw.decode("utf-8")
        require("struct BernApplication: App {" in text, "actual application entry missing")
        for token in ["/// Generated from the `main_window` component.", "struct AppView_main_window: View {",
                      "AppView_main_window(", "AppView_frame(", "/// Root of the `main` window."]:
            require(token in text, "actual Gallery Scene/Frame route missing: " + token)
        sliced, frame = frame_slice(raw)
        build = json.loads(build_raw)
        require(build["target"] == "swiftui-modern-macos" and build["platform"] == "macos"
                and build["ui"] == "swiftui-modern" and build["minimum_macos"] == "13.0"
                and build["profile"] == "release" and build["app_bundle"] == "Gallery.app"
                and build["generator"] == "bern-backend-swiftui", "wrong real Gallery macos_modern build metadata")
        result["generated"]["frame"] = frame
        result["build"] = build
        result["BernApp.swift"] = {"exists": False, "reason": "exact e48 application entry is in BernGenerated.swift"}
        for name, data in [("Frame.component.swift", sliced)]:
            require(not (out / name).exists(), "output overwrite refused: " + name)
            (out / name).write_bytes(data)
        result["success"] = True
    except Exception as exc:
        result["success"] = False
        result["error"] = str(exc)
    write_json(out / "after.json", result)
    included = sorted(p for p in out.iterdir() if p.is_file() and not p.is_symlink()
                      and p.name not in ["generate.full.log", "SHA256SUMS"])
    (out / "SHA256SUMS").write_text("".join(sha(p.read_bytes()) + "  " + p.name + "\n" for p in included))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "collect"])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    repo, out = args.source.resolve(), args.output.resolve()
    if args.mode == "prepare":
        prepare(repo, out)
    else:
        sys.exit(collect(repo, out))
