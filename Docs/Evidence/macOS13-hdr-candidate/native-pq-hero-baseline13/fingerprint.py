from pathlib import Path
import datetime, hashlib, json, os, subprocess
D=Path(__file__).resolve().parent
def call(args):
    p=subprocess.run(args,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
    return {'exit_code':p.returncode,'output':p.stdout}
names=['Dependencies.swift','ProductImage.exact.swift','ProductImage.swift','ProductStyle.exact.swift','ProductStyle.swift','ProductHero.exact.swift','ProductHero.base.swift','ProductHero.swift','Driver.swift.inc','prepare.py','source-provenance.json','sdk14-unreachable-gainmap.patch','sdk14-unused-clock.patch','compose.py','build.sh','fingerprint.py','HeroBaselineProbe','build.log','build-attempt-1.log']
report={'built_at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hashes':{n:hashlib.sha256((D/n).read_bytes()).hexdigest() for n in names},
    'target':'arm64-apple-macos13.0','language_mode':'5','optimization':'O','jobs':2,
    'swift':call(['xcrun','swiftc','--version']),'sdk':call(['xcrun','--show-sdk-version']),
    'file':call(['file',str(D/'HeroBaselineProbe')]),
    'mach_build':call(['xcrun','vtool','-show-build',str(D/'HeroBaselineProbe')]),
    'codesign_verify':call(['codesign','--verify','--strict',str(D/'HeroBaselineProbe')]),
    'codesign':call(['codesign','-dvvv',str(D/'HeroBaselineProbe')]),
    'driver_composition_policy':'Exact base plus one recorded compiler/availability guard in the excluded timer callback plus same-file driver. Runtime check requires coordinator timer absent/flight_count0. Not complete unmodified coordinator compilation or flight validation.',
    'hero_base_matches_extraction':hashlib.sha256((D/'ProductHero.base.swift').read_bytes()).hexdigest()==json.loads((D/'source-provenance.json').read_text())['generated_files']['ProductHero.swift']['sha256'],
    'warning_policy':'Existing product exhaustive-switch warning retained; no product warning suppression.'}
assert report['hero_base_matches_extraction']
assert report['codesign_verify']['exit_code']==0
(D/'build-fingerprint.json').write_text(json.dumps(report,indent=2,sort_keys=True)+'\n')
print(json.dumps({'binary_sha256':report['hashes']['HeroBaselineProbe'],'strict_signature':True,'exact_hero_base_retained':True,'unused_clock_adaptation_recorded':True}))
