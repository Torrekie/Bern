"""Compile/link the frozen observer only. Never execute the resulting binary."""
import hashlib
import json
import shutil
import struct
import subprocess
import time
from pathlib import Path

base = Path(__file__).resolve().parent
source = base / 'gallery-frame-reference.swift'
expected = '77e4bb6849ea226cb4bcc4bacac7b08197e8f5a18f4aa991752d81cea44c4db8'
digest = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert digest(source) == expected
build = base / 'aot'
assert not build.exists(), 'Do not overwrite a previously built observer'
build.mkdir()
cache = base / 'aot-module-cache'
assert not cache.exists()
compiler = subprocess.check_output(['xcrun', '--find', 'swiftc'], text=True).strip()
sdk = subprocess.check_output(['xcrun', '--show-sdk-path'], text=True).strip()
sdk_version = subprocess.check_output(['xcrun', '--show-sdk-version'], text=True).strip()
toolchain = subprocess.run([compiler, '--version'], text=True, capture_output=True, check=True)
binary = build / 'FrameObserver'
args = [compiler, '-swift-version', '5', '-target', 'arm64-apple-macos13.0',
        '-sdk', sdk, '-warnings-as-errors', '-module-cache-path', str(cache),
        str(source), '-o', str(binary)]
record = {'scope': 'AOT compile/link only; no observer/application/CLI/UI execution',
          'source_sha256': expected, 'source': str(source), 'compiler': compiler,
          'compiler_version': (toolchain.stdout + toolchain.stderr).strip(),
          'sdk': sdk, 'sdk_version': sdk_version, 'arguments': args, 'binary_executed': False}
started = time.monotonic()
try:
    with (build / 'build.log').open('w') as log:
        result = subprocess.run(args, stdout=log, stderr=subprocess.STDOUT, check=False)
    record['compiler_exit_code'] = result.returncode
    record['elapsed_seconds'] = time.monotonic() - started
    assert result.returncode == 0, 'AOT compile/link failed; inspect aot/build.log'
    record['binary_sha256'] = digest(binary)
    record['binary_bytes'] = binary.stat().st_size
    data = binary.read_bytes()
    magic, cpu, subtype, kind, count, command_bytes, flags, reserved = struct.unpack_from('<IiiIIIII', data)
    assert magic == 0xfeedfacf and cpu == 0x100000c and kind == 2
    offset, versions = 32, []
    fmt = lambda v: f'{v >> 16}.{(v >> 8) & 255}.{v & 255}'
    for _ in range(count):
        cmd, size = struct.unpack_from('<II', data, offset)
        assert size >= 8 and offset + size <= 32 + command_bytes
        if cmd == 0x32:
            platform, minimum, version, tools = struct.unpack_from('<IIII', data, offset + 8)
            versions.append({'platform': platform, 'minimum': fmt(minimum), 'sdk': fmt(version)})
        offset += size
    # Record the SDK requested at compile time separately from the SDK value
    # emitted by this local linker's LC_BUILD_VERSION. The required runtime
    # contract here is a macOS13 arm64 executable, not an assumed SDK field.
    assert len(versions) == 1 and versions[0]['platform'] == 1 and versions[0]['minimum'] == '13.0.0', versions
    record['architecture'] = 'arm64'
    record['load_build_version'] = versions[0]
    for name, command in [('signature.log', ['/usr/bin/codesign', '--verify', '--strict', '--verbose=2', str(binary)]),
                          ('signature-details.log', ['/usr/bin/codesign', '-d', '--verbose=4', str(binary)]),
                          ('linked-frameworks.txt', ['/usr/bin/otool', '-L', str(binary)])]:
        p = subprocess.run(command, text=True, capture_output=True, check=False)
        (build / name).write_text(p.stdout + p.stderr)
        assert p.returncode == 0, (name, p.returncode)
    assert '/CryptoKit.framework/' in (build / 'linked-frameworks.txt').read_text()
    assert digest(source) == expected
    record['strict_signature_valid'] = True
    record['cryptokit_linked_normally'] = True
finally:
    record['module_cache_logical_bytes_removed'] = sum(p.stat().st_size for p in cache.rglob('*') if p.is_file()) if cache.exists() else 0
    if cache.exists():
        shutil.rmtree(cache)
    record['module_cache_removed'] = not cache.exists()
    (build / 'build.json').write_text(json.dumps(record, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: record[k] for k in ['compiler_exit_code', 'source_sha256', 'binary_sha256', 'architecture', 'module_cache_removed']}))
