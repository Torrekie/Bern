from pathlib import Path
from io import BytesIO
import json,hashlib,sys
import numpy as np
from PIL import Image,ImageCms

REPO=next(p for p in Path(__file__).resolve().parents if (p/'Cargo.toml').is_file() and (p/'crates/bern-backend-swiftui').is_dir())
ROOT=REPO
OUT=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else Path(__file__).resolve().parent
REF=REPO/'Docs/Evidence/macOS14-reference-normal/images-layout-light.png'
r=json.loads((OUT/'report.json').read_text())

def srgb(path):
    im=Image.open(path)
    icc=im.info.get('icc_profile')
    assert icc
    rgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB')
    return np.asarray(rgb,dtype=float)

reference=srgb(REF)
ref_ramp=reference[409:432,435:627].mean(axis=0)
res={'reference':str(REF.relative_to(ROOT)),'reference_sha256':hashlib.sha256(REF.read_bytes()).hexdigest(),
     'reference_ramp_roi':[435,409,627,432],'interior_columns':[2,190],
     'analysis':'ICC->sRGB per image, then average each pair of C13 2x samples into the corresponding1pt A14 column; no phase fit or image rescaling. Raw PNGs unchanged.',
     'captures':[]}
for cap in r['captures']:
    path=OUT/(cap['stage']+'.png')
    ar=srgb(path)
    scale=cap['scale'];assert scale==2
    title=cap['image_height']-cap['content_height']*scale
    item={'stage':cap['stage'],'current':cap['current'],'potential':cap['potential'],'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'views':{}}
    for name,f in cap['frames'].items():
        x=int(f['x']*scale);y=int(title+f['y']*scale)
        ramp=ar[y+79*2:y+102*2,x:x+192*2].mean(axis=0).reshape(192,2,3).mean(axis=1)
        delta=ramp[2:190]-ref_ramp[2:190]
        values=[]
        for left,right in [(0.15,0.35),(.65,.85)]:
            roi=ar[y+int(108*.15*scale):y+int(108*.4*scale),x+int(192*left*scale):x+int(192*right*scale)]
            values.append(roi.mean(axis=(0,1)).tolist())
        item['views'][name]={'top_halves_srgb_mean':values,'ramp_MAE_codes':float(np.abs(delta).mean()),'ramp_max_error_codes':float(np.abs(delta).max()),'ramp_bias_codes':delta.mean(axis=0).tolist(),'ramp_columns':ramp.tolist()}
        print(cap['stage'],name,'blocks',values,'ramp MAE',np.abs(delta).mean(),'max',np.abs(delta).max())
    res['captures'].append(item)
(OUT/'metrics.json').write_text(json.dumps(res,indent=2)+'\n')
