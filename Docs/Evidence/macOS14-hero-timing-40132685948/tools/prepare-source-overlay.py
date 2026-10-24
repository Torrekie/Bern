"""Prepare the five-file source overlay and a temporary standalone package."""
import hashlib,json,shutil,subprocess
from pathlib import Path
workspace=Path(__file__).resolve().parent.parent
repo=workspace/'outputs/Bern';base=repo/'.github/scripts/hero-coordinator-sdr-probe'
prep=workspace/'work/hero-coordinator-timing-preparation'
overlay=repo/'.github/scripts/hero-timing-probe'
package=workspace/'work/hero-timing-20261025/package-source'
assert not overlay.exists() and not package.exists()
overlay.mkdir();package.parent.mkdir();shutil.copytree(base,package)
base_commit='4fc027626aa33b5140a4881708a100fc4d2a7c7d'
base_map=json.loads((base/'source-provenance.json').read_text())
for name,meta in base_map['files'].items():
    data=subprocess.check_output(['git','show',base_commit+':.github/scripts/hero-coordinator-sdr-probe/'+name],cwd=repo)
    assert data==(base/name).read_bytes() and hashlib.sha256(data).hexdigest()==meta['sha256'],name
for name in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc'):
    shutil.copyfile(prep/name,overlay/name);shutil.copyfile(prep/name,package/name)
readme='''# Bounded native/sampler timing observation

This five-file overlay reuses the committed hero-coordinator-sdr-probe source
package, exact image/style/dependency inputs, named asset and run-one wrapper.
Build copies that package and overwrites these five files. Assemble the same
AppKit/SwiftUI imports + ProductHero.swift + FlightSDR.swift.inc + Driver.swift.inc
into CoordinatorSDR.assembled.swift; only the executable name is HeroTimingProbe.
SDK26.2/arm64/min13 and ordinary NSApplication.run remain. This cohort runs only
default on13/14; no repeated SDR candidate experiment is performed.

The diagnostic adds bounded in-memory scalar timing around the existing native
timer registration, first tick/applied progress, sampler callback/prologue and
weak-wrapper matching. No extra native/window/image queries, timers, dispatches,
layout/flush, image retention or animation assignments are added. Original
motion, phase band, deadlines, PNG limits and native/execution/SDR assertions
remain. Partial acquisition stays failed even if timing coverage is complete.
All serialization follows original teardown. Recorded monotonic boundaries are
not rendered-frame synchronization, first-visible-frame timestamps or a unique
root cause. No product code/UI widget or deployment baseline is changed.
'''
(overlay/'README.md').write_text(readme);(package/'README.md').write_text(readme)
digest=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
data={k:v for k,v in base_map.items() if k not in ('files','kind','scope','source_preparation_manifest_sha256')}
data.update(kind='actual_coordinator_timing_fixture',
            base_source_commit=base_commit,base_source_path='.github/scripts/hero-coordinator-sdr-probe',
            scope='Default13/14 bounded scalar trace; original native/SDR gates preserved, no product adoption or complete UI acceptance',
            files={p.relative_to(package).as_posix():{'bytes':p.stat().st_size,'sha256':digest(p)}
                   for p in sorted(package.rglob('*')) if p.is_file() and p.name!='source-provenance.json'})
text=json.dumps(data,indent=2,sort_keys=True)+'\n'
(overlay/'source-provenance.json').write_text(text);(package/'source-provenance.json').write_text(text)
print(json.dumps({'overlay_files':len(list(overlay.iterdir())),'package_input_files':len(data['files']),
                  'provenance_sha256':digest(overlay/'source-provenance.json')},indent=2))
