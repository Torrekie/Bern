"""Read-only inputs: actual three-scenario raw AX/CLI reports and PNG metadata."""
from pathlib import Path
import hashlib
import json
from PIL import Image

HERE = Path(__file__).resolve().parent
INPUTS = {
    'clean13': HERE/'runtime',
    'upstream14': HERE.parent/'macOS14-film-timing',
    'f9_port14': HERE/'comparison-inputs/f9-port14-40062837456',
}
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()

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

runs = {key:read(directory) for key,directory in INPUTS.items()}
comparison = []
for scenario, case in runs['clean13']['cases'].items():
    item = dict(scenario=scenario,clean_center=case['center_x'],clean_identity=case['largest'],references={})
    for reference in ['upstream14','f9_port14']:
        other = runs[reference]['cases'][scenario]
        delta = {key:[a-b for a,b in zip(rect,other['images'][key])] for key,rect in case['images'].items()}
        item['references'][reference] = dict(identity=other['largest'],center_x=other['center_x'],
            center_delta=case['center_x']-other['center_x'],frame_deltas=delta,
            max_abs_frame_component_delta=max(abs(v) for values in delta.values() for v in values))
    comparison.append(item)
result = dict(conclusion='Clean e48 runs successfully in all three fresh inactive 13 processes and shows Glen in each. Wait/direct match all six measured AX image frames of both 14 references within 0.00001 pt. Immediate differs by 35 pt from upstream14 and 36 pt from f9-port14; it is not a three-scenario visual parity pass.',
    runs=runs,comparison=comparison,
    limits=[
        'All three sequences were sampled once. Clean13 is inactive 2x with a unique local bundle/ad-hoc signature; references are active 14/1x with original bundle identities.',
        'Immediate in every run first resizes 900x652 to 920x668, while wait/direct restore 920x668 before the resize request. Inspector exit timing and startup/window history remain coupled.',
        'AX image frames and actual stable PNG are observed. No native Binding setter trace, active 13 color/material proof, physical gesture or endpoint/resize followup is supplied by this clean run.',
        'First Last and wide-window differences remain open in separate d146/f9 followup evidence. This source is clean e48 with existing 9dd Runtime, not the diagnostic744/d146 executable.'
    ])
# Added analysis only; raw reports, command outputs and PNG bytes are never rewritten.
(HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(comparison,indent=2))
