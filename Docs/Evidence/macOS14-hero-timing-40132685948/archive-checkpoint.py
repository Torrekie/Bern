"""Archive the bounded checkpoint; retain canonical Git sources and original evidence."""
import datetime,hashlib,json,os,shutil,subprocess
from collections import Counter
from pathlib import Path
root=Path(__file__).resolve().parent;workspace=root.parent.parent;repo=workspace/'outputs/Bern'
target=repo/'Docs/Evidence/macOS14-hero-timing-40132685948';assert not target.exists()
extra={'source-preparation':'hero-coordinator-timing-preparation','ci-preparation':'hero-timing-ci-preparation',
       'code-review':'hero-timing-code-review','native-review':'hero-timing-native-review',
       'closure':'hero-timing-closure','picture-scene-next-step':'picture-scene-next-step'}
sources={'.':root,**{n:workspace/'work'/v for n,v in extra.items()}}
for n,p in sources.items():
    assert p.is_dir() and not p.is_symlink() and not any(q.is_symlink() for q in p.rglob('*'))
    if n!='.':assert (p/'SHA256SUMS').is_file()
review=json.loads((sources['native-review']/'review.json').read_text())
assert review['status']=='strict13_and14_native_trace_pass'
assert not (root/'probe').exists() and not (root/'package-source').exists()
assert not (root/'build/hero-timing-probe.tar.gz').exists()
shutil.copytree(root,target)
for n,p in sources.items():
    if n!='.':shutil.copytree(p,target/n)
builder=workspace/'work/prepare-hero-timing.py';shutil.copyfile(builder,target/'tools/prepare-source-overlay.py')
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def verify(src,dst):
    paths=[q for q in src.rglob('*') if q.is_file()]
    for q in paths:assert q.read_bytes()==(dst/q.relative_to(src)).read_bytes(),q
    return {'files':len(paths),'logical_bytes':sum(q.stat().st_size for q in paths)}
copies={n:verify(p,target if n=='.' else target/n) for n,p in sources.items()}
assert builder.read_bytes()==(target/'tools/prepare-source-overlay.py').read_bytes()
aliases=[];seen={}
for p in sorted(target.rglob('*')):
    if not p.is_file():continue
    assert p.stat().st_nlink==1
    key=(p.stat().st_size,H(p))
    if key in seen:
        canonical=seen[key];assert p.read_bytes()==canonical.read_bytes()
        aliases.append({'alias':str(p.relative_to(target)),'canonical':str(canonical.relative_to(target)),'bytes':p.stat().st_size})
        p.unlink();os.link(canonical,p)
    else:seen[key]=p
counts=Counter(q.stat().st_ino for q in target.rglob('*') if q.is_file())
for q in target.rglob('*'):
    if q.is_file():assert q.stat().st_nlink==counts[q.stat().st_ino]
for n,p in sources.items():
    verify(p,target if n=='.' else target/n);shutil.rmtree(p)
    p.symlink_to(target if n=='.' else target/n,target_is_directory=True)
builder_bytes=builder.stat().st_size;builder.unlink()
cleanup={'recorded_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'verified_work_copies_replaced_by_archive_symlinks':copies,
         'logical_duplicate_work_bytes_removed':sum(v['logical_bytes'] for v in copies.values())+builder_bytes,
         'one_off_builder_archived_and_removed_from_work_bytes':builder_bytes,'internal_hardlink_aliases':aliases,
         'nominal_internal_duplicate_bytes':sum(v['bytes'] for v in aliases),
         'scope':'Only frozen task-owned copies, byte-checked before removal; all hardlinks internal. Payload cleanup in artifact-cleanup.json. No host cache/toolchain/defaults/TCC/history cleanup. Logical bytes are not APFS/net space measurements.'}
(target/'cleanup.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
prov=json.loads((target/'build/source-provenance.json').read_text());overlay={'ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc','README.md','source-provenance.json'}
for name,v in prov['files'].items():
    commit='cc96030b22c74010df79423979aee1abf83b7cb5' if name in overlay else '4fc027626aa33b5140a4881708a100fc4d2a7c7d'
    directory='.github/scripts/hero-timing-probe/' if name in overlay else '.github/scripts/hero-coordinator-sdr-probe/'
    data=subprocess.check_output(['git','show',commit+':'+directory+name],cwd=repo)
    assert hashlib.sha256(data).hexdigest()==v['sha256']
final={'ci_run':40132685948,'source_commit':'cc96030b22c74010df79423979aee1abf83b7cb5',
       'harness_commit':'d72cb5f9bcec8a90fa394bca1060ed0f392ba8f3','native_status':review['status'],
       'native_review_sha256':H(target/'native-review/review.json'),'canonical_git_input_members_verified':len(prov['files']),
       'original_png_count':len(list(target.glob('runtime*/*.png'))),'binary_tar_and_reconstructed_source_removed':True,
       'whole_goal_complete':False,'goal_status':'active','new_remote_attempts':1}
(target/'final-validation.json').write_text(json.dumps(final,indent=2,sort_keys=True)+'\n')
files=sorted(q for q in target.rglob('*') if q.is_file())
manifest=''.join(H(q)+'  '+q.relative_to(target).as_posix()+'\n' for q in files)
(target/'SHA256SUMS.final').write_text(manifest)
for line in manifest.splitlines():
    sha,name=line.split('  ',1);assert H(target/name)==sha
print(json.dumps({'archive':str(target),'manifest_files':len(files),'manifest_sha256':H(target/'SHA256SUMS.final'),
                  'removed_duplicate_work_logical_bytes':cleanup['logical_duplicate_work_bytes_removed'],
                  'internal_aliases':len(aliases),'nominal_internal_duplicate_bytes':cleanup['nominal_internal_duplicate_bytes']},indent=2))
