#!/usr/bin/env python3
from pathlib import Path
import hashlib
import json

D = Path(__file__).resolve().parent
p = json.loads((D / 'source-provenance.json').read_text())
for name, info in p['generated_files'].items():
    data = (D / name).read_bytes()
    assert len(data) == info['bytes'] and hashlib.sha256(data).hexdigest() == info['sha256'], name
assert hashlib.sha256((D / 'NativeCI.swift.inc').read_bytes()).hexdigest() == p['native_ci_helper_sha256']
print(json.dumps({'generated_sources_verified': len(p['generated_files']), 'compiled_or_run': False}))
