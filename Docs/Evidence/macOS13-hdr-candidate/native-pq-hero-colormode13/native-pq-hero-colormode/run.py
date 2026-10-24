#!/usr/bin/env python3
"""One explicitly selected process only; never starts a mode matrix."""
from pathlib import Path
import datetime
import hashlib
import json
import subprocess
import sys
import time

D = Path(__file__).resolve().parent
REPO = D.parents[1] / 'outputs/Bern'
assert len(sys.argv) == 2, 'Supply one new output directory'
output = Path(sys.argv[1]).expanduser().resolve()
assert not output.exists(), 'Refuse to overwrite retained runtime evidence'
assets = REPO / 'Docs/Evidence/macOS13-hdr-candidate/color-probe13'
inputs = [assets / 'source-named-pq.png', assets / 'source-ffb-icc.png']
expected = ['3efb40d42933dade20c11d2654d86afd25b1e02c838d9b080bb1233faa36da5b',
            'fa3fdc43d91518c145c08b01ba6181ec063c68158e57d312a1ff942571c2a12e']
assert [hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs] == expected
binary = D / 'HeroColorModeProbe'
fp = json.loads((D / 'build-fingerprint.json').read_text())
assert hashlib.sha256(binary.read_bytes()).hexdigest() == fp['hashes']['HeroColorModeProbe']
output.mkdir(parents=True)
command = [str(binary), *[str(p) for p in inputs], str(output)]
start = time.monotonic()
receipt = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'command': command,
           'assets': {str(p.relative_to(REPO)): h for p, h in zip(inputs, expected)},
           'binary_sha256': fp['hashes']['HeroColorModeProbe'], 'timeout_seconds': 15}
with (output / 'runtime.log').open('w') as log:
    p = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT)
    receipt['own_pid'] = p.pid
    try:
        receipt['exit_code'] = p.wait(timeout=15)
    except subprocess.TimeoutExpired:
        p.kill()
        receipt['exit_code'] = p.wait()
        receipt['wrapper_timeout'] = True
receipt['elapsed_seconds'] = time.monotonic() - start
receipt['finished_utc'] = datetime.datetime.now(datetime.timezone.utc).isoformat()
(output / 'run-receipt.json').write_text(json.dumps(receipt, indent=2, sort_keys=True) + '\n')
print(json.dumps({k: receipt[k] for k in ['own_pid', 'exit_code', 'elapsed_seconds']}))
raise SystemExit(0 if receipt['exit_code'] == 0 else 1)
