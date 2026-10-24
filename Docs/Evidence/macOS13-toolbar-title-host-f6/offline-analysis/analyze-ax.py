"""Offline AX ancestry and geometry extraction; never executes app/observer code."""
from collections import Counter
import hashlib
import json
from pathlib import Path
import sys


def analyze(stage):
    ax = stage['ax']; rows = {e['node_index']: e for e in ax['elements']}
    def ancestors(e):
        path, seen, index = [], set(), e['parent_index']
        while index is not None:
            assert index not in seen; seen.add(index)
            parent = rows[index]; path.append(parent); index = parent['parent_index']
        return path
    window = [e for e in rows.values() if e.get('AXRole') == 'AXWindow' and e.get('AXIdentifier') == 'main']
    assert len(window) == 1; window = window[0]; origin = window['frame_screen_points']
    in_window = lambda e: any(a['node_index'] == window['node_index'] for a in ancestors(e))
    toolbar = [e for e in rows.values() if e.get('AXRole') == 'AXToolbar' and in_window(e)]
    assert len(toolbar) == 1; toolbar = toolbar[0]
    title = [e for e in rows.values() if e.get('AXRole') == 'AXStaticText'
        and e['parent_index'] == window['node_index'] and e.get('AXValue') == window['AXTitle']]
    assert len(title) == 1; title = title[0]
    toggle = [e for e in rows.values() if e.get('AXRole') == 'AXButton'
        and e.get('AXDescription') == 'Toggle Sidebar' and e['parent_index'] == toolbar['node_index']]
    assert len(toggle) == 1; toggle = toggle[0]
    inner = [e for e in rows.values() if e.get('AXRole') == 'AXButton'
        and e.get('AXDescription') == 'Toggle Sidebar' and e['parent_index'] == toggle['node_index']]
    assert len(inner) == 1; inner = inner[0]
    outline = [e for e in rows.values() if e.get('AXRole') == 'AXOutline'
        and e.get('AXIdentifier') == 'main_window.sidebar_search' and in_window(e)]
    assert len(outline) == 1; outline = outline[0]
    sidebar = next(a for a in ancestors(outline) if a.get('AXRole') == 'AXScrollArea')
    scrolls = [e for e in rows.values() if e.get('AXRole') == 'AXScrollArea' and in_window(e)
               and e['node_index'] != sidebar['node_index']]
    detail = max(scrolls, key=lambda e: e['frame_screen_points']['width'])

    def describe(e):
        frame = e['frame_screen_points']
        return dict(node_index=e['node_index'], role=e.get('AXRole'), title=e.get('AXTitle'),
            value=e.get('AXValue'), description=e.get('AXDescription'), identifier=e.get('AXIdentifier'),
            local_frame=dict(x=frame['x']-origin['x'], y=frame['y']-origin['y'], width=frame['width'], height=frame['height']),
            ancestors=[dict(index=a['node_index'], role=a.get('AXRole'), title=a.get('AXTitle')) for a in ancestors(e)])
    selected = dict(window=describe(window), toolbar=describe(toolbar), title=describe(title),
        outer_toggle=describe(toggle), inner_toggle=describe(inner), sidebar_scroll=describe(sidebar),
        sidebar_outline=describe(outline), detail_scroll=describe(detail))
    errors, exceptional = Counter(), []
    for e in rows.values():
        menu = e.get('AXRole') == 'AXMenuBar' or any(a.get('AXRole') == 'AXMenuBar' for a in ancestors(e))
        for name, code in e['attribute_errors'].items():
            errors[f'{name}:{code}'] += 1
            if code not in [0, -25205, -25212]:
                exceptional.append(dict(index=e['node_index'], role=e.get('AXRole'), attribute=name,
                    code=code, under_menu_bar=menu,
                    ancestors=[dict(index=a['node_index'], role=a.get('AXRole')) for a in ancestors(e)]))
    return dict(index=stage['index'], option=stage['option'],
        cg_window_name=stage['capture']['own_window'].get('kCGWindowName'),
        ax_window_title=window['AXTitle'], selected=selected,
        flags={k: ax[k] for k in ['tree_complete', 'complete', 'query_failed', 'structural_query_failed', 'truncated', 'visited', 'discovered']},
        optional_error_counts=dict(errors), non_unsupported_optional_errors=exceptional)


def main():
    assert len(sys.argv) == 3, 'RAW OUTPUT_JSON (new file)'
    raw, out = [Path(s).resolve() for s in sys.argv[1:]]
    assert not out.exists() and raw not in out.parents
    count = 0
    for line in (raw/'SHA256SUMS').read_text().splitlines():
        digest, name = line.split('  ', 1)
        assert hashlib.sha256((raw/name).read_bytes()).hexdigest() == digest; count += 1
    report = dict(raw=str(raw), ledger_entries_verified=count,
        ledger_sha256=hashlib.sha256((raw/'SHA256SUMS').read_bytes()).hexdigest(),
        scope='AX bounds in window-local top-left points, not native NSView frames or glyph ink bounds; no effective-light/13vs14 verdict.', variants={})
    for side in ['A', 'B']:
        d = json.loads((raw/side/'runtime/result.json').read_text())
        report['variants'][side] = dict(source=d['source_sha'], elapsed_seconds=d['elapsed_seconds'],
            window_titles=[s['capture']['own_window'].get('kCGWindowName') for s in d['stages']],
            stages=[analyze(s) for s in d['stages']])
    report['pairs'] = []
    for a, b in zip(report['variants']['A']['stages'], report['variants']['B']['stages']):
        deltas = {key: {axis: b['selected'][key]['local_frame'][axis]-a['selected'][key]['local_frame'][axis]
                  for axis in ['x', 'y', 'width', 'height']} for key in a['selected']}
        report['pairs'].append(dict(index=a['index'], option=a['option'], local_frame_deltas_B_minus_A=deltas,
            max_abs_selected_frame_delta=max(abs(v) for delta in deltas.values() for v in delta.values()),
            same_window_title=a['ax_window_title'] == b['ax_window_title']))
    out.write_text(json.dumps(report, indent=2)+'\n')


if __name__ == '__main__': main()
