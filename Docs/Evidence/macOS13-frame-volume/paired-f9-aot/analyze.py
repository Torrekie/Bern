"""Offline C13/A14/B14 Frame measurements. Never starts an app or changes a PNG."""
import argparse
from collections import Counter
import hashlib
from io import BytesIO
import json
from pathlib import Path
import numpy as np
import PIL
from PIL import Image, ImageCms

ROOT = Path(__file__).resolve().parent
parser = argparse.ArgumentParser()
parser.add_argument('--reference', type=Path, default=ROOT.parents[1] / 'macOS14-frame-volume/paired-40065164350')
REFERENCE = parser.parse_args().reference.resolve()
NAMES = ['frame-closed-light', 'frame-open-light', 'volume-popover-light']
SIDES = {'A14': REFERENCE / 'a', 'B14': REFERENCE / 'b', 'C13': ROOT / 'run-aot'}
STABLE = [n + '-stable' for n in NAMES] + ['dismissed']
sha = lambda b: hashlib.sha256(b).hexdigest()


def load(path, scale):
    im = Image.open(path)
    icc = im.info['icc_profile']
    rgb = np.asarray(ImageCms.profileToProfile(im.convert('RGB'),
        ImageCms.ImageCmsProfile(BytesIO(icc)), ImageCms.createProfile('sRGB'),
        renderingIntent=1, outputMode='RGB')).astype(np.float64)
    raw = np.asarray(im.convert('RGBA'))
    alpha = raw[:, :, 3].astype(np.float64)
    point = lambda a: a.reshape(a.shape[0] // scale, scale, a.shape[1] // scale, scale, *a.shape[2:]).mean((1, 3))
    return {'native_rgb': rgb, 'native_rgba': raw, 'rgb': point(rgb), 'alpha': point(alpha),
            'icc_sha256': sha(icc), 'icc_bytes': len(icc), 'png_sha256': sha(path.read_bytes()),
            'pixels': list(im.size), 'scale': scale}


def metric(a, b, mask=None):
    assert a.shape == b.shape
    d = abs(a - b)
    values = d if mask is None else d[mask]
    assert values.size
    return {'mean_absolute_rgb_error_255': float(values.mean()), 'maximum_channel_error_255': float(values.max()),
            'fraction_pixels_over_channel_error': {str(t): float((values.max(-1) > t).mean()) for t in [0, 1, 2, 5, 10]}}


def roi(image, r, scale=1):
    x0, y0, x1, y1 = [round(x * scale) for x in r]
    return image[y0:y1, x0:x1]


def bbox(mask, rectangle, scale):
    y, x = np.nonzero(mask)
    return [float(x.min() / scale + rectangle[0]), float(y.min() / scale + rectangle[1]),
            float((x.max() + 1) / scale + rectangle[0]), float((y.max() + 1) / scale + rectangle[1])] if len(x) else None


reports = {k: json.loads((p / 'report.json').read_text()) for k, p in SIDES.items()}
images = {side: {n: load(p / (n + '.png'), 2 if side == 'C13' else 1) for n in NAMES} for side, p in SIDES.items()}
result = {'scope': 'One active local macOS13 f9 Frame run vs the existing active A/B14 run; light/normal only.',
    'method': 'Each original ICC -> sRGB, relative colorimetric, via LittleCMS; only then exact2x2 arithmetic area average C13 to logical1x points. No translation, fitted color correction or layout compensation.',
    'software': {'pillow': PIL.__version__, 'littlecms': ImageCms.core.littlecms_version, 'numpy': np.__version__},
    'reference': 'macOS14-frame-volume/paired-40065164350', 'captures': {}, 'runtime': {}, 'geometry': {}, 'ink_and_bezel': {}, 'color_samples': {}}

for side, report in reports.items():
    assert report['success'] is True
    assert all(report[k] for k in ['accessibility_trusted', 'screen_recording', 'post_event_access'])
    assert not any(report['system_preferences'].values())
    for check in report['window_array_checks']:
        assert check['exact_ids_and_owner'] is True
        assert sorted(check['requested_ids']) == sorted(d['kCGWindowNumber'] for d in check['descriptions'])
        assert all(d['kCGWindowOwnerPID'] == check['own_pid'] for d in check['descriptions'])
    assert all(e['sent'] and e['window_id'] == e['nsevent_window_number'] == e['roundtrip_nsevent_window_number'] for e in report['heartbeat_events'])
    caps = {c['png']: c for c in report['captures']}
    assert [len(caps[n + '.png']['window_ids']) for n in NAMES] == [1, 2, 1]
    assert set(caps[NAMES[1] + '.png']['window_ids']) == set(caps[NAMES[0] + '.png']['window_ids'] + caps[NAMES[2] + '.png']['window_ids'])
    for n in NAMES:
        c, im = caps[n + '.png'], images[side][n]
        assert c['png_sha256'] == im['png_sha256'] and c['icc_sha256'] == im['icc_sha256']
        assert c['stable_equal_comparisons'] >= 4 and c['samples'] >= 5
        assert c['pixels_per_point'] == [im['scale'], im['scale']]
    ready = next(s['media'] for s in report['stages'] if s['stage'] == 'video-ready')
    assert ready['phase'] == 'Ready' and ready['source_bound'] and ready['owner'] == 'main#1'
    stable = [s for s in report['stages'] if s['stage'] in STABLE]
    assert len(stable) == 4
    assert all(s['media']['phase'] == 'Paused' and s['media']['position_ms'] == 0 and s['media']['source_version'] == 1
               and s['media']['error'] is None and s['media']['source_bound'] and s['media']['owner'] == 'main#1' for s in stable)
    end = stable[-1]
    assert end['stage'] == 'dismissed' and not any(c['target'].endswith('.volume_level') for c in end['controls'])
    assert next(c for c in end['controls'] if c['target'] == 'frame.volume')['value'] == 'closed'
    popup_ids = caps['volume-popover-light.png']['window_ids']
    assert not any(w['kCGWindowNumber'] in popup_ids for w in end['own_windows'])
    popup, main = [caps[n + '.png']['canvas_screen_top_left_points'] for n in ['volume-popover-light', 'frame-open-light']]
    scale = images[side]['volume-popover-light']['scale']
    x, y, w, h = [round(v * scale) for v in [popup['x'] - main['x'], popup['y'] - main['y'], popup['width'], popup['height']]]
    panel = images[side]['volume-popover-light']['native_rgba']
    crop = images[side]['frame-open-light']['native_rgba'][y:y + h, x:x + w]
    opaque = panel[:, :, 3] == 255
    mismatch = int(np.any(crop[:, :, :3] != panel[:, :, :3], -1)[opaque].sum())
    assert opaque.any() and mismatch == 0
    awake = [s['elapsed'] for s in report['stages'] if s['stage'] == 'awake-check']
    result['runtime'][side] = {'success': True, 'elapsed_seconds': report['elapsed_seconds'],
        'source_sha': report['source_sha'], 'bundled_clip_sha256': report['bundled_tides_sha256'],
        'heartbeat_events': len(report['heartbeat_events']), 'raw_window_id_roundtrips': len(report['window_array_checks']),
        'awake_source_gate_minimum_seconds': 3.2, 'awake_gate_reached_and_passed': True, 'awake_stage_elapsed_seconds': awake,
        'awake_note': 'Stage first/last timestamps alone are not the loop duration; success follows the unchanged bounded3.2second loop.',
        'ready_then_paused_zero': True, 'popup_visually_dismissed': True, 'stable_buffer_comparisons_each': [caps[n + '.png']['stable_equal_comparisons'] for n in NAMES],
        'composite_popup_fully_opaque_native_pixels': int(opaque.sum()), 'composite_popup_opaque_mismatched_pixels': mismatch,
        'main_outer_points': caps[NAMES[0] + '.png']['canvas_screen_top_left_points'],
        'popup_relative_points': {'x': popup['x'] - main['x'], 'y': popup['y'] - main['y'], 'width': popup['width'], 'height': popup['height']},
        'frontmost_before': report.get('frontmost_before'), 'frontmost_after': report.get('frontmost_after'),
        'capture_frontmost_own_app_enforced_by_source': True, 'capture_time_ax_focused_or_first_responder_collected': False}

assert len({r['bundled_tides_sha256'] for r in reports.values()}) == 1
for name in NAMES:
    local = images['C13'][name]
    entry = {'source_images': {side: {k: im[name][k] for k in ['pixels', 'scale', 'icc_sha256', 'icc_bytes', 'png_sha256']} for side, im in images.items()}, 'comparisons': {}}
    rois = {'frame_detail': [211, 52, 920, 668], 'video': [251, 167, 880, 521],
            'video_interior': [280, 190, 850, 495], 'controls_row': [245, 526, 885, 557]}
    for side in ['A14', 'B14']:
        ref = images[side][name]
        pair = {'whole_icc_srgb_area': metric(ref['rgb'], local['rgb'])}
        if name != 'volume-popover-light':
            pair['rois_points'] = rois
            pair['roi_metrics'] = {k: metric(roi(ref['rgb'], r), roi(local['rgb'], r)) for k, r in rois.items()}
        else:
            opaque = (ref['alpha'] == 255) & (local['alpha'] == 255)
            pair['common_fully_opaque_pixels'] = int(opaque.sum())
            pair['fully_opaque_rgb'] = metric(ref['rgb'], local['rgb'], opaque)
            pair['alpha_mean_absolute_error_255'] = float(abs(ref['alpha'] - local['alpha']).mean())
            pair['alpha_bbox_points'] = {s: {str(t): bbox(images[s][name]['alpha'] > t, [0, 0, 266, 106], 1) for t in [0, 127, 254]} for s in [side, 'C13']}
        entry['comparisons'][side + '_C13'] = pair
    result['captures'][name] = entry

for stage in STABLE:
    entries = {side: next(s for s in report['stages'] if s['stage'] == stage) for side, report in reports.items()}
    targets = [g['target'] for g in entries['C13']['native_geometry']]
    result['geometry'][stage] = {}
    for target in targets:
        frames = {side: next(g for g in e['native_geometry'] if g['target'] == target) for side, e in entries.items()}
        a, c = [frames[s]['relative_to_main_outer_points'] for s in ['A14', 'C13']]
        result['geometry'][stage][target] = {'frames': frames,
            'C13_minus_A14_xywh': {k: c[k] - a[k] for k in ['x', 'y', 'width', 'height']},
            'C13_minus_A14_center': [c['x'] + c['width'] / 2 - a['x'] - a['width'] / 2, c['y'] + c['height'] / 2 - a['y'] - a['height'] / 2]}

for side in SIDES:
    scale = images[side][NAMES[0]]['scale']
    main, popup = images[side][NAMES[0]]['native_rgb'], images[side][NAMES[2]]['native_rgb']
    masks = {}
    for label, r in {'caption_bezel': [245, 526, 362, 557], 'size_bezel': [363, 526, 615, 557],
                     'volume_bezel_and_glyph': [612, 526, 649, 557], 'rest_text': [650, 526, 885, 557]}.items():
        region = roi(main, r, scale)
        masks[label] = {'roi_points': r, 'mean_rgb_gt_threshold_bbox': {str(t): bbox(region.mean(-1) > t, r, scale) for t in [65, 95, 130, 160, 200, 225]}}
    for label, r in {'popup_title': [23, 27, 105, 51], 'popup_label': [23, 54, 80, 80]}.items():
        region = roi(popup, r, scale)
        masks[label] = {'roi_points': r, 'mean_rgb_gt_threshold_bbox': {str(t): bbox(region.mean(-1) > t, r, scale) for t in [150, 180, 210, 230]}}
    r = [76, 54, 242, 82]
    region = roi(popup, r, scale)
    masks['popup_slider_visible'] = {'roi_points': r,
        'red_track_predicate': 'R>G+40 and R>B+10',
        'red_track_bbox': bbox((region[:, :, 0] > region[:, :, 1] + 40) & (region[:, :, 0] > region[:, :, 2] + 10), r, scale),
        'neutral_knob_predicate': '125<meanRGB<180 and maxRGB-minRGB<5',
        'neutral_knob_bbox': bbox((region.mean(-1) > 125) & (region.mean(-1) < 180) & (np.ptp(region, axis=2) < 5), r, scale),
        'knob_center_sample_roi_points': [186, 66, 188, 68],
        'knob_center_mean_srgb': roi(popup, [186, 66, 188, 68], scale).mean((0, 1)).tolist()}
    for label, r in {'caption_text': [277, 535, 331, 551], 'size_text': [397, 534, 432, 552], 'size_AA_glyph': [375, 534, 397, 552]}.items():
        region = roi(main, r, scale)
        background = np.array(Counter(map(tuple, region.reshape(-1, 3))).most_common(1)[0][0])
        masks[label] = {'roi_points': r, 'modal_background_rgb': background.tolist(),
            'rgb_distance_from_modal_background_gt_threshold_bbox': {str(t): bbox(np.linalg.norm(region - background, axis=2) > t, r, scale) for t in [20, 40, 60, 80]}}
    result['ink_and_bezel'][side] = masks
    samples = {'canvas': (main, [220, 150, 240, 250]), 'popup_flat': (popup, [105, 25, 155, 45]),
        'video_gray102': (main, [275, 200, 320, 300]), 'video_gray191': (main, [345, 200, 380, 300]),
        'video_yellow': (main, [420, 200, 450, 300]), 'video_cyan': (main, [490, 200, 515, 300]),
        'video_green': (main, [555, 200, 580, 300]), 'video_magenta': (main, [620, 200, 650, 300]),
        'video_red': (main, [690, 200, 715, 300]), 'video_blue': (main, [755, 200, 785, 300])}
    result['color_samples'][side] = {n: {'roi_points': r, 'mean_srgb': roi(im, r, scale).mean((0, 1)).tolist(),
        'std_srgb': roi(im, r, scale).std((0, 1)).tolist()} for n, (im, r) in samples.items()}

result['conclusion'] = {'clip_popup_slider_point_geometry_equal': True,
    'volume_visible_bezel_20_by_20_both_with_half_point_x_shift': True,
    'speaker_glyph_threshold_130_and_160_edges_within_one_point': True,
    'volume_ax_bounds_equal': False, 'caption_and_size_bezel_widths_equal': False,
    'native_size_label_edges_within_one_point': False, 'icc_converted_colors_equal': False,
    'whole_or_detail_pixels_equal': False, 'cause_of_color_differences_established': False,
    'physical_input_dark_hdr_playback_audio_acceptance': False}
(ROOT / 'analysis').mkdir(exist_ok=True)
(ROOT / 'analysis/comparison.json').write_text(json.dumps(result, indent=2, sort_keys=True) + '\n')
print(json.dumps({'captures': {n: e['comparisons']['A14_C13']['whole_icc_srgb_area'] for n, e in result['captures'].items()},
                  'runtime_C13': result['runtime']['C13'], 'conclusion': result['conclusion']}, indent=2))
