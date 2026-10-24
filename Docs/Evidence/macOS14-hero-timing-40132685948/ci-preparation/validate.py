#!/usr/bin/env python3
"""Static timing-workflow/5-file-overlay checks; never builds or runs a probe."""
from pathlib import Path
import argparse, ast, hashlib, json, re, subprocess
import yaml

HERE=Path(__file__).resolve().parent
REPO=HERE.parent.parent/'outputs/Bern'
COMMIT='4fc027626aa33b5140a4881708a100fc4d2a7c7d'
BASE='.github/scripts/hero-coordinator-sdr-probe/'
WORKFLOW='.github/workflows/macos14-hero-coordinator-sdr-probe.yml'
MARKER='# Append-only bounded timing metadata gate; inherited native/execution/SDR gates above remain unchanged.\n'
OVERLAY={'ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc','README.md','source-provenance.json'}
def need(value,message):
    if not value: raise ValueError(message)
def sha(data):return hashlib.sha256(data).hexdigest()
def committed(path):return subprocess.run(['git','-C',str(REPO),'show',COMMIT+':'+path],capture_output=True,check=True).stdout
def blocks(shell):return re.findall(r"^python3 - <<'PY'\n(.*?)^PY\n",shell,re.M|re.S)
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--overlay-source',type=Path)
    parser.add_argument('--require-final',action='store_true')
    parser.add_argument('--output',type=Path,default=HERE/'static-review.json')
    args=parser.parse_args();output=args.output.resolve()
    need(output.parent==HERE and not output.exists(),'Use a fresh private static result filename')
    result={'framework_valid':False,'final_source_ready':False,'error':None,'compile_ui_dispatch':False}
    try:
        old_text=committed(WORKFLOW).decode();text=(HERE/'macos14-hero-timing-probe.yml').read_text()
        old=yaml.safe_load(old_text);new=yaml.safe_load(text)
        need(new['on']==old['on'] and new['permissions']==old['permissions'],'Triggers/permissions changed')
        need(set(new['jobs'])=={'build','measure'},'Unexpected jobs')
        build=new['jobs']['build'];measure=new['jobs']['measure']
        need(build['runs-on']=='macos-15' and build['env']==old['jobs']['build']['env'],'Build host/toolchain changed')
        need(measure['runs-on']=='macos-14' and measure['needs']=='build','Measure host/dependency changed')
        old_step=next(s for s in old['jobs']['measure']['steps'] if 'run' in s)
        step=next(s for s in measure['steps'] if 'run' in s)
        need(step['env']==old_step['env']=={'BERN_HERO_EXPECT_OS':'14','BERN_HERO_FLIGHT_SDR':'default'},'Only default14 is allowed')
        inherited=blocks(old_step['run'])[-1].replace('HeroCoordinatorSDRProbe','HeroTimingProbe')
        actual=blocks(step['run'])[-1];need(actual.count(MARKER)==1,'New timing boundary missing')
        need(actual.split(MARKER)[0]==inherited,'Full inherited native/execution/SDR prefix changed')
        result['inherited_prefix']={'byte_exact_after_binary_rename':True,'bytes':len(inherited.encode()),'sha256':sha(inherited.encode())}
        build_run=next(s['run'] for s in build['steps'] if 'run' in s)
        need('ditto .github/scripts/hero-coordinator-sdr-probe work/probe\n' in build_run,'Base package copy missing')
        need('cp .github/scripts/hero-timing-probe/{ProductHero.swift,FlightSDR.swift.inc,Driver.swift.inc,README.md,source-provenance.json} work/probe/\n' in build_run,'Exact5-file overlay missing')
        need(build_run.count('xcrun swiftc -O')==2 and 'test "$sdk" = 26.2' in build_run and '-target arm64-apple-macos13.0' in build_run,'One SDK26.2/min13 compile contract changed')
        need('cat work/probe/ProductHero.swift work/probe/FlightSDR.swift.inc work/probe/Driver.swift.inc >> work/probe/CoordinatorSDR.assembled.swift' in build_run,'Assembly changed')
        need(step['run'].count('python3 probe/run-one.py')==1 and '"$PWD/evidence/runtime14" 14 default\n' in step['run'],'Single default14 call changed')
        wrapper=committed(BASE+'run-one.py');need(sha(wrapper)=='200403b0b4e07f49dc4f74b6af8e0b5b14d67f36a3de022f44e4c44419d8621c','Committed wrapper changed')
        ast.parse(wrapper)
        for shell in (build_run,step['run']):
            parsed=subprocess.run(['bash','-n'],input=shell,text=True,capture_output=True)
            need(parsed.returncode==0,'Shell syntax: '+parsed.stderr)
            for code in blocks(shell):ast.parse(code)
        pending=sorted(set(re.findall(r'PENDING_[A-Z0-9_]+',text)));result['pending_markers']=pending
        gate=HERE/'timing-gate.py'
        if not pending:
            definitions=gate.read_text().split('\ndef main():\n',1)[0]
            need(actual[len(inherited):]==MARKER+definitions+"\nvalidate_flight_timing_trace(d,strict=True)\n",'Inline timing definitions differ from standalone')
            ast.parse(gate.read_text());result['timing_gate_sha256']=sha(gate.read_bytes())
        if args.overlay_source:
            overlay=args.overlay_source.resolve()
            need({f.name for f in overlay.iterdir()}==OVERLAY,'Overlay must contain exactly5 declared files')
            source=json.loads((overlay/'source-provenance.json').read_text())
            base_map=json.loads(committed(BASE+'source-provenance.json'))
            need(source['kind']=='actual_coordinator_timing_fixture' and source['local_compile_attempted'] is False,'Timing source kind/precompile contract')
            need(set(source['files'])==set(base_map['files']) and len(source['files'])==12,'Full input map must stay12files')
            for name,record in source['files'].items():
                data=(overlay/name).read_bytes() if name in OVERLAY else committed(BASE+name)
                need(sha(data)==record['sha256'],'Effective overlay input hash: '+name)
            for name in ('ProductHero.swift','FlightSDR.swift.inc','Driver.swift.inc'):
                match=re.search(r"d\['files'\]\['"+re.escape(name)+r"'\]\['sha256'\]=='([^']+)'",build_run)
                need(match is not None and match.group(1)==source['files'][name]['sha256'],'Workflow literal hash: '+name)
            result['effective_overlay_map_verified']=True
            result['overlay_provenance_sha256']=sha((overlay/'source-provenance.json').read_bytes())
        result['framework_valid']=True
        result['final_source_ready']=not pending and result.get('effective_overlay_map_verified') is True
        if args.require_final:need(result['final_source_ready'],'Timing source/schema/overlay not locked')
    except Exception as error:
        result['error']=str(error);raise
    finally:output.write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
if __name__=='__main__':main()
