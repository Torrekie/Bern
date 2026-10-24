#!/usr/bin/env python3
"""Private syntax/path/source self-check; never run cargo, Swift or a product."""
import ast
import contextlib
import difflib
import hashlib
import importlib.util
import io
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import yaml

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent
REPO = ROOT.parent.parent / "outputs/Bern"
SCRIPTS = ROOT / ".github/scripts"
PACKAGE = SCRIPTS / "picture-grid-width"
WORKFLOW = ROOT / ".github/workflows/macos14-picture-grid-width.yml"
SOURCE = "9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0"


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    baseline = [REPO / ".github/scripts/picture-scene-observer" / name
                for name in ["build.py", "patch.py", "Observer.swift"]]
    baseline_before = {str(p): sha(p.read_bytes()) for p in baseline}
    result = {"scope": "private syntax/path/source check; no cargo, Swift, UI, CI or product binaries"}
    for p in PACKAGE.glob("*.py"):
        ast.parse(p.read_text())
    result["python_ast"] = "both Python files pass"
    y = yaml.load(WORKFLOW.read_text(), Loader=yaml.BaseLoader)
    assert set(y["on"]) == {"workflow_dispatch"} and not y["on"]["workflow_dispatch"]
    assert len(y["jobs"]) == 2 and y["jobs"]["capture"]["needs"] == "build"
    assert y["jobs"]["build"]["runs-on"] == "macos-15" and y["jobs"]["capture"]["runs-on"] == "macos-14"
    result["shell_syntax"] = []
    for job, body in y["jobs"].items():
        for step in body["steps"]:
            if "run" in step:
                checked = subprocess.run(["bash", "-n"], input=step["run"], text=True, capture_output=True)
                assert checked.returncode == 0, checked.stderr
                result["shell_syntax"].append({"job": job, "step": step.get("name"), "exit_code": 0})
    steps = [s for job in y["jobs"].values() for s in job["steps"]]
    assert all(s["with"]["retention-days"] == "3" for s in steps if s.get("uses", "").startswith("actions/upload-artifact@"))
    assert not any(s.get("uses", "").startswith("actions/cache/save@") for s in steps)
    for old, new, name in [(baseline[0], PACKAGE / "build.py", "build.patch"),
                           (REPO / ".github/workflows/macos14-picture-scene-observer.yml", WORKFLOW, "workflow.patch")]:
        (ROOT / name).write_text("".join(difflib.unified_diff(old.read_text().splitlines(True), new.read_text().splitlines(True),
                                fromfile=str(old.relative_to(REPO)), tofile=str(new.relative_to(ROOT)))))
    for name in ["patch.py", "GridWidthTrace.swift"]:
        assert (PACKAGE / name).read_bytes() == (ROOT.parent / "picture-grid-width-preparation" / name).read_bytes()
    result["frozen_width_two_files_reused_exactly"] = True
    rows = json.loads((REPO / "Docs/Evidence/macOS14-picture-source-40136458675/raw/before.json").read_text())["inputs"]
    for row in rows:
        original = subprocess.check_output(["git", "show", SOURCE + ":" + row["path"]], cwd=REPO)
        assert len(original) == row["bytes"] and sha(original) == row["sha256"]
    assert len(rows) == 55
    result["archived_55_inputs_vs_git9dd"] = "all bytes/count/SHA match, read-only"
    links = {SCRIPTS / "picture-source-export.py": REPO / ".github/scripts/picture-source-export.py",
             SCRIPTS / "picture-scene-observer": REPO / ".github/scripts/picture-scene-observer"}
    temporary = ROOT / "path-check-temporary"
    assert not temporary.exists() and not any(p.exists() for p in links)
    temporary.mkdir()
    source, evidence = temporary / "source", temporary / "evidence"
    source.mkdir()
    saved = {key: os.environ.get(key) for key in ["BERN_PICTURE_OBSERVER_DRIVER", "BERN_PICTURE_OBSERVER_EVIDENCE"]}
    try:
        for link, target in links.items():
            link.symlink_to(target, target_is_directory=target.is_dir())
        spec = importlib.util.spec_from_file_location("width_build_check", PACKAGE / "build.py")
        build = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(build)
        build.package_hashes()
        cli = source / build.export.CLI
        cli.parent.mkdir(parents=True)
        original = subprocess.check_output(["git", "show", SOURCE + ":" + build.export.CLI], cwd=REPO)
        cli.write_bytes(original)
        generated_root = source / "target/bern/macos_modern"
        (generated_root / "Sources").mkdir(parents=True)
        (generated_root / "Sources/BernGenerated.swift").write_bytes(b"cached output must be removed")
        sentinel = source / "target/rust-cache-sentinel"
        sentinel.write_bytes(b"keep")

        def substituted_git(repo, *args):
            assert repo == source
            if args == ("rev-parse", "HEAD"):
                return (SOURCE + "\n").encode()
            if args == ("status", "--porcelain", "--untracked-files=no"):
                return b""
            if args == ("diff", "--name-only"):
                assert cli.read_bytes() == original.replace(build.export.NEEDLE, build.HOOK + build.export.NEEDLE, 1)
                return (build.export.CLI + "\n").encode()
            raise AssertionError(args)

        build.git = substituted_git
        build.export.input_rows = lambda repo: rows if repo == source else None
        os.environ["BERN_PICTURE_OBSERVER_DRIVER"] = str(PACKAGE / "wrong.py")
        os.environ["BERN_PICTURE_OBSERVER_EVIDENCE"] = str(evidence)
        try:
            build.prepare(source, evidence)
        except AssertionError:
            pass
        else:
            raise AssertionError("wrong driver accepted")
        assert cli.read_bytes() == original and generated_root.exists() and not evidence.exists()
        os.environ["BERN_PICTURE_OBSERVER_DRIVER"] = str(PACKAGE / "build.py")
        build.prepare(source, evidence)
        assert not generated_root.exists() and sentinel.read_bytes() == b"keep"
        assert cli.read_bytes().count(build.HOOK) == cli.read_bytes().count(build.export.NEEDLE) == 1
        assert json.loads((evidence / "observer-before.json").read_text())["expected_output"] == str(generated_root)
        (generated_root / "Sources").mkdir(parents=True)
        (generated_root / "Sources/BernGenerated.swift").write_bytes((REPO / "Docs/Evidence/macOS14-picture-source-40136458675/raw/BernGenerated.swift").read_bytes())
        style = subprocess.check_output(["git", "show", SOURCE + ":crates/bern-backend-swiftui/templates/BernStyle.swift"], cwd=REPO)
        (generated_root / "Sources/BernStyle.swift").write_bytes(style)
        with contextlib.redirect_stdout(io.StringIO()):
            build.patch(generated_root)
        observer = json.loads((evidence / "instrumentation.json").read_text())
        width = json.loads((evidence / "width-instrumentation.json").read_text())
        assert observer["compiled_generated_sha256"] == build.GENERATED_SHA and observer["compiled_generated_bytes"] == 106494
        assert width["style_original_sha256"] == sha(style) and width["style_compiled_sha256"] == build.STYLE_PATCHED_SHA
        result["prepare_path_check"] = {"success": True, "actual_prepare_function_called": True,
            "Git_HEAD_status_diff_boundary": "substituted exact returns; not a real checkout guard test",
            "input_rows_boundary": "55 archived rows matched Git9dd; input_rows replaced for tiny fixture",
            "wrong_driver_rejected_before_mutation": True, "CLI_hook_written_once": True,
            "generated_output_removed": True, "Rust_target_sentinel_preserved": True}
        result["actual_patch_sequence"] = {"success": True,
            "baseline_patcher_and_Observer_used_unchanged": True,
            "generated_sha256": observer["compiled_generated_sha256"], "generated_bytes": 106494,
            "Style_original_sha256": sha(style), "Style_new_sha256": width["style_compiled_sha256"],
            "Style_new_bytes": width["style_compiled_bytes"],
            "original_guard_transaction_preserved": width["width_patch"]["original_guard_transaction_write_bytes_unchanged"],
            "temporary_generated_texts_removed": True, "product_compile_or_run": False}
        result["package_hashes"] = build.package_hashes()
    finally:
        for key, value in saved.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        for link in links:
            if link.is_symlink():
                link.unlink()
        shutil.rmtree(temporary)
    assert {str(p): sha(p.read_bytes()) for p in baseline} == baseline_before
    result["baseline_three_files_unchanged"] = True
    # A unified diff's context blank line is one space; inspect active sources only.
    active = [*PACKAGE.iterdir(), WORKFLOW]
    assert not [(str(p), n) for p in active if p.is_file() for n, line in enumerate(p.read_bytes().splitlines(), 1) if line.rstrip() != line]
    result["active_files_no_trailing_whitespace"] = True
    (ROOT / "validation.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"success": True, "shell_steps": len(result["shell_syntax"]),
                      "build_sha256": sha((PACKAGE / "build.py").read_bytes()), "workflow_sha256": sha(WORKFLOW.read_bytes())}, sort_keys=True))


if __name__ == "__main__":
    main()
