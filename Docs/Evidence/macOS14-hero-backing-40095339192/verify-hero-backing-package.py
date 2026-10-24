from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,subprocess
D=Path('work/native-pq-hero-backing-ci-40095339192');B=D/'build';P=D/'probe'
assert not P.exists();P.mkdir()
expected,name=(B/'hero-backing-probe.tar.gz.sha256').read_text().strip().split()
assert name=='hero-backing-probe.tar.gz'
archive=B/name;assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
assert 'harness_sha=0590f49e095f1eabe7553816615c67d53ad171d2' in (B/'environment.txt').read_text()
with tarfile.open(archive) as t:
 for m in t.getmembers():
  q=PurePosixPath(m.name); assert not q.is_absolute() and '..' not in q.parts and (m.isdir() or m.isfile()),m.name
 t.extractall(P)
checked=[]
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1); q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
 f=P/n;assert not f.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==h,n;checked.append(n)
assert set(checked)=={str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and f.name!='SHA256SUMS'}
p=json.loads((P/'source-provenance.json').read_text());assert p['compiled_new_sdk_image_and_hero_base_are_original_harness'] and p['runtime_backing_mode_default']==p['runtime_float_mode_default']=='off'
for n,m in p['files'].items():
 b=(P/n).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],n
binary=P/'HeroFloatProbe'
def call(a):
 r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert r.returncode==0,(a,r.stdout);return r.stdout
r={'scope':'Verified downloaded archive, complete package members and source map before executing the original signed CI binary on13.','harness_commit':'0590f49e095f1eabe7553816615c67d53ad171d2','archive_sha256':expected,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'package_verified_members':checked,'package_manifest_sha256':hashlib.sha256((P/'SHA256SUMS').read_bytes()).hexdigest(),'codesign_verify':call(['codesign','--verify','--strict','--verbose=4',str(binary)]),'archs':call(['xcrun','lipo','-archs',str(binary)]).strip(),'mach_build':call(['xcrun','vtool','-show-build',str(binary)])}
assert r['archs']=='arm64' and 'minos 13.0' in r['mach_build'] and 'sdk 26.2' in r['mach_build']
(D/'package-verification-local.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['binary_sha256','archive_sha256','archs']}))
