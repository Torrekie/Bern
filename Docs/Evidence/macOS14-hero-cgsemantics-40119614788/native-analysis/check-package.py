#!/usr/bin/env python3
"""Hash the still-present exact package once before root cleanup; no commands/native code."""
import datetime
import hashlib
import json
import re
import sys
from pathlib import Path

assert len(sys.argv) == 3, 'check-package.py COHORT OUTPUT_JSON'
D = Path(sys.argv[1]).resolve(); out = Path(sys.argv[2]).resolve()
assert not out.exists()
inputs = {}
def fp(path):
    data = path.read_bytes(); value = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    inputs[str(path)] = value; return value
def load(path):
    fp(path); return json.loads(path.read_text())
receipt = load(D / 'package-verification-local.json')
binary = D / 'probe/HeroCGSemanticsProbe'
archive = D / 'build/hero-cgsemantics-probe.tar.gz'
assert fp(binary)['sha256'] == receipt['binary_sha256'] == '68974a3fe0ae28c23ef47de9657fbc6d34287bb36f50d12d6ac69d52b3eee334'
assert fp(archive)['sha256'] == receipt['archive_sha256'] == '2c1151e83775c0a214f3ff36e33f1160883175c8709a6a86456072c52053b014'
manifest = D / 'probe/SHA256SUMS'
assert fp(manifest)['sha256'] == receipt['package_manifest_sha256']
members = []
for line in manifest.read_text().splitlines():
    expected, name = line.split('  ', 1); q = Path(name)
    assert re.fullmatch('[0-9a-f]{64}', expected) and not q.is_absolute() and '..' not in q.parts
    assert fp(D / 'probe' / q)['sha256'] == expected, name
    members.append(name)
assert len(members) == len(set(members)) == 29 and sorted(members) == sorted(receipt['package_verified_members'])
source = load(D / 'probe/source-provenance.json')
assert source['kind'] == 'original_snapshot_cg_drawing_semantics_fixture'
assert source['product_source_commit'] == 'b08db54e01ac2ec54fb84e6f2a70041f1f4c3604'
assert source['fixture_base_commit'] == '5eca0e5904117d131e1129302d50d357e4234a15'
assert len(source['files']) == receipt['source_map_inputs_verified'] == 21
for name, meta in source['files'].items(): assert fp(D / 'probe' / name) == meta, name
assert b''.join((D / 'probe' / name).read_bytes() for name in ('ProductHero.base.swift', 'FloatCapture.swift.inc', 'Driver.swift.inc')) == (D / 'probe/ProductHero.swift').read_bytes()
assert receipt['archs'] == 'arm64' and 'valid on disk' in receipt['codesign_verify']
assert 'satisfies its Designated Requirement' in receipt['codesign_verify']
assert re.search(r'^\s*minos 13\.0\s*$', receipt['mach_build'], re.M)
assert re.search(r'^\s*sdk 26\.2\s*$', receipt['mach_build'], re.M)
result = {'complete': True, 'recorded_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'binary_sha256': receipt['binary_sha256'], 'tar_sha256': receipt['archive_sha256'],
    'package_members_currently_hashed': len(members), 'source_map_currently_hashed': len(source['files']),
    'assembly_exact': True, 'root_saved_build_and_signature': receipt,
    'scope': 'Actual package/binary/tar rehash before root cleanup; saved root arm64/min13/SDK26.2/strict-signature record checked, no fresh signing/compiler/native command.',
    'input_files': inputs}
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: result[k] for k in ('complete', 'binary_sha256', 'tar_sha256', 'package_members_currently_hashed', 'source_map_currently_hashed')}))
