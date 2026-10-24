from pathlib import Path
import hashlib, json, os

base = Path(__file__).resolve().parents[2]
dest = base / 'outputs/Bern/Docs/Evidence/macOS13-picture-scene-observed-9dd'
assert not dest.exists()
dest.mkdir()
groups = {
    'picture-local13-ab': 'first-A-and-B-isolation',
    'picture-local13-ab-v2': 'A2-control-and-B-log-off',
    'picture-local13-ab-v3': 'B3-IO-on',
    'picture-local13-collector-preparation': 'collector-v1',
    'picture-local13-collector-v2': 'collector-v2',
    'picture-local13-collector-v2-review': 'collector-v2-review',
    'picture-local13-build': 'local-build',
    'picture-local13-geometry-review': 'geometry-review',
    'picture-cohort-cleanup': 'cleanup',
}
moved = []
for source, name in groups.items():
    old = base / 'work' / source
    assert old.is_dir() and not old.is_symlink()
    mode = old.stat().st_mode & 0o777
    old.chmod(mode | 0o200)
    old.rename(dest / name)
    (dest / name).chmod(mode)
    old.symlink_to(os.path.relpath(dest / name, old.parent), target_is_directory=True)
    moved.append({'previous': str(old), 'archive': name, 'previous_mode': oct(mode), 'work_alias': os.readlink(old)})
canonical = dest / 'A2-control-and-B-log-off/capture-A2'
deduplicated = []
for directory in ['first-A-and-B-isolation/capture-A', 'A2-control-and-B-log-off/capture-B', 'B3-IO-on/capture-B3']:
    for p in sorted((dest / directory).glob('*.png')):
        other = canonical / p.name
        digest = hashlib.sha256(p.read_bytes()).hexdigest()
        assert other.is_file() and hashlib.sha256(other.read_bytes()).hexdigest() == digest
        size = p.stat().st_size
        p.unlink(); p.symlink_to(os.path.relpath(other, p.parent))
        assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
        deduplicated.append({'path': str(p.relative_to(dest)), 'sha256': digest,
                             'logical_duplicate_bytes_removed': size, 'target': os.readlink(p)})
assert len(deduplicated) == 27
(dest / 'archive-layout.json').write_text(json.dumps({'moved': moved, 'exact_PNG_aliases': deduplicated,
    'duplicate_logical_bytes_removed': sum(x['logical_duplicate_bytes_removed'] for x in deduplicated),
    'physical_APFS_savings': 'not measured', 'logical_source_bytes_unchanged': True,
    'native_review': 'Will be appended after reviewer freezes; no mutable reviewer folder moved.'}, indent=2) + '\n')
print('Archived13 cohorts and 27 verified exact duplicate PNG aliases')
