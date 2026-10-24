from pathlib import Path
import json
import plistlib
import shutil
import subprocess
import uuid
from macho import macho, sha

WORK = Path(__file__).resolve().parent
ROOT = WORK.parents[1]
original = ROOT/'outputs/macOS13/Gallery.app'
original_cli = ROOT/'outputs/macOS13/bin/gallery'
before = macho(original/'Contents/MacOS/Gallery')
assert before['sha256'] == '887173af876a3f802c68dfff7fef087f318cc6909a61ea4beff69dad536dfd7e'
assert sha(original_cli.read_bytes()) == '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5'

def run(*args):
    return subprocess.check_output(list(args), stderr=subprocess.STDOUT).decode()

run('codesign', '--verify', '--deep', '--strict', str(original))
run('codesign', '--verify', '--strict', str(original_cli))
assert run('lipo', '-archs', str(original/'Contents/MacOS/Gallery')).strip() == 'arm64'
assert run('lipo', '-archs', str(original_cli)).strip() == 'arm64'
native = run('xcrun', 'vtool', '-show-build', str(original/'Contents/MacOS/Gallery'))
native += run('xcrun', 'vtool', '-show-build', str(original_cli))
assert native.count('minos 13.0') == 2
assert plistlib.loads((original/'Contents/Info.plist').read_bytes())['LSMinimumSystemVersion'] == '13.0'
isolated = WORK/'isolated/Gallery.app'
assert not isolated.exists()
isolated.parent.mkdir()
run('/usr/bin/ditto', str(original), str(isolated))
(WORK/'bin').mkdir()
shutil.copy2(original_cli, WORK/'bin/gallery')
identifier = 'dev.bern.gallery.filmbaseline.' + uuid.uuid4().hex
info = isolated/'Contents/Info.plist'
raw = info.read_bytes(); values = plistlib.loads(raw)
original_identifier = values['CFBundleIdentifier']; values['CFBundleIdentifier'] = identifier
info.write_bytes(plistlib.dumps(values, fmt=plistlib.FMT_BINARY if raw.startswith(b'bplist') else plistlib.FMT_XML, sort_keys=False))
assert macho(isolated/'Contents/MacOS/Gallery')['sha256'] == before['sha256']
sign = run('/usr/bin/codesign', '--force', '--deep', '--sign', '-', '--identifier', identifier, str(isolated))
run('/usr/bin/codesign', '--verify', '--deep', '--strict', str(isolated))
after = macho(isolated/'Contents/MacOS/Gallery')
assert before['sections'] == after['sections']
assert before['signature_storage_sizes_normalized_sha256'] == after['signature_storage_sizes_normalized_sha256']
assert macho(original/'Contents/MacOS/Gallery')['sha256'] == before['sha256']
observer = ROOT/'outputs/Bern/.github/scripts/gallery-film-probe.swift'
assert sha(observer.read_bytes()) == '79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755'
shutil.copy2(observer, WORK/'gallery-film-probe.swift')
record = dict(source_sha='f9e08b1d55bed4b9d880b19934abe48281057bb3',
    source_build=39991406873, original_delivered_bundle=str(original),
    original_identifier=original_identifier, isolated_identifier=identifier,
    before=before, after=after, code_sections_equal=True,
    normalized_signature_storage_payload_equal=True,
    strict_signature_blob_excluded_payload_equal=before['signature_command_blob_excluded_sha256']==after['signature_command_blob_excluded_sha256'],
    original_delivered_bundle_unmodified=True, cli_sha256=sha(original_cli.read_bytes()),
    observer_commit='3f434cf0313d5657a136b1f98d0ac1293b60f169',
    observer_sha256=sha(observer.read_bytes()), native_build_commands=native,
    codesign_output=sign, ui_run=False, download=False, ci_dispatch=False,
    scope='Original delivered f9 build, not744 orcandidate. Unique localbundle/ad-hoc signature alters signedexe bytes but preserves code sectionhashes.',
    trace_contract='f9 has nointernal logger; RUN explicitly unsets BERN_SCROLL_TRACE_DIR. No synthetictrace or substitute744source.',
    timing_limit='Candidate had2s traceflush+after-tracecapture; thisbaseline doesnot. Actual stablePNG/AX geometry comparison isnot millisecond-identical timing.')
(WORK/'provenance.json').write_text(json.dumps(record, indent=2)+'\n')
print(json.dumps(dict(identifier=identifier, exact_gui_sha256=before['sha256'], isolated_gui_sha256=after['sha256'], cli_sha256=record['cli_sha256']), indent=2))
