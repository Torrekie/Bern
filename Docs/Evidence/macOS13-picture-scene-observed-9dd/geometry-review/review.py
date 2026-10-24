#!/usr/bin/env python3
"""Read-only source evidence audit; writes only fresh private review JSON."""
from pathlib import Path
from PIL import Image, ImageCms
import hashlib, io, json

ROOT = Path(__file__).resolve().parent.parent.parent
OUT = Path(__file__).resolve().parent
A = ROOT / 'work/picture-local13-ab/capture-A'
REF = ROOT / 'work/picture-scene-observed14/raw'
CONTROL = ROOT / 'outputs/Bern/Docs/Evidence/macOS14-picture-scene-control-40135147500'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_text())
def normalized_prefix(d):
    rows = d['commands']
    start = next(i for i,r in enumerate(rows) if 'set-language' in r['arguments'])
    selected = False
    out = []
    for r in rows[start:]:
        args = r['arguments'][:]
        if args[0] == '--session': args[1] = '<SESSION>'
        out.append({'arguments': args, 'status': r['status']})
        if '--option' in args and args[-1] == 'Layout': selected = True
        if selected and args[-2:] == ['window','list']: break
    return out

def runs(im, scale, axis, pos, lower, upper):
    pixels = im.load()
    result = []
    for coordinate in range(int(lower*scale), int(upper*scale)):
        rgb = list(pixels[int(pos*scale),coordinate] if axis == 'x' else pixels[coordinate,int(pos*scale)])
        if result and rgb == result[-1]['rgb']:
            result[-1]['end'] = (coordinate+1)/scale
        else: result.append({'start':coordinate/scale,'end':(coordinate+1)/scale,'rgb':rgb})
    return result

def scan(p, scale):
    im = Image.open(p)
    icc = im.info['icc_profile']
    srgb = ImageCms.profileToProfile(im,ImageCms.ImageCmsProfile(io.BytesIO(icc)),ImageCms.createProfile('sRGB'),outputMode='RGB')
    # These traversals were chosen after viewing the complete, original PNG.
    # Equality runs retain every input pixel, with no threshold or resampling.
    # Card bboxes below are human complete-edge interpretations, not outputs of
    # the historical x800 algorithm, native bounds, or generic card detection.
    specs = [('x',165,90,235),('x',750,90,235),('x',800,90,235),('x',895,90,235),
             ('x',165,315,480),('x',750,315,480),('x',800,315,480),('x',895,315,480),
             ('y',200,130,181),('y',200,880,905),('y',400,130,181),('y',400,880,905)]
    return {'path':str(p.relative_to(ROOT)),'sha256':sha(p),'size_pixels':list(im.size),'scale':scale,
            'icc_sha256':hashlib.sha256(icc).hexdigest(),
            'exact_srgb_runs':[{'axis':axis,'position_points':pos,'range_points':[lo,hi],'runs':runs(srgb,scale,axis,pos,lo,hi)} for axis,pos,lo,hi in specs]}

def main():
    a, ref = load(A/'result.json'),load(REF/'result.json')
    prefix_a,prefix_ref=normalized_prefix(a),normalized_prefix(ref)
    assert prefix_a==prefix_ref
    aw = next(w for w in a['windows'] if w['png']=='images-layout-light.png')
    assert aw['bounds_points']['Width']==920 and aw['bounds_points']['Height']==668
    assert aw['pixel_width']==1840 and aw['pixel_height']==1336
    assert len(a['windows'])==9 and len(a['commands'])==59
    assert all(c['passed'] for c in a['checks'])
    assert [c['status'] for c in a['commands']]==[3]+[0]*58
    assert a['success'] is False and a['cleanup']['success'] is False
    assert sha(REF/'images-layout-light.png')==sha(CONTROL/'raw/images-layout-light.png')
    report = {
      'verdict':'A_capture_geometry_usable_first_card_129pt_HDR_147pt_cleanup_failed',
      'scope':'Read-only review of original A PNGs/data and original remote14 observed/control. No UI, resampling, image edits, matching thresholds or product edits.',
      'source_sha':a['source_sha'],'A_result_sha256':sha(A/'result.json'),
      'A_overall_success':a['success'],'A_failure':a['failure'],'A_cleanup':a['cleanup'],
      'capture_checks':{'all_14_checks_pass':True,'PNG_count':9,'command_count':59,'startup_sessions_status_3_count':1,'remaining_commands_status_0_count':58,
        'source_prefix_from_set_language_through_Layout_window_list_same_as_remote14':True,'normalized_commands':prefix_a},
      'context':{'A_os':a['os'],'reference_os':ref['os'],'appearance':'light','A_preferences':a['system_preferences'],'reference_preferences':ref['system_preferences'],
        'A_own_pid':aw['pid'],'A_own_window':aw['window_number'],'A_requested_actual_outer_points':[920,668],'A_pixels_per_point':2,'reference_pixels_per_point':1,
        'layout_selected_check':next(c for c in a['checks'] if c.get('check')=='Selected Layout'),
        'sidebar_edge_visual_interval_points':[140,141],'detail_card_left_right_points':[161,900],
        'column_context':'Both original full screenshots show four children on one row within a five-column first Grid; HDR has two children in three columns. At width719, the original formulas floor((719+16)/(120+16))=5 and floor((719+16)/(192+16))=3. Matching sidebar boundary, card span, image fit positions and width context permit using the unchanged fixed-ROI probe. Full pixel equality is not expected across different OS/display scale/color profiles.',
        'grid_width_from_visual_card_inset_points':719,'grid_width_scope':'Card span739 minus original 10pt left/right row inset; confirm with B observer before treating as native allocated grid width.'},
      'A_original_PNGs':[{'name':w['png'],'sha256':sha(A/w['png']),'pixels':[w['pixel_width'],w['pixel_height']],'points':[w['bounds_points']['Width'],w['bounds_points']['Height']]} for w in a['windows']],
      'manual_complete_original_PNG_edge_interpretation':{
        'A_images_card_half_open_points':[161,98,900,227],'reference_images_card_half_open_points':[161,98,900,223],
        'A_images_card_height_points':129,'reference_images_card_height_points':125,
        'A_HDR_card_half_open_points':[161,325,900,472],'reference_HDR_card_half_open_points':[161,321,900,468],
        'A_HDR_card_height_points':147,'reference_HDR_card_height_points':147,
        'interpretation':'The unchanged first-card top and interior pictures/captions, four extra points below its caption, then the later HDR card shifted down four points are present in the full original A screenshot. The second card keeps its 147pt height. Complete visible left/right/top/bottom edges are corroborated by multiple exact sRGB traversals, including border antialiasing at 0.5pt on A.',
        'limits':'These are original raster edge intervals in window points, not public native view bounds or a causal diagnosis. Cross14 caption raster edges differ at subpoint precision because scale2 vs scale1. PQ rendering differs visibly and is not accepted as equivalent by this geometry review.'},
      'fixed_original_measurement':{'script':'outputs/Bern/Docs/Evidence/macOS14-picture-scene-control-40135147500/measurement-review/measured.py',
        'script_sha256':sha(CONTROL/'measurement-review/measured.py'),'output':'A-fixed-original-measurement.json','output_sha256':sha(OUT/'A-fixed-original-measurement.json'),
        'unchanged_ROIs_thresholds_ICC_arguments':True,'full_ROI_scope':'Fixed ROI values remain diagnostic ink/color intervals. They are not whole native card detection, nor a geometry correction. All requested captions/headings remain visibly inside the corresponding original fixed ROIs.'},
      'scans':[scan(A/'images-layout-light.png',2),scan(REF/'images-layout-light.png',1)],
      'pending':['B capture and same13 observer noninterference comparison','B public observer event comparison against14; do not infer root cause from current A raster alone']
    }
    target=OUT/'A-review.json'
    with target.open('x') as f: json.dump(report,f,ensure_ascii=False,indent=2);f.write('\n')
    print(json.dumps({'report':str(target),'sha256':sha(target),'first_card_points':129,'HDR_card_points':147}))

if __name__=='__main__':main()
