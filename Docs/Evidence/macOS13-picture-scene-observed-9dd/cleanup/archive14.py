from pathlib import Path
import hashlib, json, os

base = Path(__file__).resolve().parents[2]
dest = base / 'outputs/Bern/Docs/Evidence/macOS14-picture-scene-observed-40138440830'
assert not dest.exists()
dest.mkdir()
groups = {
    'picture-scene-observed14': 'run',
    'picture-observed14-geometry-review': 'geometry-review',
    'picture-observed14-event-review': 'event-review',
    'picture-observed14-native-review': 'native-review',
    'picture-observed14-archive-preparation': 'archive-preparation',
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
canonical = dest.parent / 'macOS14-picture-scene-control-40135147500/raw'
deduplicated = []
for p in sorted((dest / 'run/raw').glob('*.png')):
    other = canonical / p.name
    digest = hashlib.sha256(p.read_bytes()).hexdigest()
    assert other.is_file() and hashlib.sha256(other.read_bytes()).hexdigest() == digest
    size = p.stat().st_size
    p.unlink()
    p.symlink_to(os.path.relpath(other, p.parent))
    assert hashlib.sha256(p.read_bytes()).hexdigest() == digest
    deduplicated.append({'path': str(p.relative_to(dest)), 'sha256': digest,
                         'logical_duplicate_bytes_removed': size, 'target': os.readlink(p)})
assert len(deduplicated) == 13
(dest / 'archive-layout.json').write_text(json.dumps({'moved': moved, 'exact_PNG_aliases': deduplicated,
    'duplicate_logical_bytes_removed': sum(x['logical_duplicate_bytes_removed'] for x in deduplicated),
    'physical_APFS_savings': 'not measured', 'logical_source_bytes_unchanged': True}, indent=2) + '\n')
print('Archived14 inputs and 13 verified exact duplicate PNG aliases')
