#!/usr/bin/env python3
from pathlib import Path,PurePosixPath
import hashlib,json,os,re,subprocess,sys,tarfile
assert len(sys.argv)==4,'cohort expected-harness expected-source-commit'
D=Path(sys.argv[1]).resolve();harness,source_ref=sys.argv[2:];assert re.fullmatch('[0-9a-f]{40}',harness) and re.fullmatch('[0-9a-f]{40}',source_ref)
B=D/'build';P=D/'probe';assert not P.exists();P.mkdir()
ROOT=Path(__file__).resolve().parent.parent;repo=ROOT/'outputs/Bern';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
expected,name=(B/'hero-cgsemantics-probe.tar.gz.sha256').read_text().strip().split();assert name=='hero-cgsemantics-probe.tar.gz'
archive=B/name;assert archive.stat().st_size<16*1024*1024 and sha(archive)==expected
assert 'harness_sha='+harness in (B/'environment.txt').read_text()
with tarfile.open(archive) as t:
 files=[];total=0
 for m in t.getmembers():
  q=PurePosixPath(m.name);assert not q.is_absolute() and '..' not in q.parts and (m.isdir() or m.isfile()),m.name
  if m.isfile():files.append(str(q));total+=m.size
 assert len(files)==len(set(files)) and total<32*1024*1024
 t.extractall(P,filter='data')
checked=[]
for line in (P/'SHA256SUMS').read_text().splitlines():
 h,n=line.split('  ',1);q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
 f=P/n;assert not f.is_symlink() and sha(f)==h,n;checked.append(n)
assert len(checked)==len(set(checked)) and set(checked)=={str(f.relative_to(P)) for f in P.rglob('*') if f.is_file() and f.name!='SHA256SUMS'}
p=json.loads((P/'source-provenance.json').read_text());assert p['kind']=='original_snapshot_cg_drawing_semantics_fixture' and p['fixture_base_commit']=='5eca0e5904117d131e1129302d50d357e4234a15'
assert p['product_source_commit']=='b08db54e01ac2ec54fb84e6f2a70041f1f4c3604' and p['runtime_float_mode_default']==p['runtime_backing_mode_default']=='off' and p['wrapper_backing_mode']=='off'
assert p['compiled_new_sdk_image_and_hero_base_are_original_harness'] and p['retention_provider_and_driver_unchanged']
for n,v in p['files'].items():
 q=PurePosixPath(n);assert not q.is_absolute() and '..' not in q.parts
 assert sha(P/n)==v['sha256'] and (P/n).stat().st_size==v['bytes'],n
 original=subprocess.check_output(['git','show',source_ref+':.github/scripts/hero-cgsemantics-probe/'+n],cwd=repo)
 assert (P/n).read_bytes()==original,n
assert (P/'source-provenance.json').read_bytes()==subprocess.check_output(['git','show',source_ref+':.github/scripts/hero-cgsemantics-probe/source-provenance.json'],cwd=repo)
assert (P/'ProductHero.swift').read_bytes()==b''.join((P/n).read_bytes() for n in ['ProductHero.base.swift','FloatCapture.swift.inc','Driver.swift.inc'])
binary=P/'HeroCGSemanticsProbe';env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer')
def call(a):
 r=subprocess.run(a,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True);assert r.returncode==0,(a,r.stdout);return r.stdout
result={'scope':'Downloaded complete package/tar/source-map/assembly/arm64/min13/strict signature verified before executing original signed CI binary on13; no resign or local compile.','harness_commit':harness,'source_commit':source_ref,'archive_sha256':expected,'binary_sha256':sha(binary),'package_verified_members':checked,'source_map_inputs_verified':len(p['files']),'package_manifest_sha256':sha(P/'SHA256SUMS'),'codesign_verify':call(['codesign','--verify','--strict','--verbose=4',str(binary)]),'archs':call(['xcrun','lipo','-archs',str(binary)]).strip(),'mach_build':call(['xcrun','vtool','-show-build',str(binary)])}
assert result['archs']=='arm64' and re.search(r'\bminos 13\.0\b',result['mach_build']) and int(re.search(r'\bsdk (\d+)\.',result['mach_build']).group(1))>=26
(D/'package-verification-local.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ['binary_sha256','archive_sha256','archs','source_map_inputs_verified']}))
