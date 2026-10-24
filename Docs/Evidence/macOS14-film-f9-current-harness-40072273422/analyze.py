"""Offline comparisons of preserved raw reports and PNG metadata only."""
from pathlib import Path
import hashlib
import json
from PIL import Image
HERE=Path(__file__).resolve().parent
INPUTS={
 'f9_current14':HERE/'runtime',
 'e48_current14':HERE.parent/'macOS14-film-clean-e48fff46-40071892408/runtime',
 'f9_old14':HERE.parent/'macOS13-film-clean-e48fff46/comparison-inputs/f9-port14-40062837456',
 'upstream_old14':HERE.parent/'macOS14-film-timing',
 'e48_clean13':HERE.parent/'macOS13-film-clean-e48fff46/runtime',
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
comparison=[]
for scenario,case in runs['f9_current14']['cases'].items():
    row=dict(scenario=scenario,control_identity=case['largest'],control_center=case['center_x'],references={})
    for name in ['e48_current14','f9_old14','upstream_old14','e48_clean13']:
        other=runs[name]['cases'][scenario]
        delta={key:[a-b for a,b in zip(rect,other['images'][key])] for key,rect in case['images'].items()}
        row['references'][name]=dict(identity=other['largest'],center_x=other['center_x'],
            control_minus_reference_center=case['center_x']-other['center_x'],frame_deltas=delta,
            max_abs_frame_component_delta=max(abs(v) for values in delta.values() for v in values),
            film_png_byte_identical=case['picture']['sha256']==other['picture']['sha256'])
    comparison.append(row)
result=dict(conclusion='With the current observer, old f9 reproduces all six AX image frames of its old-observer run in every scenario. Its immediate Glen remains 565 pt, versus e48/current-observer 677 pt. The startup gate alone does not reproduce the observed 677 result. This single-run control does not determine cause, prove a source regression, or establish native 14 parity.',
    runs=runs,comparison=comparison,
    limits=[
      'Current f9/e48 runs use identical observer source 79da4a84/harness 25e18cbc, active 14/1x, normal false flags and the same sequence. App sources/builds differ, and each condition has only one run.',
      'All immediate cases combine first process, actual 900x652→920x668 resizing and immediate Inspector closure. Wait/direct restore 920x668. Recorded outer history does not expose internal layout/target timing.',
      'Settled AX and stable PNG are observed; early AX walks are incomplete, with no native target/nearest/snap trace. No cause is assigned to the 112 pt current f9/e48 immediate difference.',
      'All compared PNG pairs differ in bytes. AX frame equality alone is not color/material parity. The 13 comparison is inactive 2x with a unique re-signed copy of the same e48 build code.',
      'No new application build, local UI, physical gesture or Last/resize followup occurred. Existing immediate/endpoint/wide boundaries remain open.'
    ])
(HERE/'analysis.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(comparison,indent=2))
