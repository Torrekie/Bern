"""Finish the byte-verified archive after an owned frozen work directory was read-only."""
import datetime,hashlib,json,os,shutil,stat,subprocess
from collections import defaultdict
from pathlib import Path
target=Path(__file__).resolve().parent;repo=target.parents[2];workspace=repo.parent.parent
assert repo.name=='Bern'
extra={'source-preparation':'hero-coordinator-timing-preparation','ci-preparation':'hero-timing-ci-preparation',
       'code-review':'hero-timing-code-review','native-review':'hero-timing-native-review',
       'closure':'hero-timing-closure','picture-scene-next-step':'picture-scene-next-step'}
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
remaining=workspace/'work/picture-scene-next-step';assert remaining.is_dir() and not remaining.is_symlink()
old_mode=stat.S_IMODE(remaining.stat().st_mode);assert old_mode==0o555 and remaining.stat().st_uid==os.getuid()
for q in remaining.rglob('*'):
    assert not q.is_symlink()
    if q.is_file():assert q.read_bytes()==(target/'picture-scene-next-step'/q.relative_to(remaining)).read_bytes()
for name,workname in extra.items():
    if name!='picture-scene-next-step':assert (workspace/'work'/workname).is_symlink() and (workspace/'work'/workname).resolve()==target/name
assert (workspace/'work/hero-timing-20261025').resolve()==target
remaining.chmod(old_mode|stat.S_IWUSR);shutil.rmtree(remaining)
remaining.symlink_to(target/'picture-scene-next-step',target_is_directory=True)
builder=workspace/'work/prepare-hero-timing.py';assert builder.read_bytes()==(target/'tools/prepare-source-overlay.py').read_bytes()
builder_bytes=builder.stat().st_size;builder.unlink()
def meta(paths):return {'files':len(paths),'logical_bytes':sum(p.stat().st_size for p in paths)}
current=[p for p in target.rglob('*') if p.is_file()]
original=[p for p in current if p.relative_to(target).parts[0] not in extra and p.relative_to(target).as_posix() not in ('archive-recovery.py','tools/prepare-source-overlay.py')]
copies={'.':meta(original),**{n:meta([p for p in (target/n).rglob('*') if p.is_file()]) for n in extra}}
groups=defaultdict(list)
for p in current:groups[p.stat().st_ino].append(p)
aliases=[]
for paths in groups.values():
    paths.sort()
    for p in paths:assert p.stat().st_nlink==len(paths)
    for p in paths[1:]:
        assert p.read_bytes()==paths[0].read_bytes()
        aliases.append({'alias':str(p.relative_to(target)),'canonical':str(paths[0].relative_to(target)),'bytes':p.stat().st_size})
cleanup={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_work_copies_replaced_by_archive_symlinks':copies,
 'logical_duplicate_work_bytes_removed':sum(v['logical_bytes'] for v in copies.values())+builder_bytes,
 'one_off_builder_archived_and_removed_from_work_bytes':builder_bytes,'internal_hardlink_aliases':aliases,
 'nominal_internal_duplicate_bytes':sum(v['bytes'] for v in aliases),
 'recovery':{'initial_error':'PermissionError removing last frozen task-owned picture-scene-next-step work directory',
             'copy_verification_and_internal_dedup_completed_before_error':True,'preceding_work_copies_already_replaced_by_symlinks':6,
             'remaining_source_rechecked_against_archive':True,'owned_work_dir_mode_before':oct(old_mode),
             'owned_work_dir_mode_for_removal':oct(old_mode|stat.S_IWUSR),
             'resolution':'Added owner write only to the owned work directory, removed its byte-verified duplicate, created archive symlink; archived frozen data bytes untouched.'},
 'scope':'Only frozen task-owned copies, byte-checked before removal; hardlinks internal. Artifact cleanup in artifact-cleanup.json. No unrelated/cache/toolchain/defaults/TCC/history cleanup. Logical bytes are not APFS/net space measurements.'}
(target/'cleanup.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
review=json.loads((target/'native-review/review.json').read_text());assert review['status']=='strict13_and14_native_trace_pass'
prov=json.loads((target/'build/source-provenance.json').read_text())
overlay={'ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc','README.md','source-provenance.json'}
for name,v in prov['files'].items():
    commit='cc96030b22c74010df79423979aee1abf83b7cb5' if name in overlay else '4fc027626aa33b5140a4881708a100fc4d2a7c7d'
    directory='.github/scripts/hero-timing-probe/' if name in overlay else '.github/scripts/hero-coordinator-sdr-probe/'
    b=subprocess.check_output(['git','show',commit+':'+directory+name],cwd=repo);assert hashlib.sha256(b).hexdigest()==v['sha256']
final={'ci_run':40132685948,'source_commit':'cc96030b22c74010df79423979aee1abf83b7cb5',
       'harness_commit':'d72cb5f9bcec8a90fa394bca1060ed0f392ba8f3','native_status':review['status'],
       'native_review_sha256':H(target/'native-review/review.json'),'canonical_git_input_members_verified':len(prov['files']),
       'original_png_count':len(list(target.glob('runtime*/*.png'))),'binary_tar_and_reconstructed_source_removed':True,
       'whole_goal_complete':False,'goal_status':'active','new_remote_attempts':1,'archive_cleanup_recovery_complete':True}
(target/'final-validation.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n')
files=sorted(q for q in target.rglob('*') if q.is_file() and q.name!='SHA256SUMS.final')
manifest=''.join(H(q)+'  '+q.relative_to(target).as_posix()+'\n' for q in files)
(target/'SHA256SUMS.final').write_text(manifest)
for line in manifest.splitlines():
    sha,name=line.split('  ',1);assert H(target/name)==sha
print(json.dumps({'archive':str(target),'files':len(files),'manifest_sha256':H(target/'SHA256SUMS.final'),
                  'removed_duplicate_work_logical_bytes':cleanup['logical_duplicate_work_bytes_removed'],
                  'internal_aliases':len(aliases),'nominal_internal_duplicate_bytes':cleanup['nominal_internal_duplicate_bytes'],
                  'recovery_complete':True},indent=2))
