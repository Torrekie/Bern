#!/usr/bin/env python3
"""One fixed-original reference binding only; no candidate input or native execution."""
from pathlib import Path
from io import BytesIO
import hashlib
import json
import math
import statistics
import struct
from PIL import Image, ImageCms, __version__ as pillow_version

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
spec = json.loads((HERE/'spec.json').read_text())
OUT = HERE/'reference-binding.json'
if OUT.exists():
    raise RuntimeError('Reference binding already exists; do not overwrite or retune')


def sha(data):
    return hashlib.sha256(data).hexdigest()


def need(condition, message):
    if not condition:
        raise ValueError(message)


def xywh(rect):
    return [rect[key] for key in ['x','y','width','height']]


def normalized(crop, source_profile, target_profile):
    result = ImageCms.profileToProfile(crop.convert('RGB'), source_profile, target_profile,
                                      renderingIntent=ImageCms.Intent.PERCEPTUAL,
                                      outputMode='RGB', inPlace=False, flags=ImageCms.Flags.NONE)
    need(result is not None and result.mode == 'RGB' and result.size == crop.size, 'Unexpected RGB transform result')
    result.putalpha(crop.getchannel('A'))
    return result


def summary(values):
    need(bool(values), 'Empty frozen foreground; stop without retuning')
    return {'count':len(values), 'channel_mean':[sum(v[c] for v in values)/len(values) for c in range(3)],
            'channel_min':[min(v[c] for v in values) for c in range(3)],
            'channel_max':[max(v[c] for v in values) for c in range(3)]}


binding = {'schema':'split_label_color_reference_binding_v1',
           'spec_sha256':sha((HERE/'spec.json').read_bytes()),
           'kind':'fixed_original_references_only', 'candidate_images_read':False,
           'software':{'pillow':pillow_version,'littlecms':ImageCms.core.littlecms_version},
           'references':{}}
normalized_labels = {}
try:
    target_path = ROOT/spec['color_pipeline']['target_icc']
    target_bytes = target_path.read_bytes()
    need(sha(target_bytes) == spec['color_pipeline']['target_icc_sha256'], 'Frozen target ICC differs')
    target = ImageCms.ImageCmsProfile(BytesIO(target_bytes))
    binding['target_icc_sha256'] = sha(target_bytes)
    for host, source in spec['references'].items():
        report_path = ROOT/source['report']
        report_bytes = report_path.read_bytes()
        need(sha(report_bytes) == source['report_sha256'], 'Original report digest differs')
        report = json.loads(report_bytes)
        need(report['success'] is True and report['source_sha'] == spec['base_source_sha'], 'Wrong/failed original')
        need(report['closed_only'] is True and report['row_ledger_enabled'] is False, 'Original is not uninstrumented closed control')
        need(report['expected_os'] == int(host) and report['deadline_seconds'] == 75, 'Wrong host/deadline')
        need(report['system_preferences'] == {'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}, 'Wrong normal profile')
        need(report['app_still_running_after_cleanup'] is False and report['app_termination_status'] == 0, 'Original cleanup failed')
        need(len(report['captures']) == 1, 'Expected one original closed PNG')
        capture = report['captures'][0]
        need(capture['stable_equal_comparisons'] >= 4 and capture['samples'] >= 5, 'Original unstable')
        times = [capture[key] for key in ['capture_begin_uptime_seconds','sample_begin_uptime_seconds','sample_acquired_uptime_seconds']]
        need(all(math.isfinite(t) for t in times) and times[0] <= times[1] <= times[2], 'Invalid original sample times')
        context = report['final_context']
        need(context['appearance'] == 'Light' and context['caption'] is True and context['volume'] == 'closed' and context['video'] == 'Paused0', 'Wrong closed context')
        scale = source['scale']; canvas = capture['canvas_screen_top_left_points']
        need(canvas['width'] == 920 and canvas['height'] == 668 and capture['pixels_per_point'] == [scale,scale], 'Wrong original geometry/scale')
        stages = [stage for stage in report['stages'] if 'native_geometry' in stage]
        for stage in stages:
            for target_name, expected in source['native_geometry'].items():
                rows = [row for row in stage['native_geometry'] if row['target'] == target_name]
                need(len(rows) == 1 and xywh(rows[0]['relative_to_main_outer_points']) == expected, 'Native geometry differs from fixed reference')
                screen = rows[0]['screen_top_left_points']
                need([screen['x']-canvas['x'],screen['y']-canvas['y'],screen['width'],screen['height']] == expected, 'Native screen/relative mismatch')
        need(any(stage['stage'] == 'closed-end' for stage in stages), 'No closed-end original')
        traces = report['ax_selector_trace']
        need(bool(traces) and all(row['method'] == 'scoped_frame_label' and row['scope']['relationship'] == 'Clip and Volume share one content AXGroup' for row in traces), 'Wrong target relationship')
        png_path = report_path.parent/capture['png']; png_bytes = png_path.read_bytes()
        need(sha(png_bytes) == source['png_sha256'] == capture['png_sha256'], 'Original PNG digest differs')
        need(struct.unpack('>IIBBBBB',png_bytes[16:29])[:4] == (920*scale,668*scale,8,6), 'Unexpected RGBA8 PNG')
        image = Image.open(png_path); image.load()
        need(image.mode == 'RGBA' and image.size == (920*scale,668*scale), 'Unexpected image mode/size')
        icc_bytes = image.info.get('icc_profile')
        need(icc_bytes and sha(icc_bytes) == source['icc_sha256'] == capture['icc_sha256'], 'Embedded original ICC differs')
        source_profile = ImageCms.ImageCmsProfile(BytesIO(icc_bytes))
        need(source_profile.profile.xcolor_space.strip() == 'RGB' and ImageCms.isIntentSupported(source_profile,ImageCms.Intent.PERCEPTUAL,ImageCms.Direction.INPUT) == 1, 'Unsupported original ICC; stop')
        crops, crop_facts = {}, {}
        for name, roi in spec['regions_half_open_points'].items():
            pixel_roi = [value*scale for value in roi]
            crop = image.crop(tuple(pixel_roi)); crops[name] = crop
            crop_facts[name] = {'half_open_native_pixels':pixel_roi,'size_pixels':list(crop.size),'raw_rgba_sha256':sha(crop.tobytes())}
        label = normalized(crops['caption_label'],source_profile,target)
        background = normalized(crops['label_background_strip'],source_profile,target)
        need(label.height == background.height, 'Frozen background row mismatch')
        need(background.getchannel('A').getextrema() == (255,255), 'Background strip is not opaque; stop')
        label_bytes, background_bytes = label.tobytes(), background.tobytes()
        raw_label = crops['caption_label'].tobytes()
        mask_runs, colors, raw_colors, mask = [], [], [], bytearray(label.width*label.height)
        backgrounds = []
        for y in range(label.height):
            row_background = [statistics.median(background_bytes[(y*background.width+x)*4+c] for x in range(background.width)) for c in range(3)]
            backgrounds.append(row_background)
            run_start = None; runs = []
            for x in range(label.width):
                offset = (y*label.width+x)*4
                selected = label_bytes[offset+3] == 255 and max(abs(label_bytes[offset+c]-row_background[c]) for c in range(3)) >= spec['foreground_mask']['linf_threshold_0_255']
                if selected:
                    mask[y*label.width+x] = 1
                    colors.append(tuple(label_bytes[offset:offset+3])); raw_colors.append(tuple(raw_label[offset:offset+3]))
                    if run_start is None: run_start = x
                elif run_start is not None:
                    runs.append([run_start,x]); run_start = None
            if run_start is not None: runs.append([run_start,label.width])
            if runs: mask_runs.append({'y':y,'runs_half_open_x':runs})
        stats = summary(colors)
        full = normalized(crops['frame'],source_profile,target)
        if host == '13': full = full.resize((709,616),Image.Resampling.BOX)
        normalized_labels[host] = colors
        binding['references'][host] = {'report_path':str(report_path.relative_to(ROOT)),'report_sha256':sha(report_bytes),
             'png_path':str(png_path.relative_to(ROOT)),'png_sha256':sha(png_bytes),'icc_sha256':sha(icc_bytes),
             'source_profile_description':ImageCms.getProfileDescription(source_profile).strip(),
             'scale':scale,'native_geometry':source['native_geometry'],'geometry_stage_count':len(stages),
             'context':context,'sample_times':times,'crops':crop_facts,
             'label_normalized_native_rgba_sha256':sha(label_bytes),'background_row_median_srgb8':backgrounds,
             'foreground':{'selection':spec['foreground_mask'],'mask_size_native_pixels':list(label.size),
                           'mask_byte_encoding':'Row-major one byte0/1 per native label pixel; runs reconstruct exactly',
                           'mask_sha256':sha(mask),'mask_count':len(colors),'runs':mask_runs,
                           'raw_rgb':summary(raw_colors),'normalized_srgb8_rgb':stats},
             'full_frame_processed_1pixel_per_point_rgba_sha256':sha(full.tobytes())}
    target_mean = binding['references']['14']['foreground']['normalized_srgb8_rgb']['channel_mean']
    values = normalized_labels['13']
    binding['foreground_target14_rgb_mean'] = target_mean
    binding['original13_error_to_target14'] = {
        'per_channel_mean_absolute_error':[sum(abs(value[c]-target_mean[c]) for value in values)/len(values) for c in range(3)],
        'per_channel_max_absolute_error':[max(abs(value[c]-target_mean[c]) for value in values) for c in range(3)],
        'per_channel_signed_mean_bias':[sum(value[c]-target_mean[c] for value in values)/len(values) for c in range(3)]}
    binding['success'] = True
    binding['scope'] = 'One original-reference specification binding. No candidate paths, hashes, pixels, binary assumption or acceptance result.'
except Exception as error:
    binding['success'] = False
    binding['error'] = type(error).__name__+': '+str(error)
    binding['scope'] = 'Stop; preserve this binding failure. Do not retune thresholds/ROI or read candidate.'
OUT.write_text(json.dumps(binding,indent=2,ensure_ascii=False,sort_keys=True)+'\n')
print(json.dumps({'success':binding['success'], 'foreground_counts':{host:value['foreground']['mask_count'] for host,value in binding['references'].items()},
                  'foreground_target14_rgb_mean':binding.get('foreground_target14_rgb_mean'),
                  'original13_error_to_target14':binding.get('original13_error_to_target14'), 'error':binding.get('error')},indent=2))
raise SystemExit(0 if binding['success'] else 1)
