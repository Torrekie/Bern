#!/usr/bin/env python3
"""Offline retained-PNG analysis; no native runtime or executable is invoked."""
from pathlib import Path
import datetime, gzip, hashlib, io, json, subprocess, sys
from PIL import Image, ImageCms, ImageStat, ImageChops, __version__ as pillow_version
import analyze as atlas

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
OLD = ROOT / 'outputs/Bern/Docs/Evidence/macOS14-hero-snapshot-40080838898'
LOCAL = ROOT / 'work/hero-snapshot-native-view13'
FROZEN13 = ROOT / 'outputs/Bern/Docs/Evidence/macOS13-hdr-candidate/native-pq-hero-static-route13/fixture/runtime13-overlay'
inputs, commands = {}, []

def digest(data): return hashlib.sha256(data).hexdigest()
def read(path):
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = {'bytes': len(data), 'sha256': digest(data)}
    return data
def js(path): return json.loads(read(path))
def run(args, label):
    command = [sys.executable, '-B'] + [str(a) for a in args]
    with (HERE / (label + '.stdout.log')).open('wb') as out, (HERE / (label + '.stderr.log')).open('wb') as err:
        completed = subprocess.run(command, cwd=ROOT, stdout=out, stderr=err, timeout=60)
    commands.append({'command': command, 'exit_code': completed.returncode})
    assert completed.returncode == 0, label + ' failed; retain partial logs'
def analysis(label): return json.loads((HERE / (label + '-analysis') / 'analysis.json').read_text())

def load(directory):
    report = js(directory / 'report.json')
    assert report['success'] and report['completed_phases'] == 2
    assert report['cache_unchanged'] and report['cache_before'] == report['cache_after']
    assert report['frontmost_before'] == report['frontmost_after'] and report['activation_calls'] == 0
    assert all(v is False for k in ['normal_before', 'normal_after'] for v in report[k].values())
    result = {}
    for capture in report['captures']:
        assert capture['phase'] not in result and capture['consecutive_equal_buffers'] >= 5
        assert not capture['key'] and not capture['active'] and capture['live_metal_count'] == 0
        assert capture['manager']['flight_count'] == 0 and capture['manager']['timer_exists'] is False
        name = Path(capture['png']); assert not name.is_absolute() and '..' not in name.parts
        data = read(directory / name); assert digest(data) == capture['png_sha256']
        atlas.png_header(data)
        image = Image.open(io.BytesIO(data)); image.load()
        assert image.mode in ('RGB', 'RGBA') and list(image.size) == capture['capture_size']
        profile = image.info['icc_profile']; assert digest(profile) == capture['capture_icc_sha256']
        raw = image.convert('RGB')
        norm = ImageCms.profileToProfile(raw, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
            ImageCms.createProfile('sRGB'), renderingIntent=0, outputMode='RGB', flags=0)
        panes = {}
        assert set(capture['rois']) == set(atlas.NAMES)
        for role, roi in capture['rois'].items():
            box = atlas.rect_box(roi['screenshot_pixels'], role)
            assert 0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height
            assert image.mode == 'RGB' or image.getchannel('A').crop(box).getextrema() == (255, 255)
            panes[role] = {'geometry': roi, 'raw': atlas.measure(raw.crop(box), spec, ImageStat),
                           'srgb': atlas.measure(norm.crop(box), spec, ImageStat)}
        result[capture['phase']] = panes
    assert set(result) == set(atlas.PHASES)
    return report, result

def pairwise(left, right):
    rows = []
    for phase in atlas.PHASES:
        for role in atlas.NAMES:
            a, b = left[phase][role], right[phase][role]
            assert a['geometry'] == b['geometry'], 'No geometry registration is permitted'
            rows.append({'phase': phase, 'role': role, 'geometry': a['geometry'],
                'raw': atlas.compare(a['raw'], b['raw'], ImageChops, ImageStat),
                'srgb': atlas.compare(a['srgb'], b['srgb'], ImageChops, ImageStat)})
    return rows

def ramp_stats(columns):
    return {'columns': len(columns), 'mean_rgb': [sum(r[c] for r in columns) / len(columns) for c in range(3)],
            'column_mean_min_rgb': [min(r[c] for r in columns) for c in range(3)],
            'column_mean_max_rgb': [max(r[c] for r in columns) for c in range(3)]}
def sub(a,b): return [x-y for x,y in zip(a,b)]
def vector_stats(rows):
    return {'mean_absolute_codes': sum(abs(x) for r in rows for x in r) / (3*len(rows)),
            'max_absolute_codes': max(abs(x) for r in rows for x in r)}

assert not (HERE / 'summary.json').exists() and not (HERE / 'execution.json').exists()
started = datetime.datetime.now(datetime.timezone.utc).isoformat()
spec = js(HERE / 'atlas-rois.json')
try:
    frozen14 = js(OLD / 'analysis/host-analyzer/sdk26-14-analysis/analysis.json')
    assert frozen14['versions'] == {'pillow': pillow_version, 'littlecms': ImageCms.core.littlecms_version}
    assert frozen14['analyzer_sha256'] == digest((HERE/'analyze.py').read_bytes())
    assert frozen14['atlas_spec_sha256'] == digest((HERE/'atlas-rois.json').read_bytes())
    for label, directory in [('control', LOCAL/'runtime13-control'), ('image-view', LOCAL/'runtime13-image-view'), ('reference14', OLD/'runtime40080838898/runtime14')]:
        run([HERE/'analyze.py', directory/'report.json', '--output', HERE/(label+'-analysis')], label)
    repeated14 = analysis('reference14')
    assert repeated14['comparisons'] == frozen14['comparisons'], 'Recomputed14 metrics differ from frozen baseline'
    assert [c['rois'] for c in repeated14['captures']] == [c['rois'] for c in frozen14['captures']]
    assert repeated14['ramp_column_means']['sha256'] == frozen14['ramp_column_means']['sha256']
    for label in ['control', 'image-view']:
        run([HERE/'compare.py', HERE/(label+'-analysis/analysis.json'), HERE/'reference14-analysis/analysis.json',
            '--output', HERE/(label+'-crosshost')], label+'-crosshost')
    cr, control = load(LOCAL/'runtime13-control'); nr, native = load(LOCAL/'runtime13-image-view')
    _, frozen = load(FROZEN13)
    load(OLD/'runtime40080838898/runtime14')  # Verify retained reference PNG/report hashes/ICC too.
    assert cr['native_display']['selected'] == 'control' and cr['native_display']['records'] == []
    nd = nr['native_display']; assert nd['selected'] == 'image-view' and nd['success'] and nd['error'] is None
    assert [r['stage'] for r in nd['records']] == ['mounted','post_progress_0_png','post_progress_1_png','post_final_guards']
    for field in ['child_identity','flight_identity','image_identity']:
        assert len({r[field] for r in nd['records']}) == 1
    assert all(r['child_class'] == 'NSImageView' and r['same_from_to_image'] and r['skip_original_draw'] for r in nd['records'])
    base_control, candidate_delta = pairwise(frozen,control), pairwise(control,native)
    assert all(r[d]['rgb_exact'] for r in base_control for d in ['raw','srgb'])
    nonempty = []
    for phase in atlas.PHASES:
        pane = native[phase]['flight-named']; rect = pane['geometry']['host_top_left_points']
        assert rect == {'x':16,'y':244,'width':320,'height':180}
        image = pane['raw']['image']; extrema = ImageStat.Stat(image).extrema
        assert any(a != b for a,b in extrema), 'Candidate named ROI is uniform/empty'
        nonempty.append({'phase':phase,'opaque':True,'pixel_size':list(image.size),'raw_channel_extrema':extrema,
            'distinct_patch_mean_rgb':len({tuple(p['mean_rgb']) for p in pane['raw']['patches'].values()}),
            'atlas_patch_and_ramp_interiors_measured':True,'geometry':pane['geometry']})
    cross = {label:json.loads((HERE/(label+'-crosshost/comparison.json')).read_text()) for label in ['control','image-view']}
    residuals=[]
    for a,b in zip(cross['control']['comparisons'],cross['image-view']['comparisons']):
        assert a['phase']==b['phase'] and a['source']==b['source']
        patches={}; oldv=[];newv=[];counts={'smaller_absolute_residual_channels':0,'larger_absolute_residual_channels':0,'unchanged_channels':0}
        for name in sorted(a['patches']):
            old=a['patches'][name]['residual_13_minus_14']; new=b['patches'][name]['residual_13_minus_14']
            patches[name]={'control_D13_minus_D14':old,'image_view_D13_minus_D14':new,
                           'signed_change':sub(new,old),'absolute_residual_change':sub(list(map(abs,new)),list(map(abs,old)))}
            oldv.append(old);newv.append(new)
            for x,y in zip(old,new):
                z=abs(y)-abs(x)
                counts['unchanged_channels' if abs(z)<1e-12 else 'larger_absolute_residual_channels' if z>0 else 'smaller_absolute_residual_channels']+=1
        residuals.append({'phase':a['phase'],'source':a['source'],'control':vector_stats(oldv),'image_view':vector_stats(newv),'patches':patches,**counts})
    ramp_data={label:json.loads(gzip.decompress((HERE/(label+'-analysis/ramp-column-means.json.gz')).read_bytes())) for label in ['control','image-view','reference14']}
    ramp_rows=[]
    for phase in atlas.PHASES:
        stats={label:{role:ramp_stats(ramp_data[label][phase][role]['icc_to_srgb']) for role in ['body-named','flight-named']} for label in ramp_data}
        d={label:sub(v['flight-named']['mean_rgb'],v['body-named']['mean_rgb']) for label,v in stats.items()}
        ramp_rows.append({'phase':phase,'native_ramp_stats':stats,'hero_minus_body_mean_rgb':d,
            'control_D13_minus_D14':sub(d['control'],d['reference14']),
            'image_view_D13_minus_D14':sub(d['image-view'],d['reference14']),
            'scope':'Native-resolution whole-ramp aggregate only; no cross-host column pairing/resampling.'})
    result={'complete':True,'versions':repeated14['versions'],'atlas_spec_sha256':digest((HERE/'atlas-rois.json').read_bytes()),
        'reference14_recomputed_metrics_equal_frozen':True,'frozen_static13_overlay_to_control':base_control,
        'control_to_image_view':candidate_delta,'candidate_named_nonempty_geometry':nonempty,
        'crosshost_patch_residual_change':residuals,'gray_ramp_aggregate':ramp_rows,
        'native_display_reported':nd,'inputs':inputs,
        'scope':'Actual original renderer snapshot NSImage in stock NSImageView; not an original-CGImage NSImageView experiment. Encoded RGB codes, no physical HDR/causal/rounding claim. Full10patches and gray-ramp; no image registration/resampling or cross-host pixel equality.'}
    (HERE/'summary.json').write_text(json.dumps(result,indent=2,sort_keys=True)+'\n')
finally:
    (HERE/'execution.json').write_text(json.dumps({'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'commands':commands,'python':sys.version,'pillow':pillow_version,'littlecms':ImageCms.core.littlecms_version,'no_ui_compile_ci_or_input_writes':True},indent=2,sort_keys=True)+'\n')
