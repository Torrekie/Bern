"""Bounded stock-Name-input session; never changes the delivered application."""
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import shutil
import subprocess
import sys
import time
import uuid

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
REPO = ROOT / 'outputs/Bern'
GUI_SHA = 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b'
CLI_SHA = '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2, ensure_ascii=False) + '\n')

def run(args, label, env=None, allow=False, timeout=15):
    p = subprocess.run([str(v) for v in args], capture_output=True, timeout=timeout, env=env)
    (HERE / (label + '.stdout')).write_bytes(p.stdout)
    (HERE / (label + '.stderr')).write_bytes(p.stderr)
    write(label + '.command.json', {'argv': [str(v) for v in args], 'returncode': p.returncode})
    if not allow:
        assert p.returncode == 0, label
    return p

def prepare():
    assert not (HERE / 'isolation.json').exists()
    original = ROOT / 'outputs/macOS13/Showcase.app'
    cli = ROOT / 'outputs/macOS13/bin/showcase'
    assert sha(original / 'Contents/MacOS/Showcase') == GUI_SHA and sha(cli) == CLI_SHA
    helper = REPO / 'Docs/Evidence/macOS13-film-first-last-e48-20261025/preparation/driver/prepare-film13.py'
    spec = importlib.util.spec_from_file_location('macho_only', helper)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    before = m.members(original)
    binary_before = m.macho(original / 'Contents/MacOS/Showcase')
    app = HERE / 'runtime/Showcase.app'
    app.parent.mkdir()
    run(['codesign', '--verify', '--deep', '--strict', original], 'original-signature')
    run(['codesign', '--verify', '--strict', cli], 'cli-signature')
    run(['ditto', original, app], 'copy')
    assert m.members(app) == before
    identifier = 'dev.bern.native13.input.' + uuid.uuid4().hex
    info = app / 'Contents/Info.plist'
    data = plistlib.loads(info.read_bytes())
    assert data['CFBundleExecutable'] == 'Showcase' and data['LSMinimumSystemVersion'] == '13.0'
    data['CFBundleIdentifier'] = identifier
    info.write_bytes(plistlib.dumps(data, sort_keys=False))
    run(['codesign', '--force', '--deep', '--sign', '-', '--identifier', identifier, app], 'private-sign')
    run(['codesign', '--verify', '--deep', '--strict', app], 'private-signature')
    after = m.members(app)
    changed = [p for p in before if before[p] != after[p]]
    assert set(changed) <= {'Contents/Info.plist', 'Contents/MacOS/Showcase', 'Contents/_CodeSignature/CodeResources'}
    binary_after = m.macho(app / 'Contents/MacOS/Showcase')
    assert binary_before['sections'] == binary_after['sections']
    assert binary_before['signature_storage_sizes_normalized_sha256'] == binary_after['signature_storage_sizes_normalized_sha256']
    assert m.members(original) == before
    for suffix in ['Library/Preferences/' + identifier + '.plist', 'Library/Saved Application State/' + identifier + '.savedState']:
        assert not (Path.home() / suffix).exists()
    source = REPO / 'Docs/Evidence/macOS13-film-first-last-e48-20261025/preparation/source/FocusGuard.swift'
    guard = source.read_text().replace('dev.bern.frame13.', 'dev.bern.native13.input.').replace('Gallery', 'Showcase')
    (HERE / 'FocusGuard.swift').write_text(guard)
    sdk = subprocess.check_output(['xcrun', '--sdk', 'macosx', '--show-sdk-path'], text=True).strip()
    run(['xcrun', 'swiftc', '-swift-version', '5', '-target', 'arm64-apple-macosx13.0', '-sdk', sdk,
         '-module-cache-path', HERE / 'module-cache', HERE / 'FocusGuard.swift', '-o', HERE / 'FocusGuard'], 'build-guard', timeout=90)
    run(['codesign', '--force', '--sign', '-', HERE / 'FocusGuard'], 'sign-guard')
    run(['codesign', '--verify', '--strict', HERE / 'FocusGuard'], 'guard-signature')
    run(['xcrun', 'vtool', '-show-build', HERE / 'FocusGuard'], 'guard-build-metadata')
    write('isolation.json', {'source_sha': '9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0',
        'app': str(app), 'cli': str(cli), 'identifier': identifier, 'original_app': str(original),
        'original_gui_sha256': GUI_SHA, 'cli_sha256': CLI_SHA, 'private_gui_sha256': sha(app / 'Contents/MacOS/Showcase'),
        'macho_sections_unchanged': True, 'normalized_non_signature_bytes_unchanged': True,
        'changed_members': changed, 'original_members': before, 'private_members': after,
        'macho_helper_source': str(helper), 'macho_helper_sha256': sha(helper),
        'guard_source_sha256': sha(HERE / 'FocusGuard.swift'), 'guard_sha256': sha(HERE / 'FocusGuard'),
        'guard_adaptation': 'Only private-identity prefix and exact executable basename changed; no cleanup ordering changes.',
        'requested_sdk': sdk, 'ipc': '/tmp/bern-native13-' + uuid.uuid4().hex[:12], 'deadline_seconds': 300,
        'scope': 'Existing stock Name input, draft/UI result and one Return submission. No product source changes or pixel comparison.'})

def watch():
    lock = json.loads((HERE / 'isolation.json').read_text())
    app = Path(lock['app']); guard = HERE / 'FocusGuard'
    env = {k:v for k,v in os.environ.items() if not k.startswith('BERN_')}
    env['BERN_IPC_DIR'] = lock['ipc']
    ipc = Path(lock['ipc']); ipc.mkdir(mode=0o700)
    write('environment.json', {'BERN_IPC_DIR': str(ipc), 'inherited_BERN_variables_removed': True,
        'appearance_and_motion': 'System defaults; no forced BERN render/appearance/motion or diagnostic observer.'})
    initial = json.loads(run([guard, 'inspect', app], 'before-launch').stdout)
    assert initial['own'] is None and initial['front']['kernel_start'] is not None
    write('original-front.json', initial['front'])
    child = None
    try:
        with (HERE / 'application.log').open('wb') as log:
            child = subprocess.Popen([str(app / 'Contents/MacOS/Showcase'), '-AppleLanguages', '(en)', '-AppleLocale', 'en_US'], env=env, stdout=log, stderr=log)
        deadline = time.monotonic() + 18
        while time.monotonic() < deadline and child.poll() is None:
            p = run([lock['cli'], 'sessions'], 'sessions', env=env, allow=True)
            try:
                sessions = json.loads(p.stdout)
                if p.returncode == 0 and len(sessions) == 1:
                    own = json.loads(run([guard, 'inspect', app], 'ready-identity').stdout)['own']
                    assert own['pid'] == child.pid and own['kernel_start'] is not None
                    write('own.json', own)
                    write('ready.json', {'pid': child.pid, 'session': sessions[0]['session_id'], 'ipc': str(ipc), 'cli': lock['cli']})
                    break
            except (ValueError, KeyError, TypeError):
                pass
            time.sleep(0.2)
        assert (HERE / 'ready.json').exists(), 'Startup did not become ready'
        deadline = time.monotonic() + lock['deadline_seconds']
        while time.monotonic() < deadline and not (HERE / 'finish').exists() and child.poll() is None:
            time.sleep(0.2)
    finally:
        cleanup = {'child_started': child is not None, 'deadline_or_finish': (HERE / 'finish').exists()}
        if child is not None and not (HERE / 'own.json').exists():
            inspection = json.loads(run([guard, 'inspect', app], 'early-cleanup-identity').stdout)
            if inspection['own'] is not None and inspection['own']['pid'] == child.pid:
                write('own.json', inspection['own'])
        if (HERE / 'own.json').exists():
            p = run([guard, 'cleanup', app, HERE / 'original-front.json', HERE / 'own.json'], 'cleanup-guard', allow=True)
            cleanup['guard_returncode'] = p.returncode
            cleanup['guard'] = json.loads(p.stdout)
        if child is not None:
            try: cleanup['child_exit'] = child.wait(timeout=4)
            except subprocess.TimeoutExpired: cleanup['child_exit'] = 'still-running-preserved'
        post = json.loads(run([guard, 'inspect', app], 'post-cleanup-identity').stdout)
        cleanup['post'] = post
        if post['own'] is None:
            identifier = lock['identifier']
            prefs = Path.home() / 'Library/Preferences' / (identifier + '.plist')
            state = Path.home() / 'Library/Saved Application State' / (identifier + '.savedState')
            if prefs.exists():
                run(['/usr/bin/defaults', 'delete', identifier], 'private-preferences-delete', timeout=60)
                if prefs.exists():
                    assert plistlib.loads(prefs.read_bytes()) == {}, 'Private domain was not cleared'
                    prefs.unlink()
            if state.exists():
                assert not state.is_symlink()
                shutil.rmtree(state)
            temporary_state = Path(os.environ['TMPDIR']) / (identifier + '.savedState')
            if temporary_state.exists():
                assert not temporary_state.is_symlink()
                shutil.rmtree(temporary_state)
            cleanup['temporary_saved_state_absent'] = not temporary_state.exists()
            cleanup['ipc_members_before_removal'] = [str(p.relative_to(ipc)) for p in ipc.rglob('*')]
            assert not any(p.is_symlink() for p in ipc.rglob('*'))
            shutil.rmtree(ipc)
            cleanup['ipc_absent'] = not ipc.exists()
            cleanup['private_preferences_absent'] = not prefs.exists()
            cleanup['private_saved_state_absent'] = not state.exists()
        cleanup['original_gui_unchanged'] = sha(Path(lock['original_app']) / 'Contents/MacOS/Showcase') == GUI_SHA
        cleanup['original_cli_unchanged'] = sha(Path(lock['cli'])) == CLI_SHA
        write('cleanup.json', cleanup)

if __name__ == '__main__':
    assert len(sys.argv) == 2 and sys.argv[1] in ['prepare', 'watch']
    {'prepare': prepare, 'watch': watch}[sys.argv[1]]()
