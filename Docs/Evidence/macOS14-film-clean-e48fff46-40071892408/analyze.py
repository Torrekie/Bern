"""Offline comparison. No application execution or raw-input mutation."""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE=Path(__file__).resolve().parent
INPUTS={
 'clean14':HERE/'runtime',
 'clean13':HERE.parent/'macOS13-film-clean-e48fff46/runtime',
 'upstream14':HERE.parent/'macOS14-film-timing',
 'f9_port14':HERE.parent/'macOS13-film-clean-e48fff46/comparison-inputs/f9-port14-40062837456',
}
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()

def read(directory):
    report = json.loads((directory/'result.json').read_text())
    cases = {}
    for case in report['cases']:
        capture = case['film']; bounds = capture['bounds_points']
        images = {}
        for e in case['settled_ax']['elements']:
            if e['role'] != 'AXImage':
                continue
            f = e['frame']
            images[e['text']] = [f['x']-bounds['X'], f['y']-bounds['Y'], f['width'], f['height']]
        largest = max(images, key=lambda key: images[key][2])
        changes = []
        for command in report['commands']:
            arguments = command['arguments']
            if case['session'] not in arguments or 'window' not in arguments:
                continue
            if 'list' not in arguments and 'resize' not in arguments:
                continue
            try:
                value = json.loads((directory/command['stdout']).read_text())
            except (ValueError, FileNotFoundError):
                continue
            if not value:
                continue
            changes.append(dict(kind='resize' if 'resize' in arguments else 'list',
                command_stdout=command['stdout'], value=value))
        resize_index = next(i for i, item in enumerate(changes) if item['kind']=='resize')
        before = changes[resize_index-1] if resize_index else None
        png = directory/capture['png']
        with Image.open(png) as image:
            icc = image.info.get('icc_profile')
            picture = dict(png=capture['png'],sha256=sha(png),pixels=list(image.size),
                icc_sha256=hashlib.sha256(icc).hexdigest() if icc else None,
                raw_equal_comparisons=capture['equal_comparisons'])
        first_second = []
        for sample in case['first_second_ax']:
            first_second.append(dict(start_after_select=sample['start_uptime']-case['select_start_uptime'],
                end_after_select=sample['end_uptime']-case['select_start_uptime'],truncated=sample['truncated'],
                elements=[e for e in sample['elements'] if e['role'] in ['AXSplitGroup','AXScrollArea']]))
        rect = images[largest]
        cases[case['scenario']] = dict(pid=case['pid'],session=case['session'],largest=largest,
            center_x=rect[0]+rect[2]/2,largest_rect=rect,images=images,
            ax_complete=not case['settled_ax']['truncated'],ax_image_count=len(images),
            final_window_bounds=bounds,pre_resize_list=before,resize_response=changes[resize_index],
            close_to_select_seconds=case['select_start_uptime']-case['close_return_uptime'] if 'close_return_uptime' in case else None,
            first_second_geometry=first_second,picture=picture)
    fronts = sorted({(s['front']['front_pid'],s['front'].get('front_bundle'))
                     for s in report.get('inactive_capture_samples',[])})
    return dict(source_sha=report['source_sha'],observer_harness_sha=report['harness_sha'],
        os=report['os'],normal_flags=report['system_preferences'],observation=report.get('observation_mode','active14 original observer'),
        activation_requests=report.get('activation_requests'),sampled_fronts=fronts,
        sampled_inactive_count=len(report.get('inactive_capture_samples',[])),cases=cases)


runs={name:read(directory) for name,directory in INPUTS.items()}
comparisons=[]
for scenario,case in runs['clean14']['cases'].items():
    row=dict(scenario=scenario,clean14_identity=case['largest'],clean14_center=case['center_x'],references={})
    for name in ['clean13','upstream14','f9_port14']:
        other=runs[name]['cases'][scenario]
        delta={key:[a-b for a,b in zip(rect,other['images'][key])] for key,rect in case['images'].items()}
        row['references'][name]=dict(identity=other['largest'],center_x=other['center_x'],
            center_delta=case['center_x']-other['center_x'],frame_deltas=delta,
            max_abs_frame_component_delta=max(abs(v) for values in delta.values() for v in values),
            film_png_byte_identical=case['picture']['sha256']==other['picture']['sha256'])
    comparisons.append(row)
result=dict(conclusion='The same exact clean e48 application succeeds on native 14. Wait/direct reproduce all six AX image frames of both old 14 references exactly and match inactive 13 within 0.00001 pt. Immediate is Glen 677, distinct from upstream 566, f9-port 565 and inactive 13 clean 601; runtime success is not full visual parity.',
    runs=runs,comparison=comparisons,
    limits=[
      'The current observer content is 3f434cf/79da4a84 and adds a startup-window readiness gate. Old upstream14/f9-port14 three-scenario observers predate that gate. Source and observer changes are not isolated in this comparison.',
      'Every dataset runs immediate first after an actual 900x652→920x668 resize; wait/direct restore 920x668 before a no-change resize. First-process/layout/window-restoration and Inspector exit remain coupled.',
      'Each sequence was sampled once. Settled AX and actual stable PNG are observed; no internal target/nearest/native-snap trace or complete early width transition is supplied.',
      'The 13 sample is inactive 2x/unique bundle signature while all 14 references are active 1x/original identity. Equal AX frames are not active color/material parity. All compared PNG pairs differ in bytes.',
      'No Last/resize followup or physical gesture was requested. Earlier open endpoint/resize boundaries remain.'
    ])
(HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(comparisons,indent=2))
