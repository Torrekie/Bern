#!/usr/bin/env python3
"""Fixed-source, fixed-ROI offline diagnostic; no App/helper or native UI calls."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import struct
import platform
from PIL import Image, ImageCms, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = json.loads((HERE / 'spec.json').read_text())
ROI = spec['fixed_frame_roi_half_open_points']
NORMAL = {'increase_contrast': False, 'reduce_motion': False, 'reduce_transparency': False}
SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
TARGETS = ['frame.volume', 'frame.clip']


def sha(data):
    return hashlib.sha256(data).hexdigest()


def required(condition, message):
    if not condition:
        raise ValueError(message)


def relative(frame, canvas):
    return {'x': frame['x']-canvas['x'], 'y': frame['y']-canvas['y'],
            'width': frame['width'], 'height': frame['height']}


def statistics(a, b, channels):
    required(len(a) == len(b), 'Same comparison byte length required')
    sums = [0] * channels
    maxima = [0] * channels
    changed = [0] * channels
    any_changed = 0
    count = len(a) // channels
    for offset in range(0, len(a), channels):
        differences = [abs(a[offset+c]-b[offset+c]) for c in range(channels)]
        any_changed += any(differences)
        for c, value in enumerate(differences):
            sums[c] += value
            maxima[c] = max(maxima[c], value)
            changed[c] += value != 0
    return {'pixels': count, 'changed_pixels': any_changed,
            'changed_fraction': any_changed/count if count else None,
            'channel_mean_abs_0_255': [value/count for value in sums] if count else None,
            'channel_max_abs_0_255': maxima if count else None,
            'channel_changed_pixel_counts': changed,
            'exact_equal': a == b}


result = {'schema': 1, 'kind': spec['kind'], 'pixel_gate_pass': False,
          'scope': 'Original uninstrumented controls only; not cross-OS equivalence or layout acceptance',
          'software': {'python': platform.python_version(), 'pillow': pillow_version,
                       'littlecms': ImageCms.core.littlecms_version},
          'spec_sha256': sha((HERE/'spec.json').read_bytes()), 'inputs': {},
          'fixed_frame_roi_half_open_points': ROI}
loaded = {}
for name, source in spec['sources'].items():
    report_path = ROOT/source['report']
    raw_report = report_path.read_bytes()
    required(sha(raw_report) == source['report_sha256'], 'Report digest differs: '+name)
    report = json.loads(raw_report)
    required(report['success'] is True and report['source_sha'] == SOURCE, 'Original capture failed/wrong source')
    required(report['closed_only'] is True and report['row_ledger_enabled'] is False, 'Only uninstrumented closed control allowed')
    required(report['expected_os'] == int(name) and report['system_preferences'] == NORMAL, 'Wrong OS/profile')
    required(report['app_still_running_after_cleanup'] is False and report['app_termination_status'] == 0, 'Cleanup report failed')
    required(len(report['captures']) == 1, 'One closed capture required')
    capture = report['captures'][0]
    required(capture['png'] == 'frame-closed-light.png' and capture['stable_equal_comparisons'] >= 4, 'Wrong capture')
    canvas = capture['canvas_screen_top_left_points']
    required(canvas['width'] == 920 and canvas['height'] == 668, 'Wrong point canvas')
    scale = source['pixels_per_point']
    required(capture['pixels_per_point'] == [scale, scale], 'Wrong scale')
    png_path = report_path.parent/capture['png']
    png = png_path.read_bytes()
    required(sha(png) == source['png_sha256'] == capture['png_sha256'], 'PNG digest differs')
    required(png[:8] == b'\x89PNG\r\n\x1a\n' and png[12:16] == b'IHDR', 'Expected PNG IHDR')
    ihdr = struct.unpack('>IIBBBBB', png[16:29])
    required(ihdr[:4] == (920*scale, 668*scale, 8, 6), 'Expected original RGBA8 image')
    image = Image.open(png_path)
    image.load()
    required(image.mode == 'RGBA' and image.size == (920*scale, 668*scale), 'Unexpected native pixels')
    icc = image.info.get('icc_profile')
    required(icc and sha(icc) == source['icc_sha256'] == capture['icc_sha256'], 'Embedded ICC digest differs')
    profile = ImageCms.ImageCmsProfile(BytesIO(icc))
    native_roi = [value*scale for value in ROI]
    crop = image.crop(tuple(native_roi))
    alpha_hist = crop.getchannel('A').histogram()
    geometry_stages = [stage for stage in report['stages'] if 'native_geometry' in stage]
    stage_geometry = {}
    for stage in geometry_stages:
        for target in TARGETS:
            rows = [row for row in stage['native_geometry'] if row['target'] == target]
            required(len(rows) == 1, 'Missing/ambiguous native target')
            row = rows[0]
            required(relative(row['screen_top_left_points'], canvas) == row['relative_to_main_outer_points'], 'Screen/relative geometry differs')
            stage_geometry.setdefault(target, []).append(row['relative_to_main_outer_points'])
    final = [stage for stage in geometry_stages if stage['stage'] == 'closed-end']
    required(len(final) == 1, 'Missing unique closed-end')
    selected = {row['target']: row for row in final[0]['native_geometry']}
    traces = report['ax_selector_trace']
    trace_summary = []
    parents = []
    for trace in traces:
        required(trace['method'] == 'scoped_frame_label' and trace['requested_cli_target'] in TARGETS, 'Unexpected selector provenance')
        scope = trace['scope']
        required(scope['relationship'] == 'Clip and Volume share one content AXGroup' and scope['cli_labels'] == ['Clip', 'Volume'], 'Wrong Frame target relationship')
        required(scope['main_window_id'] == capture['window_ids'][0], 'Wrong main window binding')
        required(scope['clip']['description'] == 'Clip' and scope['clip']['role'] == 'AXUnknown', 'Wrong clip identity')
        required(scope['volume']['description'] == 'Volume' and scope['volume']['role'] == 'AXButton' and 'AXPress' in scope['volume']['actions'], 'Wrong volume identity')
        main = scope['main_window']['frame_screen_top_left_points']
        required(main == canvas, 'AX/CG main canvas mismatch')
        parent_relative = relative(scope['parent']['frame_screen_top_left_points'], main)
        parents.append(parent_relative)
        trace_summary.append({'requested_cli_target': trace['requested_cli_target'], 'method': trace['method'],
                              'actual_identifier': trace['native']['identifier'], 'parent_relative_points': parent_relative})
    required(parents and all(parent == parents[0] for parent in parents), 'Changing parent context')
    required(parents[0] == {'x': ROI[0], 'y': ROI[1], 'width': ROI[2]-ROI[0], 'height': ROI[3]-ROI[1]}, 'Historical ROI/parent context mismatch; do not fit ROI')
    profile_facts = {'bytes': len(icc), 'sha256': sha(icc),
                     'description': ImageCms.getProfileDescription(profile).strip(),
                     'color_space': profile.profile.xcolor_space.strip(),
                     'connection_space': profile.profile.connection_space.strip(),
                     'device_class': profile.profile.device_class.strip(), 'version': profile.profile.version,
                     'input_intent0_supported': ImageCms.isIntentSupported(profile, ImageCms.Intent.PERCEPTUAL, ImageCms.Direction.INPUT) == 1}
    result['inputs'][name] = {'report_path': str(report_path.relative_to(ROOT)), 'report_sha256': sha(raw_report),
                             'png_path': str(png_path.relative_to(ROOT)), 'png_bytes': len(png), 'png_sha256': sha(png),
                             'native_size_pixels': list(image.size), 'mode': image.mode, 'ihdr': list(ihdr),
                             'canvas_screen_top_left_points': canvas, 'pixels_per_point': scale,
                             'embedded_icc': profile_facts, 'raw_roi_half_open_pixels': native_roi,
                             'raw_roi_size_pixels': list(crop.size), 'raw_roi_rgba_sha256': sha(crop.tobytes()),
                             'raw_roi_alpha': {'min': crop.getchannel('A').getextrema()[0], 'max': crop.getchannel('A').getextrema()[1],
                                               'opaque_pixels': alpha_hist[255], 'nonopaque_pixels': sum(alpha_hist[:255]),
                                               'fully_transparent_pixels': alpha_hist[0]},
                             'closed_end_geometry': selected, 'native_geometry_stage_count': len(geometry_stages),
                             'geometry_constant_over_collected_stages': {target: all(row == rows[0] for row in rows) for target, rows in stage_geometry.items()},
                             'selector_trace_count': len(traces), 'selector_summary': trace_summary,
                             'scope_parent_relative_points': parents[0],
                             'context': report['final_context'], 'os': report['os'], 'display': report['displays'],
                             'capture_stable_equal_comparisons': capture['stable_equal_comparisons'],
                             'private_or_original_gui_sha256': report['app_executable_sha256'], 'cli_sha256': report['cli_sha256']}
    loaded[name] = {'crop': crop, 'profile': profile, 'facts': profile_facts}

native = {}
for target in TARGETS:
    a = result['inputs']['13']['closed_end_geometry'][target]
    b = result['inputs']['14']['closed_end_geometry'][target]
    ar, br = a['relative_to_main_outer_points'], b['relative_to_main_outer_points']
    native[target] = {'13_relative_points': ar, '14_relative_points': br,
                      'delta_13_minus14_points': {key: ar[key]-br[key] for key in ['x','y','width','height']},
                      'equal_relative_rect': ar == br,
                      'center_delta_13_minus14_points': {'x': ar['x']+ar['width']/2-br['x']-br['width']/2,
                                                       'y': ar['y']+ar['height']/2-br['y']-br['height']/2},
                      '13_role': a['role'], '14_role': b['role'],
                      '13_actual_ax_identifier': a['actual_ax_identifier'], '14_actual_ax_identifier': b['actual_ax_identifier'],
                      'identity_scope': 'Scoped CLI label/role/action/shared AXGroup relation; inherited identifier is not a direct target match; not a Cocoa class or Layout width.'}
result['native_geometry'] = native
result['raw_comparison'] = {'profiles_equal': spec['sources']['13']['icc_sha256'] == spec['sources']['14']['icc_sha256'],
                            'scales_equal': False, 'raw_cross_scale_exact_test_performed': False,
                            'reason': 'Different native scale and embedded display profiles; raw hashes are receipts only.'}

try:
    for name, value in loaded.items():
        required(value['facts']['color_space'] == 'RGB' and value['facts']['input_intent0_supported'], 'Unsupported source RGB ICC; stop processing')
    target = ImageCms.ImageCmsProfile(ImageCms.createProfile('sRGB'))
    target_bytes = target.tobytes()
    required(ImageCms.isIntentSupported(target, ImageCms.Intent.PERCEPTUAL, ImageCms.Direction.OUTPUT) == 1, 'Unsupported sRGB output profile')
    processed = {}
    processed_facts = {}
    for name, value in loaded.items():
        crop = value['crop']
        normalized = ImageCms.profileToProfile(crop.convert('RGB'), value['profile'], target,
                                               renderingIntent=ImageCms.Intent.PERCEPTUAL,
                                               outputMode='RGB', inPlace=False, flags=ImageCms.Flags.NONE)
        required(normalized is not None and normalized.mode == 'RGB' and normalized.size == crop.size, 'Unexpected ICC transform result')
        normalized.putalpha(crop.getchannel('A'))
        required(normalized.getchannel('A').tobytes() == crop.getchannel('A').tobytes(), 'Alpha changed during ICC normalization')
        if name == '13':
            normalized = normalized.resize((ROI[2]-ROI[0], ROI[3]-ROI[1]), Image.Resampling.BOX)
        required(normalized.size == (709,616) and normalized.mode == 'RGBA', 'Unexpected normalized ROI shape')
        processed[name] = normalized.tobytes()
        hist = normalized.getchannel('A').histogram()
        processed_facts[name] = {'rgba8_srgb_1pixel_per_point_sha256': sha(processed[name]), 'size_pixels': list(normalized.size),
                                 'alpha': {'opaque_pixels': hist[255], 'nonopaque_pixels': sum(hist[:255]), 'fully_transparent_pixels': hist[0]},
                                 'scale_operation': 'fixed exact 2x2 RGBA BOX at window integer phase' if name == '13' else 'unchanged1x'}
    a, b = processed['13'], processed['14']
    rgba_stats = statistics(a, b, 4)
    opaque_a, opaque_b = bytearray(), bytearray()
    for offset in range(0, len(a), 4):
        if a[offset+3] == b[offset+3] == 255:
            opaque_a.extend(a[offset:offset+3]); opaque_b.extend(b[offset:offset+3])
    result['processed_diagnostic'] = {'status': 'completed_diagnostic_only',
                                    'source_profiles_differ': True, 'target_profile_description': ImageCms.getProfileDescription(target).strip(),
                                    'target_profile_sha256': sha(target_bytes), 'target_profile_bytes': len(target_bytes),
                                    'icc_intent': 0, 'icc_flags': 0, 'black_point_compensation': False,
                                    'pipeline': spec['raster_policy'], 'scale_pipeline': spec['scale_policy'],
                                    'full_fixed_roi': rgba_stats, 'channel_order': ['R','G','B','A'],
                                    'both_alpha255_rgb_only': statistics(opaque_a, opaque_b, 3), 'opaque_channel_order': ['R','G','B'],
                                    'normalized_sources': processed_facts,
                                    'limitations': ['Perceptual ICC conversion and encoded-sRGB8 premultiplied BOX are stated appearance diagnostics, not linear-light or physical luminance error.',
                                                    'Nonopaque pixels remain in full ROI RGBA metrics; only the separately stated both-alpha255 RGB metric has direct opaque-color meaning.',
                                                    'No acceptance threshold, adaptive ROI, fitting, extra region matrix, output image or PixelGate PASS.']}
    (HERE/'target-sRGB.icc').write_bytes(target_bytes)
except Exception as error:
    result['processed_diagnostic'] = {'status': 'stopped_without_raster_comparison', 'error': type(error).__name__+': '+str(error),
                                    'scope': 'Raw/native facts retained. No new profile assumptions or package installation.'}

result['limits'] = ['The two original controls are uninstrumented and the collector provides no Caption/Size Layout child widths.',
                    'These facts do not identify a UI root cause, Cocoa view class or row allocation.',
                    'Private CFID/signature, OS, display/profile/scale, CI/local and cleanup differences remain recorded context.',
                    'No row ledger read or interpreted. Prior failed cohorts and gates remain unchanged.']
(HERE/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
print(json.dumps({'native_geometry': native, 'processed_diagnostic': result['processed_diagnostic']},ensure_ascii=False,indent=2))
