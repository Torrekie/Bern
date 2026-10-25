#!/usr/bin/env python3
"""Build the frozen env-only collector and original guard; never run either."""
import hashlib
import json
import re
import subprocess
import time
from pathlib import Path

root = Path(__file__).resolve().parent
source = root / "film-observer13-driver-preparation/source"
out = root / "film-observer13-helper-build"
assert source.is_dir() and not source.is_symlink() and not out.exists()
out.mkdir()
compiler = "/Applications/Xcode.app/Contents/Developer/Toolchains/XcodeDefault.xctoolchain/usr/bin/swiftc"
sdk = "/Applications/Xcode.app/Contents/Developer/Platforms/MacOSX.platform/Developer/SDKs/MacOSX14.2.sdk"
sha = lambda data: hashlib.sha256(data).hexdigest()
pins = {"FilmFirstLast.swift": "8bdf078fd1b75c8e4dd8b5c20725a12462491c9e92108818fd0b6e86b812ad0b",
        "FocusGuard.swift": "ab78c7d374169478a5f99c1a3000f9a6180338b78e2f250e5ff1446f7e19345d"}

def source_rows():
    rows = []
    for name, expected in pins.items():
        path = source / name
        assert path.is_file() and not path.is_symlink()
        data = path.read_bytes()
        assert sha(data) == expected
        rows.append({"path": str(path), "bytes": len(data), "sha256": expected})
    return rows

record = {"kind": "film_last_observer13_helpers_build_only", "success": False,
          "target": "arm64-apple-macosx13.0", "language_mode": "5",
          "requested_sdk_path": sdk, "commands": [], "binaries": {},
          "scope": "Build-only; no helper, App, native capture or UI execution"}

def command(argv, name, timeout=60):
    start = time.monotonic()
    result = subprocess.run(argv, capture_output=True, timeout=timeout)
    data = result.stdout + result.stderr
    path = out / name
    assert len(data) <= 131072
    path.write_bytes(data)
    record["commands"].append({"argv": argv, "exit_code": result.returncode,
        "duration_seconds": time.monotonic() - start,
        "log": {"path": str(path), "bytes": len(data), "sha256": sha(data)}})
    assert result.returncode == 0, name
    return data.decode()

try:
    manifest = source / "SHA256SUMS"
    assert sha(manifest.read_bytes()) == "8b6ac6b1c6997b8affedff173eb7f52626eb5e9c15eb3519505ba22bab1c9240"
    record["source_package_manifest_sha256"] = sha(manifest.read_bytes())
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        assert Path(name).name == name and sha((source / name).read_bytes()) == digest
    record["source_before"] = source_rows()
    record["compiler_version"] = subprocess.check_output([compiler, "-version"], text=True)
    record["actual_metadata"] = {}
    for name in ["FilmFirstLast", "FocusGuard"]:
        binary = out / name
        command([compiler, "-sdk", sdk, "-swift-version", "5", "-O", "-j", "2",
                 "-target", record["target"], "-module-cache-path", str(out / "module-cache"),
                 str(source / (name + ".swift")), "-o", str(binary)], name + ".compile.log")
        command(["codesign", "--verify", "--strict", str(binary)], name + ".signature.txt", 15)
        metadata = command(["xcrun", "vtool", "-show-build", str(binary)], name + ".build.txt", 15)
        minimum = re.findall(r"^\s*minos\s+(\S+)", metadata, re.M)
        embedded = re.findall(r"^\s*sdk\s+(\S+)", metadata, re.M)
        assert minimum == ["13.0"] and len(embedded) == 1
        assert command(["lipo", "-archs", str(binary)], name + ".arch.txt", 15).strip() == "arm64"
        record["actual_metadata"][name] = {"min_os": minimum[0], "embedded_sdk": embedded[0]}
        record["binaries"][name] = {"path": str(binary), "bytes": binary.stat().st_size,
                                    "sha256": sha(binary.read_bytes())}
    record["source_after"] = source_rows()
    assert record["source_before"] == record["source_after"]
    assert len({x["embedded_sdk"] for x in record["actual_metadata"].values()}) == 1
    record["actual_min_os"] = "13.0"
    record["actual_embedded_sdk"] = record["actual_metadata"]["FilmFirstLast"]["embedded_sdk"]
    record["sdk_metadata_note"] = "Actual embedded SDK is read from each binary, separately from requested headers."
    record["success"] = True
except Exception as error:
    record["error"] = type(error).__name__ + ": " + str(error)
(out / "build.json").write_text(json.dumps(record, indent=2) + "\n")
print(json.dumps({k: record[k] for k in ["kind", "success", "binaries"]}))
raise SystemExit(0 if record["success"] else 1)
