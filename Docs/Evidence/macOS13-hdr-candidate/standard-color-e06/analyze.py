import hashlib,io,json,pathlib
import numpy as np
import PIL
from PIL import Image,ImageCms
D=pathlib.Path(__file__).resolve().parent
report=json.loads((D/'report.json').read_text())
REPO=next((p for p in D.parents if (p/'.github/scripts/hdr-tone-probe.swift').exists()),D.parent.parent/'outputs/Bern')
source_report=REPO/'Docs/Evidence/macOS13-hdr-candidate/color-probe13/report.json'
source=json.loads(source_report.read_text())
im=Image.open(D/'capture.png')
rgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(im.info['icc_profile'])),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
array=np.asarray(rgb,dtype=np.float64)
views={}
for name,entry in report['frames'].items():
    r=entry['screenshot_pixels'];x,y,w,h=[int(round(r[k])) for k in ['x','y','width','height']]
    assert w==640 and h==360
    crop=array[y:y+h,x:x+w]
    patches={}
    for p in source['patches']:
        r=p['source_rect'];xx=int(r['x'])+8;yy=int(r['y'])+8
        roi=crop[yy:yy+104,xx:xx+112]
        patches[p['name']]=[round(float(v),6) for v in roi.mean(axis=(0,1))]
    ramp=crop[260:340,4:636].mean(axis=0)
    views[name]={'patches':patches,'ramp':ramp,'crop':crop}
comparisons={}
for left,right in [('product-standard-ffb','product-standard-named'),('product-standard-ffb','native-swiftui-named'),('product-standard-named','native-swiftui-named')]:
    delta=np.array(list(views[left]['patches'].values()))-np.array(list(views[right]['patches'].values()))
    rd=views[left]['ramp']-views[right]['ramp']
    comparisons[left+' vs '+right]={'patch_mean_rgb_max_absolute_delta_codes':float(np.abs(delta).max()),'patch_mean_rgb_mae_codes':float(np.abs(delta).mean()),'ramp_mean_column_rgb_max_absolute_delta_codes':float(np.abs(rd).max()),'ramp_mean_column_rgb_mae_codes':float(np.abs(rd).mean()),'ramp_column_count':len(rd),'whole_image_rgb_pixels_exactly_equal':bool(np.array_equal(views[left]['crop'],views[right]['crop'])),'patch_mean_rgb_deltas':{p:[round(float(v),6) for v in a] for p,a in zip(views[left]['patches'],delta)}}
summary={'scope':report['scope'],'capture_success':report['success'],'cicp_normalization_same_as_product_named_pq':True,'product_equals_native_named_pq':False,'outcome':'Both product Standard sources agree exactly in measured image pixels; native13 namedPQ remains different in color and gray-ramp output. No native-equivalence pass.','measurement':'One native WindowServer capture; source and output images are640x360 pixels; ICC->sRGB with Pillow ImageCms perceptual intent0 flags0.10patch means over112x104-pixel interiors; gray ramp columns4..635 over80rows y260..339. No rescaling or phase fitting. Encoded8-bit sRGB code values, not linear EDR or physical nits.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'patches':source['patches'],'views':{k:{'mean_srgb_rgb_by_patch':v['patches']} for k,v in views.items()},'comparisons':comparisons,'runtime_sha256':report['runtime_sha256'],'product_commit':report['product_commit'],'frontmost_before':report['frontmost_pid_before'],'frontmost_after':report['frontmost_pid_after'],'activation_calls':report['activation_calls'],'window_seconds':report['window_seconds'],'current_headrooms':[c['current_headroom'] for c in report['captures']],'edr_requests':report['product_edr_requests'],'stopped_metal_views':report['stopped_metal_views'],'limitations':['Product Standard vs macOS13 native namedPQ only; no macOS14 runtime, High, HLG, arbitrary metadata/ICC/alpha/EXIF or physical brightness equivalence.','Color atlas includes out-of-output-gamut BT.2020 patches; compare complete native pipelines rather than inferring a unique scalar mapper.']}
(D/'validation.json').write_text(json.dumps(summary,indent=2,sort_keys=True)+'\n')
np.savez_compressed(D/'ramp-columns.npz',**{k:v['ramp'] for k,v in views.items()})
print(json.dumps({'comparisons':{k:{a:b for a,b in v.items() if a!='patch_mean_rgb_deltas'} for k,v in comparisons.items()},'patches':{k:v['patches'] for k,v in views.items()}},indent=2))
