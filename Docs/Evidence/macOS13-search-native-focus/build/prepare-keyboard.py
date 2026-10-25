import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import subprocess
import sys
import uuid

root = Path(__file__).resolve().parent
workspace = root.parents[1]
original = workspace / 'outputs/macOS13/Showcase.app'
cli = workspace / 'outputs/macOS13/bin/showcase'
private = root / 'Keyboard.app'
assert not private.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(original / 'Contents/MacOS/Showcase') == 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b'
assert sha(cli) == '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
helper = workspace / 'outputs/Bern/Docs/Evidence/macOS13-toolbar-title-host-f6/capture-pair/run-pair.py'
spec = importlib.util.spec_from_file_location('prior_macho_audit', helper)
module = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(module)
before = module.members(original)
machos = module.app_machos(original)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(original)], check=True, capture_output=True)
entitlements = subprocess.run(['codesign', '-d', '--entitlements', ':-', str(original)], check=True, capture_output=True)
assert entitlements.stdout in [b'', b'\n'], 'Unexpected original entitlements; do not strip'
subprocess.run(['ditto', str(original), str(private)], check=True, capture_output=True)
assert module.members(private) == before
identifier = 'dev.bern.search-native13.' + uuid.uuid4().hex
assert not (Path.home() / 'Library/Preferences' / (identifier + '.plist')).exists()
assert not (Path.home() / 'Library/Saved Application State' / (identifier + '.savedState')).exists()
info = private / 'Contents/Info.plist'
data = plistlib.loads(info.read_bytes())
data['CFBundleIdentifier'] = identifier
info.write_bytes(plistlib.dumps(data, sort_keys=False))
subprocess.run(['codesign', '--force', '--deep', '--sign', '-', '--identifier', identifier, str(private)], check=True, capture_output=True)
subprocess.run(['codesign', '--verify', '--deep', '--strict', str(private)], check=True, capture_output=True)
after = module.members(private)
signed = module.app_machos(private)
assert before.keys() == after.keys()
changed = [k for k in before if before[k] != after[k]]
assert set(changed) <= module.ALLOWED and machos.keys() == signed.keys()
for name in machos:
    assert machos[name]['sections'] == signed[name]['sections']
    assert machos[name]['signature_storage_sizes_normalized_sha256'] == signed[name]['signature_storage_sizes_normalized_sha256']
report = {'source_sha': '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0', 'original': str(original),
          'private': str(private), 'private_identifier': identifier, 'cli': str(cli), 'cli_sha256': sha(cli),
          'original_members': before, 'private_members': after, 'changed_members': changed,
          'original_machos': machos, 'private_machos': signed,
          'original_entitlements_stdout': entitlements.stdout.decode(),
          'original_entitlements_stderr': entitlements.stderr.decode(),
          'strict_original_private_codesign_passed': True,
          'focus_guard_sha256': sha(root / 'FocusGuard'), 'profile_reader_sha256': sha(root / 'Profile'),
          'profile_source_sha256': sha(root / 'Profile.swift')}
(root / 'keyboard-prepare.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'success': True, 'app': str(private), 'identifier': identifier, 'changed_members': changed}))
