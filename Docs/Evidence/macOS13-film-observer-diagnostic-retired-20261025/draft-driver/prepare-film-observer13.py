#!/usr/bin/env python3
"""One exact-build observer Film copy; original CLI and fixed actual14 data prerequisite, no UI."""
import argparse
import hashlib
import json
import plistlib
import re
import struct
import subprocess
import uuid
from pathlib import Path

SOURCE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
CONTROL_GUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c"
CONTROL_CLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
BUILD_RUN = 40070407306
ARTIFACT_ID = 12550744117
ARCHIVE_SHA256 = "e7ee2c11f7795bf9391b275ec9f6be329feceebf890193ee53434ec0607c3067"
KIND = "film_last_observer13_capture"

OBSERVER_GUI = 'e2fbcea5fdc4cea6ebcfb00e1214e55badd78d82a31ebd248e18971e2f6c39a2'
OBSERVER_MANIFEST_SHA = 'fdb3ff8ca2fc2235531289c98fd5724f1eae816babd9646c83bf74587d86243f'

ALLOWED = {"Contents/Info.plist", "Contents/MacOS/Gallery", "Contents/_CodeSignature/CodeResources"}

# Exact reviewed Mach-O helper logic, read as source; only app basename assertion adapted.
def sha(data):
    return hashlib.sha256(data).hexdigest()


def macho(path):
    raw = path.read_bytes()
    header = struct.unpack_from('<8I', raw)
    assert header[0] == 0xfeedfacf and header[1] == 0x100000c
    sections, segments, signature, offset = [], [], None, 32
    for _ in range(header[4]):
        command, size = struct.unpack_from('<II', raw, offset)
        assert size >= 8 and offset+size <= len(raw)
        if command == 0x1d:
            data_offset, data_size = struct.unpack_from('<II', raw, offset+8)
            signature = dict(command_offset=offset, command_size=size,
                             data_offset=data_offset, data_size=data_size)
        if command == 0x19:
            name = raw[offset+8:offset+24].rstrip(b'\0').decode()
            values = struct.unpack_from('<4Q', raw, offset+24)
            segments.append(dict(name=name, command_offset=offset,
                                 vmaddr=values[0], vmsize=values[1], fileoff=values[2], filesize=values[3]))
            count = struct.unpack_from('<I', raw, offset+64)[0]
            for index in range(count):
                values = struct.unpack_from('<16s16sQQIIIIIIII', raw, offset+72+80*index)
                section, segment, address, length, start = values[:5]
                zero = values[8] & 255 in (1, 0xc, 0x12)
                data = b'' if zero else raw[start:start+length]
                assert zero or len(data) == length
                sections.append(dict(segment=segment.rstrip(b'\0').decode(),
                    section=section.rstrip(b'\0').decode(), address=address, size=length,
                    file_offset=start, zero_fill=zero, sha256=None if zero else sha(data)))
        offset += size
    assert offset == 32+header[5] and signature
    lo = signature['command_offset']; hi = lo+signature['command_size']
    start = signature['data_offset']; end = start+signature['data_size']
    assert hi <= start and end <= len(raw)
    strict = sha(raw[:lo]+raw[hi:start]+raw[end:])
    normalized = bytearray(raw)
    for segment in segments:
        if segment['name'] == '__LINKEDIT':
            n = segment['command_offset']
            normalized[n+32:n+40] = bytes(8)
            normalized[n+48:n+56] = bytes(8)
    return dict(path=str(path), bytes=len(raw), sha256=sha(raw), signature=signature,
        segments=segments, sections=sections,
        signature_command_blob_excluded_sha256=strict,
        signature_storage_sizes_normalized_sha256=sha(normalized[:lo]+normalized[hi:start]+normalized[end:]))


def members(app):
    assert not any(p.is_symlink() for p in app.rglob('*')), 'Unexpected app symlink'
    return {str(p.relative_to(app)): sha(p.read_bytes()) for p in sorted(app.rglob('*')) if p.is_file()}


def app_machos(app):
    result = {}
    for p in sorted(app.rglob('*')):
        if p.is_file():
            with p.open('rb') as stream: magic = stream.read(4)
            if magic == b'\xcf\xfa\xed\xfe': result[str(p.relative_to(app))] = macho(p)
            else: assert magic not in [b'\xfe\xed\xfa\xcf', b'\xca\xfe\xba\xbe', b'\xbe\xba\xfe\xca',
                                      b'\xca\xfe\xba\xbf', b'\xbf\xba\xfe\xca', b'\xce\xfa\xed\xfe', b'\xfe\xed\xfa\xce']
    assert 'Contents/MacOS/Gallery' in result
    return result


REFERENCE14_SHA = '8921655dea0938f76e49cfc808414d3278fce1deabeca1b98f5fd1d5bdfe8f50'
REFERENCE14_RESULT_SHA = '54b06d51178cf8e57d947c2de193f837b36ab0a52fa0e341357f0d6972cba0bf'
REFERENCE14_SOURCE_SHA = '6c4d5c93c9331ba4dd6427aa18799b6a1e720b6e2e006e036fb908ced4f9e635'


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_reference(path):
    path=path.resolve(strict=True)
    assert file_hash(path)==REFERENCE14_SHA
    ref=json.loads(path.read_text())
    assert ref['schema']=='bern_exact_e48_film_first_last14_reference_v1' and ref['reference_data_complete'] is True
    assert ref['source_sha']==SOURCE and ref['gui_sha256']==CONTROL_GUI and ref['cli_sha256']==CONTROL_CLI
    assert ref['build_run']==40070407306 and ref['run_id']==40165343690
    assert ref['harness_sha']=='2cff19aad748ac673fefda921b313886bb902e4b'
    assert ref['collector_source_sha256']==REFERENCE14_SOURCE_SHA
    limits=ref['limits']
    assert limits['termination_or_restored_front_receipt_available'] is False
    assert limits['old_CI_cleanup_order_stop_before_restore'] is True and limits['does_not_satisfy_local13_kernel_cleanup_gate'] is True
    children=[]
    for entry,expected_path,expected_sha in [(ref['raw_result'],'raw/result.json',REFERENCE14_RESULT_SHA),
        (ref['collector_source'],'raw/gallery-film-probe.swift',REFERENCE14_SOURCE_SHA),
        (ref['initial_setup']['png'],'raw/direct-film.png','46ae79801159c1a9b26e6a86225e51bcfc34a667bf215ec94a611c6cfe8b00d8'),
        (ref['first_last']['png'],'raw/direct-last.png','13788694f15e1d1c87111de35daac508c6fa65e7f725ae4639136504013e6522')]:
        assert entry['path']==expected_path and entry['sha256']==expected_sha
        child=(path.parent/entry['path']).resolve(strict=True)
        assert child.is_relative_to(path.parent) and file_hash(child)==expected_sha
        children.append(child)
    raw=json.loads(children[0].read_text())
    assert raw['success'] is True and raw['source_sha']==SOURCE and raw['harness_sha']==ref['harness_sha']
    assert raw['expected_os_major']==14 and raw['requested_scenario']=='direct' and raw['followup_sequence']=='last-resize'
    assert raw['system_preferences']=={'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}
    assert len(raw['cases'])==1
    case=raw['cases'][0]
    assert ref['initial_setup']['capture']==case['film'] and ref['initial_setup']['terminal_ax']==case['settled_ax']
    assert ref['first_last']['stage']=='last' and ref['first_last']['json_pointer']=='/cases/0/followup_stages/0'
    assert case['followup_stages'][0]['stage']=='last'
    assert ref['first_last']['capture']==case['followup_stages'][0]['capture'] and ref['first_last']['terminal_ax']==case['followup_stages'][0]['ax']
    return ref,[path,*children]


def read_observer_manifest(path):
    path = path.resolve(strict=True)
    assert path.is_file() and not path.is_symlink() and file_hash(path) == OBSERVER_MANIFEST_SHA
    value = json.loads(path.read_text())
    assert value['schema'] == 'bern_film_last_observer_build_v1' and value['success'] is True
    assert value['source_sha'] == SOURCE and value['run_id'] == '40176620054'
    assert value['harness_sha'] == '892c392ffec22a10b282e8d27d41386bac5def64'
    assert value['gui'] == {'bytes': 3770800, 'sha256': OBSERVER_GUI}
    assert len(value['app_members']) == 10 and value['app_members']['Contents/MacOS/Gallery'] == value['gui']
    assert value['build']['architecture'] == 'arm64' and value['build']['minimum_macos'] == '13.0'
    assert value['build']['profile'] == 'release' and value['toolchain']['actual_app_embedded_sdk'] == '26.2'
    assert value['generated_actual']['BernRuntime.swift']['sha256'] == 'e38647f3b918e4d0c4c503eb8876889578a35b57efdb8feeaadafaac5a51f663'
    assert value['generated_actual']['BernGenerated.swift']['sha256'] == 'f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653'
    assert value['generated_actual']['BernStyle.swift']['sha256'] == '179b406b1a7246e855ac7634bf225d1680016033fb1044035fb0137399c81e0e'
    return value, path


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--delivery-receipt-sha256", required=True)
    parser.add_argument("--reference14", required=True, type=Path)
    parser.add_argument("--observer-build", required=True, type=Path)
    parser.add_argument("--observer-build-sha256", required=True)
    parser.add_argument("--diagnostic-destination", required=True, type=Path)
    parser.add_argument("observer_app", type=Path)
    parser.add_argument("control_cli", type=Path)
    parser.add_argument("gallery_build_json", type=Path)
    parser.add_argument("fresh_work", type=Path)
    args = parser.parse_args()
    if not args.prepare:
        print("Plan only; explicit --prepare required. No copies, signing, commands, UI or cleanup ran.")
        return 0
    observer, observer_build_path = read_observer_manifest(args.observer_build)
    assert args.observer_build_sha256 == OBSERVER_MANIFEST_SHA
    reference, reference_inputs = read_reference(args.reference14)
    reference_pins = {str(p):file_hash(p) for p in reference_inputs}
    original, cli, build_file = [p.resolve(strict=True) for p in [args.observer_app, args.control_cli, args.gallery_build_json]]
    assert original.is_dir() and cli.is_file() and build_file.is_file()
    build_bytes = build_file.read_bytes(); build = json.loads(build_bytes)
    assert build["source_sha"] == SOURCE and build["build_run"] == "https://github.com/Torrekie/Bern/actions/runs/"+str(BUILD_RUN)
    assert build["artifact_id"] == ARTIFACT_ID and build["archive_sha256"] == ARCHIVE_SHA256
    assert build["executable_sha256"] == CONTROL_GUI and build["cli_sha256"] == CONTROL_CLI
    assert build["architecture"] == "arm64" and build["minimum_macos"] == "13.0" and build["sdk"] == "26.2"
    delivery_file = (build_file.parent / build["delivery_receipt"]).resolve(strict=True)
    assert delivery_file.is_file()
    delivery_bytes = delivery_file.read_bytes()
    assert re.fullmatch(r"[0-9a-f]{64}", args.delivery_receipt_sha256)
    assert sha(delivery_bytes) == args.delivery_receipt_sha256
    delivery = json.loads(delivery_bytes)
    assert delivery["source_sha"] == SOURCE and delivery["build_run"] == BUILD_RUN
    assert delivery["artifact_id"] == ARTIFACT_ID and delivery["archive_sha256"] == ARCHIVE_SHA256
    assert delivery["delivered_gui_sha256"] == CONTROL_GUI and delivery["delivered_cli_sha256"] == CONTROL_CLI
    assert delivery["strict_signatures_after_move"] is True
    assert sha((original / "Contents/MacOS/Gallery").read_bytes()) == OBSERVER_GUI
    assert sha(cli.read_bytes()) == CONTROL_CLI
    original_info = plistlib.loads((original / "Contents/Info.plist").read_bytes())
    assert original_info["CFBundleIdentifier"] == "dev.bern.gallery" and original_info["CFBundleExecutable"] == "Gallery"
    assert original_info["LSMinimumSystemVersion"] == "13.0"
    original_members = members(original)
    observer_rows = observer["app_members"]
    assert original_members == {name: row["sha256"] for name, row in observer_rows.items()}
    assert all((original / name).stat().st_size == row["bytes"] for name, row in observer_rows.items())
    out = args.fresh_work.resolve()
    assert args.diagnostic_destination.is_absolute()
    diagnostic_destination = args.diagnostic_destination.resolve()
    assert diagnostic_destination == out / "diagnostic/film-last-observation.json"
    inputs = [Path(__file__).resolve().parent, original, cli, build_file, delivery_file, observer_build_path.parent, observer_build_path, args.reference14.resolve(strict=True).parent, *reference_inputs]
    assert not out.exists() and all(out != p and out not in p.parents and p not in out.parents for p in inputs), "Output and inputs must not overlap in either direction"
    out.mkdir(parents=True)
    evidence = out / "film"; evidence.mkdir()
    diagnostic_destination.parent.mkdir(mode=0o700)
    assert diagnostic_destination.parent.stat().st_mode & 0o777 == 0o700
    assert not diagnostic_destination.exists() and not diagnostic_destination.is_symlink()
    commands = []
    def command(argv, log):
        result = subprocess.run([str(v) for v in argv], capture_output=True, timeout=30)
        log.write_bytes(result.stdout + result.stderr)
        commands.append({"argv": [str(v) for v in argv], "status": result.returncode, "log": str(log.relative_to(out))})
        assert result.returncode == 0, str(log)
        return result.stdout
    original_machos = app_machos(original)
    original_cli_macho = macho(cli)
    command(["codesign", "--verify", "--deep", "--strict", original], evidence / "original-signature.txt")
    command(["codesign", "--verify", "--strict", cli], evidence / "original-cli-signature.txt")
    for label, binary in [("gui", original / "Contents/MacOS/Gallery"), ("cli", cli)]:
        metadata = command(["xcrun", "vtool", "-show-build", binary], evidence / ("original-"+label+"-build.txt")).decode()
        assert re.findall(r"^\s*minos\s+(\S+)", metadata, re.M) == ["13.0"]
        assert re.findall(r"^\s*sdk\s+(\S+)", metadata, re.M) == ["26.2"]
    app = out / "runtime-work/film/Gallery.app"; app.parent.mkdir(parents=True)
    command(["ditto", original, app], evidence / "copy.txt")
    assert members(app) == original_members
    identifier = "dev.bern.frame13.filmobserver."+uuid.uuid4().hex
    prefs = Path.home() / "Library/Preferences" / (identifier+".plist")
    state = Path.home() / "Library/Saved Application State" / (identifier+".savedState")
    assert not any(p.exists() or p.is_symlink() for p in [prefs, state])
    info = app / "Contents/Info.plist"; old_raw = info.read_bytes(); old_plist = plistlib.loads(old_raw)
    assert old_plist == original_info
    changed_plist = dict(old_plist); changed_plist["CFBundleIdentifier"] = identifier
    info.write_bytes(plistlib.dumps(changed_plist, fmt=plistlib.FMT_BINARY if old_raw.startswith(b"bplist") else plistlib.FMT_XML, sort_keys=False))
    command(["codesign", "--force", "--deep", "--sign", "-", "--identifier", identifier, app], evidence / "resign.txt")
    command(["codesign", "--verify", "--deep", "--strict", app], evidence / "signature.txt")
    private_members = members(app); private_machos = app_machos(app)
    assert original_members.keys() == private_members.keys() and original_machos.keys() == private_machos.keys()
    changed = [name for name in original_members if original_members[name] != private_members[name]]
    assert set(changed) <= ALLOWED
    assert plistlib.loads(info.read_bytes()) == changed_plist
    for name, before in original_machos.items():
        assert before["sections"] == private_machos[name]["sections"]
        assert before["signature_storage_sizes_normalized_sha256"] == private_machos[name]["signature_storage_sizes_normalized_sha256"]
    assert members(original) == original_members and sha(cli.read_bytes()) == CONTROL_CLI
    assert build_file.read_bytes() == build_bytes and delivery_file.read_bytes() == delivery_bytes
    assert file_hash(observer_build_path) == OBSERVER_MANIFEST_SHA
    assert all(file_hash(Path(name))==h for name,h in reference_pins.items())
    receipt = {"reference14":str(args.reference14.resolve(strict=True)),"reference14_sha256":REFERENCE14_SHA,"kind": KIND, "source_sha": SOURCE, "original_app": str(original), "private_app": str(app),
        "private_bundle_id": identifier, "original_gui_sha256": OBSERVER_GUI,
        "private_gui_sha256": sha((app / "Contents/MacOS/Gallery").read_bytes()),
        "changed_members": changed, "original_members": original_members, "private_members": private_members,
        "original_machos": original_machos, "private_machos": private_machos, "original_cli_macho": original_cli_macho,
        "sections_and_signature_storage_sizes_normalized_equal": True, "whole_GUI_bytes_equal": False,
        "originals_unchanged": True, "cli": str(cli), "cli_sha256": CONTROL_CLI,
        "preferences_path": str(prefs), "saved_state_path": str(state),
        "delivery_receipt": str(delivery_file), "delivery_receipt_sha256": sha(delivery_bytes),
        "gallery_build_json": str(build_file), "gallery_build_json_sha256": sha(build_bytes),
        "observer_build_manifest": str(observer_build_path), "observer_build_manifest_sha256": OBSERVER_MANIFEST_SHA,
        "observer_source_app_sha256": OBSERVER_GUI, "diagnostic_destination": str(diagnostic_destination)}
    receipt_file = evidence / "isolation.json"
    receipt_file.write_text(json.dumps(receipt, indent=2)+"\n")
    film = {"app": str(app), "cli": str(cli), "bundle_id": identifier,
        "private_gui_sha256": receipt["private_gui_sha256"], "original_gui_sha256": OBSERVER_GUI,
        "cli_sha256": CONTROL_CLI, "receipt": str(receipt_file)}
    locks = {"schema": "bern_film_last_observer13_locks_v1", "kind": KIND, "source_sha": SOURCE,
        "film": film, "reference14":str(args.reference14.resolve(strict=True)), "reference14_sha256":REFERENCE14_SHA, "delivery_receipt": str(delivery_file), "delivery_receipt_sha256": sha(delivery_bytes),
        "gallery_build_json": str(build_file), "gallery_build_json_sha256": sha(build_bytes), "commands": commands,
        "observer_build_manifest": str(observer_build_path), "observer_build_manifest_sha256": OBSERVER_MANIFEST_SHA,
        "observer_source_app_sha256": OBSERVER_GUI, "diagnostic_destination": str(diagnostic_destination),
        "scope": "Private actual401766 observer Film first-Last preparation only; original CLI31a and fixed actual14 data prerequisite, no strong14 cleanup claim, no UI. Source observer App e2fb and delivered CLI unchanged. Private CFID/signature bytes alone may change; every Mach-O section and normalized non-signature byte verified. Fresh diagnostic destination is separate from capture/cleanup truth. Not visual or diagnostic acceptance."}
    (out / "locks.json").write_text(json.dumps(locks, indent=2)+"\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
