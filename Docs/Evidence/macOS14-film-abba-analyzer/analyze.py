"""Offline only. No app execution, network, image verdict or source-cause inference."""
import hashlib
import json
import math
from pathlib import Path, PurePosixPath
import sys

NAMES = ['Gingham', 'Tartan', 'Madras', 'Glen', 'Houndstooth', 'Windowpane']
ORDER = ['A1', 'B1', 'B2', 'A2']
SOURCES = {'A': 'f9e08b1d55bed4b9d880b19934abe48281057bb3',
           'B': 'e48fff46b3a92a28465ad74295bd273a9d69af7d'}
GUI = {'A': '887173af876a3f802c68dfff7fef087f318cc6909a61ea4beff69dad536dfd7e',
       'B': 'd44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c'}
ALLOWED = {'Contents/Info.plist', 'Contents/MacOS/Gallery', 'Contents/_CodeSignature/CodeResources'}


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def ledger(raw):
    entries = {}
    assert not any(p.is_symlink() for p in raw.rglob('*')), 'Unexpected symlink'
    for line in (raw/'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1); path = PurePosixPath(name)
        assert len(digest) == 64 and not path.is_absolute() and '..' not in path.parts
        assert name not in entries and sha(raw/name) == digest, name
        entries[name] = digest
    actual = {str(p.relative_to(raw)) for p in raw.rglob('*') if p.is_file() and p != raw/'SHA256SUMS'}
    assert actual == entries.keys(), 'Ledger has missing or unlisted files'
    return dict(verified_files=len(entries), ledger_sha256=sha(raw/'SHA256SUMS'), all_match=True)


def read(path):
    return json.loads(path.read_text())


def case_data(case, data):
    shot = case['film']; bounds = shot['bounds_points']; walk = case['settled_ax']
    images = [e for e in walk['elements'] if e['role'] == 'AXImage' and e['text'] in NAMES]
    complete = not walk['truncated'] and len(images) == 6 and {e['text'] for e in images} == set(NAMES)
    frames = {}
    for image in images:
        f = image.get('frame', {})
        if set(f) != {'x', 'y', 'width', 'height'} or not all(math.isfinite(v) for v in f.values()):
            complete = False; continue
        frames[image['text']] = dict(x=f['x']-bounds['X'], y=f['y']-bounds['Y'],
                                    width=f['width'], height=f['height'])
    for f in frames.values():
        f['center_x'] = f['x']+f['width']/2; f['center_y'] = f['y']+f['height']/2
    startup = [s for s in data['startup_readiness'] if s['pid'] == case['pid']]
    assert len(startup) == 1 and startup[0]['samples']
    return dict(pid=case['pid'], session=case['session'], startup=startup[0],
        startup_ready_bounds=startup[0]['samples'][-1]['own_native_window']['kCGWindowBounds'],
        final_bounds_points=bounds, png=shot['png'], png_stable_comparisons=shot['equal_comparisons'],
        png_elapsed=shot['elapsed_seconds'], pixels=shot['pixels'],
        png_contract_pass=shot['equal_comparisons'] >= 4 and bounds['Width'] == 920 and bounds['Height'] == 668,
        select_start_uptime=case['select_start_uptime'], close_return_uptime=case.get('close_return_uptime'),
        settled_walk={k: walk[k] for k in ['start_uptime', 'end_uptime', 'visited', 'truncated']},
        settled_walk_seconds=walk['end_uptime']-walk['start_uptime'],
        settled_six_frames_complete=complete, missing_images=sorted(set(NAMES)-frames.keys()),
        frames_window_points=frames,
        first_second_walks=[{k: s.get(k) for k in ['start_uptime', 'end_uptime', 'visited', 'truncated', 'pattern_label_count', 'missing']}
                            for s in case['first_second_ax']])


def compare(groups, first, second):
    result = dict(direction=second+' minus '+first, scenarios={})
    for scenario in ['immediate', 'wait', 'direct']:
        cases = [groups.get(g, {}).get('cases', {}).get(scenario) for g in [first, second]]
        if not all(c and c['settled_six_frames_complete'] for c in cases):
            result['scenarios'][scenario] = dict(available=False, reason='Missing group or incomplete settled AX; no fallback substituted')
            continue
        a, b = [c['frames_window_points'] for c in cases]
        delta = {name: {k: b[name][k]-a[name][k] for k in a[name]} for name in NAMES}
        result['scenarios'][scenario] = dict(available=True, delta_pt=delta,
            max_abs_frame_delta_pt=max(abs(delta[n][k]) for n in NAMES for k in ['x', 'y', 'width', 'height']))
    return result


def main():
    assert len(sys.argv) == 6, 'RAW OUTPUT EXPECTED_HARNESS EXPECTED_OBSERVER_SHA EXPECTED_DRIVER_SHA'
    raw, out = [Path(p).resolve() for p in sys.argv[1:3]]
    harness, observer, driver = sys.argv[3:]
    assert raw != out and raw not in out.parents and not out.exists()
    out.mkdir(parents=True)
    report = dict(scope='Offline acquisition/startup/repetition/source-associated geometry only; no pixel or causal verdict', groups={})
    try:
        report['integrity'] = ledger(raw)
        assert sha(raw/'gallery-film-probe.swift') == observer
        assert sha(raw/'gallery-film-abba.py') == driver
        summary = read(raw/'summary.json')
        assert summary['collection_harness_sha'] == harness and summary['observer_sha256'] == observer
        report['wrapper'] = summary
        for item in summary['legs']:
            name = item['leg']; assert name in ORDER and item['source_sha'] == SOURCES[name[0]]
            group = dict(wrapper_validated=item.get('completed', False), cases={})
            report['groups'][name] = group
            isolation = read(raw/name/'isolation.json')
            assert isolation['identifier'] == item['bundle_id']
            original = read(raw/('source-'+name[0])/'original-regular-members.json')
            assert original == isolation['copied_regular_members']
            assert original['Contents/MacOS/Gallery'] == GUI[name[0]]
            signed = isolation['signed_regular_members']; assert original.keys() == signed.keys()
            assert {k for k in original if original[k] != signed[k]} <= ALLOWED
            for path, before in isolation['before'].items():
                after = isolation['after'][path]
                assert before['sections'] == after['sections']
                assert before['signature_storage_sizes_normalized_sha256'] == after['signature_storage_sizes_normalized_sha256']
            group['isolation_records_consistent'] = True
            runtime = raw/name/'runtime/result.json'
            if not runtime.exists():
                group['observer_report_missing'] = True; continue
            data = read(runtime)
            assert data['source_sha'] == item['source_sha'] and data['harness_sha'] == harness
            group.update(observer_success=data.get('success'), normal_preferences=data['system_preferences'],
                         observation=data['observation_mode'], ax_trusted=data['accessibility_trusted'],
                         screen_preflight=data['screen_recording_preflight'], displays=data['displays'],
                         activations=data['activation_requests'], bundle_id=item['bundle_id'])
            group['normal_permission_active_contract'] = (data['observation_mode'] == 'active'
                and data['accessibility_trusted'] is True and data['screen_recording_preflight'] is True
                and all(v is False for v in data['system_preferences'].values())
                and all(a['after']['front_pid'] == a['pid'] for a in data['activation_requests']))
            for case in data['cases']:
                assert (runtime.parent/case['film']['png']).is_file()
                group['cases'][case['scenario']] = case_data(case, data)
            group['fresh_pid_count'] = len({c['pid'] for c in data['cases']})
            group['fresh_session_count'] = len({c['session'] for c in data['cases']})
        report['acquisition'] = dict(wrapper_success=summary['success'], phase=summary.get('phase'),
            failure=summary.get('failure'), not_started=[g for g in ORDER if g not in report['groups']],
            cases_present=sum(len(g['cases']) for g in report['groups'].values()),
            complete_six_frame_cases=sum(c['settled_six_frames_complete'] for g in report['groups'].values() for c in g['cases'].values()),
            all_four_wrapper_validated=len(summary['legs']) == 4 and all(i.get('completed') for i in summary['legs']),
            unique_bundle_ids=len({i['bundle_id'] for i in summary['legs']}), cleanup=summary.get('cleanup'))
        report['same_source_repetition'] = {a+'-'+b: compare(report['groups'], a, b) for a, b in [('A1', 'A2'), ('B1', 'B2')]}
        report['between_source_geometry'] = {a+'-'+b: compare(report['groups'], a, b)
            for a, b in [('A1', 'B1'), ('A1', 'B2'), ('A2', 'B1'), ('A2', 'B2')]}
        report['analysis_completed'] = True
    except Exception as error:
        report['analysis_completed'] = False; report['analysis_failure'] = type(error).__name__+': '+str(error)
    (out/'analysis.json').write_text(json.dumps(report, indent=2)+'\n')
    (out/'SHA256SUMS').write_text(sha(out/'analysis.json')+'  analysis.json\n')
    return 0 if report['analysis_completed'] else 1


if __name__ == '__main__':
    sys.exit(main())
