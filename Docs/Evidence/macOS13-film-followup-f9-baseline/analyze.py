"""Offline comparison of preserved raw AX geometry and WindowServer PNGs."""
from pathlib import Path
import hashlib
import json
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
EVIDENCE = HERE.parent
INPUTS = {
    'old13': HERE/'runtime',
    'candidate13': EVIDENCE/'macOS13-film-initial-candidate-d14655fb/runtime',
    'native14': EVIDENCE/'macOS14-film-followup-40067683100',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

def states(directory):
    report = json.loads((directory/'result.json').read_text())
    case = report['cases'][0]
    stages = [('initial', case['settled_ax'], case['film'], case['select_start_uptime'])]
    stages.extend((s['stage'], s['ax'], s['capture'], s['action_start_uptime'])
                  for s in case['followup_stages'])
    values = {}
    for name, ax, capture, start in stages:
        bounds = capture['bounds_points']
        images = []
        for element in ax['elements']:
            if element['role'] != 'AXImage':
                continue
            f = element['frame']
            images.append(dict(identity=element['text'], local_rect=[
                f['x']-bounds['X'], f['y']-bounds['Y'], f['width'], f['height']]))
        dominant = max(images, key=lambda item: item['local_rect'][2])
        x, y, width, height = dominant['local_rect']
        values[name] = dict(identity=dominant['identity'], local_rect=dominant['local_rect'],
            center_x=x+width/2, center_y=y+height/2, images=images,
            window_bounds=bounds, ax_complete=not ax['truncated'],
            ax_image_count=len(images), raw_equal_comparisons=capture['equal_comparisons'],
            png=capture['png'], png_sha256=sha(directory/capture['png']),
            action_seconds_since_film_select=start-case['select_start_uptime'])
    fronts = sorted({(s['front']['front_pid'], s['front'].get('front_bundle'))
                     for s in report.get('inactive_capture_samples', [])})
    return dict(source_sha=report['source_sha'], harness_sha=report['harness_sha'],
        os=report['os'], observation=report['observation_mode'],
        profile=report['system_preferences'], pid=case['pid'], success=report['success'],
        activation_requests=report['activation_requests'], sampled_fronts=fronts,
        sampled_inactive_count=len(report.get('inactive_capture_samples', [])),
        internal_trace=case.get('internal_trace'), stages=values)

def pixel_comparison(left, right):
    a, b = Image.open(left), Image.open(right)
    assert a.size == b.size
    x, y = np.asarray(a.convert('RGBA'), dtype=np.int16), np.asarray(b.convert('RGBA'), dtype=np.int16)
    difference = np.abs(x[:, :, :3]-y[:, :, :3])
    opaque = (x[:, :, 3] == 255) & (y[:, :, 3] == 255)
    return dict(size=list(a.size), byte_identical=sha(left)==sha(right),
        icc_identical=a.info.get('icc_profile')==b.info.get('icc_profile'),
        alpha_identical=bool(np.array_equal(x[:, :, 3], y[:, :, 3])),
        opaque_pixel_count=int(opaque.sum()), opaque_rgb_max=int(difference[opaque].max()),
        opaque_rgb_mean=float(difference[opaque].mean()),
        scope='Raw encoded RGB diagnostic only. Different fronts, state history, and geometry prevent a pixel-equivalence conclusion.')

runs = {name: states(directory) for name, directory in INPUTS.items()}
rows = []
for stage in runs['old13']['stages']:
    old, candidate, native = (runs[name]['stages'][stage] for name in INPUTS)
    rows.append(dict(stage=stage, identities=[old['identity'], candidate['identity'], native['identity']],
        center_x=[old['center_x'], candidate['center_x'], native['center_x']],
        candidate_minus_old_center=candidate['center_x']-old['center_x'],
        old_minus_native_center=old['center_x']-native['center_x'],
        candidate_minus_native_center=candidate['center_x']-native['center_x'],
        candidate_minus_old_rect=[c-o for c, o in zip(candidate['local_rect'], old['local_rect'])],
        png_candidate_vs_old=pixel_comparison(INPUTS['candidate13']/candidate['png'], INPUTS['old13']/old['png'])))
output = dict(conclusion='The candidate reproduces native14 initial Glen identity and measured geometry. The large wide-window difference already exists in old13. First/Last-again/restore/wide differ from old13 by about 0.186 pt; the first Last differs by 7.186 pt and remains a separate, unproven-history case. This is not full visual or endpoint parity.',
    runs=runs, comparison=rows,
    limits=[
        'Both 13 runs are inactive/2x; native 14 is active/1x. The 13 fronts differ: old13 Codex, candidate13 Simulator.',
        'Candidate includes a two-second one-shot trace flush and after-trace capture before Last; the uninstrumented f9 baseline has no such wait. No extra pause or synthetic trace was added.',
        'Each sequence was run once. AX identity/frame, raw-buffer stability, and actual PNG are observed; binding setters, physical gesture behavior, and causes of the endpoint differences are not.',
        'Initial target default 3 is unchanged. Candidate nearest/follow trace is diagnostic evidence, not coverage of every native binding setter.',
        'The clean semantic patch is a separate uncompiled proposal; the diagnostic candidate build/CI cannot be claimed to validate a logger-free whole app.'
    ])
(HERE/'analysis.json').write_text(json.dumps(output, indent=2)+'\n')
print(json.dumps(rows, indent=2))
