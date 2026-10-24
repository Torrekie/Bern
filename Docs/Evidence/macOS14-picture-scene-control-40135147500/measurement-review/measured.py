#!/usr/bin/env python3
# Path/scale/output adapter of work/images-layout-geometry/measure.py.
# Frozen source SHA256: a113c13160ab40d73756ffa3ff70ee889987d847ff5daac87cd90821dd98875c
from pathlib import Path
from collections import Counter
from PIL import Image, ImageCms
import numpy as np
import argparse, io, json, hashlib

rois = {
    'images_heading': (165,68,310,94),
    'contain_picture': (173,108,300,198),
    'cover_picture': (321,104,447,201),
    'fill_picture': (468,104,595,201),
    'mark_picture': (642,104,714,174),
    'contain_caption': (190,201,285,222),
    'cover_caption': (340,201,425,222),
    'fill_caption': (490,201,575,222),
    'mark_caption': (638,175,719,199),
    'images_footer': (160,230,899,271),
    'hdr_heading': (165,289,350,317),
    'gain_caption': (225,445,354,466),
    'pq_caption': (493,439,572,466),
    'hdr_footer': (204,475,900,515),
    'layers_heading': (165,537,350,566),
}

def main():
    parser = argparse.ArgumentParser(description='Original fixed-ROI/scanline measurement only; no native card bbox detection.')
    parser.add_argument('png', type=Path)
    parser.add_argument('scale', type=int, help='Actual integer pixels per window point; no image resampling')
    parser.add_argument('output', type=Path, help='Fresh JSON file in an existing directory')
    args = parser.parse_args()
    path, scale, output = args.png.resolve(strict=True), args.scale, args.output.absolute()
    if scale <= 0: parser.error('scale must be a positive integer')
    if output.exists() or output.is_symlink(): parser.error('output already exists; no overwrite')
    if not output.parent.is_dir(): parser.error('output parent directory must already exist')
    raw = path.read_bytes()
    im = Image.open(io.BytesIO(raw))
    if im.format != 'PNG': parser.error('input must be an original PNG')
    if im.size != (920*scale,668*scale): parser.error('expected exactly 920x668 window points at the supplied scale')
    icc = im.info.get('icc_profile')
    if not isinstance(icc,bytes) or not icc: parser.error('input PNG lacks an embedded ICC profile')
    a = np.array(ImageCms.profileToProfile(im, ImageCms.ImageCmsProfile(io.BytesIO(icc)), ImageCms.createProfile('sRGB'), outputMode='RGB'))
    row = {'path':str(path),'scale':scale,'sha256':hashlib.sha256(raw).hexdigest(),'icc_sha256':hashlib.sha256(icc).hexdigest(),'regions':{}}
    for label,roi in rois.items():
        x0,y0,x1,y1 = [int(v*scale) for v in roi]; sub=a[y0:y1,x0:x1]
        bg=np.array(Counter(map(tuple,sub.reshape(-1,3))).most_common(1)[0][0]); rgb=sub.astype(int)
        mask = rgb.max(axis=2)-rgb.min(axis=2)>35 if label.endswith('_picture') else rgb.mean(axis=2)<bg.mean()-25
        yy,xx=np.where(mask)
        if not len(xx): row['regions'][label]={'none':True};continue
        bands=[]
        for y in np.where(mask.any(axis=1))[0]:
            if bands and y==bands[-1][-1]+1: bands[-1].append(int(y))
            else: bands.append([int(y)])
        row['regions'][label]={'bounds':[(x0+int(xx.min()))/scale,(y0+int(yy.min()))/scale,(x0+int(xx.max())+1)/scale,(y0+int(yy.max())+1)/scale], 'y_bands':[[(y0+b[0])/scale,(y0+b[-1]+1)/scale]for b in bands], 'background_srgb':bg.tolist()}
    # Original flat-column runs only. A plateau is not a full native-card bbox.
    x=800*scale
    segments=[]
    for y in range(92*scale,580*scale):
        rgb=tuple(int(v)for v in a[y,x])
        if segments and rgb==segments[-1]['rgb']: segments[-1]['end']=(y+1)/scale
        else: segments.append({'start':y/scale,'end':(y+1)/scale,'rgb':rgb})
    row['flat_x800_segments']=[s for s in segments if s['end']-s['start']>=1]
    row['input_size_pixels'] = list(im.size)
    row['expected_window_points'] = [920,668]
    row['source_algorithm_sha256'] = 'a113c13160ab40d73756ffa3ff70ee889987d847ff5daac87cd90821dd98875c'
    row['measured_script_sha256'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    row['scope'] = 'Original ICC to sRGB with unchanged ImageCms arguments/ROIs/thresholds; no resampling. Region bounds are ink/color within fixed ROIs, half-open points. x800 runs are a scanline, not native card outer bounds; outer edges require separate complete-edge review.'
    with output.open('x') as target:
        json.dump(row,target,indent=2);target.write('\n')
    print(json.dumps({'output':str(output),'sha256':row['sha256'],'icc_sha256':row['icc_sha256'],'size':list(im.size),'scale':scale}))

if __name__ == '__main__':
    main()
