#!/usr/bin/env python3
from pathlib import Path
import hashlib,json
D=Path(__file__).resolve().parent
p=json.loads((D/'source-provenance.json').read_text())
for name,meta in p['generated_files'].items():
    raw=(D/name).read_bytes()
    assert len(raw)==meta['bytes'] and hashlib.sha256(raw).hexdigest()==meta['sha256'],name
for line in (D/'SHA256SUMS').read_text().splitlines():
    wanted,name=line.split('  ',1)
    assert hashlib.sha256((D/name).read_bytes()).hexdigest()==wanted,name
print('Frozen source/manifest hashes verified; no build or UI performed by this verifier')
