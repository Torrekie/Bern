#!/usr/bin/env python3
"""Run frozen statistics only after a separately saved independent approval exists."""
from pathlib import Path
import datetime,hashlib,json,subprocess,sys
D=Path(__file__).resolve().parent;ROOT=D.parent.parent;BASE=ROOT/'outputs/Bern/Docs/Evidence/macOS14-hero-float-40091326190';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert len(sys.argv)==2,'independent review approval JSON required'
approval=Path(sys.argv[1]).resolve();review=json.loads(approval.read_text())
# Root must pin the reviewed evidence using a small separate approval created after inspection.
assert review['independent_geometry_review_passed'] is True and review['lane_contract_reviewed'] is True
assert review['geometry_sha256']==sha(D/'result/geometry.json') and review['geometry_script_sha256']==sha(D/'structure.py')
for name,expected in review['review_artifact_hashes'].items():assert sha(ROOT/name)==expected,name
geometry=json.loads((D/'result/geometry.json').read_text());assert geometry['complete'] and geometry['all4_directions_unique']
assert not (D/'known-extraction-execution.json').exists();rows=[]
for major in [13,14]:
 records=[x for x in geometry['records'] if x['actual_os_major']==major];assert len(records)==2
 directions={x['selected_direction'] for x in records};assert len(directions)==1 and 'unknown' not in directions
 direction=next(iter(directions));out=D/f'host{major}-known';assert not out.exists()
 args=[sys.executable,'-B',str(D/'analyze_float.py'),str(BASE/f'same-binary-13-14/runtime{major}/on/report.json'),'--output',str(out),'--row-direction',direction,'--orientation-evidence',str(D/'result/geometry.json')]
 r={'host':major,'argv':args,'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat()}
 with (D/f'host{major}-known.stdout.log').open('w') as o,(D/f'host{major}-known.stderr.log').open('w') as e:
  r['exit_code']=subprocess.run(args,stdout=o,stderr=e,timeout=30).returncode
 r['finished_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat();rows.append(r)
 (D/'known-extraction-execution.json').write_text(json.dumps({'approval_sha256':sha(approval),'script_sha256':sha(D/'analyze_float.py'),'rows':rows},indent=2,sort_keys=True)+'\n')
 assert r['exit_code']==0,(major,r['exit_code'])
print(json.dumps({'hosts':len(rows),'both_exit0':True,'row_direction':'independently approved per run'}))
