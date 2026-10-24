#!/usr/bin/env python3
"""Private static framework checks only. No workflow dispatch, build or native run."""
from pathlib import Path
import argparse, ast, hashlib, json, re, subprocess
import yaml

HERE = Path(__file__).resolve().parent

def require(value, message):
    if not value:
        raise ValueError(message)

def digest(data): return hashlib.sha256(data).hexdigest()
def blocks(shell):
    return re.findall(r"^python3 - <<'PY'\n(.*?)^PY\n", shell, flags=re.MULTILINE|re.DOTALL)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,default=HERE/'static-review.json')
    parser.add_argument('--require-final-source',action='store_true')
    parser.add_argument('--source-package',type=Path)
    args=parser.parse_args()
    output=args.output.resolve()
    require(output.parent==HERE and not output.exists(),'Use a fresh static result filename in this private directory')
    result={'static_framework_valid':False,'final_source_ready':False,'error':None,'compile_ui_ci_dispatch':False}
    try:
        old_text=(HERE/'workflow.base.yml').read_text()
        new_text=(HERE/'macos14-hero-coordinator-sdr-probe.yml').read_text()
        old=yaml.safe_load(old_text); new=yaml.safe_load(new_text)
        require(new['on']=={'workflow_dispatch':None},'Dispatch trigger changed')
        require(new['permissions']=={'contents':'read'},'Permissions expanded')
        require(set(new['jobs'])=={'build','measure'},'Unexpected job/matrix')
        require(new['concurrency']['cancel-in-progress'] is False,'Cancellation behavior changed')
        build=new['jobs']['build']; measure=new['jobs']['measure']
        require(build['runs-on']=='macos-15' and build['timeout-minutes']==8,'Build host/timeout changed')
        require(build['env']=={'DEVELOPER_DIR':'/Applications/Xcode_26.3.app/Contents/Developer'},'Toolchain changed')
        require(measure['runs-on']=='macos-14' and measure['needs']=='build' and measure['timeout-minutes']==5,'Measure job changed')
        old_run=next(s['run'] for s in old['jobs']['measure']['steps'] if 'run' in s)
        new_measure_step=next(s for s in measure['steps'] if 'run' in s)
        new_run=new_measure_step['run']
        require(new_measure_step['env']=={'BERN_HERO_EXPECT_OS':'14','BERN_HERO_FLIGHT_SDR':'default'},'14 environment must be explicit default')
        require(new_run.count('python3 probe/run-one.py')==1 and '"$PWD/evidence/runtime14" 14 default\n' in new_run,'Need exactly one default14 wrapper call')
        old_gate=blocks(old_run)[-1]; new_gate=blocks(new_run)[-1]
        marker='# Append-only SDR metadata gate; inherited native/execution gate above remains unchanged.\n'
        require(new_gate.count(marker)==1,'Append-only boundary missing')
        prefix=new_gate.split(marker)[0]
        expected=old_gate.replace('HeroCoordinatorAppProbe','HeroCoordinatorSDRProbe')
        require(prefix==expected,'Inherited native/execution gate prefix is not exact')
        definitions=(HERE/'flight-sdr-gate.py').read_text().split('\ndef main():\n',1)[0]
        require(new_gate[len(prefix):]==marker+definitions+"\nvalidate_flight_sdr(d,receipt,'default',14)\n",
                'Embedded additive gate is not byte-identical to the standalone definitions')
        ast.parse((HERE/'flight-sdr-gate.py').read_text())
        result['additive_gate_definitions_byte_exact']=True
        result['additive_gate_sha256']=digest((HERE/'flight-sdr-gate.py').read_bytes())
        result['inherited_gate_prefix']={'byte_exact_after_binary_path_substitution':True,
            'bytes':len(prefix.encode()),'sha256':digest(prefix.encode())}
        build_run=next(s['run'] for s in build['steps'] if 'run' in s)
        require('test "$sdk" = 26.2' in build_run,'SDK26.2 assertion missing')
        require(build_run.count('xcrun swiftc -O')==2,'Need one recorded command and one real compile')
        require('-target arm64-apple-macos13.0' in build_run,'ARM64/min13 target missing')
        assembly='cat work/probe/ProductHero.swift work/probe/FlightSDR.swift.inc work/probe/Driver.swift.inc >> work/probe/CoordinatorSDR.assembled.swift'
        require(build_run.count(assembly)==1,'Three-part assembly changed')
        require('clockguard' not in new_text.lower() and 'shim' not in new_text.lower(),'Unexpected clock guard/shim')
        require('HeroCoordinatorAppProbe' not in new_text and 'hero-coordinator-app-probe' not in new_text,'Old package path remains')
        for shell in (build_run,new_run):
            parsed=subprocess.run(['bash','-n'],input=shell,text=True,capture_output=True)
            require(parsed.returncode==0,'Shell syntax failure: '+parsed.stderr)
            for code in blocks(shell): ast.parse(code)
        ast.parse((HERE/'run-one.py').read_text())
        wrapper=(HERE/'run-one.py').read_bytes()
        require("'"+digest(wrapper)+"'" in build_run,'Build provenance does not lock this wrapper SHA')
        require("mode in ('default','baked-pair')" in wrapper.decode(),'Mode enum changed')
        require("assert major!=14 or mode=='default'" in wrapper.decode(),'Wrapper permits candidate14')
        require('p.wait(timeout=15)' in wrapper.decode() and 'timeout_seconds=15' in wrapper.decode(),'Wrapper timeout changed')
        require("env.pop('BERN_MOTION',None)" in wrapper.decode(),'Child motion environment changed')
        require("(out/'runtime.log').open('x')" in wrapper.decode() and "(out/'run-receipt.json').open('x')" in wrapper.decode(),'Acquisition files can overwrite')
        result['yaml_python_shell_syntax_valid']=True
        result['wrapper_sha256']=digest(wrapper)
        pending=sorted(set(re.findall(r'PENDING_[A-Z0-9_]+',new_text)))
        result['pending_source_contract_markers']=pending
        result['static_framework_valid']=True
        if args.source_package:
            package=args.source_package.resolve()
            data=json.loads((package/'source-provenance.json').read_text())
            require(data['kind']=='actual_coordinator_sdr_fixture','Unexpected source provenance kind')
            for name,record in data['files'].items():
                rel=Path(name)
                require(not rel.is_absolute() and '..' not in rel.parts,'Unsafe provenance path')
                target=package/rel
                require(not target.is_symlink() and digest(target.read_bytes())==record['sha256'],'Source provenance mismatch: '+name)
            for name in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc','run-one.py'):
                require(name in data['files'],'Missing assembled source: '+name)
                match=re.search(r"d\['files'\]\['"+re.escape(name)+r"'\]\['sha256'\]=='([^']+)'",build_run)
                require(match is not None and match.group(1)==data['files'][name]['sha256'],'Workflow literal/source SHA mismatch: '+name)
            result['source_package_hashes_verified']=True
        result['final_source_ready']=not pending and result.get('source_package_hashes_verified') is True
        if args.require_final_source:
            require(result['final_source_ready'],'Final source names/hashes/schema and assembled package must be locked first')
    except Exception as error:
        result['error']=str(error)
        raise
    finally:
        output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')

if __name__=='__main__': main()
