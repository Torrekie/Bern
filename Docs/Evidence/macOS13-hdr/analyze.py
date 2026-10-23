from pathlib import Path
from PIL import Image, ImageCms, ImageStat
from io import BytesIO
import json
base=Path(__file__).resolve().parent
report=json.loads((base/'report.json').read_text())
results=[]
for sample in report['samples']:
    if 'frames' not in sample:continue
    path=base/(sample['stage']+'.png')
    original=Image.open(path)
    rgb=ImageCms.profileToProfile(original,ImageCms.ImageCmsProfile(BytesIO(original.info['icc_profile'])),ImageCms.createProfile('sRGB'),outputMode='RGB')
    scale=sample['scale'];top=original.height-sample['content_height']*scale
    values={}
    for name,fr in sample['frames'].items():
        pair=[]
        for a,b in ((.15,.35),(.65,.85)):
            box=(round((fr['x']+fr['width']*a)*scale),round(top+(fr['y']+fr['height']*.15)*scale),round((fr['x']+fr['width']*b)*scale),round(top+(fr['y']+fr['height']*.55)*scale))
            pair.append({'roi':box,'srgb_mean':ImageStat.Stat(rgb.crop(box)).mean})
        values[name]=pair
    results.append({'stage':sample['stage'],'headroom':sample['headroom'],'values':values})
(base/'metrics.json').write_text(json.dumps(results,indent=2))
for r in results:
    print(r['stage'],r['headroom'],{k:[round(vv['srgb_mean'][0],3) for vv in v] for k,v in r['values'].items()})
