from pathlib import Path
import shutil,hashlib,json,datetime,os,subprocess
R=Path.cwd(); E=R/'outputs/Bern/Docs/Evidence';L=R/'work/native-pq-hero-backing-observer';C=R/'work/native-pq-hero-backing-ci-40095339192';T=R/'work/native-pq-hero-static-route13';A=R/'work/hero-backing-crosshost-analysis';Q=R/'work/hero-backing-ci-preparation';P=R/'work/hero-actual-overlay-route-preparation';Plan=R/'work/hero-actual-overlay-route-plan'
local=E/'macOS13-hdr-candidate/native-pq-hero-backing13';cohort=E/'macOS14-hero-backing-40095339192';route=E/'macOS13-hdr-candidate/native-pq-hero-static-route13'
assert all(not p.exists() for p in [local,cohort,route])
owned=[L/'HeroFloatCaptureProbe',C/'probe/HeroFloatProbe',T/'HeroFloatCaptureProbe',C/'build/hero-backing-probe.tar.gz']
fp=json.loads((L/'build-fingerprint.json').read_text()); assert hashlib.sha256(owned[0].read_bytes()).hexdigest()==fp['hashes']['HeroFloatCaptureProbe']
fp2=json.loads((T/'build-fingerprint.json').read_text());assert hashlib.sha256(owned[2].read_bytes()).hexdigest()==fp2['hashes']['HeroFloatCaptureProbe']
pv=json.loads((C/'package-verification-local.json').read_text());assert hashlib.sha256(owned[1].read_bytes()).hexdigest()==pv['binary_sha256'];assert hashlib.sha256(owned[3].read_bytes()).hexdigest()==pv['archive_sha256']
for d in [L,T]:
 p=json.loads((d/'source-provenance.json').read_text())
 for n,m in p['generated_files'].items():
  b=(d/n).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],n
# Only the root's compiler/probe writers matching these exact task paths matter.
proc=subprocess.check_output(['ps','-axo','pid=,comm=,args='],text=True);matches=[]
for line in proc.splitlines():
 parts=line.strip().split(None,2)
 if len(parts)<3: continue
 pid,comm,args=parts
 if any(x in comm for x in ['swift','clang','HeroFloat']) and any(str(d) in args or str(d) in comm for d in [L,C,T]): matches.append(line.strip())
assert not matches,matches
removed=[{'path':str(f.relative_to(R)),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'kind':'fingerprinted_owned_binary_or_transport'} for f in owned]
cache=L/'modules';cache_files=[f for f in cache.rglob('*') if f.is_file()];removed.append({'path':str(cache.relative_to(R)),'bytes':sum(f.stat().st_size for f in cache_files),'files':len(cache_files),'kind':'owned_module_cache_reused_for_two_local_builds_no_matching_writers'})
# Exclude only expendable artifacts, preserving original source/build/runtime metadata.
def ignore(path,names):
 p=Path(path)
 return [n for n in names if (p/n) in owned or (p/n)==cache]
shutil.copytree(L,local/'fixture',ignore=ignore)
shutil.copytree(C,cohort/'same-binary-13-14',ignore=ignore)
shutil.copytree(T,route/'fixture',ignore=ignore)
shutil.copytree(A,cohort/'analysis')
shutil.copytree(Q,cohort/'ci-preparation')
shutil.copytree(P,route/'source-preparation')
shutil.copytree(Plan,route/'route-plan')
control=R/'work/hero-float-control/compare-control.py'
for d in [local,cohort,route]:
 (d/'controls').mkdir();shutil.copy2(control,d/'controls/compare-control.py')
for d,script in [(local,'prepare-hero-backing-local.py'),(cohort,'verify-hero-backing-package.py'),(cohort,'prepare-hero-backing-harness.py'),(route,'prepare-hero-static-route-local.py')]:
 shutil.copy2(R/'work'/script,d/script)
# Verify each archived source file byte-for-byte before retiring the work copies.
copies=[(L,local/'fixture'),(C,cohort/'same-binary-13-14'),(T,route/'fixture'),(A,cohort/'analysis'),(Q,cohort/'ci-preparation'),(P,route/'source-preparation'),(Plan,route/'route-plan')]
duplicates=[]
for source,target in copies:
 count=0;total=0
 for f in source.rglob('*'):
  if not f.is_file() or f in owned or cache in f.parents: continue
  other=target/f.relative_to(source);assert other.is_file() and hashlib.sha256(other.read_bytes()).digest()==hashlib.sha256(f.read_bytes()).digest(),str(f)
  total+=f.stat().st_size;count+=1
 duplicates.append({'path':str(source.relative_to(R)),'archive':str(target.relative_to(R)),'verified_files':count,'bytes':total})
# Intentional artifact deletion exceptions remain explicit; original manifests are preserved.
cleanup={'created_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Only this root-owned completed backing/route experiment binaries, transport, active local module cache after both local builds, and byte-verified duplicate work. Sources/PNGs/ICC/receipts/results preserved. No unrelated apps/caches/preferences/defaults/TCC/simulators removed.','matching_writers_before_cleanup':matches,'expendable_artifacts_removed':removed,'duplicate_work_replaced_by_archive_symlinks':duplicates,'expendable_artifact_bytes':sum(x['bytes'] for x in removed),'duplicate_logical_bytes':sum(x['bytes'] for x in duplicates),'physical_apfs_reclaim_or_net_disk_delta_claim':False,'original_manifest_exceptions':['Local build fingerprints retain removed executable hashes.','CI probe/SHA256SUMS retains original HeroFloatProbe member; binary was independently verified before execution/removal.','CI archive checksum remains as provenance; transport tar intentionally removed.']}
for f in owned:f.unlink()
shutil.rmtree(cache)
for source,target in copies:
 shutil.rmtree(source); source.symlink_to(os.path.relpath(target,source.parent),target_is_directory=True)
for script in ['prepare-hero-backing-local.py','verify-hero-backing-package.py','prepare-hero-backing-harness.py','prepare-hero-static-route-local.py']:
 (R/'work'/script).unlink()
(E/'macOS13-hdr-candidate/hero-backing-route-cleanup-20261024.json').write_text(json.dumps(cleanup,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:cleanup[k] for k in ['expendable_artifact_bytes','duplicate_logical_bytes']}))
