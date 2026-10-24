"""Reuse the frozen app-cohort pixel functions; no new registration or images."""
import importlib.util, json, sys, hashlib
from pathlib import Path

assert len(sys.argv) == 5, 'FROZEN_ANALYZER LEFT_RUNTIME RIGHT_RUNTIME FRESH_OUTPUT'
script, left, right, output = map(lambda p: Path(p).resolve(), sys.argv[1:])
assert not output.exists()
spec = importlib.util.spec_from_file_location('frozen_app_pixels', script)
module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
inputs = {}
a = module.load_runtime(left, ['before', 'settled'], inputs)
b = module.load_runtime(right, ['before', 'settled'], inputs)
assert a['report']['actual_os_major'] == b['report']['actual_os_major']
checks = {}
for phase, roi in [('before', 'source'), ('settled', 'destination')]:
    checks[phase] = module.compare(a, phase, roi, b, phase, roi)
success = all(row[mode]['exact'] for row in checks.values() for mode in ('raw', 'srgb'))
result = {'exact_endpoint_controls':success, 'checks':checks, 'inputs':inputs,
          'analyzer_path':str(script), 'analyzer_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),
          'scope':'Corresponding measured opaque endpoint ROIs within one OS major, raw and ICC intent0 sRGB; host/display identity remains a separate observation. No mid registration, source-to-destination equality or general visual acceptance'}
output.parent.mkdir(parents=True, exist_ok=True)
output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({'exact_endpoint_controls':success, 'checks':checks},indent=2))
raise SystemExit(0 if success else 1)
