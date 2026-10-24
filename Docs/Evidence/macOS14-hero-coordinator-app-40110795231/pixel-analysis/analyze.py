#!/usr/bin/env python3
"""Prepared only: read original PNGs/reports and write one fresh, small numeric JSON."""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import io
import json
from PIL import Image, ImageCms, ImageChops, ImageStat

def digest(data):
    return hashlib.sha256(data).hexdigest()

def integer_box(rect, size):
    values = [rect['x'], rect['y'], rect['x'] + rect['width'], rect['y'] + rect['height']]
    assert all(abs(v - round(v)) < 1e-6 for v in values), 'Nonintegral measured pixel ROI; no resampling'
    box = tuple(round(v) for v in values)
    assert 0 <= box[0] < box[2] <= size[0] and 0 <= box[1] < box[3] <= size[1], 'ROI outside image'
    return box

def opaque(row, box):
    return row['image'].mode == 'RGB' or row['image'].getchannel('A').crop(box).getextrema() == (255, 255)

def load_runtime(directory, phases, inputs):
    report_file = directory / 'report.json'
    if not report_file.is_file():
        return {'error': 'Missing report', 'rows': {}, 'directory': str(directory)}
    raw_report = report_file.read_bytes()
    inputs[str(report_file)] = {'sha256': digest(raw_report), 'bytes': len(raw_report), 'kind': 'report'}
    report = json.loads(raw_report)
    rows, errors = {}, []
    for capture in report.get('captures', []):
        phase = capture.get('phase')
        if phase not in phases:
            continue
        try:
            assert phase not in rows, 'Duplicate capture phase'
            relative = PurePosixPath(capture['png'])
            assert not relative.is_absolute() and '..' not in relative.parts, 'Unsafe PNG path'
            path = directory / str(relative)
            data = path.read_bytes()
            inputs[str(path)] = {'sha256': digest(data), 'bytes': len(data), 'kind': 'original_png'}
            assert digest(data) == capture['png_sha256'], 'PNG/report SHA mismatch'
            image = Image.open(io.BytesIO(data)); image.load()
            assert image.mode in ('RGB', 'RGBA'), 'Unexpected capture pixel mode'
            assert list(image.size) == capture['capture_size'], 'PNG/report size mismatch'
            profile = image.info.get('icc_profile'); assert profile, 'Missing embedded ICC'
            assert digest(profile) == capture['capture_icc_sha256'], 'PNG/report ICC SHA mismatch'
            raw = image.convert('RGB')
            srgb = ImageCms.profileToProfile(raw, ImageCms.ImageCmsProfile(io.BytesIO(profile)),
                ImageCms.createProfile('sRGB'), renderingIntent=0, outputMode='RGB', flags=0)
            rows[phase] = {'capture': capture, 'image': image, 'raw': raw, 'srgb': srgb,
                           'icc_sha256': digest(profile), 'png_sha256': digest(data)}
        except (AssertionError, KeyError, OSError, ValueError) as error:
            errors.append({'phase': phase, 'reason': str(error)})
    return {'report': report, 'rows': rows, 'errors': errors, 'directory': str(directory),
            'error': None if report.get('success') is True else 'Native acquisition report is partial/failed'}

def require(runtime, phases):
    assert runtime.get('error') is None, runtime.get('error')
    assert not runtime.get('errors'), runtime.get('errors')
    assert all(phase in runtime['rows'] for phase in phases), 'Missing required capture(s)'

def roi(runtime, phase, name):
    row = runtime['rows'][phase]
    box = integer_box(row['capture']['rois'][name]['screenshot_pixels'], row['image'].size)
    assert opaque(row, box), 'ROI is not entirely alpha255'
    return row, box

def compare(a, a_phase, a_name, b, b_phase, b_name):
    require(a, [a_phase]); require(b, [b_phase])
    left, lb = roi(a, a_phase, a_name); right, rb = roi(b, b_phase, b_name)
    assert (lb[2] - lb[0], lb[3] - lb[1]) == (rb[2] - rb[0], rb[3] - rb[1]), 'Different ROI size; no resampling'
    result = {'status': 'performed', 'left_roi_pixels': lb, 'right_roi_pixels': rb,
              'size_pixels': [lb[2] - lb[0], lb[3] - lb[1]], 'opaque': True,
              'embedded_icc_identical': left['icc_sha256'] == right['icc_sha256'],
              'left_icc_sha256': left['icc_sha256'], 'right_icc_sha256': right['icc_sha256']}
    for mode in ('raw', 'srgb'):
        x, y = left[mode].crop(lb), right[mode].crop(rb)
        difference = ImageChops.difference(x, y); stats = ImageStat.Stat(difference)
        result[mode] = {'mae': sum(stats.mean) / 3, 'max': max(v[1] for v in stats.extrema),
                        'exact': difference.getbbox() is None}
    return result

def timing(runtime):
    require(runtime, ['in-flight'])
    report = runtime['report']; capture = runtime['rows']['in-flight']['capture']
    arm = report['midflight_sampling']['armed']; sampled = report['midflight_sampling']['capture_sample']
    assert report['native_gates']['midband_armed'] is True and report['native_gates']['next_sample_captured'] is True
    assert sampled['sample_index'] == arm['sample_index'] + 1
    assert 0.2 < arm['progress'] < 0.8
    assert sampled['flight_identity'] == arm['flight_identity']
    for prefix, sample in [('armed', arm), ('capture', sampled)]:
        assert capture[prefix + '_sample_index'] == sample['sample_index']
        assert capture[prefix + '_sample_state'] == sample['state']
        assert capture[prefix + '_sample_uptime'] == sample['uptime']
        expected_progress = capture['armed_progress'] if prefix == 'armed' else capture['capture_sample_progress']
        assert expected_progress == sample['progress']
        row = report['samples'][sample['sample_index']]
        assert row['sample_index'] == sample['sample_index']
        assert all(row[k] == value for k, value in sample['state'].items())
    assert capture['trigger_refers_to'] == 'armed_sample'
    assert capture['trigger_state'] == arm['state'] and capture['trigger_progress'] == arm['progress']
    return {'status': 'performed', 'policy': report['midflight_sampling']['policy'], 'armed': arm,
            'capture_sample': sampled, 'capture_before_uptime': capture['capture_before_uptime'],
            'capture_after_uptime': capture['capture_after_uptime'], 'state_before': capture['state_before'],
            'state_after': capture['state_after'], 'actual_native_rois': capture['rois'],
            'interpretation': 'Native state/time brackets and measured ROI only; not the rendered frame or synchronization.'}

def execution_model(runtime):
    require(runtime, [])
    report = runtime['report']
    model = report['execution_model']
    assert model['kind'] == 'nsapplication_run_delegate_default_timer', 'Unexpected execution model'
    for name in ('launch_completed_count', 'loop_entry_count', 'loop_return_count',
                 'terminal_count', 'stop_calls', 'wake_count'):
        assert model[name] == 1, f'{name} must be one'
    for name in ('sampler_reentrant_callbacks', 'sampler_callbacks_after_terminal'):
        assert model[name] == 0, f'{name} must be zero'
    assert model['sampler_max_depth'] == 1
    assert model['sampler_callback_count'] > 0
    assert 0 < len(report['samples']) <= 512
    assert model['sampler_observed_modes'] == [model['sampler_mode']], 'Observer mode mismatch'
    assert model['sampler_interval_seconds'] == 1 / 60
    assert model['sampler_invalidated_before_stop'] is True
    assert model['wake_after_terminal'] is True
    assert model['wake_posted_to_own_app_queue'] is True
    assert model['wake_type'] == 'applicationDefined'
    assert model['preload_started_uptime'] <= model['preload_completed_uptime']
    assert model['preload_completed_uptime'] - model['preload_started_uptime'] <= 3
    assert model['loop_entry_uptime'] <= model['launch_completed_uptime']
    assert model['launch_completed_uptime'] <= model['terminal_uptime'] <= model['loop_return_uptime']
    assert report.get('execution_contract_error') is None
    return {'status': 'performed', 'reported': model,
            'interpretation': 'Reported execution counters and timestamps only. Invalidated-before-stop is the source-path flag, not an independent Timer.isValid observation. No display synchronization or cause inference.'}

def mid_bounds(runtime):
    require(runtime, ['before', 'in-flight'])
    before = runtime['rows']['before']; mid = runtime['rows']['in-flight']
    assert before['image'].size == mid['image'].size, 'Window raster size changed'
    source = before['capture']['rois']['source']
    pixels, points = source['screenshot_pixels'], source['root_points']
    sx, sy = pixels['width'] / points['width'], pixels['height'] / points['height']
    assert sx > 0 and abs(sx - sy) < 1e-6, 'Nonuniform measured conversion'
    # Actual captured source ROI establishes root origin/scale; logical flight rect is never a pixel ROI.
    rx, ry = pixels['x'] - points['x'] * sx, pixels['y'] - points['y'] * sy
    inset = {'x': rx + 12 * sx, 'y': ry + 12 * sy,
             'width': (1024 - 24) * sx, 'height': (440 - 24) * sy}
    box = integer_box(inset, mid['image'].size)
    assert opaque(mid, box), 'Fixed12pt root inset contains nonopaque pixels'
    crop = mid['srgb'].crop(box)
    bounds = ImageChops.difference(crop, Image.new('RGB', crop.size, (255, 255, 255))).getbbox()
    root_bounds = None if bounds is None else [(bounds[0] + box[0] - rx) / sx, (bounds[1] + box[1] - ry) / sy,
                                              (bounds[2] + box[0] - rx) / sx, (bounds[3] + box[1] - ry) / sy]
    return {'status': 'performed', 'root_inset_points': 12, 'inset_screenshot_pixels': box,
            'alpha_extrema': [255, 255], 'measured_scale': [sx, sy], 'measured_root_origin_pixels': [rx, ry],
            'embedded_icc_sha256': mid['icc_sha256'], 'normalized_nonwhite_bbox_root_points': root_bounds,
            'interpretation': 'Nonwhite pixels within fixed opaque inset; white cells can be omitted. Not exact flight bounds, fitted registration or cause.'}

def component(operation):
    try:
        return operation()
    except (AssertionError, KeyError, OSError, ValueError, TypeError, IndexError) as error:
        return {'status': 'not_performed', 'reason': str(error)}

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--new-root', type=Path, required=True)
    parser.add_argument('--old-root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    assert not args.output.exists(), 'Refuse to overwrite derived results'
    inputs, hosts = {}, {}
    for major in (13, 14):
        new = load_runtime(args.new_root / f'runtime{major}', ['before', 'in-flight', 'settled'], inputs)
        old = load_runtime(args.old_root / f'runtime{major}', ['before', 'settled'], inputs)
        hosts[str(major)] = {
            'new_runtime_issues': {'report': new.get('error'), 'captures': new.get('errors', [])},
            'old_runtime_issues': {'report': old.get('error'), 'captures': old.get('errors', [])},
            'new_before_to_settled': component(lambda: compare(new, 'before', 'source', new, 'settled', 'destination')),
            'old_to_new_before_control': component(lambda: compare(old, 'before', 'source', new, 'before', 'source')),
            'old_to_new_settled_control': component(lambda: compare(old, 'settled', 'destination', new, 'settled', 'destination')),
            'new_execution_model': component(lambda: execution_model(new)),
            'new_execution_model_reported': new.get('report', {}).get('execution_model'),
            'new_native_gates_reported': new.get('report', {}).get('native_gates'),
            'new_midflight_timing': component(lambda: timing(new)),
            'new_midflight_fixed_inset_bounds': component(lambda: mid_bounds(new))}
    result = {'scope': 'Original PNG/report hashes, new AppKit execution metadata, intent0-perceptual ICC-to-sRGB opaque same-size endpoint comparisons and fixed12pt opaque root-inset mid bounds only. No derived images, registration, resampling, synchronized/cross-host mid equality or cause attribution.',
              'script_sha256': digest(Path(__file__).read_bytes()), 'inputs': inputs, 'hosts': hosts,
              'input_roots': {'new': str(args.new_root.resolve()), 'old': str(args.old_root.resolve())}}
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
    for major, host in hosts.items():
        print(json.dumps({'os': major, 'endpoint': host['new_before_to_settled'],
            'before_control': host['old_to_new_before_control'], 'settled_control': host['old_to_new_settled_control'],
            'mid_bounds': host['new_midflight_fixed_inset_bounds'], 'timing_status': host['new_midflight_timing']['status'],
            'execution_model_status': host['new_execution_model']['status']}))

if __name__ == '__main__':
    main()
