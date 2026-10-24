from pathlib import Path
import shutil,hashlib,json,datetime,os,subprocess
R=Path.cwd();E=R/'outputs/Bern/Docs/Evidence';C=R/'work/native-pq-hero-route-ci-40097558084';L=R/'work/native-pq-hero-existing-rgba8-13';A=R/'work/hero-route-crosshost-analysis';Q=R/'work/hero-route-ci-preparation';F=R/'work/hero-existing-format-preparation';FA=R/'work/hero-existing-rgba8-analysis';FP=R/'work/hero-existing-format-plan'
cohort=E/'macOS14-hero-route-40097558084';local=E/'macOS13-hdr-candidate/native-pq-hero-existing-rgba8-13'
assert not cohort.exists() and not local.exists() and all(d.is_dir() for d in [A,Q,F,FA,FP])
# Pin the actual executed artifacts before excluding them from retained archives.
owned=[C/'probe/HeroFloatProbe',C/'build/hero-route-probe.tar.gz',L/'HeroFloatCaptureProbe'];pv=json.loads((C/'package-verification-local.json').read_text());bp=json.loads((L/'build-fingerprint.json').read_text())
for f,h in zip(owned,[pv['binary_sha256'],pv['archive_sha256'],bp['hashes']['HeroFloatCaptureProbe']]):assert hashlib.sha256(f.read_bytes()).hexdigest()==h
for n,m in json.loads((L/'source-provenance.json').read_text())['generated_files'].items():
 b=(L/n).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],n
proc=subprocess.check_output(['ps','-axo','pid=,comm=,args='],text=True);matches=[]
for line in proc.splitlines():
 parts=line.strip().split(None,2)
 if len(parts)==3 and any(s in parts[1] for s in ['swift','clang','HeroFloat']) and any(str(d) in parts[1] or str(d) in parts[2] for d in [C,L]):matches.append(line.strip())
assert not matches,matches
cache=L/'modules';cf=[f for f in cache.rglob('*') if f.is_file()]
removed=[{'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'kind':'owned_verified_completed_binary_or_transport'} for f in owned]
removed.append({'path':str(cache.relative_to(R)),'bytes':sum(f.stat().st_size for f in cf),'files':len(cf),'kind':'owned_completed_module_cache_no_matching_writers'})
def ignore(path,names):return [n for n in names if Path(path)/n in owned or Path(path)/n==cache]
copies=[(C,cohort/'same-binary-13-14'),(A,cohort/'analysis'),(Q,cohort/'ci-preparation'),(L,local/'fixture'),(F,local/'source-preparation'),(FA,local/'analysis'),(FP,local/'source-plan')]
for source,target in copies:shutil.copytree(source,target,ignore=ignore)
for d in [cohort,local]:
 (d/'controls').mkdir();shutil.copy2(R/'work/hero-float-control/compare-control.py',d/'controls/compare-control.py')
for n,d in [('verify-hero-route-package.py',cohort),('prepare-hero-route-harness.py',cohort),('prepare-hero-existing-format-local.py',local)]:shutil.copy2(R/'work'/n,d/n)
shutil.copy2(Path(__file__),cohort/'archive-hero-route-and-format.py')
duplicates=[]
for source,target in copies:
 files=[f for f in source.rglob('*') if f.is_file() and f not in owned and cache not in f.parents]
 for f in files:
  other=target/f.relative_to(source);assert other.is_file() and hashlib.sha256(other.read_bytes()).digest()==hashlib.sha256(f.read_bytes()).digest(),str(f)
 duplicates.append({'path':str(source.relative_to(R)),'archive':str(target.relative_to(R)),'verified_files':len(files),'bytes':sum(f.stat().st_size for f in files)})
cleanup={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'This root-owned completed static-route/early-existing-format experiment only. Sources, complete and failed raw evidence retained; unrelated apps/caches/preferences/defaults/TCC/simulators untouched.','matching_writers_before_cleanup':matches,'expendable_artifacts_removed':removed,'duplicate_work_replaced_by_archive_symlinks':duplicates,'expendable_artifact_bytes':sum(x['bytes'] for x in removed),'duplicate_logical_bytes':sum(x['bytes'] for x in duplicates),'physical_apfs_reclaim_or_net_disk_delta_claim':False,'original_manifest_exceptions':['Original CI package manifest retains the executed/removed HeroFloatProbe hash.','Original transport checksum retained; tar intentionally removed.','Local build fingerprint retains executed/removed binary hash; original prebuild source manifest preserved.']}
for f in owned:f.unlink()
shutil.rmtree(cache)
for source,target in copies:
 shutil.rmtree(source);source.symlink_to(os.path.relpath(target,source.parent),target_is_directory=True)
for n in ['verify-hero-route-package.py','prepare-hero-route-harness.py','prepare-hero-existing-format-local.py']:(R/'work'/n).unlink()
(E/'macOS13-hdr-candidate/hero-route-format-cleanup-20261024.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:cleanup[k] for k in ['expendable_artifact_bytes','duplicate_logical_bytes']}))
