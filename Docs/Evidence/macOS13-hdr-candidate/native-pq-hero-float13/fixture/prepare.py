#!/usr/bin/env python3
"""Source-only isolated extraction; never compiles or launches the fixture."""
from pathlib import Path
import difflib
import hashlib
import json
import subprocess

D = Path(__file__).resolve().parent
REPO = D.parents[1] / 'outputs/Bern'
PIN = '34dbeff0c4a9ab07828e8459ea990efba2f9fbf2'
PRIOR = '1a77dd3165ea420e64d422ae62a49dadf9aa31f5'
SHARED = '.github/scripts/hero-snapshot-probe/'
LOCAL = D.parents[1] / 'work/native-pq-hero-cgmetadata-local13'
sha = lambda b: hashlib.sha256(b).hexdigest()
def source(name, ref=PIN):
    return subprocess.check_output(['git', 'show', f'{ref}:{SHARED}{name}'], cwd=REPO)

names = ['Dependencies.swift', 'ProductImage.exact.swift', 'ProductStyle.exact.swift',
         'ProductStyle.swift', 'ProductHero.exact.swift', 'assets/source-named-pq.png',
         'assets/source-ffb-icc.png']
files = {name: source(name) for name in names}
driver = source('Driver.swift.inc').decode()
hero = source('ProductHero.base.swift').decode()
assert driver == source('Driver.swift.inc', PRIOR).decode()
assert hero == source('ProductHero.base.swift', PRIOR).decode()
assert driver.encode() == (LOCAL / 'Driver.swift.inc').read_bytes()
files['Driver.v2.base.swift.inc'] = driver.encode()
files['ProductHero.v2.base.swift'] = hero.encode()
files['ProductImage.v2.base.swift'] = source('ProductImage.swift')
files['source-provenance.v2.base.json'] = source('source-provenance.json')
files['ProductImage.swift'] = (LOCAL / 'ProductImage.swift').read_bytes()
files['sdk14-unreachable-gainmap.patch'] = (LOCAL / 'sdk14-unreachable-gainmap.patch').read_bytes()
files['local-sdk14-clock.patch'] = (LOCAL / 'local-sdk14-clock.patch').read_bytes()
local_combined = (LOCAL / 'ProductHero.swift').read_text()
assert local_combined.endswith(driver)
clocked = local_combined[:-len(driver)]
old_clock = '                MainActor.assumeIsolated { self?.tick() }\n'
new_clock = '''                #if compiler(>=6.0)
                MainActor.assumeIsolated { self?.tick() }
                #else
                // Diagnostic SDK14.2 only: this static-endpoint fixture must
                // never start the coordinator's clock. Keep the actual14 call.
                if #available(macOS 14, *) {
                    MainActor.assumeIsolated { self?.tick() }
                } else {
                    preconditionFailure("Static endpoint fixture unexpectedly started its excluded timer")
                }
                #endif
'''
assert hero.count(old_clock) == 1
assert clocked == hero.replace(old_clock, new_clock)
files['ProductHero.clock-adapted.swift'] = clocked.encode()

changes = [
    ('    fixtureSnapshotCGImageObservations.append(FixtureSnapshotCGImageDescriptor(scalars: record, space: space))\n',
     '    fixtureSnapshotCGImageObservations.append(FixtureSnapshotCGImageDescriptor(scalars: record, space: space))\n    FixtureSnapshotFloatCapture.observe(image, key: key)\n'),
    ('    @MainActor static func main() { exit(run()) }',
     '    @MainActor static func main() {\n        let status = run()\n        exit(status == 0 && FixtureSnapshotFloatCapture.finalizationFailed ? 1 : status)\n    }'),
    ('        defer {\n            let observationsBeforeCleanup',
     '        defer {\n            FixtureSnapshotFloatCapture.freezePrimary()\n            let observationsBeforeCleanup'),
    ('            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)\n',
     '            try FileManager.default.createDirectory(at: output, withIntermediateDirectories: true)\n            guard FixtureFloatCaptureMode.selected != nil else {\n                throw FixtureFailure(message: "Invalid BERN_HERO_FLOAT_CAPTURE; off/on required before window creation")\n            }\n'),
    ('            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString\n',
     '            report["os"] = ProcessInfo.processInfo.operatingSystemVersionString\n            let floatCapture = FixtureSnapshotFloatCapture.finish(output: output, acquisitionSucceeded: report["success"] as? Bool == true)\n            report["snapshot_float_capture"] = floatCapture\n            if floatCapture["success"] as? Bool != true {\n                report["success"] = false\n                if report["error"] == nil { report["error"] = floatCapture["error"] }\n            }\n'),
    ('No retained image, observer pixel/provider readback, NSImage recache, conversion or relabel. Not a zero-observer-effect claim.',
     'The v2 metadata observer retains no image; separate opt-in raw capture lifetime/provider reads are reported in snapshot_float_capture. No NSImage recache, conversion or relabel. Not a zero-observer-effect claim.'),
]
derived = driver
for old, new in changes:
    assert derived.count(old) == 1, old
    derived = derived.replace(old, new)
undo = derived
for old, new in reversed(changes):
    assert undo.count(new) == 1
    undo = undo.replace(new, old)
assert undo == driver
files['Driver.swift.inc'] = derived.encode()
files['float-capture-driver.patch'] = ''.join(difflib.unified_diff(
    driver.splitlines(True), derived.splitlines(True),
    fromfile='committed-v2/Driver.swift.inc', tofile='isolated-float/Driver.swift.inc')).encode()
include = (D / 'FloatCapture.swift.inc').read_bytes()
files['ProductHero.swift'] = clocked.encode() + include + b'\n' + derived.encode()
files['local-image-imports-and-sdk14.patch'] = ''.join(difflib.unified_diff(
    files['ProductImage.v2.base.swift'].decode().splitlines(True), files['ProductImage.swift'].decode().splitlines(True),
    fromfile='committed-v2/ProductImage.swift', tofile='local-SDK14/ProductImage.swift')).encode()
for name, raw in files.items():
    path = D / name
    if path.exists() and path.read_bytes() != raw:
        raise SystemExit(f'Refuse to overwrite differing derived source: {name}')
for name, raw in files.items():
    path = D / name; path.parent.mkdir(parents=True, exist_ok=True); path.write_bytes(raw)

generated = {f.relative_to(D).as_posix(): {'sha256': sha(f.read_bytes()), 'bytes': f.stat().st_size}
             for f in sorted(D.rglob('*')) if f.is_file() and f.name not in ('source-provenance.json', 'SHA256SUMS', 'static-validation.json')}
provenance = {
    'base_harness_commit': PIN, 'prior_harness_commit_identical_driver_hero': PRIOR,
    'product_source_commit': 'b08db54e01ac2ec54fb84e6f2a70041f1f4c3604',
    'immutable_driver_sha256': sha(driver.encode()), 'immutable_hero_base_sha256': sha(hero.encode()),
    'local_sdk14_source_archive': str(LOCAL.resolve()),
    'local_adaptations': ['Exact archived gain-map compiler guard/imports', 'Exact archived unused-clock compiler/availability guard'],
    'diagnostic_change': 'Process-cached off/on; on retains at most the two original primary renderer CGImages, freezes before original cleanup, exports each provider once after teardown with strict layout/length and4MiB raw budget, then releases fixture references. Off retains no image and reads no snapshot provider.',
    'unchanged': ['Actual snapshot renderer/colorMode/NSImage construction and Flight.draw', 'Existing v2 ICC metadata serialization after teardown', 'Original window/panes/fit/two phases/five raw buffers/normal/front/cache/noMetal/noTimer/deadlines', 'Outer wrapper timeout15seconds'],
    'no_row_direction_or_zero_observer_effect_claim': True,
    'prepared_only': 'No Swift compilation, runtime, UI/CI, publication, product/harness/index modification.',
    'generated_files': generated,
}
(D / 'source-provenance.json').write_text(json.dumps(provenance, indent=2, sort_keys=True) + '\n')
manifest = []
for f in sorted(D.rglob('*')):
    if f.is_file() and f.name not in ('SHA256SUMS', 'static-validation.json'):
        manifest.append(sha(f.read_bytes()) + '  ' + f.relative_to(D).as_posix() + '\n')
(D / 'SHA256SUMS').write_text(''.join(manifest))
print(json.dumps({'prepared': True, 'base_commit': PIN, 'source_files': len(manifest),
                  'source_provenance_sha256': sha((D / 'source-provenance.json').read_bytes())}))
