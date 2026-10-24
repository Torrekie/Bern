import hashlib, json, shutil
from pathlib import Path

root = Path(__file__).resolve().parent.parent
base = root / 'outputs/Bern/.github/scripts/hero-coordinator-app-probe'
prep = root / 'work/hero-coordinator-sdr-preparation'
ci = root / 'work/hero-coordinator-sdr-ci-preparation'
target = root / 'work/hero-coordinator-sdr-20261025/probe-source'
assert not target.exists()
target.mkdir(parents=True)
for name in ('Dependencies.swift', 'ProductHero.exact.swift', 'ProductImage.exact.swift',
             'ProductImage.swift', 'ProductStyle.exact.swift', 'ProductStyle.swift',
             'assets/source-named-pq.png'):
    (target/name).parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(base/name, target/name)
for name in ('ProductHero.swift', 'FlightSDR.swift.inc', 'Driver.swift.inc'):
    shutil.copyfile(prep/name, target/name)
shutil.copyfile(ci/'run-one.py', target/'run-one.py')
(target/'README.md').write_text('''# Private actual-coordinator SDR experiment

This extends the frozen actual NSApplication.run coordinator fixture with one
private Standard named-PQ snapshot display candidate. It is not product code or
whole-UI acceptance. Original timer, spring, drawing, scene and native gates
remain. macOS 14 runs default only; macOS 13 runs default before baked-pair.

Assemble imports AppKit/SwiftUI, ProductHero.swift, FlightSDR.swift.inc and
Driver.swift.inc into CoordinatorSDR.assembled.swift. Keep the separate exact
Image/Style/Dependencies inputs. Use the new SDK26.2 compiler targeting arm64
macOS13; no static clock guard, fake timer or actor shim is added.

BERN_HERO_FLIGHT_SDR=default observes each actual snapshot with scalar/space
metadata and weak references, without creating CI objects or retaining the
original CGImage. baked-pair uses the fixed native recipe separately for each
actual snapshot and one shared context: CIImage(toneMapHDRtoSDR:true, no space
override), exact extent, RGBA8/sRGB/deferred:false. Actual tone mapping remains
unknown. Invalid/incomplete geometry/layout/conversion/mapping fails without a
successful original-image fallback. Reports retain both same-key ordinals,
actual Flight.from/to NSImage identities and synchronous setup timestamps.

The original acquisition freezes before original cleanup; post-teardown metadata
serialization clears helper-owned cache/context/space/weak references. This
does not establish global deallocation or zero observer overhead. The original
native/execution gate remains the prefix; appended checks verify new evidence.
Before/mid/settled PNGs still require visibility/color/timing review. Mid PNGs
at different progress are not cross-OS pixel-equality targets. Production intent
routing, High/HLG/other input geometry and general animation are unverified.
''')
def digest(p): return hashlib.sha256(p.read_bytes()).hexdigest()
d = {
    'kind': 'actual_coordinator_sdr_fixture',
    'product_source_commit': 'b08db54e01ac2ec54fb84e6f2a70041f1f4c3604',
    'original_hero_sha256': digest(target/'ProductHero.exact.swift'),
    'assembly': 'imports AppKit/SwiftUI + ProductHero.swift + FlightSDR.swift.inc + Driver.swift.inc into CoordinatorSDR.assembled.swift',
    'local_compile_attempted': False,
    'no_sdk14_unused_clock_or_gainmap_guards_in_newsdk_package': True,
    'scope': 'Private actual Standard named transition; native gates and timing evidence only, no product adoption or complete visual acceptance',
    'source_preparation_manifest_sha256': digest(prep/'SHA256SUMS'),
    'files': {p.relative_to(target).as_posix(): {'bytes':p.stat().st_size,'sha256':digest(p)}
              for p in sorted(target.rglob('*')) if p.is_file()}
}
(target/'source-provenance.json').write_text(json.dumps(d, indent=2, sort_keys=True)+'\n')
print(json.dumps({'package':str(target),'files':len(d['files']),
                  'provenance_sha256':digest(target/'source-provenance.json')},indent=2))
