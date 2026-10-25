#!/usr/bin/env python3
"""Publish only the committed, reviewed bounded observer build package."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(__file__).resolve().parent
repo = root.parent / "outputs/Bern"
index = root / "film-last-observer-publish.index"
receipt = root / "film-last-observer-publication.json"
assert len(sys.argv) == 2, "expected exact reviewed source commit"
source = sys.argv[1]
assert not index.exists() and not Path(str(index) + ".lock").exists()
assert not receipt.exists()
env = dict(os.environ)
env.pop("GIT_INDEX_FILE", None)

def git(*args, data=None):
    return subprocess.check_output(["git", *args], cwd=repo, env=env, input=data)

package = ".github/scripts/film-last-observer/"
paths = [package + name for name in [
    "build.py", "patch.py", "FilmLastObservation.swift.inc", "README.md",
    "source-proof.json", "source-SHA256SUMS", "README.build.md",
]] + [".github/workflows/macos13-film-last-observer-build.yml"]
try:
    assert git("rev-parse", "HEAD").decode().strip() == source
    assert not git("status", "--porcelain").strip(), "working tree must be clean"
    env["GIT_INDEX_FILE"] = str(index)
    parent = git("rev-parse", "ci/macos14-reference").decode().strip()
    git("read-tree", parent)
    git("restore", "--source=" + source, "--staged", "--", *paths)
    tree = git("write-tree").decode().strip()
    changed = git("diff", "--name-only", parent, tree).decode().splitlines()
    assert sorted(changed) == sorted(paths), changed
    rows = []
    for path in paths:
        raw = git("show", source + ":" + path)
        assert raw == git("show", tree + ":" + path)
        rows.append({"path": path, "bytes": len(raw), "sha256": hashlib.sha256(raw).hexdigest()})
    commit = git("commit-tree", tree, "-p", parent,
                 data=b"Build bounded Film Last observer [skip ci]\n").decode().strip()
    git("update-ref", "refs/heads/ci/macos14-reference", commit, parent)
    record = {"source_commit": source, "parent_harness": parent, "harness_commit": commit,
              "tree": tree, "files": rows, "push_performed_by_script": False,
              "dispatch_performed_by_script": False}
    receipt.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"harness_commit": commit, "changed_paths": changed}))
finally:
    index.unlink(missing_ok=True)
    Path(str(index) + ".lock").unlink(missing_ok=True)
