#!/usr/bin/env python3
"""Offline data export only. No UI, subprocess, image transform, or visual verdict."""
import argparse
import hashlib
import io
import json
import math
from pathlib import Path

SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
REFERENCE_SHA = '8921655dea0938f76e49cfc808414d3278fce1deabeca1b98f5fd1d5bdfe8f50'
COLLECTOR_SOURCE_SHA = 'c4a1bd81e61079a75047e9cfc1f1407b2f12de1ccad7744878ff98975839ee9b'
NAMES = ('Gingham', 'Tartan', 'Madras', 'Glen', 'Houndstooth', 'Windowpane')


def check(value, message):
    if not value:
        raise ValueError(message)


def digest(data):
    return hashlib.sha256(data).hexdigest()


def read(path, expected=None):
    path = Path(path).resolve(strict=True)
    check(path.is_file(), 'Not a regular resolved file: ' + str(path))
    data = path.read_bytes()
    check(expected is None or digest(data) == expected, 'SHA mismatch: ' + str(path))
    return data, {'path': str(path), 'bytes': len(data), 'sha256': digest(data)}


def document(path, expected=None):
    data, identity = read(path, expected)
    return json.loads(data), identity


def child(parent, name):
    check(isinstance(name, str) and Path(name).name == name and name not in ('', '.', '..'), 'Expected local basename')
    path = (parent / name).resolve(strict=True)
    check(path.parent == parent.resolve(strict=True), 'Referenced file escaped its report directory')
    return path


def number(value):
    check(type(value) in (int, float) and math.isfinite(value), 'Missing/nonfinite numeric value')
    return value


def png_metadata(path, capture, expected=None):
    from PIL import Image
    data, identity = read(path, expected)
    with Image.open(io.BytesIO(data)) as image:
        check(image.format == 'PNG', 'Not PNG')
        def metadata(value):
            if isinstance(value, bytes):
                return {'raw_bytes': len(value), 'sha256': digest(value)}
            if isinstance(value, dict):
                return {str(k): metadata(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [metadata(v) for v in value]
            check(value is None or isinstance(value, (str, int, float, bool)), 'Unsupported metadata value')
            return value
        bounds = capture['bounds_points']
        width, height = number(bounds['Width']), number(bounds['Height'])
        check(width > 0 and height > 0, 'Invalid capture bounds')
        check(list(image.size) == capture['pixels'], 'PNG size disagrees with actual capture record')
        icc = image.info.get('icc_profile')
        result = {'file': identity, 'format': image.format, 'pixels': list(image.size), 'mode': image.mode,
                  'metadata': metadata(image.info), 'capture_scale_ratios': {'x': image.width / width, 'y': image.height / height},
                  'icc_raw_profile': None if icc is None else {'bytes': len(icc), 'sha256': digest(icc)},
                  'pixel_scope': 'Original PNG bytes only; no raster load/convert/resize, colour transform, ROI, or pixel comparison.'}
        return result


def state_export(parent, capture, ax, controls, context, png_sha=None):
    check(ax.get('truncated') is False, 'Terminal AX truncated')
    origin = {'x': number(capture['bounds_points']['X']), 'y': number(capture['bounds_points']['Y'])}
    rows = [r for r in ax['elements'] if r.get('role') == 'AXImage' and r.get('text') in NAMES]
    check(len(rows) == 6 and {r['text'] for r in rows} == set(NAMES), 'Need exactly six unique AXImage names')
    images = {}
    for row in rows:
        frame = {key: number(row['frame'][key]) for key in ('x', 'y', 'width', 'height')}
        check(frame['width'] > 0 and frame['height'] > 0, 'Nonpositive AXImage size')
        relative = {**frame, 'x': frame['x'] - origin['x'], 'y': frame['y'] - origin['y']}
        images[row['text']] = {'raw_AXImage_row': row, 'screen_xywh': frame, 'capture_origin_relative_xywh': relative}
    return {'capture': capture, 'capture_origin_screen_points': origin, 'terminal_ax_metadata': {k: v for k, v in ax.items() if k != 'elements'},
            'images': {name: images[name] for name in NAMES}, 'controls': controls, 'context_and_timing': context,
            'png': png_metadata(child(parent, capture['png']), capture, png_sha),
            'sampling_limit': 'PNG precedes the terminal AX walk. Separate observations, not atomic or exact animation samples.'}


def commands_export(parent, commands):
    # Preserve the complete original command records, including startup nonzero statuses.
    logs = {}
    for command in commands:
        for key in ('stdout', 'stderr'):
            if key in command:
                name = command[key]
                _, identity = read(child(parent, name))
                logs[name] = identity
    return {'records': commands, 'referenced_log_identities': logs,
            'limit': '14 retains its complete original command table, including subsequent followups; only initial and first Last geometry are exported.'}


def reference_export(reference_path):
    reference, reference_identity = document(reference_path, REFERENCE_SHA)
    check(reference['schema'] == 'bern_exact_e48_film_first_last14_reference_v1' and reference['source_sha'] == SOURCE, 'Wrong reference')
    base = reference_path.resolve(strict=True).parent
    raw_path = base / reference['raw_result']['path']
    raw, raw_identity = document(raw_path, reference['raw_result']['sha256'])
    case = raw['cases'][0]
    last = case['followup_stages'][0]
    check(raw['success'] is True and case['scenario'] == 'direct' and last['stage'] == 'last', 'Reference scope differs')
    check(reference['initial_setup']['capture'] == case['film'] and reference['initial_setup']['terminal_ax'] == case['settled_ax'], 'Initial reference binding differs')
    check(reference['first_last']['capture'] == last['capture'] and reference['first_last']['terminal_ax'] == last['ax'], 'Last reference binding differs')
    initial_context = {k: case[k] for k in ('scenario', 'pid', 'session', 'select_start_uptime') if k in case}
    last_context = {k: v for k, v in last.items() if k not in ('capture', 'ax', 'controls')}
    states = {
        'initial': state_export(raw_path.parent, case['film'], case['settled_ax'], case['controls'], initial_context, reference['initial_setup']['png']['sha256']),
        'last': state_export(raw_path.parent, last['capture'], last['ax'], last['controls'], last_context, reference['first_last']['png']['sha256'])}
    return {'identity': reference_identity, 'raw_report_identity': raw_identity, 'reference_metadata': {k: v for k, v in reference.items() if k not in ('initial_setup', 'first_last')},
            'report_truth': {k: v for k, v in raw.items() if k not in ('cases', 'commands')},
            'commands': commands_export(raw_path.parent, raw['commands']), 'states': states,
            'cleanup_limit': 'Old14 stop-before-restore collector; no strong termination/restored-front receipt. Never substitute for the13 cleanup gate.'}


def local_export(report_path):
    report, identity = document(report_path)
    check(report.get('kind') == 'film_first_last13_capture' and report.get('source_sha') == SOURCE and report.get('expected_os') == 13, 'Wrong local report scope')
    check(report.get('row_ledger_enabled') is False and report.get('scroll_trace_enabled') is False, 'Unexpected instrumentation')
    stages = report.get('stages', [])
    check([s.get('stage') for s in stages] == ['initial', 'last'], 'Missing/additional/out-of-order Film states')
    states = {}
    for stage in stages:
        context = {k: v for k, v in stage.items() if k not in ('capture', 'ax', 'controls')}
        states[stage['stage']] = state_export(report_path.parent, stage['capture'], stage['ax'], stage['controls'], context)
    return {'raw_report_identity': identity, 'report_truth': {k: v for k, v in report.items() if k not in ('stages', 'commands')},
            'commands': commands_export(report_path.parent, report['commands']), 'states': states,
            'truth_limit': 'Collector success and every cleanup value remain original data. This script does not override the outer wrapper result or validate private-signature normalization.'}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--reference', type=Path, required=True)
    parser.add_argument('--collector-source', type=Path, required=True)
    parser.add_argument('--local-report', type=Path, required=True)
    parser.add_argument('--watchdog', type=Path, required=True, help='Actual complete outer watchdog JSON; success/false/defaults timeout remain unmodified.')
    parser.add_argument('--truth-json', nargs=2, action='append', default=[], metavar=('NAME', 'PATH'), help='Actual wrapper/guard/post-cleanup/build JSON; copied semantically with full raw identity, never used to rewrite a result.')
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    check(not args.output.exists(), 'Fresh output JSON required')
    check(args.output.parent.is_dir(), 'Output parent must already exist')
    check(args.output.resolve() not in (args.reference.resolve(), args.collector_source.resolve(), args.local_report.resolve(), args.watchdog.resolve()), 'Output overlaps a direct input')
    _, collector_identity = read(args.collector_source, COLLECTOR_SOURCE_SHA)
    reference = reference_export(args.reference)
    local = local_export(args.local_report)
    watchdog, watchdog_identity = document(args.watchdog)
    truth = {'watchdog': {'identity': watchdog_identity, 'original_JSON_values': watchdog}}
    for name, path in args.truth_json:
        check(name not in truth, 'Duplicate truth label')
        check(args.output.resolve() != Path(path).resolve(), 'Output overlaps a truth input')
        data, identity = document(Path(path))
        truth[name] = {'identity': identity, 'original_JSON_values': data}
    differences = {}
    for state in ('initial', 'last'):
        differences[state] = {'capture_origin_delta_13_minus_14': {k: local['states'][state]['capture_origin_screen_points'][k] - reference['states'][state]['capture_origin_screen_points'][k] for k in ('x', 'y')}, 'images': {}}
        for name in NAMES:
            left = local['states'][state]['images'][name]
            right = reference['states'][state]['images'][name]
            differences[state]['images'][name] = {
                key + '_delta_13_minus_14': {axis: left[key][axis] - right[key][axis] for axis in ('x', 'y', 'width', 'height')}
                for key in ('screen_xywh', 'capture_origin_relative_xywh')}
    result = {'schema': 'bern_film_first_last13_offline_export_v1', 'kind': 'data_export_no_acceptance_verdict',
              'collector_source_identity': collector_identity, 'local13': local, 'reference14': reference,
              'actual_additional_truth': truth, 'point_differences': differences,
              'limits': ['Exactly initial and first Last image geometry; initial is setup context and does not reopen stopped wait/direct acceptance.',
                         'No coordinate fit, tolerance, target-position criterion, pixel normalization, ROI, colour matching, visual equivalence or causal conclusion.',
                         'Original collectors, startup/heartbeat/sampling timing and cleanup differ. OS screen scale is reported, never resampled.',
                         'A failed wrapper/defaults5s cleanup remains failed even if a collector or later separate cleanup succeeded.',
                         'Missing/incomplete actual data stops this export; raw evidence stays untouched. No synthetic local values or fallback states.']}
    # Exclusive creation protects inputs and any previous analysis; no source/report is modified.
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')


if __name__ == '__main__':
    main()
