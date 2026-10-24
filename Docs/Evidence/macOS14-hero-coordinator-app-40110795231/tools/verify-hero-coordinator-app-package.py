from pathlib import Path,PurePosixPath
import tarfile,hashlib,json,subprocess,sys
assert len(sys.argv)==3
D=Path(sys.argv[1]).resolve();H=sys.argv[2];B=D/'build';P=D/'probe';assert len(H)==40 and not P.exists();P.mkdir()
expected,name=(B/'hero-coordinator-app-probe.tar.gz.sha256').read_text().strip().split();assert name=='hero-coordinator-app-probe.tar.gz'
a=B/name;assert hashlib.sha256(a.read_bytes()).hexdigest()==expected
assert 'harness_sha='+H in (B/'environment.txt').read_text()
with tarfile.open(a) as t:
 seen=set()
 for m in t.getmembers():
  q=PurePosixPath(m.name);assert not q.is_absolute() and '..' not in q.parts and (m.isdir() or m.isfile()),m.name
  assert str(q) not in seen;seen.add(str(q))
 t.extractall(P)
names=[]
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
 f=P/n;assert f.is_file() and not f.is_symlink() and hashlib.sha256(f.read_bytes()).hexdigest()==h,n;names.append(n)
assert len(names)==len(set(names)) and set(names)=={str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and f.name!='SHA256SUMS'}
p=json.loads((P/'source-provenance.json').read_text());assert p['kind']=='actual_coordinator_app_loop_fixture' and p['no_old_snapshot_metadata_float_backing_route_hooks'] is True and p['no_sdk14_unused_clock_or_gainmap_guards_in_newsdk_package'] is True
assert p['original_hero_sha256']=='8e1e90a00ff2f386a38ed8c4977af27a505571051560d50406e9e54b69ed186c'
for n,m in p['files'].items():
 b=(P/n).read_bytes();assert len(b)==m['bytes'] and hashlib.sha256(b).hexdigest()==m['sha256'],n
b=P/'HeroCoordinatorAppProbe'
def call(v):
 r=subprocess.run(v,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert r.returncode==0,(v,r.stdout);return r.stdout
r={'harness_commit':H,'archive_sha256':expected,'binary_sha256':hashlib.sha256(b.read_bytes()).hexdigest(),'verified_package_members':names,'package_manifest_sha256':hashlib.sha256((P/'SHA256SUMS').read_bytes()).hexdigest(),'codesign_verify':call(['codesign','--verify','--strict','--verbose=4',str(b)]),'archs':call(['xcrun','lipo','-archs',str(b)]).strip(),'mach_build':call(['xcrun','vtool','-show-build',str(b)]),'scope':'Exact original signed coordinator binary verified before13 execution; no signing/rebuild.'}
assert r['archs']=='arm64' and 'minos 13.0' in r['mach_build'] and 'sdk 26.2' in r['mach_build']
(D/'package-verification-local.json').write_text(json.dumps(r,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:r[k] for k in ['binary_sha256','archive_sha256','archs']}))
