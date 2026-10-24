"""Read archived ABBA reports only; exclude every truncated walk's geometry."""
import hashlib
import json
import math
from pathlib import Path
import sys

NAMES = {'Gingham', 'Tartan', 'Madras', 'Glen', 'Houndstooth', 'Windowpane'}


def full_frames(walk):
    if walk.get('truncated', True): return None
    rows = [e for e in walk['elements'] if e['role'] == 'AXImage' and e['text'] in NAMES]
    if len(rows) != 6 or {e['text'] for e in rows} != NAMES: return None
    result = {}
    for row in rows:
        f = row.get('frame', {})
        if set(f) != {'x', 'y', 'width', 'height'} or not all(math.isfinite(v) for v in f.values()): return None
        if min(f['width'], f['height']) <= 0: return None
        result[row['text']] = f
    return result


def main():
    assert len(sys.argv) == 3, 'RAW OUTPUT_JSON (must not exist)'
    raw, out = [Path(p).resolve() for p in sys.argv[1:]]
    assert not out.exists() and raw not in out.parents
    ledger = raw/'SHA256SUMS'; count = 0
    for line in ledger.read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert hashlib.sha256((raw/name).read_bytes()).hexdigest() == digest
        count += 1
    report = dict(input_raw=str(raw), input_ledger_sha256=hashlib.sha256(ledger.read_bytes()).hexdigest(),
        ledger_entries_verified=count, coordinate_contract='All raw AX frames are screen points. Reference-normalized values subtract final Film PNG origin, not a concurrent early CG measurement.',
        command_contract='select end includes the observer first-second loop; CLI return does not prove application animation/layout completion.', cases=[])
    for leg in ['A1', 'B1', 'B2', 'A2']:
        data = json.loads((raw/leg/'runtime/result.json').read_text())
        for case in data['cases']:
            commands = [c for c in data['commands'] if case['session'] in c['arguments']]
            select = next(c for c in commands if 'select' in c['arguments'] and 'Film' in c['arguments'])
            t0 = select['start_uptime']
            events = {}
            for key, required in [('resize', ['window', 'resize']), ('inspector_open', ['set-bool', 'true']),
                                  ('inspector_close', ['set-bool', 'false']), ('select', ['select', 'Film'])]:
                matches = [c for c in commands if all(v in c['arguments'] for v in required)]
                if not matches: continue
                assert len(matches) == 1
                command = matches[0]
                response_text = (raw/leg/'runtime'/command['stdout']).read_text()
                events[key] = dict(raw=command,
                    start_ms_from_select=(command['start_uptime']-t0)*1000,
                    end_ms_from_select=(command['end_uptime']-t0)*1000,
                    response=json.loads(response_text) if response_text.strip() else None,
                    stdout_empty=not bool(response_text.strip()))
            samples, complete = [], []
            for index, walk in enumerate(case['first_second_ax']):
                frames = full_frames(walk)
                sample = dict(index=index, start_uptime=walk['start_uptime'], end_uptime=walk['end_uptime'],
                    start_ms_from_select=(walk['start_uptime']-t0)*1000,
                    end_ms_from_select=(walk['end_uptime']-t0)*1000,
                    visited=walk.get('visited'), truncated=walk.get('truncated'), complete_six_images=frames is not None)
                if frames is not None:
                    complete.append(dict(sample, raw_screen_frames=frames,
                        accessibility_container_frames=[e for e in walk['elements'] if e['role'] in ['AXSplitGroup', 'AXScrollArea']]))
                samples.append(sample)
            settled = full_frames(case['settled_ax']); assert settled is not None
            first = complete[0] if complete else None
            reference = case['film']['bounds_points']
            if first:
                first['max_frame_difference_to_settled_pt'] = max(abs(first['raw_screen_frames'][n][k]-settled[n][k]) for n in NAMES for k in ['x', 'y', 'width', 'height'])
                f = first['raw_screen_frames']['Glen']
                first['glen_center_x_minus_final_window_x'] = f['x']+f['width']/2-reference['X']
                first['glen_width'] = f['width']
            startup = next(s for s in data['startup_readiness'] if s['pid'] == case['pid'])
            compact_startup = []
            for sample in startup['samples']:
                native = sample.get('own_native_window') or {}
                compact_startup.append(dict(uptime=sample['uptime'],
                    native_bounds=native.get('kCGWindowBounds'), native_window_id=native.get('kCGWindowNumber'),
                    native_alpha=sample.get('own_native_window_alpha'),
                    cli_windows=[{k: w.get(k) for k in ['window', 'frame', 'lifecycle', 'visibility']} for w in sample['windows']]))
            row = dict(leg=leg, source=data['source_sha'], scenario=case['scenario'], pid=case['pid'],
                select_cli_start_uptime=t0, select_marker_uptime=case['select_start_uptime'],
                close_return_marker_uptime=case.get('close_return_uptime'),
                startup_deadline_uptime=startup['deadline_uptime'], startup_samples=compact_startup,
                commands=events, early_walks=samples, first_complete_walk=first,
                settled_walk={k: case['settled_ax'][k] for k in ['start_uptime', 'end_uptime', 'visited', 'truncated']},
                final_png_reference=reference,
                native_clip_or_swiftui_viewport_observations=0)
            if 'inspector_ax' in case:
                walk = case['inspector_ax']
                row['inspector_ax'] = dict(start_uptime=walk['start_uptime'], end_uptime=walk['end_uptime'], truncated=walk['truncated'])
                if not walk['truncated']:
                    row['inspector_ax']['accessibility_container_frames'] = [e for e in walk['elements'] if e['role'] in ['AXSplitGroup', 'AXScrollArea']]
            report['cases'].append(row)
    out.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__': main()
