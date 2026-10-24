from pathlib import Path
import hashlib,json,shutil,subprocess,datetime
R=Path.cwd(); A=R/'outputs/Bern/Docs/Evidence/macOS14-hero-coordinator-40103369574'
assert not A.exists();A.mkdir()
def digest(f):
 h=hashlib.sha256()
 with f.open('rb') as s:
  for b in iter(lambda:s.read(1048576),b''):h.update(b)
 return h.hexdigest()
items=[('work/native-pq-hero-coordinator-ci-40103369574','same-binary-13-14'),('work/hero-coordinator-crosshost-analysis','native-analysis'),('work/hero-coordinator-pixel-analysis','pixel-analysis'),('work/hero-coordinator-preparation','source-preparation'),('work/hero-coordinator-ci-preparation','ci-preparation'),('work/hero-coordinator-preflight','local-static-preflight'),('work/hero-coordinator-sampling-plan','next-sampling-plan')]
excluded={R/'work/native-pq-hero-coordinator-ci-40103369574/probe/HeroCoordinatorProbe',R/'work/native-pq-hero-coordinator-ci-40103369574/build/hero-coordinator-probe.tar.gz'}
cache=R/'work/hero-coordinator-preflight/modules'
receipt={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Owned completed coordinator cohort only. No active HeroCoordinatorProbe/swiftc or lsof open module writers observed before archive. All retained work files are byte-verified before duplicate removal. Logical byte counts are not APFS recovered space or net free-space change.','excluded_artifacts':[],'duplicates':[]}
for s,d in items:
 src=R/s;dst=A/d;assert src.is_dir() and not src.is_symlink();dst.mkdir()
 n=0;size=0
 for f in sorted(src.rglob('*')):
  if not f.is_file() or f in excluded or cache in f.parents:continue
  assert not f.is_symlink()
  rel=f.relative_to(src);to=dst/rel;to.parent.mkdir(parents=True,exist_ok=True)
  shutil.copy2(f,to);assert digest(f)==digest(to)
  n+=1;size+=f.stat().st_size
 receipt['duplicates'].append({'work':s,'archive':str(dst.relative_to(R)),'verified_files':n,'logical_bytes':size})
(A/'tools').mkdir()
for name in ('prepare-hero-coordinator-base.py','verify-hero-coordinator-package.py'):
 f=R/'work'/name;to=A/'tools'/name;shutil.copy2(f,to);assert digest(f)==digest(to)
 receipt['duplicates'].append({'work':str(f.relative_to(R)),'archive':str(to.relative_to(R)),'verified_files':1,'logical_bytes':f.stat().st_size})
for arg,out in (('status','ci-jobs.json'),('artifacts','ci-artifacts.json')):
 p=subprocess.run(['python3','-B','work/github-ci.py',arg,'40103369574'],capture_output=True,text=True,check=True)
 json.loads(p.stdout);(A/out).write_text(p.stdout)
# Native probe and package are excluded only after their independent pre-run verification receipts and metadata were retained.
for f in sorted(excluded):
 assert f.is_file();receipt['excluded_artifacts'].append({'path':str(f.relative_to(R)),'logical_bytes':f.stat().st_size,'sha256':digest(f)})
assert next(x for x in receipt['excluded_artifacts'] if x['path'].endswith('HeroCoordinatorProbe'))['sha256']=='5739a0405bf78c04e71a46116c99fd48a7fa7b0b659bf8e97744ee3982ecea36'
assert next(x for x in receipt['excluded_artifacts'] if x['path'].endswith('.tar.gz'))['sha256']=='a8b62da12b02c0a33803bf82c44b8921ad84beb5c4761e4eae80e03fcc99a0f5'
cachefiles=[f for f in cache.rglob('*') if f.is_file()]
receipt['excluded_artifacts'].append({'path':str(cache.relative_to(R)),'logical_bytes':sum(f.stat().st_size for f in cachefiles),'files':len(cachefiles),'purpose':'Completed local target14 typecheck module cache; no executable built.'})
for f in excluded:f.unlink()
shutil.rmtree(cache)
# Rehash retained files once again immediately before replacing work duplicates with archive symlinks.
for s,d in items:
 src=R/s;dst=A/d
 srcfiles=sorted(str(f.relative_to(src)) for f in src.rglob('*') if f.is_file())
 dstfiles=sorted(str(f.relative_to(dst)) for f in dst.rglob('*') if f.is_file())
 assert srcfiles==dstfiles
 for rel in srcfiles:assert digest(src/rel)==digest(dst/rel)
 shutil.rmtree(src);src.symlink_to(dst)
for name in ('prepare-hero-coordinator-base.py','verify-hero-coordinator-package.py'):(R/'work'/name).unlink()
receipt['expendable_artifact_logical_bytes']=sum(x['logical_bytes'] for x in receipt['excluded_artifacts'])
receipt['byte_verified_duplicate_logical_bytes']=sum(x['logical_bytes'] for x in receipt['duplicates'])
(A/'cleanup.json').write_text(json.dumps(receipt,indent=2,sort_keys=True)+'\n')
print(json.dumps({'archive':str(A.relative_to(R)),'artifacts_removed':receipt['expendable_artifact_logical_bytes'],'duplicates_removed':receipt['byte_verified_duplicate_logical_bytes']},indent=2))
