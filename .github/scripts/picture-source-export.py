#!/usr/bin/env python3
"""Export exact-source generated Swift from a disposable CI checkout, before target.plan."""
import argparse, difflib, hashlib, json, shutil, subprocess, sys
from pathlib import Path

SOURCE_SHA = "9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0"
CLI = "crates/bern-cli/src/main.rs"
NEEDLE = b"        let plan = match target.plan(&app, &context) {\n"
MARKER = "BERN_DIAGNOSTIC_GENERATE_ONLY: generated files written; skipped target.plan and product build"
HOOK = ("        if std::env::var_os(\"BERN_DIAGNOSTIC_GENERATE_ONLY\").as_deref()\n"
        "            == Some(std::ffi::OsStr::new(\"1\"))\n"
        "        {\n"
        "            eprintln!(\"" + MARKER + "\");\n"
        "            return ExitCode::SUCCESS;\n"
        "        }\n").encode()
CLI_ORIGINAL_SHA256 = "63af68fa7f763b118ca34ed432b0f1b9fdfa2b3190582ebde747135303d0fa64"
INPUT_PATHS = [
    "Cargo.toml", "Cargo.lock", CLI, "crates/bern-cli/Cargo.toml",
    "crates/bern-backend-swiftui/Cargo.toml",
    "crates/bern-backend-swiftui/src/lib.rs",
    "crates/bern-backend-swiftui/src/names.rs",
    "crates/bern-backend-swiftui/src/glue.rs",
    "crates/bern-backend-swiftui/src/resources.rs",
    "crates/bern-backend-swiftui/src/style.rs",
    "crates/bern-backend-swiftui/src/swift",
    "crates/bern-backend-swiftui/templates/BernAppKit.swift",
    "crates/bern-backend-swiftui/templates/BernCompatibility.swift",
    "crates/bern-backend-swiftui/templates/BernMedia.swift",
    "crates/bern-backend-swiftui/templates/BernRuntime.swift",
    "crates/bern-backend-swiftui/templates/BernStyle.swift",
    "crates/bern-backend-swiftui/templates/BernSvg.swift",
    "crates/bern-backend-swiftui/templates/bern.h",
    "examples/showcase",
]
MAX_SOURCE = 1024 * 1024
MAX_LOG = 128 * 1024

def sha(data): return hashlib.sha256(data).hexdigest()
def write_json(path, data):
    raw = (json.dumps(data, indent=2, sort_keys=True) + "\n").encode()
    assert len(raw) <= 256 * 1024, "metadata too large"
    path.write_bytes(raw)
def git(repo, *args):
    return subprocess.check_output(["git", "-C", str(repo), *args])
def file_meta(path):
    if not path.exists(): return {"exists": False}
    assert path.is_file() and not path.is_symlink(), str(path)
    data = path.read_bytes()
    return {"exists": True, "bytes": len(data), "sha256": sha(data)}
def source_meta(repo):
    base = repo / "target/bern/macos_modern"
    return {name: file_meta(base / name) for name in
            ["Sources/BernGenerated.swift", "Sources/BernApp.swift", "build.json"]}
def input_rows(repo):
    names = git(repo, "ls-tree", "-r", "--name-only", SOURCE_SHA, "--", *INPUT_PATHS).decode().splitlines()
    assert names and CLI in names and "Cargo.lock" in names
    assert len(names) == len(set(names))
    rows = []
    for name in names:
        data = (repo / name).read_bytes()
        original = git(repo, "show", SOURCE_SHA + ":" + name)
        assert data == original, "input mismatch: " + name
        rows.append({"path": name, "bytes": len(data), "sha256": sha(data)})
    return rows

def prepare(repo, out):
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "before.json").exists(), "fresh preparation required"
    assert git(repo, "rev-parse", "HEAD").decode().strip() == SOURCE_SHA
    assert not git(repo, "status", "--porcelain", "--untracked-files=no").strip(), "tracked checkout must be clean"
    rows = input_rows(repo)
    before = (repo / CLI).read_bytes()
    assert sha(before) == CLI_ORIGINAL_SHA256, "original CLI SHA mismatch"
    assert before.count(NEEDLE) == 1, "target.plan hook must match once"
    assert b"BERN_DIAGNOSTIC_GENERATE_ONLY" not in before, "hook already present"
    after = before.replace(NEEDLE, HOOK + NEEDLE, 1)
    diff = "".join(difflib.unified_diff(before.decode().splitlines(True), after.decode().splitlines(True),
                                       fromfile="a/" + CLI, tofile="b/" + CLI)).encode()
    write_json(out / "before.json", {"source_sha": SOURCE_SHA, "source_tree": git(repo, "rev-parse", "HEAD^{tree}").decode().strip(),
        "inputs": rows, "cli_before_sha256": sha(before), "cli_after_expected_sha256": sha(after),
        "hook_match_count": 1, "cached_generated_before_removal": source_meta(repo),
        "output_reset": "target/bern/macos_modern removed after recording; Rust build/cache paths retained"})
    (out / "cli-generate-only.patch").write_bytes(diff)
    target_output = repo / "target/bern/macos_modern"
    target_root = (repo / "target").resolve()
    assert target_root == repo / "target", "target root symlink refused"
    assert target_output.resolve() == target_root / "bern/macos_modern", "output escaped expected target subtree"
    assert target_output.resolve().is_relative_to(target_root), "output outside target"
    assert not target_output.is_symlink(), "unexpected output symlink"
    if target_output.exists(): shutil.rmtree(target_output)
    (repo / CLI).write_bytes(after)
    assert git(repo, "diff", "--name-only").decode().splitlines() == [CLI]
    assert (repo / CLI).read_bytes() == after


def collect(repo, out):
    result = {"source_sha": SOURCE_SHA, "success": False, "product_compile_attempted_by_this_driver": None}
    try:
        log = (out / "generate.full.log").read_bytes()
        result["log"] = {"full_bytes": len(log), "full_sha256": sha(log), "truncated": len(log) > MAX_LOG}
        kept = log if len(log) <= MAX_LOG else log[:MAX_LOG//2] + b"\n[bounded log: middle omitted]\n" + log[-MAX_LOG//2:]
        (out / "generate.log").write_bytes(kept)
        before = json.loads((out / "before.json").read_text())
        assert git(repo, "rev-parse", "HEAD").decode().strip() == SOURCE_SHA
        result["generated_after"] = source_meta(repo)
        result["tracked_diff_paths"] = git(repo, "diff", "--name-only").decode().splitlines()
        assert result["tracked_diff_paths"] == [CLI]
        patched = (repo / CLI).read_bytes()
        assert sha(patched) == before["cli_after_expected_sha256"], "CLI changed after patch"
        assert patched.count(NEEDLE) == 1 and patched.count(HOOK) == 1
        # Check all original generator/templates/application inputs again; CLI is the sole intentional mutation.
        for row in before["inputs"]:
            if row["path"] != CLI:
                assert sha((repo / row["path"]).read_bytes()) == row["sha256"], row["path"]
        rc = int((out / "generate.exit-code.txt").read_text())
        result["cargo_exit_code"] = rc
        result["generate_only_marker_count"] = log.count(MARKER.encode())
        assert rc == 0 and result["generate_only_marker_count"] == 1, "generate-only did not complete exactly once"
        result["product_compile_attempted_by_this_driver"] = False
        base = repo / "target/bern/macos_modern"
        assert not (base / "Showcase.app/Contents/MacOS/Showcase").exists(), "unexpected product executable"
        assert not (base / "bin/showcase").exists(), "unexpected product CLI"
        generated = base / "Sources/BernGenerated.swift"
        raw = generated.read_bytes()
        assert 0 < len(raw) <= MAX_SOURCE, "generated source empty or over cap"
        text = raw.decode("utf-8")
        assert text.startswith("// Generated by Bern from the Rust declarations. Do not edit.\n")
        assert "struct BernApplication: App {" in text, "actual application entry missing"
        lines = text.splitlines()
        comments = [(i, line) for i, line in enumerate(lines) if line.startswith("/// Generated from the `") and line.endswith("` component.")]
        layout = [(i, line) for i, line in comments if line.split("`")[1].endswith("layout_page")]
        assert len(layout) == 1, "layout_page component must locate uniquely"
        start, comment = layout[0]
        end = next((i for i, _ in comments if i > start), len(lines))
        assert not (base / "Sources/BernApp.swift").exists(), "unexpected BernApp.swift; inspect instead of relabeling"
        build = json.loads((base / "build.json").read_text())
        assert build["ui"] == "swiftui-modern" and build["minimum_macos"] == "13.0" and build["profile"] == "release"
        result.update({"generated": {"path": "BernGenerated.swift", "bytes": len(raw), "sha256": sha(raw),
            "layout_page": {"component_comment": comment, "start_line": start + 1, "end_line_inclusive": end,
                            "range_policy": "component comment through before next component comment", "slice_sha256": sha("\n".join(lines[start:end]).encode())}},
            "BernApp.swift": {"exists": False, "reason": "not a generated file in exact 9dd target; BernApplication is inside BernGenerated.swift"},
            "build": build})
        assert not (out / "BernGenerated.swift").exists(), "output overwrite refused"
        (out / "BernGenerated.swift").write_bytes(raw)
        result["success"] = True
    except Exception as exc:
        result["success"] = False
        result["error"] = str(exc)
    write_json(out / "after.json", result)
    included = sorted(p for p in out.iterdir() if p.is_file() and p.name not in ["generate.full.log", "SHA256SUMS"])
    (out / "SHA256SUMS").write_text("".join(sha(p.read_bytes()) + "  " + p.name + "\n" for p in included))
    return 0 if result["success"] else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "collect"])
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.mode == "prepare": prepare(args.source.resolve(), args.output.resolve())
    else: sys.exit(collect(args.source.resolve(), args.output.resolve()))
