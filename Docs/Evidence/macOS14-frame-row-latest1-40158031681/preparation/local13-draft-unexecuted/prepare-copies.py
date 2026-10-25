#!/usr/bin/env python3
"""Private Gallery copies only. No actions unless --prepare; never launches UI."""
import argparse
import hashlib
import json
import plistlib
import struct
import subprocess
import uuid
from pathlib import Path

SOURCE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
CONTROL_GUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c"
CONTROL_CLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
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


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--prepare", action="store_true")
    parser.add_argument("--observer-build-sha256", required=True)
    parser.add_argument("control_app", type=Path)
    parser.add_argument("control_cli", type=Path)
    parser.add_argument("observer_app", type=Path)
    parser.add_argument("observer_cli", type=Path)
    parser.add_argument("observer_build_json", type=Path)
    parser.add_argument("fresh_work", type=Path)
    args = parser.parse_args()
    if not args.prepare:
        print("Plan only; explicit --prepare required. No copies, signing, commands, UI or cleanup ran.")
        return 0
    inputs = [p.resolve(strict=True) for p in [args.control_app,args.control_cli,args.observer_app,args.observer_cli,args.observer_build_json]]
    control_app,control_cli,observer_app,observer_cli,build_file = inputs
    assert sha(build_file.read_bytes()) == args.observer_build_sha256
    build = json.loads(build_file.read_text())
    assert build["success"] is True and build["source_sha"] == SOURCE
    assert build["build"]["ui"] == "swiftui-modern" and build["build"]["minimum_macos"] == "13.0"
    binaries = build["binaries"]
    observer_gui_hash = binaries["Gallery.app/Contents/MacOS/Gallery"]["sha256"]
    observer_cli_hash = binaries["bin/gallery"]["sha256"]
    assert sha((control_app/"Contents/MacOS/Gallery").read_bytes()) == CONTROL_GUI
    assert sha(control_cli.read_bytes()) == CONTROL_CLI
    assert sha((observer_app/"Contents/MacOS/Gallery").read_bytes()) == observer_gui_hash
    assert sha(observer_cli.read_bytes()) == observer_cli_hash
    out = args.fresh_work.resolve()
    assert not out.exists() and all(out != p and out not in p.parents and p not in out.parents for p in inputs), 'Output and inputs must not overlap in either direction'
    out.mkdir(parents=True)
    commands=[]; groups={}
    def command(argv,log):
        result=subprocess.run([str(v) for v in argv],capture_output=True,timeout=30)
        log.write_bytes(result.stdout+result.stderr)
        commands.append({"argv":[str(v) for v in argv],"status":result.returncode,"log":str(log.relative_to(out))})
        assert result.returncode==0, str(log)
    for side,original,cli,expected_gui,expected_cli in [("control",control_app,control_cli,CONTROL_GUI,CONTROL_CLI),("observer",observer_app,observer_cli,observer_gui_hash,observer_cli_hash)]:
        evidence=out/side;evidence.mkdir()
        original_members=members(original); original_machos=app_machos(original)
        command(["codesign","--verify","--deep","--strict",original],evidence/"original-signature.txt")
        command(["codesign","--verify","--strict",cli],evidence/"original-cli-signature.txt")
        app=out/"runtime-work"/side/"Gallery.app";app.parent.mkdir(parents=True)
        command(["ditto",original,app],evidence/"copy.txt")
        assert members(app)==original_members
        identifier="dev.bern.frame13."+side+"."+uuid.uuid4().hex
        prefs=Path.home()/"Library/Preferences"/(identifier+".plist")
        state=Path.home()/"Library/Saved Application State"/(identifier+".savedState")
        assert not any(p.exists() or p.is_symlink() for p in [prefs,state])
        info=app/"Contents/Info.plist";old_raw=info.read_bytes();old_plist=plistlib.loads(old_raw)
        assert old_plist["CFBundleIdentifier"]=="dev.bern.gallery" and old_plist["CFBundleExecutable"]=="Gallery"
        changed_plist=dict(old_plist);changed_plist["CFBundleIdentifier"]=identifier
        info.write_bytes(plistlib.dumps(changed_plist,fmt=plistlib.FMT_BINARY if old_raw.startswith(b"bplist") else plistlib.FMT_XML,sort_keys=False))
        command(["codesign","--force","--deep","--sign","-","--identifier",identifier,app],evidence/"resign.txt")
        command(["codesign","--verify","--deep","--strict",app],evidence/"signature.txt")
        private_members=members(app);private_machos=app_machos(app)
        assert original_members.keys()==private_members.keys() and original_machos.keys()==private_machos.keys()
        changed=[name for name in original_members if original_members[name]!=private_members[name]]
        assert set(changed)<=ALLOWED
        assert plistlib.loads(info.read_bytes())==changed_plist
        for name,before in original_machos.items():
            assert before["sections"]==private_machos[name]["sections"]
            assert before["signature_storage_sizes_normalized_sha256"]==private_machos[name]["signature_storage_sizes_normalized_sha256"]
        assert members(original)==original_members and sha(cli.read_bytes())==expected_cli
        receipt={"variant":side,"source_sha":SOURCE,"original_app":str(original),"private_app":str(app),"private_bundle_id":identifier,"original_gui_sha256":expected_gui,"private_gui_sha256":sha((app/"Contents/MacOS/Gallery").read_bytes()),"changed_members":changed,"original_members":original_members,"private_members":private_members,"original_machos":original_machos,"private_machos":private_machos,"sections_and_signature_storage_sizes_normalized_equal":True,"whole_GUI_bytes_equal":False,"originals_unchanged":True,"cli":str(cli),"cli_sha256":expected_cli,"preferences_path":str(prefs),"saved_state_path":str(state)}
        (evidence/"isolation.json").write_text(json.dumps(receipt,indent=2)+"\n")
        groups[side]={"app":str(app),"cli":str(cli),"bundle_id":identifier,"private_gui_sha256":receipt["private_gui_sha256"],"original_gui_sha256":expected_gui,"cli_sha256":expected_cli,"receipt":str(evidence/"isolation.json")}
    locks={"schema":"bern_frame_row_local13_locks_v1","source_sha":SOURCE,"groups":groups,"observer_build_receipt":str(build_file),"observer_build_sha256":args.observer_build_sha256,"commands":commands,"scope":"Private preparation only; no UI. Original artifacts unchanged; only private Info.plist CFBundleIdentifier/signature bytes differ; every Mach-O section and normalized non-signature byte verified."}
    (out/"locks.json").write_text(json.dumps(locks,indent=2)+"\n")
    return 0


if __name__=="__main__":
    raise SystemExit(main())
