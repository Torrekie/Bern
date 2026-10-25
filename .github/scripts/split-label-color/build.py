#!/usr/bin/env python3
"""Build provenance for one unaccepted selected-label color candidate."""
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
sys.dont_write_bytecode = True
SOURCE = "ce462b3ef5d11b72d51ddf9158940d686bc7707a"
BASE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
STYLE = "crates/bern-backend-swiftui/templates/BernStyle.swift"
INPUTS = ["Cargo.toml", "Cargo.lock", "crates", "examples/gallery"]
STYLE_META = (211493, "8219c50ec45a81eb7516b63bddbc7541211006c1a09f0069a93390707c0c6df0")
GENERATED_META = (81110, "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653")
BASE_STYLE_SHA = "3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89"
CLI_SHA = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
HELPER_SOURCES = {"FrameColorCapture.swift":"fa850da24c63d6f8a543808b59ff07d5a5535d718ef2fec949b99df6f8dc9b69",
                  "FrameColorGate.swift":"f8a3f035a357a211f86ba5ca70774745324db5e1778f5a7644384fc95978a618"}
PACKAGE = Path(__file__).resolve().parent

def need(ok, message):
    if not ok:
        raise ValueError(message)

def sha(data):
    return hashlib.sha256(data).hexdigest()

def regular(path):
    need(path.is_file() and not path.is_symlink(), "regular file required: "+str(path))
    return path.read_bytes()

def git(repo, *args):
    return subprocess.check_output(["git", *args], cwd=repo)

def tree(repo, ref):
    entries = {}
    for raw in git(repo, "ls-tree", "-r", "-z", ref, "--", *INPUTS).split(b"\0"):
        if not raw:
            continue
        meta, path = raw.split(b"\t", 1)
        mode, kind, blob = meta.decode().split()
        name = path.decode()
        need(kind == "blob" and mode in ("100644","100755"), "ordinary tracked source required")
        entries[name] = {"mode":mode, "blob":blob}
    need(len(entries) == 631, "fixed 631 inputs required")
    return entries

def snapshot(repo):
    need(git(repo,"rev-parse","HEAD").decode().strip() == SOURCE, "exact candidate HEAD required")
    need(not git(repo,"status","--porcelain","--untracked-files=no").strip(), "tracked source must be clean")
    original, candidate = tree(repo,BASE), tree(repo,SOURCE)
    need(original.keys() == candidate.keys(), "source membership changed")
    need([n for n in original if original[n] != candidate[n]] == [STYLE], "only Style may differ from original e48")
    need(sha(git(repo,"show",BASE+":"+STYLE)) == BASE_STYLE_SHA, "original Style mismatch")
    rows = []
    for name in sorted(candidate):
        data = regular(repo/name)
        blob = hashlib.sha1(b"blob "+str(len(data)).encode()+b"\0"+data).hexdigest()
        need(blob == candidate[name]["blob"], "live source differs from committed candidate: "+name)
        rows.append({"path":name, "bytes":len(data), "sha256":sha(data),
                     "baseline_git_blob":original[name]["blob"], "candidate_git_blob":blob,
                     "mode":candidate[name]["mode"]})
    data = regular(repo/STYLE)
    need((len(data),sha(data)) == STYLE_META, "candidate Style mismatch")
    return rows

def write_json(path, value):
    need(not path.exists(), "fresh receipt required: "+str(path))
    path.write_text(json.dumps(value,indent=2,sort_keys=True)+"\n")

def package_sources():
    need(set(HELPER_SOURCES) == {"FrameColorCapture.swift","FrameColorGate.swift"}, "unfrozen helper source locks")
    hashes = {n:sha(regular(PACKAGE/n)) for n in ["build.py",*HELPER_SOURCES]}
    need(all(hashes[n] == h for n,h in HELPER_SOURCES.items()), "helper source changed")
    return hashes

def prepare(repo,out):
    need(repo.resolve() == repo and out.resolve() == out, "canonical paths required")
    need(out.is_dir() and {p.name for p in out.iterdir()} <= {"environment.txt"}, "fresh build evidence required")
    rows = snapshot(repo)
    target = repo/"target/bern/macos_modern"
    removed = None
    if target.exists():
        need(target.resolve() == target and target.is_dir(), "unsafe cached target")
        d = json.loads(regular(target/"build.json"))
        need(d["ui"] == "swiftui-modern" and d["minimum_macos"] == "13.0" and
             d["architecture"] == "arm64" and d["target"] == "swiftui-modern-macos" and
             d["app_bundle"] in ["Gallery.app","Showcase.app"], "cached target not this port")
        removed = {"path":str(target),"prior_build":d}
        shutil.rmtree(target)
    write_json(out/"prepare.json", {"source_sha":SOURCE,"baseline_sha":BASE,"inputs":rows,
               "package_sources":package_sources(),"removed_generated_target":removed,
               "scope":"original full product plan, no generation hook or source mutation"})

def collect(repo,out):
    result = {"schema":"bern_split_label_color_build_v1","success":False,"source_sha":SOURCE,
              "baseline_sha":BASE,"run_id":os.environ.get("GITHUB_RUN_ID"),
              "harness_sha":os.environ.get("GITHUB_SHA")}
    try:
        before = json.loads(regular(out/"prepare.json"))
        need(snapshot(repo) == before["inputs"], "source changed during build")
        need(package_sources() == before["package_sources"], "package changed during build")
        log = regular(out/"build.full.log")
        result["log"] = {"full_bytes":len(log),"full_sha256":sha(log),"truncated":len(log)>131072}
        (out/"build.log").write_bytes(log[:131072])
        need(len(log) <= 131072, "build log exceeded fixed collection cap")
        need(regular(out/"build.exit-code.txt").strip() == b"0", "full product build failed")
        target = repo/"target/bern/macos_modern"
        for name,expected in [("BernStyle.swift",STYLE_META),("BernGenerated.swift",GENERATED_META)]:
            data = regular(target/"Sources"/name)
            need((len(data),sha(data)) == expected, "compiled source differs: "+name)
        build = json.loads(regular(target/"build.json"))
        need(build["ui"] == "swiftui-modern" and build["minimum_macos"] == "13.0" and
             build["architecture"] == "arm64" and build["app_bundle"] == "Gallery.app" and
             build["profile"] == "release", "wrong product plan")
        members = {}
        app = target/"Gallery.app"
        need(not any(p.is_symlink() for p in app.rglob("*")), "unexpected product symlink")
        for p in sorted(app.rglob("*")):
            if p.is_file():
                data = regular(p); members[str(p.relative_to(app))] = {"bytes":len(data),"sha256":sha(data)}
        binaries = {}
        for name in ["Gallery.app/Contents/MacOS/Gallery","bin/gallery"]:
            data = regular(target/name); binaries[name] = {"bytes":len(data),"sha256":sha(data)}
        need(binaries["bin/gallery"]["sha256"] == CLI_SHA, "unrelated CLI changed")
        helpers = {}
        for name in ["FrameColorCapture","FrameColorGate"]:
            data = regular(out/name)
            helpers[name] = {"bytes":len(data),"sha256":sha(data),"source_sha256":HELPER_SOURCES[name+".swift"]}
        result.update({"success":True,"build":build,"binaries":binaries,"app_members":members,
                       "helpers":helpers,"package_sources":before["package_sources"],
                       "prepare_sha256":sha(regular(out/"prepare.json")),
                       "compiled_style_sha256":STYLE_META[1],"compiled_generated_sha256":GENERATED_META[1],
                       "compiled_sources":{str(p.relative_to(target/"Sources")):sha(regular(p))
                        for p in sorted((target/"Sources").rglob("*")) if p.is_file()}})
    except Exception as error:
        result["failure"] = type(error).__name__+": "+str(error)
    write_json(out/"candidate-build.json",result)
    need(result["success"], result.get("failure","collect failed"))

if __name__ == "__main__":
    need(len(sys.argv) == 4 and sys.argv[1] in ["prepare","collect"], "usage: build.py prepare|collect SOURCE EVIDENCE")
    repo,out = [Path(p).resolve() for p in sys.argv[2:]]
    (prepare if sys.argv[1] == "prepare" else collect)(repo,out)
