#!/usr/bin/env python3
"""Package two private identities from one local compiled Scene executable."""
import hashlib
import importlib.util
import json
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys

root = Path(__file__).resolve().parent
compiled = root / 'Showcase'
assert compiled.is_file()
audit = root.parents[1] / 'outputs/Bern/Docs/Evidence/macOS13-toolbar-title-host-f6/capture-pair/run-pair.py'
spec = importlib.util.spec_from_file_location('bern_prior_macho_audit', audit)
module = importlib.util.module_from_spec(spec)
sys.dont_write_bytecode = True
spec.loader.exec_module(module)
compiled_macho = module.macho(compiled)
report = {'single_compiled_executable': compiled_macho, 'apps': {},
          'comparison': 'Info.plist/signature may differ; all Mach-O sections and signature-storage-normalized non-signature bytes must match the one compiler output'}
for mode in ['true', 'false']:
    app = root / ('ShowsTitle-' + mode + '.app')
    assert not app.exists()
    exe = app / 'Contents/MacOS/Showcase'
    exe.parent.mkdir(parents=True)
    shutil.copy2(compiled, exe)
    with (app / 'Contents/Info.plist').open('wb') as f:
        plistlib.dump({'CFBundleExecutable': 'Showcase',
                      'CFBundleIdentifier': 'dev.bern.toolbar-showstitle.r20261025.' + mode,
                      'CFBundleName': 'Toolbar Scene Probe', 'CFBundlePackageType': 'APPL',
                      'CFBundleVersion': '1', 'CFBundleShortVersionString': '1.0',
                      'LSMinimumSystemVersion': '13.0', 'NSPrincipalClass': 'NSApplication',
                      'NSHighResolutionCapable': True}, f)
    subprocess.run(['codesign', '--force', '--sign', '-', str(app)], check=True, capture_output=True)
    verify = subprocess.run(['codesign', '--verify', '--deep', '--strict', str(app)], check=True, capture_output=True)
    info = module.macho(exe)
    assert info['sections'] == compiled_macho['sections']
    assert info['signature_storage_sizes_normalized_sha256'] == compiled_macho['signature_storage_sizes_normalized_sha256']
    report['apps'][mode] = {'path': str(app), 'members': module.members(app), 'macho': info,
                            'strict_codesign_verify_returncode': verify.returncode}
(root / 'prepare.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({'success': True, 'compiled_sha256': hashlib.sha256(compiled.read_bytes()).hexdigest(),
                  'modes': list(report['apps'])}))
