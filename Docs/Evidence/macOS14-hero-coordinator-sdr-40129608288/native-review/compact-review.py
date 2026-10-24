#!/usr/bin/env python3
# Lossless removal of repeated live-observer descriptor fields, not a gate replay.
from pathlib import Path
import hashlib,json
O=Path(__file__).resolve().parent;p=O/'review.json';original=p.read_bytes();d=json.loads(original)
assert d['status']=='two13_native_pass_14_partial'
for key,process in d['processes'].items():
    values=process.pop('live_samples');shared=[];rows=[]
    for value in values:
        assert len(value['flights'])==1
        f=value['flights'][0]
        descriptor={k:f[k] for k in ('view_identity','started_uptime','from_nsimage_id','to_nsimage_id')}
        if descriptor not in shared:shared.append(descriptor)
        frame=f['frame']
        rows.append([value['sample_index'],value['uptime'],value['stage'],value['timer_exists'],shared.index(descriptor),f['progress'],[frame[k] for k in ('x','y','width','height')]])
    process['live_scalar_trace']={'columns':['sample_index','uptime','stage','timer_exists','descriptor_index','progress','frame_xywh'],'descriptors':shared,'rows':rows,'row_count':len(rows),'scope':'All originally extracted live scalar rows; this is not a rendered-frame or presentation trace.'}
d['serialization_postprocessing']={'script_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'input_review_sha256':hashlib.sha256(original).hexdigest(),'action':'Replace duplicated live descriptor dictionaries with shared descriptors and all original scalar rows. No gate rerun, assertion change, omitted live row or pixel operation.'}
p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
print(json.dumps({'status':d['status'],'review_bytes':p.stat().st_size,'input_files':len(d['input_files']),'live_rows':{k:v['live_scalar_trace']['row_count'] for k,v in d['processes'].items()}}))
