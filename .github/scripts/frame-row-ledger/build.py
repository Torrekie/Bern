#!/usr/bin/env python3
"""Patch exact e48 generated sources, then continue the original product plan.

Frozen patcher, ledger, closed collector and pixel gate; no early-return hook.
"""
import argparse
import difflib
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

sys.dont_write_bytecode = True
PACKAGE = Path(__file__).resolve().parent
EXPORT = PACKAGE.parent / "frame-source-export.py"
EXPORT_SHA256 = "5b4a254565f437f819a308f8cf3c5b1990b937f76b9918ff5b935e91e1a2b017"
MARKER = "BERN_FRAME_ROW_PATCHED: original target.plan follows"
DRIVER = "BERN_FRAME_ROW_OBSERVER_DRIVER"
EVIDENCE = "BERN_FRAME_ROW_OBSERVER_EVIDENCE"
HOOK = ('''        if let Some(driver) = std::env::var_os("BERN_FRAME_ROW_OBSERVER_DRIVER") {
            let status = Command::new("python3")
                .arg(driver).arg("patch").arg(&context.output_dir).status();
            match status {
                Ok(status) if status.success() => eprintln!("''' + MARKER + '''"),
                _ => return ExitCode::FAILURE,
            }
        }
''').encode()
FILES = ("BernGenerated.swift", "BernStyle.swift")
ORIGINAL = {"BernGenerated.swift": (81110, "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653"),
            "BernStyle.swift": (210785, "3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89")}
COMPILED = {"BernGenerated.swift": (81150, "709d1c95afbc2b894a3f7d3baf88e423d1f384bfb5c21b893fc7362bc012a511"),
            "BernStyle.swift": (222921, "b3361ab4ff9ee1f7a4284cfba06df101c829fdfdd5ea5f8b040eeee1cd7569db")}
LOCKED_PATCH = {"patch.py": "815322661ba0681f89b6737bd70c88e58a5ee28cd4886eabd885f940b833b6ed",
                "RowLedger.swift": "680fbf705238a12c734d9b7c21a33b4911f077f16ae8fd7146d19a31d827bdbf",
                "FrameClosed.swift": "dcbd5405f31e0797937049feed74c4d54d7136da602636077085a856b2f2cd3d",
                "PixelGate.swift": "10ca1789d7356a369c629e4b575d42744d1d3a0b505c4562bb6f51e00a41a253"}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def source_guard():
    require(EXPORT.is_file() and sha(EXPORT.read_bytes()) == EXPORT_SHA256, "frozen source guard missing/changed")
    spec = importlib.util.spec_from_file_location("frame_source_guard", EXPORT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def package_hashes():
    names = ("build.py", "patch.py", "RowLedger.swift", "FrameClosed.swift", "PixelGate.swift")
    require(all((PACKAGE / name).is_file() and not (PACKAGE / name).is_symlink() for name in names),
            "complete frozen package required")
    result = {name: sha((PACKAGE / name).read_bytes()) for name in names}
    require(all(result[name] == value for name, value in LOCKED_PATCH.items()), "frozen patch/helper/collector/gate changed")
    return result


def source_rows(target):
    return {str(p.relative_to(target)): sha(p.read_bytes()) for p in sorted((target / "Sources").rglob("*"))
            if p.is_file() and not p.is_symlink()}


def apply_diff(original, diff, reverse=False):
    """Check the patcher's two ordinary unified diffs against real before/after bytes."""
    lines = diff.splitlines(keepends=True)
    require(len(lines) >= 3 and lines[0].startswith(b"--- ") and lines[1].startswith(b"+++ "), "unified headers required")
    original_lines, output, cursor, index = original.splitlines(keepends=True), [], 0, 2
    while index < len(lines):
        match = re.fullmatch(rb"@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@[^\n]*\n", lines[index])
        require(match is not None, "ordinary unified hunk required")
        values = [int(v) if v is not None else 1 for v in match.groups()]
        start, expected_read, expected_write = (values[2], values[3], values[1]) if reverse else (values[0], values[1], values[3])
        begin = max(0, start - 1)
        require(cursor <= begin <= len(original_lines), "hunk position out of order")
        output.extend(original_lines[cursor:begin]); cursor = begin
        consumed = emitted = 0; index += 1
        while index < len(lines) and not lines[index].startswith(b"@@ "):
            line = lines[index]; tag, payload = line[:1], line[1:]
            require(tag in (b" ", b"-", b"+"), "unsupported unified line")
            if reverse and tag != b" ":
                tag = b"+" if tag == b"-" else b"-"
            if tag in (b" ", b"-"):
                require(cursor < len(original_lines) and original_lines[cursor] == payload, "diff context differs")
                cursor += 1; consumed += 1
            if tag in (b" ", b"+"):
                output.append(payload); emitted += 1
            index += 1
        require((consumed, emitted) == (expected_read, expected_write), "hunk counts differ")
    return b"".join(output + original_lines[cursor:])


def prepare(repo, out):
    export = source_guard()
    export.require_head(repo)
    require(not export.git(repo, "status", "--porcelain", "--untracked-files=no").strip(), "tracked checkout must be clean")
    require(Path(os.environ[DRIVER]).resolve() == PACKAGE / "build.py", "driver path mismatch")
    require(Path(os.environ[EVIDENCE]).resolve() == out, "evidence path mismatch")
    require(os.environ.get("BERN_DIAGNOSTIC_GENERATE_ONLY") is None, "source-only mode must be unset")
    hashes = package_hashes()  # bind every external input before source mutation
    rows = export.original_input_rows(repo)
    original = (repo / export.CLI).read_bytes()
    require(sha(original) == export.CLI_ORIGINAL_SHA256 and original.count(export.NEEDLE) == 1, "exact CLI hook missing")
    require(DRIVER.encode() not in original, "hook already present")
    patched = original.replace(export.NEEDLE, HOOK + export.NEEDLE, 1)
    target = repo / "target/bern/macos_modern"
    require((repo / "target").resolve() == repo / "target" and target.resolve() == target and not target.is_symlink(), "target escape/symlink")
    out.mkdir(parents=True, exist_ok=True)
    require({p.name for p in out.iterdir()} <= {"environment.txt", "harness-inputs.sha256"}, "fresh evidence required")
    export.write_json(out / "observer-before.json", {
        "source_sha": export.SOURCE_SHA, "harness_sha": os.environ.get("GITHUB_SHA"),
        "inputs": rows, "package_hashes": hashes, "source_guard_sha256": EXPORT_SHA256,
        "cli_original_sha256": sha(original), "cli_patched_sha256": sha(patched),
        "expected_output": str(target), "cached_before_removal": export.generated_meta(repo),
    })
    (out / "cli-observer.patch").write_text("".join(difflib.unified_diff(
        original.decode().splitlines(True), patched.decode().splitlines(True),
        fromfile="a/" + export.CLI, tofile="b/" + export.CLI)))
    if target.exists():
        require(target.is_dir(), "expected generated directory")
        shutil.rmtree(target)
    (repo / export.CLI).write_bytes(patched)
    require(export.git(repo, "diff", "HEAD", "--name-only").decode().splitlines() == [export.CLI], "unexpected tracked change")


def verify_diffs(target, patch_dir, original=None):
    differences = list(patch_dir.glob("*.patch"))
    require(len(differences) == 2, "exactly Generated and Style diffs required")
    rows = {}
    for path in differences:
        diff = path.read_bytes(); headers = diff.splitlines()[:2]
        name = Path(headers[0][4:].decode().split("\t")[0]).name
        require(name in FILES and name not in rows and Path(headers[1][4:].decode().split("\t")[0]).name == name, "unexpected diff target")
        compiled = (target / "Sources" / name).read_bytes()
        restored = apply_diff(compiled, diff, reverse=True)
        require((len(restored), sha(restored)) == ORIGINAL[name], "restored source differs from frozen e48 source")
        require((len(compiled), sha(compiled)) == COMPILED[name], "compiled source differs from frozen diagnostic")
        require(apply_diff(restored, diff) == compiled, "diff forward reconstruction failed")
        if original is not None:
            require(restored == original[name], "diff did not restore original bytes")
        rows[name] = {"original_sha256": sha(restored), "compiled_sha256": sha(compiled),
                      "original_bytes": len(restored), "compiled_bytes": len(compiled), "diff_sha256": sha(diff)}
    require(set(rows) == set(FILES), "missing changed source")
    return rows


def patch(target):
    export = source_guard(); out = Path(os.environ[EVIDENCE]).resolve()
    before = json.loads((out / "observer-before.json").read_text())
    require(target == Path(before["expected_output"]) and target.resolve() == target, "unexpected hook output")
    require(package_hashes() == before["package_hashes"], "package changed after prepare")
    require(not (out / "instrumentation.json").exists(), "patch already called")
    original = {name: (target / "Sources" / name).read_bytes() for name in FILES}
    require(all((len(data), sha(data)) == ORIGINAL[name] for name, data in original.items()), "generated/style input lock failed")
    require(not any(p.is_symlink() for p in (target / "Sources").rglob("*")), "source symlink refused")
    source_before = source_rows(target)
    patch_dir = out / "frame-row-patch"
    require(not patch_dir.exists(), "fresh patch evidence required")
    subprocess.run([sys.executable, str(PACKAGE / "patch.py"), str(target), str(patch_dir)], check=True)
    rows = verify_diffs(target, patch_dir, original)
    helper = (PACKAGE / "RowLedger.swift").read_bytes()
    require((target / "Sources/BernStyle.swift").read_bytes().endswith(helper), "ledger must append to Style tail")
    source_after = source_rows(target)
    require(source_before.keys() == source_after.keys(), "unexpected source file addition/removal")
    require({name for name in source_before if source_before[name] != source_after[name]} == {"Sources/" + n for n in FILES}, "only Generated/Style may change")
    proof = export.bounded_file(patch_dir / "patch-proof.json", export.MAX_JSON)
    parsed = json.loads(proof)
    require(parsed["source_sha"] == export.SOURCE_SHA and parsed["frame_tag_count"] == 1
            and all(parsed[key] is True for key in ["inverse_exact_original_style", "inverse_exact_original_generated",
                                                   "original_measurement_and_place_calls_unchanged"]), "patch proof incomplete")
    export.write_json(out / "instrumentation.json", {"success": True, "files": rows,
        "package_hashes": package_hashes(), "patch_proof_sha256": sha(proof),
        "observer_style_tail_sha256": sha(helper), "roundtrip_original_bytes_equal": True})


def collect(repo, out):
    export = source_guard()
    require(not (out / "observer-build.json").exists(), "fresh collect required")
    result = {"success": False, "source_sha": export.SOURCE_SHA}
    try:
        log = (out / "build.full.log").read_bytes(); cap = 128 * 1024
        omission = b"\n[bounded middle omitted]\n"; budget = cap - len(omission)
        kept = log if len(log) <= cap else log[:budget//2] + omission + log[-(budget-budget//2):]
        (out / "build.log").write_bytes(kept)
        result["log"] = {"full_sha256": sha(log), "full_bytes": len(log), "marker_count": log.count(MARKER.encode()), "truncated": len(log) > cap}
        before = json.loads((out / "observer-before.json").read_text()); export.require_head(repo)
        require(export.git(repo, "diff", "HEAD", "--name-only").decode().splitlines() == [export.CLI], "only CLI may differ")
        original = export.git(repo, "show", export.SOURCE_SHA + ":" + export.CLI)
        require((repo / export.CLI).read_bytes() == original.replace(export.NEEDLE, HOOK + export.NEEDLE, 1), "CLI hook changed")
        require(package_hashes() == before["package_hashes"], "package changed")
        require([r["path"] for r in before["inputs"]] == export.input_names(repo), "fixed631input list differs")
        for row in before["inputs"]:
            if row["path"] != export.CLI:
                require(sha((repo / row["path"]).read_bytes()) == row["sha256"], "input changed: " + row["path"])
        require(int((out / "build.exit-code.txt").read_text()) == 0 and log.count(MARKER.encode()) == 1, "build/hook failed")
        instrument = json.loads((out / "instrumentation.json").read_text()); target = Path(before["expected_output"])
        require(verify_diffs(target, out / "frame-row-patch") == instrument["files"], "compiled source/roundtrip proof changed")
        require(sha((out / "frame-row-patch/patch-proof.json").read_bytes()) == instrument["patch_proof_sha256"], "patch proof changed")
        require(instrument["success"] is True and instrument["package_hashes"] == package_hashes(), "instrumentation incomplete")
        build = json.loads((target / "build.json").read_text())
        require(build["ui"] == "swiftui-modern" and build["minimum_macos"] == "13.0" and build["profile"] == "release" and build["app_bundle"] == "Gallery.app", "wrong Gallery build")
        binaries = {name: {"bytes": (target / name).stat().st_size, "sha256": sha((target / name).read_bytes())}
                    for name in ["Gallery.app/Contents/MacOS/Gallery", "bin/gallery"]}
        require(all(r["bytes"] > 0 for r in binaries.values()), "missing product")
        result.update(success=True, instrumentation=instrument, binaries=binaries, build=build)
    except Exception as exc:
        result["error"] = str(exc)
    export.write_json(out / "observer-build.json", result)
    print(json.dumps({"success": result["success"], "error": result.get("error")}))
    return 0 if result["success"] else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("mode", choices=["prepare", "patch", "collect"])
    parser.add_argument("paths", nargs="+")
    args = parser.parse_args()
    paths = [Path(p).resolve() for p in args.paths]
    if args.mode == "patch" and len(paths) == 1:
        patch(paths[0])
    elif args.mode == "prepare" and len(paths) == 2:
        prepare(*paths)
    elif args.mode == "collect" and len(paths) == 2:
        sys.exit(collect(*paths))
    else:
        parser.error("prepare|collect SOURCE EVIDENCE; patch OUTPUT_ROOT")
