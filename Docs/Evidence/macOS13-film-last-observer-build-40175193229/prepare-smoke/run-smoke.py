#!/usr/bin/env python3
"""Exercise only real prepare against a disposable exact-e48 checkout."""
import hashlib
import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parent / "outputs/Bern"
draft = root / "film-last-observer-build-preparation/.github/scripts/film-last-observer"
case = root / "film-last-observer-build-smoke"
assert len(sys.argv) == 2
expected_driver = sys.argv[1]
assert not case.exists() and not case.is_symlink()
case.mkdir()
source = case / "source"
package = case / "harness/.github/scripts/film-last-observer"
evidence = case / "evidence"
package.mkdir(parents=True)
env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
env.pop("GIT_INDEX_FILE", None)
start = time.monotonic()
commands = []

def run(argv, *, cwd=None):
    t = time.monotonic()
    p = subprocess.run(argv, cwd=cwd, env=env, capture_output=True, timeout=60)
    assert len(p.stdout) + len(p.stderr) < 131072
    commands.append({"argv": list(map(str, argv)), "exit_code": p.returncode,
                     "seconds": time.monotonic() - t,
                     "stdout": p.stdout.decode(errors="replace"),
                     "stderr": p.stderr.decode(errors="replace")})
    assert p.returncode == 0, commands[-1]
    return p.stdout

try:
    for name in ["build.py", "patch.py", "FilmLastObservation.swift.inc", "README.md",
                 "source-proof.json", "source-SHA256SUMS", "README.build.md"]:
        p = draft / name
        assert p.is_file() and not p.is_symlink()
        shutil.copyfile(p, package / name)
    assert hashlib.sha256((package / "build.py").read_bytes()).hexdigest() == expected_driver
    guard = subprocess.check_output(["git", "-C", str(repo), "show",
        "2cff19aad748ac673fefda921b313886bb902e4b:.github/scripts/frame-source-export.py"], env=env)
    assert hashlib.sha256(guard).hexdigest() == "5b4a254565f437f819a308f8cf3c5b1990b937f76b9918ff5b935e91e1a2b017"
    (package.parent / "frame-source-export.py").write_bytes(guard)
    run(["git", "-c", "core.hooksPath=/dev/null", "clone", "--shared", "--no-checkout", str(repo), str(source)])
    run(["git", "-C", str(source), "-c", "core.hooksPath=/dev/null", "checkout", "--detach",
         "e48fff46b3a92a28465ad74295bd273a9d69af7d"])
    run([sys.executable, str(package / "build.py"), "prepare", str(source), str(evidence)])
    status = run(["git", "-C", str(source), "status", "--porcelain", "--untracked-files=no"]).decode()
    before = json.loads((evidence / "before.json").read_text())
    assert before["input_count"] == 631
    assert set(before["templates"]) == {"crates/bern-backend-swiftui/templates/BernRuntime.swift", "crates/bern-backend-swiftui/templates/BernStyle.swift"}
    result = {"success": True, "scope": "Actual prepare only; no generator/compiler/product/native/CI execution",
              "driver_sha256": expected_driver, "input_count": before["input_count"],
              "templates": before["templates"], "source_status": status,
              "generated_target_exists": (source / "target/bern/macos_modern").exists()}
except Exception as exc:
    result = {"success": False, "error": str(exc)}
result.update({"seconds": time.monotonic() - start, "commands": commands})
(case / "smoke.json").write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps({k: v for k, v in result.items() if k != "commands"}))
sys.exit(0 if result["success"] else 1)
