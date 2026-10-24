"""Archive byte-verified evidence and remove only this checkpoint's duplicates."""
import datetime,hashlib,json,os,shutil
from collections import Counter
from pathlib import Path

root=Path(__file__).resolve().parent; workspace=root.parent.parent
target=workspace/'outputs/Bern/Docs/Evidence/macOS14-hero-coordinator-sdr-40129608288'
assert not target.exists()
extras={
 'source-preparation':'hero-coordinator-sdr-preparation',
 'ci-preparation':'hero-coordinator-sdr-ci-preparation',
 'code-review':'hero-coordinator-sdr-code-review',
 'native-review':'hero-coordinator-sdr-native-review',
 'observation-plan':'hero-coordinator-sdr-observation-plan',
 'next-observer-plan':'hero-coordinator-sdr-next-observer-plan'}
sources={'.':root,**{name:workspace/'work'/directory for name,directory in extras.items()}}
for name,source in sources.items():
    assert source.is_dir() and not source.is_symlink(),source
    assert not any(p.is_symlink() for p in source.rglob('*')),source
    if name!='.':assert (source/'SHA256SUMS').is_file(),source
review=json.loads((sources['native-review']/'review.json').read_text())
assert review['status']=='two13_native_pass_14_partial'
assert not (root/'probe/HeroCoordinatorSDRProbe').exists()
assert not (root/'build/hero-coordinator-sdr-probe.tar.gz').exists()
shutil.copytree(root,target)
for name,source in sources.items():
    if name!='.':shutil.copytree(source,target/name)
builder=workspace/'work/prepare-coordinator-sdr-package.py'
assert builder.is_file();shutil.copyfile(builder,target/'tools/prepare-source-package.py')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def check_copy(source,destination):
    original={p.relative_to(source).as_posix():digest(p) for p in source.rglob('*') if p.is_file()}
    for name,sha in original.items():assert digest(destination/name)==sha,name
    return {'files':len(original),'logical_bytes':sum((source/name).stat().st_size for name in original)}
checked={name:check_copy(source,target if name=='.' else target/name) for name,source in sources.items()}
assert builder.read_bytes()==(target/'tools/prepare-source-package.py').read_bytes()
dedup=[];seen={}
for path in sorted(target.rglob('*')):
    if not path.is_file():continue
    assert path.stat().st_nlink==1,path
    key=(path.stat().st_size,digest(path))
    if key in seen:
        canonical=seen[key];assert path.read_bytes()==canonical.read_bytes()
        dedup.append({'alias':str(path.relative_to(target)),'canonical':str(canonical.relative_to(target)),'bytes':path.stat().st_size})
        path.unlink();os.link(canonical,path)
    else:seen[key]=path
counts=Counter(p.stat().st_ino for p in target.rglob('*') if p.is_file())
for p in target.rglob('*'):
    if p.is_file():assert p.stat().st_nlink==counts[p.stat().st_ino],p
for name,source in sources.items():
    check_copy(source,target if name=='.' else target/name)
    shutil.rmtree(source)
    source.symlink_to(target if name=='.' else target/name,target_is_directory=True)
builder_bytes=builder.stat().st_size;builder.unlink()
cleanup={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'byte_verified_work_copies_replaced_by_archive_symlinks':checked,
 'logical_duplicate_work_bytes_removed':sum(v['logical_bytes'] for v in checked.values())+builder_bytes,
 'one_off_package_builder_copied_to_archive_and_removed_from_work':builder_bytes,
 'internal_hardlink_aliases':dedup,'nominal_internal_duplicate_bytes':sum(v['bytes'] for v in dedup),
 'scope':'Only frozen, task-owned current checkpoint trees; all copied bytes checked before removal. Internal archive hardlinks only, no external hardlinks. Binary/tar cleanup is in artifact-cleanup.json. Logical bytes are not APFS/net free-space measurements; no unrelated cache/defaults/TCC/history/toolchain cleanup.'}
(target/'cleanup.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
final={'ci_run':40129608288,'source_commit':'dcf1fdb3ef1a3f689898d08af4e3065b0646b481',
 'harness_commit':'ac426048bcea23eafa8aefe75c4620590e140dc5','native_status':review['status'],
 'native_review_sha256':digest(target/'native-review/review.json'),
 'source_map_members_retained':len(json.loads((target/'probe/source-provenance.json').read_text())['files']),
 'original_png_count':len(list(target.glob('runtime*/*.png'))),
 'binary_absent_after_review':not (target/'probe/HeroCoordinatorSDRProbe').exists(),
 'tar_absent_after_review':not (target/'build/hero-coordinator-sdr-probe.tar.gz').exists(),
 'whole_goal_complete':False,'goal_status':'active','new_remote_attempts':1}
(target/'final-validation.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n')
files=sorted(p for p in target.rglob('*') if p.is_file())
manifest=''.join(digest(p)+'  '+p.relative_to(target).as_posix()+'\n' for p in files)
(target/'SHA256SUMS.final').write_text(manifest)
for line in manifest.splitlines():
    sha,name=line.split('  ',1);assert digest(target/name)==sha,name
print(json.dumps({'archive':str(target),'manifest_files':len(files),'manifest_sha256':digest(target/'SHA256SUMS.final'),
 'removed_duplicate_work_logical_bytes':cleanup['logical_duplicate_work_bytes_removed'],
 'internal_aliases':len(dedup),'nominal_internal_duplicate_bytes':cleanup['nominal_internal_duplicate_bytes']},indent=2))
