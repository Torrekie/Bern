from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,subprocess,sys
assert len(sys.argv)==3, 'download root, expected harness commit'
D=Path(sys.argv[1]).resolve();H=sys.argv[2];B=D/'build';P=D/'probe'
assert len(H)==40 and not P.exists();P.mkdir()
expected,name=(B/'hero-route-probe.tar.gz.sha256').read_text().strip().split()
assert name=='hero-route-probe.tar.gz'
archive=B/name;assert hashlib.sha256(archive.read_bytes()).hexdigest()==expected
assert 'harness_sha='+H in (B/'environment.txt').read_text()
with tarfile.open(archive) as t:
 seen=set()
 for m in t.getmembers():
  q=PurePosixPath(m.name);assert not q.is_absolute() and '..' not in q.parts and (m.isdir() or m.isfile()),m.name
  assert str(q) not in seen,m.name;seen.add(str(q))
 t.extractall(P)
checked=[]
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
 f=P/n;assert not f.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==h,n;checked.append(n)
assert len(checked)==len(set(checked))
assert set(checked)=={str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and f.name!='SHA256SUMS'}
p=json.loads((P/'source-provenance.json').read_text())
assert p['kind']=='actual_existing_overlay_static_route_fixture'
assert p['compiled_new_sdk_image_and_hero_base_are_original_harness'] is True
assert p['required_backing_and_float_selected']=='off' and p['runtime_static_route_default']=='root'
assert p['runtime_backing_mode_default']==p['runtime_float_mode_default']=='off'
for n,m in p['files'].items():
 b=(P/n).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],n
binary=P/'HeroFloatProbe'
def call(a):
 r=subprocess.run(a,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert r.returncode==0,(a,r.stdout);return r.stdout
r={'scope':'Downloaded route archive, complete package/source hashes and original strict signature checked before running on13.','harness_commit':H,'archive_sha256':expected,'binary_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'package_verified_members':checked,'package_manifest_sha256':hashlib.sha256((P/'SHA256SUMS').read_bytes()).hexdigest(),'codesign_verify':call(['codesign','--verify','--strict','--verbose=4',str(binary)]),'archs':call(['xcrun','lipo','-archs',str(binary)]).strip(),'mach_build':call(['xcrun','vtool','-show-build',str(binary)])}
assert r['archs']=='arm64' and 'minos 13.0' in r['mach_build'] and 'sdk 26.2' in r['mach_build']
(D/'package-verification-local.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['binary_sha256','archive_sha256','archs']}))
