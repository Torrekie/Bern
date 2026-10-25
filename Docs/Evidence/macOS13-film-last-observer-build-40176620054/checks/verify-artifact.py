#!/usr/bin/env python3
"""Verify the single corrected CI artifact in memory; never extract/launch an App."""
import hashlib
import json
import struct
import sys
import tarfile
from pathlib import Path, PurePosixPath

base = Path(sys.argv[1]).resolve(strict=True)
output = Path(sys.argv[2]).resolve()
assert not output.exists()
sha = lambda raw: hashlib.sha256(raw).hexdigest()
raw = (base / "observer-build.json").read_bytes()
record = json.loads(raw)
assert record["success"] is True and record["cargo_exit_code"] == 0
assert record["source_sha"] == "e48fff46b3a92a28465ad74295bd273a9d69af7d"
assert record["harness_sha"] == "892c392ffec22a10b282e8d27d41386bac5def64"
assert record["run_id"] == "40176620054"
assert record["normal_cli_not_hooked"] and record["other_fixed_inputs_unchanged"] == 629
assert record["native_execution_performed"] is False
assert record["toolchain"]["selected_sdk"] == record["toolchain"]["actual_app_embedded_sdk"] == "26.2"
assert record["templates"]["crates/bern-backend-swiftui/templates/BernStyle.swift"]["sha256"] == "179b406b1a7246e855ac7634bf225d1680016033fb1044035fb0137399c81e0e"
for name, expected in [
    ("BernRuntime.generated.swift", "e38647f3b918e4d0c4c503eb8876889578a35b57efdb8feeaadafaac5a51f663"),
    ("BernGenerated.generated.swift", "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653"),
]:
    assert sha((base / name).read_bytes()) == expected
archive = base / "gallery-film-last-observer.tar.gz"
checksum, filename = (base / (archive.name + ".sha256")).read_text().strip().split("  ")
assert filename == archive.name and sha(archive.read_bytes()) == checksum
members = {}
with tarfile.open(archive, "r:gz") as tar:
    names = set()
    for member in tar.getmembers():
        path = PurePosixPath(member.name)
        assert not path.is_absolute() and ".." not in path.parts
        assert member.name not in names
        names.add(member.name)
        assert member.isdir() or member.isfile()
        assert member.name == "observer-build.json" or path.parts[0] == "Gallery.app"
        if not member.isfile():
            continue
        assert 0 <= member.size <= 16 * 1024 * 1024
        data = tar.extractfile(member).read()
        assert len(data) == member.size
        if member.name == "observer-build.json":
            assert data == raw
        else:
            relative = str(path.relative_to("Gallery.app"))
            members[relative] = {"bytes": len(data), "sha256": sha(data)}
            if relative == "Contents/MacOS/Gallery":
                executable = data
assert "observer-build.json" in names and members == record["app_members"]
assert {"bytes": len(executable), "sha256": sha(executable)} == record["gui"]
magic, cpu, subtype, kind, count, size, flags, reserved = struct.unpack_from("<IiiIIIII", executable)
assert magic == 0xfeedfacf and cpu == 0x100000c and kind == 2
assert 0 < count < 1000 and 32 + size <= len(executable)
offset = 32
build_versions = []
signatures = []
for _ in range(count):
    cmd, length = struct.unpack_from("<II", executable, offset)
    assert length >= 8 and offset + length <= 32 + size
    if cmd == 0x32:
        assert length >= 24
        platform, minimum, sdk, tools = struct.unpack_from("<IIII", executable, offset + 8)
        assert platform == 1 and minimum == 0x000d0000 and sdk == 0x001a0200
        build_versions.append({"platform": platform, "minimum": "13.0", "sdk": "26.2"})
    if cmd == 0x1d:
        data_offset, data_size = struct.unpack_from("<II", executable, offset + 8)
        assert data_size > 0 and data_offset + data_size <= len(executable)
        signatures.append({"offset": data_offset, "bytes": data_size})
    offset += length
assert offset == 32 + size and len(build_versions) == len(signatures) == 1
result = {
    "success": True, "scope": "In-memory source, tar member and actual Mach-O identity verification only",
    "observer_build_json_sha256": sha(raw), "archive_sha256": checksum,
    "gui": record["gui"], "app_regular_file_count": len(members),
    "actual_macho": {"architecture": "arm64", "filetype": "MH_EXECUTE", "build_versions": build_versions,
                     "code_signature_command": signatures[0]},
    "strict_signature_validation": "CI pinned collect and additional workflow verification; not rerun locally",
    "App_extracted_or_resigned_or_launched": False,
    "native_or_observation_effect_or_visual_acceptance": False,
}
output.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n")
print(json.dumps(result))
