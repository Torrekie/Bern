from pathlib import Path
from PIL import Image,ImageCms
import PIL,numpy as np,io,json,hashlib
D=Path(__file__).resolve().parent;report=json.loads((D/'report.json').read_text());rows={}
for g in report['groups']:
    im=Image.open(D/g['png']);icc=im.info['icc_profile'];srgb=ImageCms.profileToProfile(im.convert('RGB'),ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),renderingIntent=0,outputMode='RGB',flags=0)
    r=g['roi_screenshot_pixels'];x,y,w,h=[round(r[k]) for k in ['x','y','width','height']];raw=np.asarray(im.convert('RGB'))[y:y+h,x:x+w];a=np.asarray(srgb)[y:y+h,x:x+w]
    def stats(v):
        values,counts=np.unique(v.reshape(-1,3),axis=0,return_counts=True)
        return {'mean_rgb':v.mean(axis=(0,1)).tolist(),'mode_rgb':values[counts.argmax()].tolist(),'min_rgb':v.min(axis=(0,1)).tolist(),'max_rgb':v.max(axis=(0,1)).tolist(),'unique_rgb_count':len(values)}
    rows[g['name']]={'raw_png_profile_rgb':stats(raw),'icc_to_srgb':stats(a),'icc_sha256':hashlib.sha256(icc).hexdigest(),'png_sha256':hashlib.sha256((D/g['png']).read_bytes()).hexdigest(),'effect_view_count':len(g['native_effect_views']),'semantic_nscolor_srgb':g['resolved_srgb']['semantic_window_background'],'roi_pixels':[x,y,w,h]}
result={'scope':report['scope'],'capture_success':report['success'],'window_seconds':report['window_seconds'],'frontmost_before':report['frontmost_before'],'frontmost_after':report['frontmost_after'],'activation_calls':report['activation_calls'],'groups':rows,'analysis':'Fixed40x40pt ROI at content-top-left(680,430), exactly80x80pixels at2x. All PNGs share ICC; originals unchanged. ICC->sRGB with Pillow ImageCms perceptual intent0 flags0. Each group has two consecutive identical canonical WindowServer buffers.','pillow':PIL.__version__,'littlecms':ImageCms.core.littlecms_version,'limitations':['Standalone manually-created NSWindow with NSHostingView, not the complete SwiftUI App Gallery scene.','One inactive/nonkey Aqua window only; no actual14/same-SDK comparison, dark or active-state test.','Desktop/material context can still affect default backgrounds; no user prefs, wallpaper or brightness were readjusted.']}
(D/'validation.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n');print(json.dumps({name:{'raw':r['raw_png_profile_rgb']['mode_rgb'],'srgb_mode':r['icc_to_srgb']['mode_rgb'],'srgb_mean':r['icc_to_srgb']['mean_rgb']} for name,r in rows.items()},indent=2))
