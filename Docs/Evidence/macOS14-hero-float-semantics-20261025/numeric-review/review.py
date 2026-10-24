#!/usr/bin/env python3
"""Independent struct<4H/<4e raw check; no root helper imports or raw copies."""
import collections
import datetime
import hashlib
import json
import math
import struct
import sys
from pathlib import Path

assert len(sys.argv) == 3, 'review.py GEOMETRY_DIRECTORY OUTPUT_DIRECTORY'
ROOT = Path.cwd().resolve()
D = Path(sys.argv[1]).resolve()
OUT = Path(sys.argv[2]).resolve()
assert D != OUT and D not in OUT.parents and not (OUT / 'summary.json').exists()
U16 = struct.Struct('<4H')
F16 = struct.Struct('<4e')
PATCHES = [('white203', 8, 8), ('white812', 136, 8), ('red812', 264, 8),
           ('green812', 392, 8), ('blue812', 520, 8), ('yellow812', 8, 128),
           ('warm812', 136, 128), ('cool812', 264, 128), ('warm406', 392, 128),
           ('pastel812', 520, 128)]
inputs = {}

def fp(path, data=None):
    if data is None: data = path.read_bytes()
    value = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
    inputs[str(path)] = value
    return value

def load(path):
    fp(path)
    return json.loads(path.read_text(), parse_constant=lambda v: (_ for _ in ()).throw(ValueError(v)))

def utc(value):
    return datetime.datetime.fromisoformat(value.replace('Z', '+00:00'))

def mapped(x, y, w, h, width, height):
    values = (x * width, y * height, (x + w) * width, (y + h) * height)
    divisors = (640, 360, 640, 360)
    assert all(n % d == 0 for n, d in zip(values, divisors))
    return tuple(n // d for n, d in zip(values, divisors))

def stats(data, stride, box):
    x0, y0, x1, y1 = box
    hist = [collections.Counter() for _ in range(4)]
    numeric = [dict() for _ in range(4)]
    for y in range(y0, y1):
        for x in range(x0, x1):
            offset = y * stride + x * 8
            words = U16.unpack_from(data, offset)
            values = F16.unpack_from(data, offset)
            for c in range(4):
                hist[c][words[c]] += 1
                numeric[c][words[c]] = values[c]
    count = (x1 - x0) * (y1 - y0)
    channels = {}
    for c, name in enumerate('RGBA'):
        ordered = sorted(hist[c]); h = hist[c]; values = numeric[c]
        finite = [b for b in ordered if math.isfinite(values[b])]
        finite_count = sum(h[b] for b in finite)
        text = [f'0x{b:04x}' for b in ordered]
        channels[name] = {
            'sample_count': count, 'finite_count': finite_count,
            'nan_count': sum(h[b] for b in ordered if math.isnan(values[b])),
            'positive_infinity_count': sum(h[b] for b in ordered if values[b] == math.inf),
            'negative_infinity_count': sum(h[b] for b in ordered if values[b] == -math.inf),
            'finite_numeric_min': min(values[b] for b in finite),
            'finite_numeric_mean': math.fsum(values[b] * h[b] for b in finite) / finite_count,
            'finite_numeric_max': max(values[b] for b in finite),
            'numeric_less_than_zero_count': sum(h[b] for b in ordered if values[b] < 0),
            'numeric_greater_than_one_count': sum(h[b] for b in ordered if values[b] > 1),
            'numeric_equal_one_count': sum(h[b] for b in ordered if values[b] == 1),
            'positive_zero_bits_count': h.get(0, 0), 'negative_zero_bits_count': h.get(0x8000, 0),
            'unique_uint16_bit_pattern_count': len(ordered),
            'first_32_sorted_unique_bits_hex': text[:32],
            'all_unique_bits_hex_if_at_most_64': text if len(text) <= 64 else None,
            'full_bit_histogram_sha256': hashlib.sha256(b''.join(struct.pack('<HI', b, h[b]) for b in ordered)).hexdigest(),
            'histogram_hash_encoding': 'Sorted pairs of uint16LE bits and uint32LE exact count; not a numeric quantization'}
    return {'raw_storage_box_half_open': list(box), 'pixel_count': count, 'RGBA': channels,
            'alpha_all_numeric_exactly_one': hist[3] == {0x3c00: count}, 'alpha_one_uint16_bits': '0x3c00'}

def compact(region):
    fields = ('finite_numeric_min', 'finite_numeric_mean', 'finite_numeric_max',
              'finite_count', 'nan_count', 'positive_infinity_count', 'negative_infinity_count',
              'numeric_less_than_zero_count', 'numeric_greater_than_one_count',
              'unique_uint16_bit_pattern_count', 'full_bit_histogram_sha256')
    return {'box': region['raw_storage_box_half_open'], 'pixels': region['pixel_count'],
            'alpha1': region['alpha_all_numeric_exactly_one'],
            'RGBA': {c: {k: v[k] for k in fields} for c, v in region['RGBA'].items()}}

binding = load(D / 'semantic-binding.json')
execution = load(D / 'known-extraction-execution.json')
geometry = load(D / 'result/geometry.json')
assert binding['independent_geometry_review_passed'] is True and binding['lane_contract_reviewed'] is True
assert binding['geometry_sha256'] == fp(D / 'result/geometry.json')['sha256']
assert binding['geometry_script_sha256'] == fp(D / 'structure.py')['sha256']
for path, expected in binding['review_artifact_hashes'].items(): assert fp(ROOT / path)['sha256'] == expected, path
lane = load(ROOT / 'work/hero-snapshot-float-lane-review/review.json')
geo_review = load(ROOT / 'work/hero-snapshot-float-geometry-independent-review/review.json')
assert geo_review['complete'] is True and geo_review['all4_unique_top_down'] is True
assert utc(lane['recorded_at_utc']) <= utc(binding['created_utc'])
assert utc(geo_review['completed_utc']) <= utc(binding['created_utc'])
assert execution['approval_sha256'] == fp(D / 'semantic-binding.json')['sha256']
assert execution['script_sha256'] == fp(D / 'analyze_float.py')['sha256']
for line in (D / 'PREDECLARED-SHA256SUMS').read_text().splitlines():
    expected, name = line.split('  ', 1)
    assert fp(D / name)['sha256'] == expected, name
fp(D / 'PREDECLARED-SHA256SUMS')
wrapper = (D / 'extract-known.py').read_text(); fp(D / 'extract-known.py')
assert wrapper.index("review['independent_geometry_review_passed']") < wrapper.index('for major in [13,14]')
assert wrapper.index("for name,expected in review['review_artifact_hashes'].items()") < wrapper.index('subprocess.run(args')
assert "review['geometry_sha256']==sha(D/'result/geometry.json')" in wrapper
assert "assert not (D/'known-extraction-execution.json').exists()" in wrapper and 'assert not out.exists()' in wrapper
assert geometry['complete'] is True and geometry['all4_directions_unique'] is True
assert [r['host'] for r in execution['rows']] == [13, 14]
for row in execution['rows']:
    assert row['exit_code'] == 0 and utc(binding['created_utc']) <= utc(row['started_utc']) <= utc(row['finished_utc'])
    assert row['argv'][row['argv'].index('--row-direction') + 1] == 'top-down'
    assert Path(row['argv'][row['argv'].index('--orientation-evidence') + 1]).resolve() == (D / 'result/geometry.json').resolve()
assert utc(execution['rows'][0]['finished_utc']) <= utc(execution['rows'][1]['started_utc'])
spec = load(D / 'atlas-rois.json')
assert spec['source_size'] == [640, 360]
assert [(v['name'], v['interior_source_rect']) for v in spec['patches']] == [
    (n, {'x': x, 'y': y, 'width': 112, 'height': 104}) for n, x, y in PATCHES]
assert spec['ramp']['interior_source_rect'] == {'x': 4, 'y': 260, 'width': 632, 'height': 80}
claimed = load(D / 'constant-patch-comparison.json')
assert claimed['complete'] is True and claimed['geometry_sha256'] == binding['geometry_sha256']
assert claimed['comparator_sha256'] == fp(D / 'compare-patches.py')['sha256']
assert utc(claimed['created_utc']) >= utc(execution['rows'][-1]['finished_utc'])
direct = {}; native_regions = []
for host in (13, 14):
    analysis_path = D / f'host{host}-known/analysis.json'
    a = load(analysis_path)
    assert claimed['inputs'][str(analysis_path.relative_to(D))] == fp(analysis_path)['sha256']
    assert a['analysis_complete'] and a['semantic_patch_values_emitted'] and a['runtime_validation_passed']
    assert a['actual_os_major'] == host and a['row_direction'] == 'top-down'
    assert a['analyzer_sha256'] == execution['script_sha256']
    assert a['independent_orientation_evidence']['sha256'] == binding['geometry_sha256']
    report_path = Path(a['report']); report = load(report_path)
    assert fp(report_path)['sha256'] == a['report_sha256']
    exports = {v['key']: v for v in report['snapshot_float_capture']['records']}
    assert len(a['records']) == 2
    for item in a['records']:
        r = item['raw_record']; key = r['key']
        assert r == exports[key]
        assert {k: r[k] for k in ('bits_per_component','bits_per_pixel','bitmap_info_raw','alpha_info_raw','byte_order_raw','pixel_format_raw','float_components')} == {
            'bits_per_component': 16, 'bits_per_pixel': 64, 'bitmap_info_raw': 4353, 'alpha_info_raw': 1, 'byte_order_raw': 4096, 'pixel_format_raw': 0, 'float_components': True}
        width, height, stride = r['width'], r['height'], r['bytes_per_row']
        assert (width, height) == ((640, 360) if host == 13 else (320, 180))
        assert stride == width * 8 and r['byte_count'] == stride * height
        raw = report_path.parent / r['file']; data = raw.read_bytes()
        assert fp(raw, data) == {'sha256': r['sha256'], 'bytes': r['byte_count']}
        g = next(g for g in geometry['records'] if g['actual_os_major'] == host and g['key'] == key)
        assert g['selected_direction'] == 'top-down' and g['raw_sha256'] == r['sha256']
        assert Path(item['resolved_file']).resolve() == raw.resolve()
        regions = {}
        for name, x, y in PATCHES:
            box = mapped(x, y, 112, 104, width, height)
            value = stats(data, stride, box)
            assert value == item['grounded_direction_patch_and_ramp_statistics'][name], (host, key, name)
            assert value['alpha_all_numeric_exactly_one']
            assert all(v['unique_uint16_bit_pattern_count'] == 1 and v['finite_count'] == value['pixel_count'] for v in value['RGBA'].values())
            regions[name] = value
        ramp = stats(data, stride, mapped(4, 260, 632, 80, width, height))
        assert ramp == item['grounded_direction_patch_and_ramp_statistics']['gray-ramp']
        old_ramp = next(v for v in claimed['native_ramp_aggregate_only'] if v['host'] == host and v['key'] == key)
        assert old_ramp['RGBA'] == ramp['RGBA'] and old_ramp['raw_storage_box_half_open'] == ramp['raw_storage_box_half_open']
        whole = stats(data, stride, (0, 0, width, height))
        assert whole == item['whole_active_pixel_buffer']
        direct[host, key] = regions
        native_regions.append({'host': host, 'key': key, 'raw_sha256': r['sha256'], 'all10_flat_regions_exact': True,
            'all11_region_statistics_exact': True, 'whole_buffer_statistics_exact': True,
            'whole_buffer': compact(whole), 'ramp_native_aggregate_only': compact(ramp)})
        assert fp(raw)['sha256'] == r['sha256']

rows = []
for key in ('baseline-body-named', 'baseline-body-custom'):
    for name, _, _ in PATCHES:
        regions = {h: direct[h, key][name] for h in (13, 14)}
        values = {str(h): {c: v['finite_numeric_mean'] for c, v in r['RGBA'].items()} for h, r in regions.items()}
        bits = {str(h): {c: v['all_unique_bits_hex_if_at_most_64'][0] for c, v in r['RGBA'].items()} for h, r in regions.items()}
        delta = {c: values['13'][c] - values['14'][c] for c in 'RGBA'}
        row = {'key': key, 'patch': name, 'sample_counts': {str(h): r['pixel_count'] for h, r in regions.items()},
            'values': values, 'bits': bits, 'numeric_13_minus_14': delta,
            'same_all_RGBA_bits': bits['13'] == bits['14'], 'same_RGB_bits': all(bits['13'][c] == bits['14'][c] for c in 'RGB'),
            'max_absolute_RGB_numeric_delta': max(abs(delta[c]) for c in 'RGB')}
        assert row == next(v for v in claimed['constant_patches'] if v['key'] == key and v['patch'] == name)
        rows.append(row)
summary = []
for key in ('baseline-body-named', 'baseline-body-custom'):
    sub = [v for v in rows if v['key'] == key]
    summary.append({'key': key, 'constant_patch_count': 10,
        'all_RGBA_bit_identical_patch_count': sum(v['same_all_RGBA_bits'] for v in sub),
        'changed_patches': [v['patch'] for v in sub if not v['same_RGB_bits']],
        'max_absolute_RGB_numeric_delta': max(v['max_absolute_RGB_numeric_delta'] for v in sub),
        'mean_of30_absolute_RGB_numeric_deltas': math.fsum(abs(v['numeric_13_minus_14'][c]) for v in sub for c in 'RGB') / 30})
assert summary == claimed['summary']
result = {'complete': True, 'method': 'Independent fixed coordinates, struct<4H and struct<4e unpack_from each original pixel. No root helper import or pipeline execution.',
    'wrapper_review': {'current_source_prevalidates_binding_and_review_hashes': True, 'receipt_approval_hash_matches_binding': True,
        'saved_reviews_and_binding_precede_all_known_extractions': True, 'two_exits_zero': True,
        'scope': 'Saved hashes, current wrapper ordering and recorded UTC receipt chronology; not independent historical execution attestation.'},
    'constant_patch_summary': summary, 'constant_patches': rows, 'four_raw_statistics_checks': native_regions,
    'scope': 'Original stored premultiplied extended-sRGB binary16 lanes using independently reviewed lane/direction binding. Alpha1. No clamp, unpremultiply, nits/display conversion, fitting/resampling/translation. Ramp only native aggregate; no paired cross-host columns or full-image equality claim.',
    'input_files': inputs, 'not_proven': ['Visible color residual cause', 'Unique OS/renderer cause', 'WindowServer equivalence', 'HDR brightness equivalence', 'UI/product/full-flight acceptance']}
encoded = json.dumps(result, indent=2, sort_keys=True, allow_nan=False) + '\n'
assert len(encoded.encode()) <= 131072
OUT.mkdir(parents=True, exist_ok=True)
(OUT / 'summary.json').write_text(encoded)
print(json.dumps({'complete': True, 'summary': summary, 'all4_whole_buffers_and44_regions_exact': True,
    'inputs': len(inputs), 'bytes': len(encoded.encode())}, sort_keys=True))
