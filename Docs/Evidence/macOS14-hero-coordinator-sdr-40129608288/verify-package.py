"""Verify and extract this one remote package; no rebuild or resign."""
import hashlib,json,os,subprocess,tarfile
from pathlib import Path,PurePosixPath

root=Path(__file__).resolve().parent
archive=root/'build/hero-coordinator-sdr-probe.tar.gz'
target=root/'probe'; assert not target.exists()
expected=(archive.with_name(archive.name+'.sha256')).read_text().split()[0]
digest=lambda b: hashlib.sha256(b).hexdigest()
assert digest(archive.read_bytes())==expected
with tarfile.open(archive,'r:gz') as tar:
    members=tar.getmembers()
    names=set()
    for m in members:
        p=PurePosixPath(m.name); assert not p.is_absolute() and '..' not in p.parts
        assert m.isdir() or m.isfile()
        assert str(p) not in names; names.add(str(p))
    target.mkdir()
    for m in members:
        p=target/PurePosixPath(m.name)
        if m.isdir(): p.mkdir(parents=True,exist_ok=True)
        else:
            p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(tar.extractfile(m).read())
            p.chmod(m.mode & 0o777)
verified=[]
for line in (target/'SHA256SUMS').read_text().splitlines():
    sha,name=line.split('  ',1); p=Path(name)
    assert not p.is_absolute() and '..' not in p.parts
    assert digest((target/p).read_bytes())==sha,name
    verified.append(name)
provenance=json.loads((target/'source-provenance.json').read_text())
assert provenance['kind']=='actual_coordinator_sdr_fixture'
for name,meta in provenance['files'].items():
    assert digest((target/name).read_bytes())==meta['sha256'],name
    assert (root/'probe-source'/name).read_bytes()==(target/name).read_bytes(),name
assert (root/'probe-source/source-provenance.json').read_bytes()==(target/'source-provenance.json').read_bytes()
assembled=b'import AppKit\nimport SwiftUI\n'+b''.join((target/name).read_bytes() for name in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc'))
assert (target/'CoordinatorSDR.assembled.swift').read_bytes()==assembled
binary=target/'HeroCoordinatorSDRProbe'
env=dict(os.environ,DEVELOPER_DIR='/Applications/Xcode.app/Contents/Developer')
checks={}
for name,argv in [('arch',['xcrun','lipo','-archs',str(binary)]),('build',['xcrun','vtool','-show-build',str(binary)]),('signature',['codesign','--verify','--strict','--verbose=4',str(binary)])]:
    result=subprocess.run(argv,env=env,capture_output=True,text=True)
    checks[name]={'argv':argv,'exit_code':result.returncode,'stdout':result.stdout,'stderr':result.stderr}
    assert result.returncode==0,checks[name]
assert checks['arch']['stdout'].strip()=='arm64'
assert 'minos 13.0' in checks['build']['stdout'] and 'sdk 26.2' in checks['build']['stdout']
result={'archive_sha256':expected,'binary_sha256':digest(binary.read_bytes()),'binary_bytes':binary.stat().st_size,
        'package_manifest_sha256':digest((target/'SHA256SUMS').read_bytes()),'verified_package_members':verified,
        'source_map_members':len(provenance['files']),'assembly_sha256':digest(assembled),'checks':checks,
        'local_compile_or_resign':False}
out=root/'package-verification-local.json';assert not out.exists();out.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
print(json.dumps({k:result[k] for k in ('archive_sha256','binary_sha256','binary_bytes','source_map_members')},indent=2))
