#!/usr/bin/env python3
"""Prepared offline wrapper. Root's hash-bound gates must precede all PNG reads."""
from pathlib import Path
import argparse, datetime, gzip, hashlib, io, json, subprocess, sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
INPUTS = {
    'default': ROOT / 'work/hero-cg-direct13/runtime13-default',
    'direct': ROOT / 'work/hero-cg-direct13/runtime13-direct',
    'reference14': ROOT / 'outputs/Bern/Docs/Evidence/macOS14-hero-cgsemantics-40119614788/same-binary-13-14/runtime14/on',
}
FROZEN14 = ROOT / 'outputs/Bern/Docs/Evidence/macOS14-hero-snapshot-40080838898/analysis/host-analyzer/sdk26-14-analysis/analysis.json'
GEOMETRY_SHA = 'aef01e69917f0d6f64c0d9f0f4f2d434511978624d052e432a6cdd800eecc0b3'
PHASES = ('progress-0', 'progress-1')
REUSED = {
    'analyze.py': '98243090f0b45fe18baed3d89d4e382c7d8f7c02662a930cfda8c87c3b0f39d4',
    'compare.py': 'c151280eb0ced6501197d56e7a8f229d73d4679ab43e931edde68c9312be0d0a',
    'atlas-rois.json': '39ca622a45c0120d08e90daa7a17a0145be1b79485decb4619a0e5a3f23cadaf',
}
inputs, commands = {}, []

def require(condition, message):
    if not condition:
        raise ValueError(message)

def digest(data): return hashlib.sha256(data).hexdigest()
def read(path):
    path = path.resolve()
    data = path.read_bytes()
    inputs[str(path.relative_to(ROOT))] = {'bytes': len(data), 'sha256': digest(data)}
    return data
def js(path): return json.loads(read(path))
def save(path, value): path.write_text(json.dumps(value, indent=2, sort_keys=True, allow_nan=False) + '\n')
def sub(a, b): return [x-y for x, y in zip(a, b)]
def indexed(captures):
    require(len(captures) == 2 and {c['phase'] for c in captures} == set(PHASES), 'Need exactly two unique phases')
    return {c['phase']: c for c in captures}

def check_gates(gates):
    require(gates.get('schema') == 1 and gates.get('approved_to_run_pixel_analysis') is True,
            'Explicit root approval is required before pixel analysis')
    require(gates.get('default_12roi_control_passed') is True and gates.get('native_runtime_gates_passed') is True,
            'Root default twelve-ROI and native gates must pass first')
    require(gates.get('geometry_plan_sha256') == GEOMETRY_SHA, 'Different geometry policy')
    require(set(gates['inputs']) == set(INPUTS), 'Gate input labels differ')
    for label, directory in INPUTS.items():
        report_data = read(directory / 'report.json')
        require(digest(report_data) == gates['inputs'][label]['report_sha256'], 'Root gate report hash mismatch: ' + label)
        captures = indexed(json.loads(report_data)['captures'])
        require(set(gates['inputs'][label]['png_sha256_by_phase']) == set(PHASES), 'Gate needs both PNG hashes')
        for phase, capture in captures.items():
            require(capture['png_sha256'] == gates['inputs'][label]['png_sha256_by_phase'][phase],
                    'Root gate PNG hash mismatch: ' + label + '/' + phase)
    require(set(gates['direct_geometry']) == set(PHASES), 'Geometry needs both phases')
    for phase in PHASES:
        gate = gates['direct_geometry'][phase]
        require(gate['upright_nonempty'] is True and gate['full_visible_extent_no_visible_background_leak'] is True,
                'Direct geometry incomplete: ' + phase)
        require(gate['evidence'] == 'root-original-png-visual-only' and gate['limitations_acknowledged'] is True,
                'Root original-PNG visual gate and its limits must be explicit')

def run(args, label, out):
    command = [sys.executable, '-B'] + [str(a) for a in args]
    with (out / (label + '.stdout.log')).open('xb') as stdout, (out / (label + '.stderr.log')).open('xb') as stderr:
        completed = subprocess.run(command, cwd=ROOT, stdout=stdout, stderr=stderr, timeout=60)
    commands.append({'command': command, 'exit_code': completed.returncode})
    require(completed.returncode == 0, label + ' failed; partial logs retained')

def load(directory, atlas, spec, pil):
    Image, ImageCms, ImageStat = pil
    report = js(directory / 'report.json')
    require(report['success'] is True and report['completed_phases'] == 2, 'Incomplete acquisition')
    require(report['cache_unchanged'] is True and report['cache_before'] == report['cache_after'], 'Cache changed')
    require(report['frontmost_before'] == report['frontmost_after'] and report['activation_calls'] == 0, 'Frontmost changed')
    require(all(v is False for key in ('normal_before', 'normal_after') for v in report[key].values()), 'Normal policy failed')
    result = {}
    for phase, capture in indexed(report['captures']).items():
        require(capture['consecutive_equal_buffers'] >= 5, 'Fewer than five stable buffers')
        require(not capture['key'] and not capture['active'] and capture['live_metal_count'] == 0, 'Capture native state failed')
        require(capture['manager']['flight_count'] == 0 and capture['manager']['timer_exists'] is False, 'Manager state failed')
        name = Path(capture['png'])
        require(not name.is_absolute() and '..' not in name.parts, 'Unsafe relative PNG path')
        data = read(directory / name)
        require(digest(data) == capture['png_sha256'], 'PNG hash mismatch')
        atlas.png_header(data)
        with Image.open(io.BytesIO(data)) as image:
            image.load()
            require(image.mode in ('RGB', 'RGBA') and list(image.size) == capture['capture_size'], 'PNG dimensions/mode differ')
            profile = image.info['icc_profile']
            require(digest(profile) == capture['capture_icc_sha256'], 'Embedded ICC differs from recorded ICC')
            raw = image.convert('RGB')
            norm = ImageCms.profileToProfile(raw, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile('sRGB'), renderingIntent=0, outputMode='RGB', flags=0)
            panes = {}
            require(set(capture['rois']) == set(atlas.NAMES), 'Unexpected pane roles')
            for role, roi in capture['rois'].items():
                box = atlas.rect_box(roi['screenshot_pixels'], role)
                require(0 <= box[0] < box[2] <= image.width and 0 <= box[1] < box[3] <= image.height, 'ROI outside PNG')
                require(image.mode == 'RGB' or image.getchannel('A').crop(box).getextrema() == (255, 255), 'Nonopaque capture')
                panes[role] = {'geometry': roi, 'raw': atlas.measure(raw.crop(box), spec, ImageStat),
                               'srgb': atlas.measure(norm.crop(box), spec, ImageStat)}
        result[phase] = panes
    return result

def pairwise(left, right, atlas, ImageChops, ImageStat):
    rows = []
    for phase in PHASES:
        for role in atlas.NAMES:
            a, b = left[phase][role], right[phase][role]
            require(a['geometry'] == b['geometry'], 'No geometry registration permitted')
            rows.append({'phase': phase, 'role': role, 'geometry': a['geometry'],
                         'raw': atlas.compare(a['raw'], b['raw'], ImageChops, ImageStat),
                         'srgb': atlas.compare(a['srgb'], b['srgb'], ImageChops, ImageStat)})
    return rows

def vector_stats(rows):
    return {'channel_mean_absolute_codes': [sum(abs(r[c]) for r in rows)/len(rows) for c in range(3)],
            'channel_max_absolute_codes': [max(abs(r[c]) for r in rows) for c in range(3)],
            'mean_absolute_codes': sum(abs(x) for r in rows for x in r)/(3*len(rows)),
            'max_absolute_codes': max(abs(x) for r in rows for x in r)}
def ramp_stats(columns):
    return {'columns': len(columns), 'mean_rgb': [sum(r[c] for r in columns)/len(columns) for c in range(3)],
            'column_mean_min_rgb': [min(r[c] for r in columns) for c in range(3)],
            'column_mean_max_rgb': [max(r[c] for r in columns) for c in range(3)]}
def classify(changes):
    return ['larger_absolute_residual' if v > 0 else 'smaller_absolute_residual' if v < 0 else 'unchanged' for v in changes]

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--gates', type=Path, required=True, help='Root-authored hash-bound approval/geometry gates JSON')
    parser.add_argument('--output', type=Path, default=HERE/'result', help='Fresh directory below this prepared analysis workspace')
    args = parser.parse_args()
    out = args.output.resolve()
    require(HERE in out.parents and not out.exists(), 'Output must be fresh and below this private analysis directory')
    out.mkdir()
    started = datetime.datetime.now(datetime.timezone.utc).isoformat()
    result = {'complete': False, 'color_conclusion_allowed': False, 'error': None}
    versions = None
    try:
        gates = js(args.gates)
        check_gates(gates)  # No PIL import or PNG read occurs before root's completed gates.
        result['root_gates'] = gates
        for name, expected in REUSED.items():
            require(digest(read(HERE/name)) == expected, 'Reused analysis file changed: ' + name)
        import analyze as atlas
        from PIL import Image, ImageCms, ImageStat, ImageChops, __version__ as pillow_version
        versions = {'pillow': pillow_version, 'littlecms': ImageCms.core.littlecms_version}
        spec = js(HERE/'atlas-rois.json')
        frozen14 = js(FROZEN14)
        require(frozen14['versions'] == versions, 'Frozen14 Pillow/LittleCMS versions differ')
        require(frozen14['analyzer_sha256'] == digest(read(HERE/'analyze.py')), 'Analyzer differs from frozen14')
        require(frozen14['atlas_spec_sha256'] == digest(read(HERE/'atlas-rois.json')), 'Atlas spec differs from frozen14')
        for label, directory in INPUTS.items():
            run([HERE/'analyze.py', directory/'report.json', '--output', out/(label+'-analysis')], label, out)
        analyses = {label: js(out/(label+'-analysis/analysis.json')) for label in INPUTS}
        for label, analysis in analyses.items():
            require(analysis['input_report_sha256'] == gates['inputs'][label]['report_sha256'], 'Child report differs from root gate')
            captures = indexed(analysis['captures'])
            require(all(captures[p]['png_sha256'] == gates['inputs'][label]['png_sha256_by_phase'][p] for p in PHASES), 'Child PNG differs from root gate')
        repeated = analyses['reference14']
        require(len(repeated['comparisons']) == 68 and len(repeated['primary_comparisons']) == 16, 'Unexpected14 comparison count')
        require(repeated['comparisons'] == frozen14['comparisons'], 'Recomputed14 metrics differ from frozen14')
        require(repeated['primary_comparisons'] == frozen14['primary_comparisons'], 'Recomputed14 primary metrics differ')
        old_captures, new_captures = indexed(frozen14['captures']), indexed(repeated['captures'])
        require(all(new_captures[p]['rois'] == old_captures[p]['rois'] for p in PHASES), 'Recomputed14 complete ROI records differ')
        require(repeated['ramp_column_means']['sha256'] == frozen14['ramp_column_means']['sha256'], 'Recomputed14 ramp gzip SHA differs; no fallback')
        result['reference14_recomputed_metrics_equal_frozen'] = True
        panes = {label: load(directory, atlas, spec, (Image, ImageCms, ImageStat)) for label, directory in INPUTS.items()}
        delta = pairwise(panes['default'], panes['direct'], atlas, ImageChops, ImageStat)
        result['default_to_direct_all_12roi'] = delta
        others = [row for row in delta if row['role'] != 'flight-named']
        result['all_other_10roi_raw_and_srgb_exact'] = all(row[d]['rgb_exact'] for row in others for d in ('raw', 'srgb'))
        require(len(others) == 10 and result['all_other_10roi_raw_and_srgb_exact'], 'Other pane control changed; no candidate color conclusion')
        nonempty = []
        for phase in PHASES:
            pane = panes['direct'][phase]['flight-named']
            require(pane['geometry']['host_top_left_points'] == {'x':16,'y':244,'width':320,'height':180}, 'Unexpected fixed named pane')
            extrema = ImageStat.Stat(pane['raw']['image']).extrema
            require(any(a != b for a, b in extrema), 'Candidate named pane uniform; no color conclusion')
            nonempty.append({'phase':phase,'geometry':pane['geometry'],'pixel_size':list(pane['raw']['image'].size),
                             'raw_channel_extrema':extrema,'scope':'Supplementary nonuniformity only; upright/visible extent are root visual gates, not proved by extrema/alpha.'})
        result['candidate_named_nonempty_geometry'] = nonempty
        for label in ('default', 'direct'):
            run([HERE/'compare.py', out/(label+'-analysis/analysis.json'), out/'reference14-analysis/analysis.json',
                 '--output', out/(label+'-crosshost')], label+'-crosshost', out)
        cross = {label:js(out/(label+'-crosshost/comparison.json')) for label in ('default','direct')}
        expected_cross = {(phase,source) for phase in PHASES for source in ('named','custom')}
        for label in ('default','direct'):
            rows = cross[label]['comparisons']
            require(len(rows) == 4 and {(r['phase'],r['source']) for r in rows} == expected_cross, 'Incomplete/duplicate crosshost rows')
        residuals = []
        for a,b in zip(cross['default']['comparisons'], cross['direct']['comparisons']):
            require((a['phase'],a['source']) == (b['phase'],b['source']), 'Crosshost row mismatch')
            patches, oldv, newv = {}, [], []
            counts = {'smaller_absolute_residual':0,'larger_absolute_residual':0,'unchanged':0}
            for name in sorted(a['patches']):
                old = a['patches'][name]['residual_13_minus_14']; new = b['patches'][name]['residual_13_minus_14']
                changes = sub(list(map(abs,new)),list(map(abs,old)))
                categories = classify(changes)
                for category in categories: counts[category] += 1
                patches[name] = {'default_D13_minus_D14':old,'direct_D13_minus_D14':new,'signed_change':sub(new,old),
                                 'absolute_residual_change':changes,'RGB_channel_classification':categories}
                oldv.append(old); newv.append(new)
            residuals.append({'phase':a['phase'],'source':a['source'],'default':vector_stats(oldv),'direct':vector_stats(newv),
                              'patches':patches,'channel_counts_no_threshold':counts})
        result['crosshost_all_patch_channel_residual_changes'] = residuals
        ramps = {label:json.loads(gzip.decompress(read(out/(label+'-analysis/ramp-column-means.json.gz')))) for label in INPUTS}
        ramp_rows = []
        for phase in PHASES:
            for source in ('named','custom'):
                stats = {label:{role:ramp_stats(ramps[label][phase][role]['icc_to_srgb']) for role in ('body-'+source,'flight-'+source)} for label in INPUTS}
                d = {label:sub(v['flight-'+source]['mean_rgb'],v['body-'+source]['mean_rgb']) for label,v in stats.items()}
                old = sub(d['default'],d['reference14']); new = sub(d['direct'],d['reference14'])
                changes = sub(list(map(abs,new)),list(map(abs,old)))
                ramp_rows.append({'phase':phase,'source':source,'native_ramp_stats':stats,'hero_minus_body_mean_rgb':d,
                                  'default_D13_minus_D14':old,'direct_D13_minus_D14':new,'signed_change':sub(new,old),
                                  'absolute_residual_change':changes,'RGB_channel_classification':classify(changes),
                                  'scope':'Native whole-ramp aggregates only; every raw/sRGB native column retained in child analyses. No crosshost column pairing, fitting or resampling.'})
        check_gates(gates)  # Recheck root-bound report/PNG identities after all analysis; no gate mutation.
        result.update(complete=True,color_conclusion_allowed=True,versions=versions,gray_ramp_all_sources=ramp_rows,
                      scope='Original actual snapshot CG direct adapter versus unchanged NSImage control. All ten patches, RGB channels, both phases and named/custom retained. Encoded codes, not physical HDR or a causal/product acceptance claim.')
    except Exception as error:
        result['error'] = str(error)
        raise
    finally:
        result['inputs'] = inputs
        save(out/'summary.json', result)
        save(out/'execution.json', {'started_utc':started,'finished_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
            'commands':commands,'python':sys.version,'versions':versions,'no_ui_compile_ci_or_input_writes':True})

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print('Offline CG-direct analysis incomplete: ' + str(error), file=sys.stderr)
        sys.exit(1)
