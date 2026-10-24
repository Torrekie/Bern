#!/usr/bin/env python3
from pathlib import Path
import datetime
import hashlib
import json
import subprocess

D = Path(__file__).resolve().parent
def call(args):
    p = subprocess.run(args, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    return {'argv': args, 'exit_code': p.returncode, 'output': p.stdout}

names = ['Dependencies.swift', 'ProductImage.swift', 'ProductStyle.swift', 'ProductHero.swift',
         'Driver.swift.inc', 'source-provenance.json', 'color-mode-snapshot.patch',
         'color-mode-driver.patch', 'sdk14-unreachable-gainmap.patch', 'sdk14-unused-clock.patch',
         'build.sh', 'verify_sources.py', 'fingerprint.py', 'build-environment.txt', 'build.log', 'HeroColorModeProbe']
report = {
    'built_at_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'hashes': {n: hashlib.sha256((D / n).read_bytes()).hexdigest() for n in names},
    'target': 'arm64-apple-macos13.0', 'language_mode': '5', 'optimization': 'O', 'jobs': 2,
    'swift': call(['xcrun', 'swiftc', '--version']), 'sdk': call(['xcrun', '--show-sdk-version']),
    'file': call(['file', str(D / 'HeroColorModeProbe')]),
    'mach_build': call(['xcrun', 'vtool', '-show-build', str(D / 'HeroColorModeProbe')]),
    'codesign_verify': call(['codesign', '--verify', '--strict', str(D / 'HeroColorModeProbe')]),
    'codesign': call(['codesign', '-dvvv', str(D / 'HeroColorModeProbe')]),
    'source_policy': 'Archived successful fixture plus public colorMode diagnostic setter/config/report only. Full actual snapshot/draw and inherited SDK14 adaptations retained.',
    'warning_policy': 'No warning suppression or warnings-as-errors assertion; preserve actual compiler log.',
}
assert report['codesign_verify']['exit_code'] == 0
(D / 'build-fingerprint.json').write_text(json.dumps(report, indent=2, sort_keys=True) + '\n')
print(json.dumps({'binary_sha256': report['hashes']['HeroColorModeProbe'], 'strict_signature': True}))
