#!/usr/bin/env python3
"""Offline/read-only validation of the one downloaded f6 Showcase artifact."""
import hashlib
import json
import plistlib
import struct
import subprocess
import tarfile
from pathlib import Path, PurePosixPath

from macho import macho

ROOT = Path(__file__).resolve().parent
TASK = ROOT.parent.parent
EXACT = ROOT / "exact"
BASE = TASK / "outputs/macOS13"


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write(name, value):
    (ROOT / name).write_text(json.dumps(value, indent=2, sort_keys=True) + "\n")


def files(directory):
    return {str(p.relative_to(directory)): {"bytes": p.stat().st_size,
            "sha256": digest(p.read_bytes())}
            for p in sorted(directory.rglob("*")) if p.is_file()}


def build_version(path):
    raw = path.read_bytes()
    header = struct.unpack_from("<8I", raw)
    assert header[0] == 0xfeedfacf and header[1] == 0x100000c
    result = []
    offset = 32
    for _ in range(header[4]):
        cmd, size = struct.unpack_from("<II", raw, offset)
        assert size >= 8 and offset + size <= len(raw)
        if cmd == 0x32:
            platform, minimum, sdk, ntools = struct.unpack_from("<4I", raw, offset + 8)
            def version(n):
                return f"{n >> 16}.{(n >> 8) & 255}.{n & 255}"
            result.append(dict(platform=platform, minimum=version(minimum),
                               sdk=version(sdk), ntools=ntools))
        offset += size
    assert len(result) == 1, result
    return result[0]


assert not EXACT.exists(), "Refuse to overwrite an existing exact extraction"
run = json.loads((ROOT / "run.json").read_text())
assert run["id"] == 40075331576 and run["conclusion"] == "success"
assert run["head_sha"] == "e44cec24fcc54030d52e2e671aec2dd62c13b7c1"
assert json.loads((ROOT / "environment-comparison.json").read_text())["toolchain_lines_identical"]
build = json.loads((ROOT / "build/build.json").read_text())
baseline_build = json.loads((TASK / "outputs/Bern/Docs/Evidence/macOS13-native-standard-full-app-9dd/build/build.json").read_text())
for key, expected in dict(ui="swiftui-modern", target="swiftui-modern-macos",
                          minimum_macos="13.0", architecture="arm64",
                          platform="macos", profile="release", app_bundle="Showcase.app").items():
    assert build[key] == expected, (key, build[key])
assert build == baseline_build
archive = ROOT / "build/showcase.tar.gz"
archive_sha = digest(archive.read_bytes())
expected_sha, expected_name = (ROOT / "build/showcase.tar.gz.sha256").read_text().split()
assert expected_name == "showcase.tar.gz" and archive_sha == expected_sha
entries = []
with tarfile.open(archive, "r:gz") as tar:
    members = tar.getmembers()
    seen = set()
    for member in members:
        p = PurePosixPath(member.name)
        assert not p.is_absolute() and ".." not in p.parts and member.name not in seen
        seen.add(member.name)
        assert p.parts[0] == "Showcase.app" or member.name == "bin/showcase", member.name
        assert member.isdir() or member.isfile(), (member.name, member.type)
        entry = dict(path=member.name, kind="directory" if member.isdir() else "file",
                     bytes=member.size, mode=oct(member.mode), mtime=member.mtime,
                     uid=member.uid, gid=member.gid, uname=member.uname, gname=member.gname)
        if member.isfile():
            entry["sha256"] = digest(tar.extractfile(member).read())
        entries.append(entry)
    assert len(members) == 25 and sum(m.isfile() for m in members) == 16
    write("tar-members.json", dict(archive_sha256=archive_sha, entries=entries))
    EXACT.mkdir()
    tar.extractall(EXACT, members=members)

before = files(EXACT)
expected_files = {e["path"]: {"bytes": e["bytes"], "sha256": e["sha256"]}
                  for e in entries if e["kind"] == "file"}
assert before == expected_files
write("exact-files-before.json", before)
commands = []
def command(args, required=True):
    proc = subprocess.run(args, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    commands.append(dict(argv=args, returncode=proc.returncode, stdout=proc.stdout, stderr=proc.stderr))
    write("static-commands.json", commands)
    if required:
        assert proc.returncode == 0, commands[-1]
    return proc

app = EXACT / "Showcase.app"
gui = app / "Contents/MacOS/Showcase"
cli = EXACT / "bin/showcase"
command(["codesign", "--verify", "--deep", "--strict", str(app)])
command(["codesign", "--verify", "--strict", str(cli)])
for path in (app, cli):
    command(["codesign", "--display", "--verbose=4", str(path)])
for path in (gui, cli):
    command(["file", str(path)])
    command(["xcrun", "vtool", "-show-build", str(path)])
    command(["xcrun", "otool", "-L", str(path)])
versions = {"GUI": build_version(gui), "CLI": build_version(cli)}
for version in versions.values():
    assert version == dict(platform=1, minimum="13.0.0", sdk="26.2.0", ntools=1), version
info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
assert info["LSMinimumSystemVersion"] == "13.0"

binaries, baseline_binaries, sections = {}, {}, {}
for label, path, base_path in (("GUI", gui, BASE / "Showcase.app/Contents/MacOS/Showcase"),
                               ("CLI", cli, BASE / "bin/showcase")):
    binaries[label] = macho(path)
    baseline_binaries[label] = macho(base_path)
    ours = {(s["segment"], s["section"]): s for s in binaries[label]["sections"]}
    old = {(s["segment"], s["section"]): s for s in baseline_binaries[label]["sections"]}
    sections[label] = dict(section_keys_equal=ours.keys() == old.keys(),
        changed_sections=[dict(segment=k[0], section=k[1], candidate=ours.get(k), baseline=old.get(k))
                          for k in sorted(ours.keys() | old.keys())
                          if ours.get(k) != old.get(k)])
write("macho-candidate.json", binaries)
write("macho-9dd-baseline.json", baseline_binaries)
write("macho-section-comparison.json", sections)
baseline_files = files(BASE / "Showcase.app")
baseline_files = {"Showcase.app/" + k: v for k, v in baseline_files.items()}
base_cli = BASE / "bin/showcase"
baseline_files["bin/showcase"] = dict(bytes=base_cli.stat().st_size, sha256=digest(base_cli.read_bytes()))
write("9dd-baseline-files.json", baseline_files)
file_comparison = dict(member_paths_identical=before.keys() == baseline_files.keys(),
    changed=[dict(path=p, candidate=before.get(p), baseline=baseline_files.get(p))
             for p in sorted(before.keys() | baseline_files.keys()) if before.get(p) != baseline_files.get(p)])
write("9dd-file-comparison.json", file_comparison)
after = files(EXACT)
assert after == before, "Static validation changed an extracted file"
write("exact-files-after.json", after)
validation = dict(success=True, scope="Static only; original CI bundle/CLI unmodified; no app or CLI execution, signing mutation, compilation or delivery.",
    run_id=run["id"], source_sha="f6be9bd95253970ad82429f8b6df107d4447e647", harness_sha=run["head_sha"],
    artifact_zip_sha256=json.loads((ROOT / "zip-members.json").read_text())["archive_sha256"],
    tar_sha256=archive_sha, toolchain_identical_to_9dd=True, build_json_identical_to_9dd=True,
    tar_entries=len(entries), regular_files=len(before), exact_files_unmodified=True,
    gui_sha256=binaries["GUI"]["sha256"], cli_sha256=binaries["CLI"]["sha256"],
    binary_versions=versions, bundle_minimum_macos=info["LSMinimumSystemVersion"],
    strict_app_signature_valid=True, strict_cli_signature_valid=True,
    comparison_to_9dd=file_comparison, exact_app_path=str(app), exact_cli_path=str(cli))
write("validation.json", validation)
print(json.dumps(validation, indent=2, sort_keys=True))
