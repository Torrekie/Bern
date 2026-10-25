from pathlib import Path
import hashlib, json, os

base = Path(__file__).resolve().parents[2]
dest = base / 'outputs/Bern/Docs/Evidence/macOS14-picture-grid-width-40144017622'
assert not dest.exists()
dest.mkdir()
groups = {
    'picture-grid-width-run': 'run',
    'picture-grid-width-local13': 'local13',
    'picture-grid-width-local13-build': 'local-build',
    'picture-grid-width14-review': 'geometry14-review',
    'picture-grid-width-cross-review': 'cross-review',
    'picture-grid-width-native-review': 'native-review',
    'picture-download-helper-review': 'download-helper-review',
    'picture-grid-width-cleanup': 'cleanup',
}
moved = []
for source, name in groups.items():
    old = base / 'work' / source
    assert old.is_dir() and not old.is_symlink()
    mode = old.stat().st_mode & 0o777
    old.chmod(mode | 0o200); old.rename(dest / name); (dest / name).chmod(mode)
    old.symlink_to(os.path.relpath(dest / name, old.parent), target_is_directory=True)
    moved.append({'previous': str(old), 'archive': name, 'work_alias': os.readlink(old), 'previous_mode': oct(mode)})
aliases = []
for directory, canonical, count in [
    ('run/raw', dest.parent / 'macOS14-picture-scene-control-40135147500/raw', 13),
    ('local13/capture', dest.parent / 'macOS13-picture-scene-observed-9dd/A2-control-and-B-log-off/capture-A2', 9),
]:
    candidates = sorted((dest / directory).glob('*.png'))
    assert len(candidates) == count
    for p in candidates:
        other = canonical / p.name
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert other.is_file() and hashlib.sha256(other.read_bytes()).hexdigest() == digest
        size = p.stat().st_size; p.unlink(); p.symlink_to(os.path.relpath(other, p.parent))
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
        aliases.append({'path': str(p.relative_to(dest)), 'sha256': digest, 'target': os.readlink(p), 'logical_duplicate_bytes_removed': size})
(dest / 'archive-layout.json').write_text(json.dumps({'moved': moved, 'exact_PNG_aliases': aliases,
    'duplicate_logical_bytes_removed': sum(r['logical_duplicate_bytes_removed'] for r in aliases),
    'physical_APFS_savings': 'not measured', 'logical_source_bytes_unchanged': True}, indent=2) + '\n')
print('Single width cohort archived; 22 exact PNG duplicates replaced by verified relative aliases')
