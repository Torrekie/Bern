#!/usr/bin/env python3
"""Offline fixed-e48 observer13 endpoint/diagnostic validator. Never launches anything."""
import argparse
import hashlib
import io
import json
import math
import re
from pathlib import Path

SOURCE = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
GUI = 'e2fbcea5fdc4cea6ebcfb00e1214e55badd78d82a31ebd248e18971e2f6c39a2'
CLI = '31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5'
CORE = 'b9a7c8d9a4060148f150c562e96297c10482181c96bf88477a6bfcf6cf5f5b06'
ORIGINAL_COLLECTOR = 'c4a1bd81e61079a75047e9cfc1f1407b2f12de1ccad7744878ff98975839ee9b'
COLLECTOR = '8bdf078fd1b75c8e4dd8b5c20725a12462491c9e92108818fd0b6e86b812ad0b'
SOURCE_PACKET = '8b6ac6b1c6997b8affedff173eb7f52626eb5e9c15eb3519505ba22bab1c9240'
GUARD = 'ab78c7d374169478a5f99c1a3000f9a6180338b78e2f250e5ff1446f7e19345d'
MANIFEST = 'fdb3ff8ca2fc2235531289c98fd5724f1eae816babd9646c83bf74587d86243f'
BASELINE_SHA = 'e47168e331b8c231755d18add58aaaf56541e59090f29e75d60e6d4486fc5c98'
BASELINE = Path('outputs/Bern/Docs/Evidence/macOS13-film-first-last-e48-20261025/raw/report.json')
PNG_PINS = {'initial': '38133c7326467de07e8981affb5b516e782c6c511b4a0a83fe35205e06350879',
            'last': 'e31e7385a300e3f686b2a434a627e0a1ad49a0214a16e92ad8188b783393cb69'}
NAMES = ('Gingham', 'Tartan', 'Madras', 'Glen', 'Houndstooth', 'Windowpane')
AXES = ('x', 'y', 'width', 'height')
SLOTS = {'request', 'schedule', 'settle', 'writer', 'terminal'}
U64 = (1 << 64) - 1


def check(value, message):
    if not value:
        raise ValueError(message)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def read(path, expected=None, cap=2 * 1024 * 1024):
    path = Path(path)
    check(not path.is_symlink() and path.is_file(), 'Regular nonsymlink file required: ' + str(path))
    check(path.stat().st_size <= cap, 'Input cap: ' + str(path))
    data = path.read_bytes()
    check(expected is None or sha(data) == expected, 'SHA mismatch: ' + str(path))
    return data, {'path': str(path.resolve()), 'bytes': len(data), 'sha256': sha(data)}


def unique(pairs):
    result = {}
    for key, value in pairs:
        check(key not in result, 'Duplicate JSON key: ' + key)
        result[key] = value
    return result


def document(path, expected=None, cap=2 * 1024 * 1024):
    data, identity = read(path, expected, cap)
    def bad(value):
        raise ValueError('Nonfinite JSON literal: ' + value)
    return json.loads(data, object_pairs_hook=unique, parse_constant=bad), identity


def number(value):
    check(type(value) in (int, float) and math.isfinite(value), 'Finite number required')
    return value


def integer(value, minimum=0):
    check(type(value) is int and minimum <= value <= U64, 'UInt64-range integer required')
    return value


def keys(value, required):
    check(type(value) is dict and set(value) == set(required.split()), 'Unexpected field set: ' + str(required))


def vector(value, fields):
    keys(value, fields)
    for item in value.values():
        number(item)


def identity(value):
    check(type(value) is str and re.fullmatch(r'ObjectIdentifier\(0x[0-9a-fA-F]+\)', value), 'Invalid native identity string')


def child(parent, name):
    check(type(name) is str and Path(name).name == name and name not in ('', '.', '..'), 'Local basename required')
    result = parent / name
    check(result.resolve().parent == parent.resolve(), 'Referenced file escaped report')
    return result


def image(path, capture, pin=None):
    from PIL import Image
    data, ident = read(path, pin, 32 * 1024 * 1024)
    with Image.open(io.BytesIO(data)) as im:
        check(im.format == 'PNG' and list(im.size) == capture['pixels'], 'PNG capture dimensions differ')
        im.load()  # Original mode only; no conversion/resampling/profile transform.
        raster = im.tobytes()
        icc = im.info.get('icc_profile')
        info = {k: ({'bytes': len(v), 'sha256': sha(v)} if isinstance(v, bytes) else v) for k, v in im.info.items()}
        meta = {'file': ident, 'pixels': list(im.size), 'mode': im.mode, 'metadata': info,
                'icc': None if icc is None else {'bytes': len(icc), 'sha256': sha(icc)},
                'raster_bytes': len(raster), 'raw_raster_sha256': sha(raster),
                'scale': {'x': im.width / number(capture['bounds_points']['Width']),
                          'y': im.height / number(capture['bounds_points']['Height'])}}
        return meta, raster


def command_body(command):
    args = command['arguments']
    return args[2:] if args[:1] == ['--session'] else args


def state(report_path, stage, pin=None):
    capture, ax = stage['capture'], stage['ax']
    check(ax.get('truncated') is False and ax.get('matching_elements_missing') is False, 'Incomplete AX walk')
    check(capture['equal_comparisons'] == 4, 'Original four-equality capture gate differs')
    check(capture['bounds_points']['Width'] == 920 and capture['bounds_points']['Height'] == 668, 'Window size differs')
    check(number(capture['elapsed_seconds']) >= 0, 'Invalid stable elapsed time')
    check(number(ax['end_uptime']) >= number(ax['start_uptime']), 'Invalid AX walk time')
    # The source budget guards loop entry; final AX calls/PNG encoding can finish later.
    # Preserve actual timings instead of inventing a stricter post-completion deadline.
    origin = {'x': number(capture['bounds_points']['X']), 'y': number(capture['bounds_points']['Y'])}
    rows = [r for r in ax['elements'] if r.get('role') == 'AXImage' and r.get('text') in NAMES]
    check(len(rows) == 6 and {r['text'] for r in rows} == set(NAMES), 'Exactly six unique AXImage rows required')
    images = {}
    for row in rows:
        raw = {a: number(row['frame'][a]) for a in AXES}
        check(raw['width'] > 0 and raw['height'] > 0, 'Nonpositive AX image extent')
        relative = dict(raw, x=raw['x'] - origin['x'], y=raw['y'] - origin['y'])
        images[row['text']] = {'raw_row': row, 'screen_xywh': raw, 'origin_relative_xywh': relative}
    png, raster = image(child(report_path.parent, capture['png']), capture, pin)
    return {'images': {n: images[n] for n in NAMES}, 'capture': capture, 'png': png,
            'ax_metadata': {k: v for k, v in ax.items() if k != 'elements'}, 'controls': stage['controls'],
            'stage_metadata': {k: v for k, v in stage.items() if k not in ('capture', 'ax', 'controls')}}, raster


def report_export(path, report, baseline=False):
    check(report.get('kind') == 'film_first_last13_capture' and report.get('source_sha') == SOURCE, 'Wrong capture scope')
    check(report.get('expected_os') == 13 and report.get('ci_run_id') == 'local', 'Wrong host mode')
    check(report.get('row_ledger_enabled') is False and report.get('scroll_trace_enabled') is False, 'Other instrumentation enabled')
    check(report.get('system_preferences') == {'increase_contrast': False, 'reduce_motion': False, 'reduce_transparency': False}, 'Normal display settings differ')
    check(report.get('scenario') == 'direct' and report.get('followup_sequence') == 'first-last-only', 'Wrong scenario')
    check(report.get('final_context') == {'appearance': 'Light', 'page': 'Film', 'requested_action': 'first Last only', 'terminal_states': 2}, 'Wrong terminal context')
    check([s.get('stage') for s in report['stages']] == ['initial', 'last'], 'Only two ordered states allowed')
    states, rasters = {}, {}
    for stage in report['stages']:
        name = stage['stage']
        states[name], rasters[name] = state(path, stage, PNG_PINS[name] if baseline else None)
    logs = {}
    for c in report['commands']:
        for field in ('stdout', 'stderr'):
            raw, ident = read(child(path.parent, c[field]))
            logs[c[field]] = ident
    return {'states': states, 'commands': report['commands'], 'referenced_logs': logs,
            'original_truth': {k: v for k, v in report.items() if k not in ('commands', 'stages')}}, rasters


def raw_object_members(text, start=0):
    decoder = json.JSONDecoder()
    def skip(index):
        while index < len(text) and text[index].isspace():
            index += 1
        return index
    index = skip(start)
    check(text[index] == '{', 'Raw JSON object expected')
    index = skip(index + 1)
    result = {}
    while text[index] != '}':
        key, index = decoder.raw_decode(text, index)
        check(type(key) is str and key not in result, 'Raw duplicate/nonstring key')
        index = skip(index)
        check(text[index] == ':', 'Raw member colon missing')
        begin = skip(index + 1)
        _, end = decoder.raw_decode(text, begin)
        result[key] = (begin, end)
        index = skip(end)
        if text[index] == '}':
            break
        check(text[index] == ',', 'Raw member delimiter missing')
        index = skip(index + 1)
    return result


def diagnostic(packet, raw_packet, report, watchdog, locks):
    keys(packet, 'schema diagnostic_complete export_trigger pid request_count eligible_schedule_count eligible_settle_count writer_count slot_limit slot_byte_limit file_byte_limit slots invalid_fields')
    check(packet['schema'] == 'bern_film_explicit_last_observation_v1' and packet['export_trigger'] == 'first_post_request_ui_inspect', 'Wrong diagnostic schema/trigger')
    check(packet['diagnostic_complete'] is True and packet['invalid_fields'] == {}, 'Core reported diagnostic incomplete')
    check(packet['request_count'] == 1 and type(packet['request_count']) is int, 'Exactly one request required')
    for field in ('slot_limit', 'slot_byte_limit', 'file_byte_limit'):
        integer(packet[field])
    check((packet['slot_limit'], packet['slot_byte_limit'], packet['file_byte_limit']) == (5, 2048, 16384), 'Core caps differ')
    for k in ('eligible_schedule_count', 'eligible_settle_count', 'writer_count'):
        integer(packet[k], 1)
    check(packet['writer_count'] <= packet['eligible_settle_count'], 'More writers than settle entries')
    slots = packet['slots']
    check(type(slots) is dict and set(slots) == SLOTS, 'Exactly five literal slots required')
    text = raw_packet.decode('utf-8')
    slot_start, _ = raw_object_members(text)['slots']
    actual_slots = raw_object_members(text, slot_start)
    check(set(actual_slots) == SLOTS, 'Raw slots differ')
    slot_sizes = {name: len(text[begin:end].encode('utf-8')) for name, (begin, end) in actual_slots.items()}
    check(all(size <= 2048 for size in slot_sizes.values()), 'Actual serialized slot exceeds2048B')
    r, s, t, w, end = [slots[k] for k in ('request', 'schedule', 'settle', 'writer', 'terminal')]
    keys(r, 'uptime owner_identity wanted position target_after_assignment swiftui')
    for field in ('wanted', 'position', 'target_after_assignment'):
        keys(r[field], 'swift_type value')
        check(r[field]['swift_type'] == 'Swift.Int64' and type(r[field]['value']) is int and r[field]['value'] == 6, 'Request not typed Int64 Last6: ' + field)
    snap = r['swiftui']
    keys(snap, 'nearest arrived arrivals stops coming viewport anchor frame_wanted initial_waiting initial_generation')
    for field in ('nearest', 'arrived', 'coming'):
        if snap[field] is not None:
            keys(snap[field], 'swift_type value')
            check(snap[field]['swift_type'] == 'Swift.Int64', 'Unexpected Film key type')
            integer(snap[field]['value'], 1)
    for field in ('arrivals', 'stops', 'initial_generation'):
        integer(snap[field])
    check(type(snap['initial_waiting']) is bool, 'Invalid initial_waiting')
    vector(snap['viewport'], 'width height'); vector(snap['anchor'], 'x y')
    if snap['frame_wanted'] is not None:
        vector(snap['frame_wanted'], 'x y width height')
    keys(s, 'uptime eligible_sequence generation live')
    integer(s['eligible_sequence'], 1)
    check(s['eligible_sequence'] == 1 and type(s['live']) is bool, 'First schedule schema')
    keys(t, 'uptime eligible_sequence generation start length scroll_identity clip_identity document_identity inputs_complete wanted minimum maximum clamped document_length insets')
    integer(t['eligible_sequence'], 1)
    check(t['eligible_sequence'] == 1 and t['inputs_complete'] is True, 'First settle inputs incomplete')
    for slot in (s, t):
        if slot['generation'] is not None:
            integer(slot['generation'])
    for field in ('start', 'length', 'wanted', 'minimum', 'maximum', 'clamped', 'document_length'):
        number(t[field])
    vector(t['insets'], 'left right top bottom')
    keys(w, 'uptime settle_sequence kind native_inputs scope')
    integer(w['settle_sequence'], 1)
    check(w['settle_sequence'] <= packet['eligible_settle_count'] and w['kind'] in ('direct', 'animator_requested'), 'Writer association invalid')
    check(w['scope'] == 'setter_requested_not_animation_completed', 'Writer must not claim completion')
    keys(w['native_inputs'], 'start length wanted minimum maximum clamped document_length insets')
    for field, value in w['native_inputs'].items():
        vector(value, 'left right top bottom') if field == 'insets' else number(value)
    keys(end, 'uptime owner_identity scroll_identity clip_identity document_identity clip_bounds document_frame document_bounds clip_flipped document_flipped insets')
    for field in ('clip_bounds', 'document_frame', 'document_bounds'):
        vector(end[field], 'x y width height')
    vector(end['insets'], 'left right top bottom')
    check(type(end['clip_flipped']) is bool and type(end['document_flipped']) is bool, 'Invalid flipped flags')
    for slot in (r, end):
        identity(slot['owner_identity'])
    check(r['owner_identity'] == end['owner_identity'], 'Weak owner identity differs')
    for field in ('scroll_identity', 'clip_identity', 'document_identity'):
        identity(t[field]); identity(end[field]); check(t[field] == end[field], 'Native identity differs: ' + field)
    owned = watchdog['bootstrap_inspect']['own']
    check(type(packet['pid']) is int and packet['pid'] == owned['pid'] and all(x['pid'] == owned['pid'] for x in report['stages']), 'Diagnostic PID not same exact owned child')
    commands = report['commands']
    actions = [(i, c) for i, c in enumerate(commands) if command_body(c) == ['ui', 'activate', '--target', 'film.to_last']]
    check(len(actions) == 1, 'Need exactly one Last activation')
    index, action = actions[0]
    check(index > 0 and command_body(commands[index - 1]) == ['ui', 'inspect'], 'Original target lookup inspect missing')
    following = commands[index + 1:]
    check(len(following) == 2 and command_body(following[0]) == ['ui', 'inspect'] and command_body(following[1]) == ['window', 'list'], 'Original postLast command prefix changed')
    inspect = following[0]
    check(all(c['status'] == 0 for c in (action, inspect, following[1])), 'Last command failed')
    last = report['stages'][1]
    check(number(commands[index - 1]['end_uptime']) <= number(action['start_uptime']), 'Command order differs')
    request_time, terminal = number(r['uptime']), number(end['uptime'])
    check(number(action['start_uptime']) <= request_time <= number(inspect['start_uptime']), 'Request outside Last action/preinspect interval')
    check(number(last['ax']['end_uptime']) <= number(inspect['start_uptime']) <= terminal <= number(inspect['end_uptime']), 'Terminal not bound to first postAX inspect')
    for slot in (s, t, w):
        check(request_time <= number(slot['uptime']) <= terminal, 'Slot outside request/terminal interval')
    check(number(t['uptime']) <= number(w['uptime']), 'First writer precedes first settle')
    # First schedule, settle and writer may be different work items. No fabricated same-work ordering.
    return {'valid': True, 'actual_serialized_slot_bytes': slot_sizes, 'original_packet': packet, 'owned_identity': owned, 'action_command': action,
            'first_postrequest_inspect': inspect, 'last_ax_end_uptime': last['ax']['end_uptime'],
            'slot_uptime_minus_request': {k: number(v['uptime']) - request_time for k, v in slots.items()},
            'limit': 'Weak identity assertions are source-backed packet claims, not an independent native object read; setter request is not animation completion. No absolute PNG timestamp exists.'}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    for name in ('report', 'watchdog', 'diagnostic', 'locks', 'build-manifest', 'output'):
        p.add_argument('--' + name, type=Path, required=True)
    p.add_argument('--baseline-report', type=Path, default=BASELINE)
    args = p.parse_args()
    inputs = [args.report, args.watchdog, args.diagnostic, args.locks, args.build_manifest, args.baseline_report]
    output = args.output.resolve()
    check(not args.output.exists() and args.output.parent.is_dir(), 'Fresh output directory with existing parent required')
    for item in inputs:
        resolved = item.resolve()
        check(output != resolved and output not in resolved.parents and resolved not in output.parents, 'Bidirectional direct-input isolation failed')
        check(output != resolved.parent and output not in resolved.parent.parents and resolved.parent not in output.parents, 'Output overlaps input directory')
    args.output.mkdir()
    result = {'schema': 'bern_film_observer13_offline_validation_v1', 'input_identities': {}, 'errors': {},
              'capture_success': None, 'cleanup_success': None, 'endpoint_control_exact': False,
              'diagnostic_valid': False, 'diagnostic_interpretation_allowed': False,
              'source_pins': {'core': CORE, 'original_order_collector': ORIGINAL_COLLECTOR, 'env_only_collector': COLLECTOR, 'local_source_packet': SOURCE_PACKET, 'guard': GUARD},
              'limits': ['Exactly initial and first Last versus fixed original13; no14 input, normalization, ROI, tolerance, fit or offset.',
                         'Whole-window raster mismatch includes sidebar/chrome differences; no automatic crop or causal attribution.',
                         'Any failed gate stops diagnostic interpretation. No retry, fallback, latest-file search or rewritten original truth.']}
    def attempt(label, function):
        try:
            return function()
        except Exception as error:
            result['errors'][label] = type(error).__name__ + ': ' + str(error)
            return None
    def load(label, path, expected=None, cap=2 * 1024 * 1024):
        value, ident = document(path, expected, cap)
        result['input_identities'][label] = ident
        return value
    report = attempt('report', lambda: load('report', args.report))
    watchdog = attempt('watchdog', lambda: load('watchdog', args.watchdog))
    locks = attempt('locks', lambda: load('locks', args.locks))
    manifest = attempt('build_manifest', lambda: load('build_manifest', args.build_manifest, MANIFEST))
    baseline = attempt('baseline', lambda: load('baseline', args.baseline_report, BASELINE_SHA))
    packet = attempt('diagnostic_file', lambda: load('diagnostic', args.diagnostic, cap=16384))
    raw_packet = None
    if packet is not None:
        raw_packet, _ = read(args.diagnostic, result['input_identities']['diagnostic']['sha256'], 16384)
    result['original_watchdog'] = watchdog
    result['original_diagnostic'] = packet
    if report is not None:
        result['capture_success'] = report.get('success')
    if watchdog is not None:
        result['cleanup_success'] = watchdog.get('cleanup_success')
    def bindings():
        check(all(x is not None for x in (report, watchdog, locks, manifest)), 'Binding documents missing')
        check(locks['schema'] == 'bern_film_last_observer13_locks_v1' and locks['kind'] == 'film_last_observer13_capture', 'Wrong new locks')
        check(watchdog['kind'] == locks['kind'] and watchdog['locks_sha256'] == result['input_identities']['locks']['sha256'], 'Watchdog/locks identity mismatch')
        check(locks['source_sha'] == watchdog['source_sha'] == report['source_sha'] == manifest['source_sha'] == SOURCE, 'Source mismatch')
        check(manifest['schema'] == 'bern_film_last_observer_build_v1' and manifest['success'] is True and manifest['run_id'] == '40176620054', 'Wrong successful build')
        check(manifest['gui'] == {'bytes': 3770800, 'sha256': GUI}, 'Wrong observer GUI')
        for doc in (locks, watchdog):
            check(doc['observer_build_manifest_sha256'] == MANIFEST and doc['observer_source_app_sha256'] == GUI, 'Observer provenance mismatch')
            check(Path(doc['diagnostic_destination']).is_absolute() and Path(doc['diagnostic_destination']) == args.diagnostic.resolve(), 'Unexpected diagnostic destination')
        film = locks['film']
        check(film['original_gui_sha256'] == GUI and film['cli_sha256'] == report['cli_sha256'] == CLI, 'Wrong observer GUI/original CLI lock')
        check(film['private_gui_sha256'] == report['app_executable_sha256'], 'Private binary/report mismatch')
        check(watchdog['collector_source_sha256'] == COLLECTOR and watchdog['focus_guard_source_sha256'] == GUARD, 'Helper source mismatch')
        check(watchdog['local_source_manifest_sha256'] == SOURCE_PACKET, 'Env-only source packet mismatch')
        check(watchdog['collector_sha256'] == report['collector_executable_sha256'], 'Collector binary mismatch')
        check(watchdog['bootstrap_inspect']['own']['bundle_id'] == film['bundle_id'] == watchdog['private_bundle_id'], 'Private owned identity mismatch')
        return True
    bound = attempt('bindings', bindings)
    if report is not None and baseline is not None:
        local = attempt('observer_endpoint', lambda: report_export(args.report, report))
        original = attempt('baseline_endpoint', lambda: report_export(args.baseline_report, baseline, True))
        if local is not None and original is not None:
            endpoint = {'observer': local[0], 'original': original[0], 'differences': {}}
            exact = True
            for name in ('initial', 'last'):
                a, b = local[0]['states'][name], original[0]['states'][name]
                deltas = {n: {scope: {axis: a['images'][n][scope][axis] - b['images'][n][scope][axis] for axis in AXES}
                              for scope in ('screen_xywh', 'origin_relative_xywh')} for n in NAMES}
                geometry_exact = all(v == 0 for n in NAMES for v in deltas[n]['origin_relative_xywh'].values())
                comparable = all(a['png'][k] == b['png'][k] for k in ('pixels', 'mode', 'icc', 'scale'))
                raster_exact = comparable and local[1][name] == original[1][name]
                endpoint['differences'][name] = {'observer_minus_original_raw_point_deltas': deltas,
                    'all_relative_xywh_exact': geometry_exact, 'png_comparable': comparable,
                    'whole_window_raw_raster_exact': raster_exact,
                    'PNG_file_bytes_equal': a['png']['file']['sha256'] == b['png']['file']['sha256'],
                    'controls_exact': a['controls'] == b['controls']}
                exact = exact and geometry_exact and raster_exact and a['controls'] == b['controls']
            result['endpoint_comparison'] = endpoint
            result['endpoint_control_exact'] = exact
    def application_log():
        data, ident = read(child(args.report.parent, 'application.log'))
        result['input_identities']['application_log'] = ident
        check(b'BERN_FILM_LAST_OBSERVATION_ERROR' not in data, 'Diagnostic export error marker present')
        return True
    log_ok = attempt('diagnostic_application_log', application_log)
    if packet is not None and bound and log_ok:
        diag = attempt('diagnostic_schema_sequence', lambda: diagnostic(packet, raw_packet, report, watchdog, locks))
        if diag is not None:
            result['diagnostic_validation'] = diag
            result['diagnostic_valid'] = True
    def capture_cleanup():
        check(report is not None and watchdog is not None and bound, 'Missing bound capture/cleanup evidence')
        for field in ('success', 'collector_success', 'cleanup_success', 'exact_child_cleanup_verified',
                      'ipc_cleanup_verified', 'private_preferences_absent_at_check', 'originals_unchanged',
                      'ownership_bootstrapped_from_exact_child', 'collector_defer_original_front_binding_verified'):
            check(watchdog.get(field) is True, 'Wrapper truth gate false/missing: ' + field)
        check(watchdog.get('collector_exit_code') == 0 and watchdog.get('private_preferences_delete_status') == 0, 'Collector/defaults exit not0')
        check(report.get('success') is True and report.get('app_still_running_after_cleanup') is False
              and report.get('app_termination_status') == 0 and report.get('ipc_removed_by_adapter') is True, 'Collector cleanup truth failed')
        def native_id(value):
            check(type(value) is dict, 'Native identity missing')
            kernel = value['kernel_start']
            integer(value['pid'], 1); integer(kernel['tv_sec'], 1); integer(kernel['tv_usec'])
            check(kernel['tv_usec'] < 1000000, 'Invalid kernel microseconds')
            return {key: value[key] for key in ('pid', 'bundle_id', 'executable_path', 'kernel_start')}
        owned = watchdog['bootstrap_inspect']['own']
        check(owned['collector_pid'] == watchdog['collector_pid'], 'Owned child/collector mismatch')
        check(watchdog['bootstrap_inspect']['success'] is True, 'Bootstrap failed')
        guard = report['kernel_guard_cleanup']
        check(guard['success'] is True and guard['own_instance_still_running'] is False, 'Kernel guard cleanup failed')
        check(native_id(guard['own']) == native_id(owned), 'Kernel-owned instance mismatch')
        original_front = native_id(watchdog['original_front'])
        check(native_id(guard['front_after_restore_before_stop']) == original_front, 'Original kernel front not restored beforestop')
        check(native_id(guard['front_after']) == original_front, 'Collector final front differs')
        outer = watchdog['outer_cleanup']
        check(outer['success'] is True and outer['own'] is None and native_id(outer['front_after']) == original_front, 'Outer cleanup/front failed')
        return True
    result['capture_cleanup_gate'] = attempt('capture_cleanup_gate', capture_cleanup) is True
    def unchanged():
        for ident in result['input_identities'].values():
            read(ident['path'], ident['sha256'], 2 * 1024 * 1024)
        if 'endpoint_comparison' in result:
            for host in ('observer', 'original'):
                for endpoint in result['endpoint_comparison'][host]['states'].values():
                    ident = endpoint['png']['file']
                    read(ident['path'], ident['sha256'], 32 * 1024 * 1024)
        return True
    attempt('inputs_unchanged', unchanged)
    result['diagnostic_interpretation_allowed'] = bool(bound and result['capture_cleanup_gate'] and result['endpoint_control_exact'] and result['diagnostic_valid'] and not result['errors'])
    with (args.output / 'analysis.json').open('x') as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
    return 0 if result['diagnostic_interpretation_allowed'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
