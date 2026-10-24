#!/usr/bin/env python3
"""Read-only native/static report verification; no image decoding or native commands."""
import ast
import hashlib
import json
import math
import re
import struct
import sys
from pathlib import Path

assert len(sys.argv) == 3, 'analyze.py FIXTURE OUTPUT_DIRECTORY'
FIXTURE = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
assert FIXTURE != OUT and FIXTURE not in OUT.parents
assert not (OUT / 'summary.json').exists(), 'Refuse to overwrite summary'
BINARY_SHA = '514079a0f294f1bc47e761e37b281f7d18271c9ecae6ab31e1b1f416f8679f1b'
PINS = {'source-provenance.json': '1bee2d61a3769e95d661ec93c9520f1853a38c8f5a66120131a89b609d32cdce',
        'build.py': 'f3099b66b8bf1cae06e1e440f297911742c61c974616e38495c760911bd84ae1',
        'run-one.py': '565f6246c70325bcb37ed2a3bc97394a430103be7290aa623c5150ceb4cf7025'}
inputs = {}

def fingerprint(path):
    data = path.read_bytes()
    value = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    inputs[str(path)] = value
    return value

def load(path):
    fingerprint(path)
    return json.loads(path.read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

def digest(value):
    assert isinstance(value, str) and len(value) == 64 and set(value) <= set('0123456789abcdef')

def number(value):
    assert type(value) in (int, float) and math.isfinite(value)

def rect(value):
    assert isinstance(value, dict) and set(value) == {'x', 'y', 'width', 'height'}
    for n in value.values(): number(n)
    assert value['width'] > 0 and value['height'] > 0

def near(value, wanted):
    rect(value)
    assert max(abs(value[k] - wanted[k]) for k in wanted) <= 1e-6

for name, expected in PINS.items():
    assert fingerprint(FIXTURE / name)['sha256'] == expected, name
for name in ('build.py', 'run-one.py'):
    ast.parse((FIXTURE / name).read_text(), filename=name)
source = load(FIXTURE / 'source-provenance.json')
assert source['kind'] == 'local_static_same_snapshot_stock_nsimageview'
assert source['diagnostic_only'] is True and source['product_changes'] is False
assert source['target'] == 'arm64-apple-macos13.0'
for name, meta in source['source_files'].items():
    assert fingerprint(FIXTURE / name) == meta, name
assert b'\n'.join((FIXTURE / name).read_bytes() for name in source['assembly']) == (FIXTURE / 'ProductHero.swift').read_bytes()
driver = (FIXTURE / 'Driver.swift.inc').read_text()
helper = (FIXTURE / 'NativeDisplay.swift.inc').read_text()
wrapper = (FIXTURE / 'run-one.py').read_text()
assert 'assert not out.exists();out.mkdir()' in wrapper
assert 'p.wait(timeout=15)' in wrapper and 'except subprocess.TimeoutExpired:p.kill()' in wrapper
assert 'try? JSONSerialization.data(withJSONObject: report' in driver
assert 'Refuse to overwrite existing report' not in driver
save = driver[driver.index('private func fixtureSavePNG'):driver.index('@MainActor private func fixtureLedger')]
assert 'fileExists' not in save
assert '.write(to: output.appendingPathComponent("hard-deadline.txt"))' in driver and '_exit(124)' in driver
assert driver.index('window?.orderOut(nil)') < driver.index('FixtureNativeDisplay.cleanup()') < driver.index('for flight in fixtureOwnedOverlayFlights')
assert 'type(of: view) == NSImageView.self' in helper and 'view.image === image' in helper
for forbidden in ('dataProvider', 'cgImage(', 'tiffRepresentation', 'bitmapImageRepForCachingDisplay', 'CIContext'):
    assert forbidden not in helper, forbidden

build = load(FIXTURE / 'build-fingerprint.json')
assert build['exit_code'] == 0 and build['binary_sha256'] == BINARY_SHA
assert build['source_provenance_sha256'] == PINS['source-provenance.json']
assert fingerprint(FIXTURE / 'build.log')['sha256'] == build['build_log_sha256']
binary = FIXTURE / 'HeroNativeDisplayProbe'
assert fingerprint(binary) == {'sha256': BINARY_SHA, 'bytes': build['binary_bytes']}
assert all(value['exit_code'] == 0 for value in build['environment'].values())
assert build['environment']['arch']['output'].strip() == 'arm64'
assert build['environment']['sdk']['output'].strip() == '14.2'
assert 'Apple Swift version 5.9.2' in build['environment']['swift']['output']
assert re.search(r'ProductVersion:\s+13\.', build['environment']['os']['output'])
assert build['argv'][build['argv'].index('-target') + 1] == 'arm64-apple-macos13.0'
assert build['argv'][build['argv'].index('-swift-version') + 1] == '5'
assert all(value['exit_code'] == 0 for value in build['checks'].values())
assert 'arm64' in build['checks']['file']['output']
assert re.search(r'^\s*minos 13\.0\s*$', build['checks']['mach_build']['output'], re.M)
assert re.search(r'^\s*sdk 14\.2\s*$', build['checks']['mach_build']['output'], re.M)
assert build['checks']['codesign_verify']['argv'] == ['codesign', '--verify', '--strict', str(binary)]
sdk = Path(build['environment']['sdk_path']['output'].strip())
headers = sdk / 'System/Library/Frameworks/AppKit.framework/Headers'
cell = headers / 'NSCell.h'; image_cell = headers / 'NSImageCell.h'
fingerprint(cell); fingerprint(image_cell)
assert re.search(r'NSImageScaleProportionallyDown = 0,[^\n]*\n\s*NSImageScaleAxesIndependently,', cell.read_text())
assert 'NSImageFrameNone = 0,' in image_cell.read_text()

roles = {'body-named': (16, 24), 'body-custom': (352, 24), 'oracle-top': (688, 24),
         'flight-named': (16, 244), 'flight-custom': (352, 244), 'oracle-bottom': (688, 244)}
local_bounds = {'x': 0, 'y': 0, 'width': 320, 'height': 180}
processes = {}
for mode in ('control', 'image-view'):
    directory = FIXTURE / ('runtime13-' + mode)
    d = load(directory / 'report.json'); receipt = load(directory / 'run-receipt.json')
    assert receipt['mode'] == mode and receipt['exit_code'] == 0 and not receipt.get('wrapper_timeout', False)
    assert receipt['timeout_seconds'] == 15 and 0 < receipt['elapsed_seconds'] < 15
    assert receipt['fresh_output_directory'] is True
    assert receipt['binary_sha256'] == receipt['binary_sha256_after'] == BINARY_SHA
    assert receipt['command'] == list(map(str, [binary, FIXTURE / 'assets/source-named-pq.png', FIXTURE / 'assets/source-ffb-icc.png', directory]))
    assert receipt['environment'] == {'BERN_HERO_NATIVE_DISPLAY': mode, 'BERN_HERO_FLOAT_CAPTURE': 'off',
           'BERN_HERO_LAYER_OBSERVE': 'off', 'BERN_HERO_STATIC_ROUTE': 'overlay', 'BERN_HERO_EXPECT_OS': '13'}
    assert set(receipt['output_files']) == {'report.json', 'runtime.log', 'progress-0.png', 'progress-1.png'}
    for name, meta in receipt['output_files'].items(): assert fingerprint(directory / name) == meta, name
    assert {f.name for f in directory.iterdir()} == set(receipt['output_files']) | {'run-receipt.json'}
    assert d['success'] is True and d.get('error') is None
    assert d['actual_os_major'] == d['expected_os_major'] == 13 and d['activation_calls'] == 0
    assert d['product_head'] == 'b08db54e01ac2ec54fb84e6f2a70041f1f4c3604'
    assert d['collection_seconds'] == 7.2 and d['watchdog_seconds'] == 7.9 and 0 < d['window_seconds'] < 7.9
    assert d['completed_phases'] == 2 and d['image_equality_collection_gate'] is False
    assert d['metal_count_before_cleanup'] == 0
    assert d['frontmost_before'] == d['frontmost_after'] and d['frontmost_before'] != receipt['own_pid']
    for key in ('normal_before', 'normal_after'):
        assert set(d[key]) == {'reduce_motion', 'reduce_transparency', 'increase_contrast'}
        assert all(v is False for v in d[key].values())
    assert d['cache_unchanged'] is True and d['cache_before'] == d['cache_after']
    for name in ('source-named-pq.png', 'source-ffb-icc.png'):
        assert d['cache_before'][name]['file_sha256'] == source['source_files']['assets/' + name]['sha256']
        assert d['cache_before'][name]['orientation'] == 'up'
    assert d['static_route'] == {'requested': 'overlay', 'selected': 'overlay', 'backing_and_float_modes_required_off': True}
    backing = d['backing_observation']
    assert backing['requested'] == backing['selected'] == 'off' and backing['success'] is True and backing['error'] is None
    assert backing['records'] == [] and backing['root'] is None and backing['overlay'] is None
    floating = d['snapshot_float_capture']
    assert floating['requested'] == floating['selected'] == 'off' and floating['success'] is True and floating['error'] is None
    for key in ('provider_copy_calls', 'retained_primary_peak_count', 'fixture_retained_images_after_export', 'total_raw_bytes'):
        assert floating[key] == 0
    assert floating['records'] == [] and floating['primary_observation_count'] == 2
    assert floating['primary_observation_keys'] == ['baseline-body-named', 'baseline-body-custom']
    captures = d['captures']; assert [c['phase'] for c in captures] == ['progress-0', 'progress-1']
    window_id = captures[0]['window_id']; assert type(window_id) is int and window_id > 0
    samples = d['samples']; assert samples and {s['phase'] for s in samples} == {'progress-0', 'progress-1'}
    for sample in samples:
        assert sample['window_id'] == window_id and sample['owner_pid'] == receipt['own_pid']
        assert sample['key'] is False and sample['active'] is False and sample['live_metal_count'] == 0
        assert sample['frontmost_pid'] == d['frontmost_before'] and sample['window_frame'] == captures[0]['window_frame']
        assert sample['manager']['flight_count'] == 0 and sample['manager']['timer_exists'] is False
        assert sample['manager']['overlay_attached'] is True
        assert sample['manager']['entries'] == {'baseline-body-named': ['baseline-body-named'], 'baseline-body-custom': ['baseline-body-custom']}
        digest(sample['raw_buffer_sha256'])
    for capture in captures:
        assert capture['png'] == capture['phase'] + '.png'
        assert fingerprint(directory / capture['png'])['sha256'] == capture['png_sha256']
        png = (directory / capture['png']).read_bytes()
        assert png[:8] == b'\x89PNG\r\n\x1a\n' and png[12:16] == b'IHDR'
        assert list(struct.unpack('>II', png[16:24])) == capture['capture_size']
        trace = [s for s in samples if s['phase'] == capture['phase']]
        assert len(trace) >= 5 and capture['consecutive_equal_buffers'] >= 5
        assert all(s['raw_buffer_sha256'] == capture['raw_buffer_sha256'] for s in trace[-5:])
        assert all(capture[k] == v for k, v in trace[-1].items())
        assert set(capture['rois']) == set(roles)
        for role, (x, y) in roles.items():
            near(capture['rois'][role]['host_top_left_points'], {'x': x, 'y': y, 'width': 320, 'height': 180})
            pixels = capture['rois'][role]['screenshot_pixels']; rect(pixels)
            assert pixels['x'] >= 0 and pixels['y'] >= 0
            assert pixels['x'] + pixels['width'] <= capture['capture_size'][0]
            assert pixels['y'] + pixels['height'] <= capture['capture_size'][1]
    assert captures[0]['rois'] == captures[1]['rois']
    for key in ('static_route_mount', 'static_route_post_png'):
        records = d[key]; assert [r['role'] for r in records] == ['flight-named', 'flight-custom']
        for record in records:
            role = record['role']; x, y = roles[role]
            wanted = {'x': x, 'y': y, 'width': 320, 'height': 180}
            near(record['desired_root_rect'], wanted); near(record['back_converted_root_rect'], wanted)
            near(record['back_converted_root_rect'], captures[0]['rois'][role]['host_top_left_points'])
            number(record['roundtrip_max_error_points']); assert 0 <= record['roundtrip_max_error_points'] <= 1e-6
            rect(record['frame_in_selected_parent'])
            assert record['window_number'] == window_id and record['parent_is_selected_route'] is True
            assert record['flight_subtree_metal_count'] == 0
    native = d['native_display']
    assert native['requested'] == native['selected'] == mode and native['target'] == 'flight-named'
    assert native['static_route_required'] == 'overlay' and native['success'] is True and native['error'] is None
    if mode == 'control':
        assert native['records'] == [] and native['cleanup'] == {'attempted': False}
    else:
        records = native['records']
        assert [r['stage'] for r in records] == ['mounted', 'post_progress_0_png', 'post_progress_1_png', 'post_final_guards']
        for key in ('child_identity', 'flight_identity', 'image_identity'):
            assert isinstance(records[0][key], str) and records[0][key]
            assert all(r[key] == records[0][key] for r in records)
        for record in records:
            assert record['child_class'] == 'NSImageView' and record['target'] == 'flight-named'
            for key in ('child_frame', 'child_bounds', 'flight_bounds'): near(record[key], local_bounds)
            assert record['nsimage_size'] == [320, 180] and record['window_number'] == window_id
            for key in ('parent_is_original_flight', 'flight_parent_is_existing_overlay', 'same_from_to_image', 'skip_original_draw'):
                assert record[key] is True
            assert record['image_scaling_raw'] == 1 and record['image_frame_style_raw'] == 0
            assert record['animates'] is False and record['flight_subtree_metal_count'] == 0
        cleanup = native['cleanup']
        assert cleanup['stage'] == 'after_orderOut_before_original_flight_removal'
        for key in ('attempted', 'child_image_assigned_nil', 'child_image_is_nil', 'child_superview_is_nil', 'helper_weak_refs_cleared'):
            assert cleanup[key] is True
        assert cleanup['scope'] == 'Only fixture child detachment and helper weak refs; not all NSImage deallocation'
    processes[mode] = {'native_verification': 'PASS', 'own_pid': receipt['own_pid'], 'binary_sha256': BINARY_SHA,
        'wrapper_elapsed_seconds': receipt['elapsed_seconds'], 'window_seconds': d['window_seconds'],
        'frontmost_before': d['frontmost_before'], 'frontmost_after': d['frontmost_after'],
        'normal_before': d['normal_before'], 'normal_after': d['normal_after'], 'cache_unchanged': d['cache_unchanged'],
        'sample_count': len(samples), 'captures': captures, 'native_display': native,
        'static_route_mount': d['static_route_mount'], 'static_route_post_png': d['static_route_post_png'],
        'float_provider_reads': floating['provider_copy_calls'], 'float_retained_peak': floating['retained_primary_peak_count'],
        'backing_records': backing['records'], 'pixel_analysis': 'NOT PERFORMED'}

result = {'success': True, 'scope': 'Offline static/native report and byte-hash verification only; no pixel decoding/comparison, native process, compiler, signing, CI or product/source edits.',
    'binary_sha256': BINARY_SHA, 'build_saved_checks': build['checks'], 'build_environment': build['environment'],
    'source_members_verified': len(source['source_files']), 'source_assembly_exact': True,
    'raw_hash_scope': 'PNG file bytes independently hashed; WindowServer raw-buffer hashes and five-equal sequence checked for report consistency only; no raw capture buffers exported or independently decoded.',
    'known_boundaries': ['Binary itself does not reject existing report/PNG paths; pinned wrapper requires a fresh absent output directory.',
        'Report finalization uses try? and may suppress write errors; this verifier instead requires fresh receipt/report/output hashes and exit0.',
        'Hard watchdog writes a separate marker with try? and _exit124 bypasses defer/report cleanup; both present runs exited0 without marker. Failure-path cleanup was not exercised.',
        'NativeDisplay helper reads no snapshot pixels/providers; inherited harness still reads WindowServer screenshot buffers.',
        'Static manual progress0/1 and stock NSImageView are not actual coordinator flight/lifecycle or pixel/color acceptance.',
        'Cleanup proves fixture-child detach/image=nil/helper weak-ref clearing, not all NSImage deallocation.'],
    'processes': processes, 'input_files': inputs, 'pixel_analysis': 'NOT PERFORMED'}
encoded = json.dumps(result, indent=2, sort_keys=True) + '\n'
assert len(encoded.encode()) <= 98304
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'summary.json').write_text(encoded)
print(json.dumps({'success': True, 'native': {k: v['native_verification'] for k, v in processes.items()},
    'binary_sha256': BINARY_SHA, 'source_members': len(source['source_files']), 'inputs': len(inputs),
    'summary_bytes': len(encoded.encode()), 'pixel_analysis': 'NOT PERFORMED'}, sort_keys=True))
