from pathlib import Path
import hashlib, json, shutil, subprocess

base = Path(__file__).resolve().parents[2]
out = Path(__file__).resolve().parent / 'retired-artifacts.json'
assert not out.exists()
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
cohort = base / 'work/picture-grid-width-run'
local = base / 'work/picture-grid-width-local13'
row = json.loads((local / 'B4/isolation.json').read_text())
app = Path(row['private_app'])
exact = cohort / 'exact'
tar = cohort / 'build/showcase-grid-width.tar.gz'
helpers = [base / 'work/picture-grid-width-local13-build' / n for n in ['Collector', 'FocusGuard']]
live = subprocess.check_output(['ps', '-axo', 'pid=,comm='], text=True)
assert not any(any(str(p) in line for p in [app, exact, *helpers]) for line in live.splitlines())
assert {str(p.relative_to(app)): sha(p) for p in app.rglob('*') if p.is_file()} == row['private_members']
assert sha(exact / 'Showcase.app/Contents/MacOS/Showcase') == '5e9790ef812c424f27bb91e3248c73ea451069d92d7d627d57428f8390a96765'
assert sha(exact / 'bin/showcase') == '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
assert sha(tar) == 'd7db5e239e86ccae5c2cdda6c6ad151bd3b06080a00299336c4d2a82aac86b0d'
assert sha(helpers[0]) == 'c3e3545585e168d50f7d96f15f76f8aa80174a061fcfa9c82ae806d8c4bba2af'
assert sha(helpers[1]) == 'e843bcc95aa390a2fb4b4b72261b1a33a9a10f0b169608d04d78a3e1b068ddae'
assert sha(base / 'outputs/macOS13/Showcase.app/Contents/MacOS/Showcase') == 'cc267abcafeec30112c2796b3c0ea7699a6836a0f09a1caa73f66ea48bfa1c1b'
assert sha(base / 'outputs/macOS13/bin/showcase') == '963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
d = {'scope': 'Completed single width diagnostic only; native reviews finished payload reads, B4 capture/cleanup/released desktop succeeded. Original delivered App/CLI retained.',
     'live_owned_executable_matches': [], 'removed': [], 'absent_private_paths': [],
     'logical_bytes_removed': 0, 'physical_APFS_savings': 'not measured'}

def save(): out.write_text(json.dumps(d, indent=2) + '\n')

def remove(p):
    if not p.exists() and not p.is_symlink():
        d['absent_private_paths'].append(str(p)); save(); return
    assert not p.is_symlink()
    files = [p] if p.is_file() else sorted(q for q in p.rglob('*') if q.is_file())
    assert all(not q.is_symlink() for q in files)
    files = [{'path': q.name if q == p else str(q.relative_to(p)), 'bytes': q.stat().st_size, 'sha256': sha(q)} for q in files]
    record = {'path': str(p), 'files': files, 'logical_bytes': sum(q['bytes'] for q in files), 'removed': False}
    d['removed'].append(record); save()
    if p.is_dir(): shutil.rmtree(p)
    else: p.unlink()
    assert not p.exists(); record['removed'] = True
    d['logical_bytes_removed'] += record['logical_bytes']; save()

for p in [app, exact, tar, *helpers]:
    assert p.is_relative_to(base / 'work'); remove(p)
runtime = local / 'runtime-work'
assert not any(p.is_file() or p.is_symlink() for p in runtime.rglob('*'))
shutil.rmtree(runtime)
identifier = row['private_bundle_id']
assert identifier.startswith('dev.bern.picture13.b4.')
temporary = Path(subprocess.check_output(['getconf', 'DARWIN_USER_TEMP_DIR'], text=True).strip()).resolve()
for p in [Path(row['preferences_path']), Path(row['saved_state_path']), temporary / (identifier + '.savedState'), Path.home() / 'Library/Caches' / identifier]:
    assert identifier in p.name; remove(p)
d['success'] = True; save()
print(json.dumps({'success': True, 'logical_bytes_removed': d['logical_bytes_removed']}))
