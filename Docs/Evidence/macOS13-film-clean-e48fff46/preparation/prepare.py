from pathlib import Path
import hashlib
import json
import plistlib
import shutil
import subprocess
import tarfile
import uuid
from macho import macho, sha

ROOT = Path(__file__).resolve().parent
BUILD = ROOT/'build'
LOCAL = ROOT/'local13'
SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
HARNESS = '25e18cbc7cd760c1c399042f1d7364c3d755a9dc'
OBSERVER = '79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755'

def run(*args):
    return subprocess.check_output(list(args), stderr=subprocess.STDOUT).decode()

environment = dict(line.split('=', 1) for line in (BUILD/'environment.txt').read_text().splitlines() if '=' in line)
assert environment['source_repository'] == 'Torrekie/Bern'
assert environment['source_sha'] == SOURCE and environment['harness_sha'] == HARNESS
artifact = json.loads((BUILD/'artifact.json').read_text())
assert artifact['workflow_run']['head_sha'] == HARNESS
assert artifact['workflow_run']['id'] == 40070407306
metadata = json.loads((BUILD/'build.json').read_text())
assert all(metadata[k] == v for k, v in {
    'app_bundle':'Gallery.app', 'architecture':'arm64', 'minimum_macos':'13.0',
    'platform':'macos', 'protocol':'gallery', 'ui':'swiftui-modern',
}.items())
archive = BUILD/'gallery.tar.gz'
archive_hash = sha(archive.read_bytes())
assert (BUILD/'gallery.tar.gz.sha256').read_text().split()[0] == archive_hash
exact = BUILD/'exact'
assert not exact.exists()
exact.mkdir()
with tarfile.open(archive) as package:
    names = set()
    for member in package.getmembers():
        name = Path(member.name)
        assert not name.is_absolute() and '..' not in name.parts
        assert member.isdir() or member.isfile()
        assert name.parts[0] in ('Gallery.app', 'bin')
        assert member.name not in names
        names.add(member.name)
    package.extractall(exact)
app = exact/'Gallery.app'
cli = exact/'bin/gallery'
assert run('lipo','-archs',str(app/'Contents/MacOS/Gallery')).strip() == 'arm64'
assert run('lipo','-archs',str(cli)).strip() == 'arm64'
assert plistlib.loads((app/'Contents/Info.plist').read_bytes())['LSMinimumSystemVersion'] == '13.0'
native = run('xcrun','vtool','-show-build',str(app/'Contents/MacOS/Gallery'))
native += run('xcrun','vtool','-show-build',str(cli))
assert native.count('minos 13.0') == 2 and native.count('sdk 26.2') == 2
run('codesign','--verify','--deep','--strict',str(app))
run('codesign','--verify','--strict',str(cli))
LOCAL.mkdir()
isolated = LOCAL/'isolated/Gallery.app'
isolated.parent.mkdir()
run('ditto',str(app),str(isolated))
before = macho(app/'Contents/MacOS/Gallery')
identifier = 'dev.bern.gallery.filmclean.'+uuid.uuid4().hex
info = isolated/'Contents/Info.plist'
raw = info.read_bytes(); values = plistlib.loads(raw)
original_identifier = values['CFBundleIdentifier']; values['CFBundleIdentifier'] = identifier
info.write_bytes(plistlib.dumps(values,fmt=plistlib.FMT_BINARY if raw.startswith(b'bplist') else plistlib.FMT_XML,sort_keys=False))
assert macho(isolated/'Contents/MacOS/Gallery')['sha256'] == before['sha256']
sign = run('codesign','--force','--deep','--sign','-','--identifier',identifier,str(isolated))
run('codesign','--verify','--deep','--strict',str(isolated))
after = macho(isolated/'Contents/MacOS/Gallery')
assert before['sections'] == after['sections']
assert before['signature_storage_sizes_normalized_sha256'] == after['signature_storage_sizes_normalized_sha256']
assert macho(app/'Contents/MacOS/Gallery')['sha256'] == before['sha256']
cli_hash = sha(cli.read_bytes())
assert cli_hash == '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5'
observer = ROOT.parents[1]/'outputs/Bern/.github/scripts/gallery-film-probe.swift'
assert sha(observer.read_bytes()) == OBSERVER
shutil.copy2(observer,LOCAL/'gallery-film-probe.swift')
repo = ROOT.parents[1]/'outputs/Bern'
style_hash = sha(subprocess.check_output(['git','-C',str(repo),'show',SOURCE+':crates/bern-backend-swiftui/templates/BernStyle.swift']))
runtime_hash = sha(subprocess.check_output(['git','-C',str(repo),'show',SOURCE+':crates/bern-backend-swiftui/templates/BernRuntime.swift']))
assert style_hash == '3912ecdbe102508771174df91f4d7baa153cca9925d89f6e68cdffc2e90cbd89'
assert runtime_hash == '255bacb40db71fa17a8bd9ecaefc1b72c187864295221727c28653a09839e16e'
provenance = dict(source_sha=SOURCE,build_harness_sha=HARNESS,build_run=40070407306,
    artifact=artifact,archive_sha256=archive_hash,gui_sha256=before['sha256'],cli_sha256=cli_hash,
    source_style_sha256=style_hash,source_runtime_sha256=runtime_hash,native_build_commands=native,
    architecture='arm64',minimum_macos='13.0',sdk='26.2',swift='6.2.4',ui='swiftui-modern',
    offline_signature_verification='Exact GUI/CLI and isolated GUI pass strict checks',
    exact_original_bundle_unchanged=True,existing_delivered_f9_bundle_untouched=True,
    app_or_cli_launched=False,source_scope='Clean initial-position Style; existing9dd Runtime/HDR preserved. No logger/nativeSnapshot.',
    extraction='ZIP digest checked against GitHub artifact; ZIP/TAR member paths/types/top-level allowlist checked before extraction')
(BUILD/'provenance.json').write_text(json.dumps(provenance,indent=2)+'\n')
isolation = dict(source_sha=SOURCE,build_run=40070407306,original_identifier=original_identifier,
    isolated_identifier=identifier,before=before,after=after,section_records_equal=True,
    normalized_signature_storage_payload_equal=True,codesign_output=sign,
    exact_original_bundle_unchanged=True,cli_sha256=cli_hash,
    scope='Same built code sections; unique local bundle identity and ad-hoc signature alter full executable bytes. No application or CLI was launched.')
(LOCAL/'isolation-provenance.json').write_text(json.dumps(isolation,indent=2)+'\n')
# Preserve exact extracted app/CLI; remove only redundant downloaded compression layers.
(BUILD/'download-cleanup.json').write_text(json.dumps(dict(artifact_zip_sha256=sha((BUILD/'artifact.zip').read_bytes()),
    tar_sha256=archive_hash,removed_logical_bytes=(BUILD/'artifact.zip').stat().st_size+archive.stat().st_size,
    exact_extracted_app_and_cli_retained=True),indent=2)+'\n')
(BUILD/'artifact.zip').unlink(); archive.unlink()
print(json.dumps(dict(exact_gui_sha256=before['sha256'],isolated_gui_sha256=after['sha256'],cli_sha256=cli_hash,
    isolated_identifier=identifier,observer_sha256=OBSERVER,style_sha256=style_hash,runtime_sha256=runtime_hash),indent=2))
