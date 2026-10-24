#!/usr/bin/env python3
"""Apply the exact-source diagnostic observer before the original product build plan."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import sys

PACKAGE = Path(__file__).resolve().parent
MARKER = "BERN_PICTURE_OBSERVER_PATCHED: original target.plan follows"
HOOK = ('''        if let Some(driver) = std::env::var_os("BERN_PICTURE_OBSERVER_DRIVER") {
            let status = Command::new("python3")
                .arg(driver).arg("patch").arg(&context.output_dir).status();
            match status {
                Ok(status) if status.success() => eprintln!("''' + MARKER + '''"),
                _ => return ExitCode::FAILURE,
            }
        }
''').encode()


def module(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    result = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(result)
    return result


export = module("picture_source_export", PACKAGE.parent / "picture-source-export.py")
sha = export.sha
git = export.git
write_json = export.write_json


def package_hashes():
    return {p.name: sha(p.read_bytes()) for p in
            [PACKAGE / "build.py", PACKAGE / "patch.py", PACKAGE / "Observer.swift"]}


def prepare(repo, out):
    assert git(repo, "rev-parse", "HEAD").decode().strip() == export.SOURCE_SHA
    assert not git(repo, "status", "--porcelain", "--untracked-files=no").strip()
    assert Path(os.environ["BERN_PICTURE_OBSERVER_DRIVER"]).resolve() == PACKAGE / "build.py"
    assert Path(os.environ["BERN_PICTURE_OBSERVER_EVIDENCE"]).resolve() == out
    original = (repo / export.CLI).read_bytes()
    assert sha(original) == export.CLI_ORIGINAL_SHA256
    assert original.count(export.NEEDLE) == 1 and b"BERN_PICTURE_OBSERVER_DRIVER" not in original
    patched = original.replace(export.NEEDLE, HOOK + export.NEEDLE, 1)
    target = repo / "target/bern/macos_modern"
    assert (repo / "target").resolve() == repo / "target"
    assert target.resolve() == repo / "target/bern/macos_modern"
    assert not target.is_symlink()
    out.mkdir(parents=True, exist_ok=True)
    assert not (out / "observer-before.json").exists()
    write_json(out / "observer-before.json", {
        "source_sha": export.SOURCE_SHA, "harness_sha": os.environ.get("GITHUB_SHA"),
        "inputs": export.input_rows(repo), "package_hashes": package_hashes(),
        "cli_original_sha256": sha(original), "cli_patched_sha256": sha(patched),
        "expected_output": str(target), "cached_before_removal": export.source_meta(repo),
    })
    import difflib
    (out / "cli-observer.patch").write_text("".join(difflib.unified_diff(
        original.decode().splitlines(True), patched.decode().splitlines(True),
        fromfile="a/" + export.CLI, tofile="b/" + export.CLI)))
    if target.exists():
        shutil.rmtree(target)
    (repo / export.CLI).write_bytes(patched)
    assert git(repo, "diff", "--name-only").decode().splitlines() == [export.CLI]


def patch(target):
    out = Path(os.environ["BERN_PICTURE_OBSERVER_EVIDENCE"]).resolve()
    before = json.loads((out / "observer-before.json").read_text())
    assert target == Path(before["expected_output"])
    assert package_hashes() == before["package_hashes"]
    source = target / "Sources/BernGenerated.swift"
    original = source.read_bytes()
    patcher = module("picture_scene_exact_patch", PACKAGE / "patch.py")
    patcher.patch(source, out / "picture-patch")
    measured = (out / "picture-patch/BernGenerated.measured.swift").read_bytes()
    helper = (PACKAGE / "Observer.swift").read_bytes()
    combined = measured + b"\n// Diagnostic observer; original Scene and layout declarations above.\n" + helper
    source.write_bytes(combined)
    assert source.read_bytes() == combined and sha(original) == patcher.SOURCE_SHA
    write_json(out / "instrumentation.json", {
        "success": True, "generated_original_sha256": sha(original),
        "generated_measured_sha256": sha(measured), "observer_helper_sha256": sha(helper),
        "compiled_generated_sha256": sha(combined), "compiled_generated_bytes": len(combined),
        "hook_count": 21, "scope": "21 appended background modifiers plus file-scope observer; original Scene/children preserved",
    })


def collect(repo, out):
    result = {"success": False, "source_sha": export.SOURCE_SHA}
    try:
        log = (out / "build.full.log").read_bytes()
        cap = 128 * 1024
        kept = log if len(log) <= cap else log[:cap // 2] + b"\n[bounded: middle omitted]\n" + log[-cap // 2:]
        (out / "build.log").write_bytes(kept)
        result["log"] = {"full_sha256": sha(log), "full_bytes": len(log), "truncated": len(log) > cap}
        before = json.loads((out / "observer-before.json").read_text())
        assert git(repo, "rev-parse", "HEAD").decode().strip() == export.SOURCE_SHA
        assert git(repo, "diff", "--name-only").decode().splitlines() == [export.CLI]
        assert sha((repo / export.CLI).read_bytes()) == before["cli_patched_sha256"]
        assert package_hashes() == before["package_hashes"]
        for row in before["inputs"]:
            if row["path"] != export.CLI:
                assert sha((repo / row["path"]).read_bytes()) == row["sha256"], row["path"]
        assert int((out / "build.exit-code.txt").read_text()) == 0
        assert log.count(MARKER.encode()) == 1
        instrument = json.loads((out / "instrumentation.json").read_text())
        assert instrument["success"] is True
        base = repo / "target/bern/macos_modern"
        assert sha((base / "Sources/BernGenerated.swift").read_bytes()) == instrument["compiled_generated_sha256"]
        build = json.loads((base / "build.json").read_text())
        assert build["ui"] == "swiftui-modern" and build["minimum_macos"] == "13.0" and build["profile"] == "release"
        binaries = {str(p.relative_to(base)): {"sha256": sha(p.read_bytes()), "bytes": p.stat().st_size}
                    for p in [base / "Showcase.app/Contents/MacOS/Showcase", base / "bin/showcase"]}
        assert all(row["bytes"] > 0 for row in binaries.values())
        result.update({"success": True, "instrumentation": instrument, "binaries": binaries, "build": build})
    except Exception as exc:
        result["success"] = False
        result["error"] = str(exc)
    write_json(out / "observer-build.json", result)
    print(json.dumps({"success": result["success"], "error": result.get("error")}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    mode = sys.argv[1]
    if mode == "patch" and len(sys.argv) == 3:
        patch(Path(sys.argv[2]).resolve())
    elif mode == "prepare" and len(sys.argv) == 4:
        prepare(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve())
    elif mode == "collect" and len(sys.argv) == 4:
        sys.exit(collect(Path(sys.argv[2]).resolve(), Path(sys.argv[3]).resolve()))
    else:
        raise SystemExit("usage: build.py prepare|collect SOURCE EVIDENCE; build.py patch OUTPUT_ROOT")
