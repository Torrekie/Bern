from pathlib import Path
import hashlib, json, os, shutil, subprocess, tempfile

base = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent
report_path = out / 'retired-artifacts.json'
assert not report_path.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
receipts = [base / p for p in [
    'work/picture-local13-ab/A/isolation.json',
    'work/picture-local13-ab/B/isolation.json',
    'work/picture-local13-ab-v2/A2/isolation.json',
    'work/picture-local13-ab-v3/B3/isolation.json']]
rows = [json.loads(p.read_text()) for p in receipts]
private_apps = [Path(r['private_app']) for r in rows]
exact = base / 'work/picture-scene-observed14/exact'
tar = base / 'work/picture-scene-observed14/build/showcase-observer.tar.gz'
helpers = [base / 'work/picture-local13-build' / p for p in
           ['Collector', 'FocusGuard', 'v2/Collector', 'v2/FocusGuard']]
live = subprocess.check_output(['ps', '-axo', 'pid=,comm='], text=True)
protected_paths = [str(p) for p in private_apps] + [str(exact)] + [str(p) for p in helpers]
assert not any(any(p in line for p in protected_paths) for line in live.splitlines())
for row, app in zip(rows, private_apps):
    assert app.is_dir() and not app.is_symlink()
    actual = {str(p.relative_to(app)): sha(p) for p in app.rglob('*') if p.is_file()}
    assert actual == row['private_members'], str(app)
assert sha(exact / 'Showcase.app/Contents/MacOS/Showcase') == 'c1d27a0435bd145f08a098adaaf22c6718c1192da15367456afb7ff151c4c12c'
assert sha(exact / 'bin/showcase') == '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
assert sha(tar) == 'bea6ff27c3b4b085d8b7459307278537a30e76e7a59ee5a8136bcb7df147bf4e'
assert sha(base / 'outputs/macOS13/Showcase.app/Contents/MacOS/Showcase') == 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b'
assert sha(base / 'outputs/macOS13/bin/showcase') == '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
report = {'scope': 'Only completed task-owned Picture copies, temporary CI payload, helper binaries and exact private identities; original delivered App/CLI preserved. Module cache is excluded while the source-preparation agent uses it.',
          'live_owned_executable_matches': [], 'removed': [], 'absent_private_paths': [],
          'logical_bytes_removed': 0, 'physical_APFS_savings': 'not measured'}

def save():
    report_path.write_text(json.dumps(report, indent=2) + '\n')

def remove(path):
    if not path.exists() and not path.is_symlink():
        report['absent_private_paths'].append(str(path)); save(); return
    assert not path.is_symlink(), str(path)
    members = [path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file())
    assert all(not p.is_symlink() for p in members)
    inventory = [{'path': str(p.relative_to(path)) if p != path else path.name,
                  'bytes': p.stat().st_size, 'sha256': sha(p)} for p in members]
    row = {'path': str(path), 'members': inventory, 'logical_bytes': sum(r['bytes'] for r in inventory), 'removed': False}
    report['removed'].append(row); save()
    if path.is_dir(): shutil.rmtree(path)
    else: path.unlink()
    assert not path.exists(); row['removed'] = True
    report['logical_bytes_removed'] += row['logical_bytes']; save()

for p in private_apps + [exact, tar] + helpers:
    assert p.is_relative_to(base / 'work'), str(p)
    remove(p)
for root in [base / 'work/picture-local13-ab/runtime-work', base / 'work/picture-local13-ab-v2/runtime-work', base / 'work/picture-local13-ab-v3/runtime-work']:
    if root.exists():
        assert not any(p.is_file() or p.is_symlink() for p in root.rglob('*'))
        shutil.rmtree(root)
temp_root = Path(subprocess.check_output(['getconf', 'DARWIN_USER_TEMP_DIR'], text=True).strip()).resolve()
for row in rows:
    identifier = row['private_bundle_id']
    assert identifier.startswith('dev.bern.picture13.') and len(identifier.rsplit('.', 1)[-1]) == 32
    candidates = [Path(row['preferences_path']), Path(row['saved_state_path']),
                  temp_root / (identifier + '.savedState'),
                  Path.home() / 'Library/Caches' / identifier]
    for p in candidates:
        assert identifier in p.name
        remove(p)
report['success'] = True; save()
print(json.dumps({'success': True, 'retired_roots': len(report['removed']),
                  'logical_bytes_removed': report['logical_bytes_removed']}))
