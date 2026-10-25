#!/usr/bin/env python3
"""One actual candidate private copy; real build and successful14 color gate required."""
import argparse
import hashlib
import json
import plistlib
import re
import struct
import subprocess
import uuid
from pathlib import Path

SOURCE = "ce462b3ef5d11b72d51ddf9158940d686bc7707a"
BASELINE = "e48fff46b3a92a28465ad74295bd273a9d69af7d"
KIND = "split_label_color_candidate13_capture"
LOCKS_SCHEMA = "bern_split_label_color_candidate13_locks_v1"
ORIGINAL_GUI = "d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c"
ORIGINAL_CLI = "31a75c0a6900d0df821c5d45f69e3a7ddc25e87e4437db023fc4fc0454f379f5"
CI_CAPTURE_SOURCE = "fa850da24c63d6f8a543808b59ff07d5a5535d718ef2fec949b99df6f8dc9b69"
CI_GATE_SOURCE = "f8a3f035a357a211f86ba5ca70774745324db5e1778f5a7644384fc95978a618"
STYLE_SOURCE = "8219c50ec45a81eb7516b63bddbc7541211006c1a09f0069a93390707c0c6df0"
GENERATED_SOURCE = "f72cb1c6082575df75f21aa994bee5301d037046c9ca253a71a905aae6ef1653"
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


def file_hash(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read_contract(build_path, build_sha, gate_path, gate_sha, control_path, candidate_path):
    for value in [build_sha,gate_sha]:
        assert re.fullmatch(r"[0-9a-f]{64}",value), "Root-reviewed actual digest required"
    build_path,gate_path,control_path,candidate_path = [p.resolve(strict=True) for p in [build_path,gate_path,control_path,candidate_path]]
    assert file_hash(build_path)==build_sha and file_hash(gate_path)==gate_sha
    manifest=json.loads(build_path.read_text());gate=json.loads(gate_path.read_text())
    assert manifest['schema']=='bern_split_label_color_build_v1' and manifest['success'] is True
    assert manifest['source_sha']==SOURCE and manifest['baseline_sha']==BASELINE
    assert re.fullmatch(r"[0-9]+",manifest['run_id']) and re.fullmatch(r"[0-9a-f]{40}",manifest['harness_sha'])
    assert manifest['compiled_style_sha256']==STYLE_SOURCE and manifest['compiled_generated_sha256']==GENERATED_SOURCE
    plan=manifest['build']
    assert plan['ui']=='swiftui-modern' and plan['minimum_macos']=='13.0' and plan['architecture']=='arm64'
    assert plan['app_bundle']=='Gallery.app' and plan['profile']=='release'
    gui=manifest['binaries']['Gallery.app/Contents/MacOS/Gallery'];cli=manifest['binaries']['bin/gallery']
    capture=manifest['helpers']['FrameColorCapture'];gate_helper=manifest['helpers']['FrameColorGate']
    for entry in [gui,cli,capture,gate_helper]:
        assert re.fullmatch(r"[0-9a-f]{64}",entry['sha256']) and type(entry['bytes']) is int and entry['bytes']>0
    assert capture['source_sha256']==CI_CAPTURE_SOURCE and gate_helper['source_sha256']==CI_GATE_SOURCE
    assert gate['kind']=='split_label_color14_no_effect' and gate['success'] is True
    assert gate['frame_detail']['equal'] is True and gate['frame_detail']['changed_pixels']==0
    assert gate['frame_roi_points']==[211,52,920,668]
    assert gate['build_manifest_sha256']==build_sha and gate['ci_run_id']==manifest['run_id'] and gate['harness_sha']==manifest['harness_sha']
    assert gate['collector_executable_sha256']==capture['sha256'] and gate['gate_executable_sha256']==gate_helper['sha256']
    inputs=[build_path,gate_path,control_path,candidate_path]
    for side,path,source,expected_gui,expected_cli in [
        ('control',control_path,BASELINE,ORIGINAL_GUI,ORIGINAL_CLI),
        ('candidate',candidate_path,SOURCE,gui['sha256'],cli['sha256'])]:
        assert file_hash(path)==gate[side+'_report_sha256']
        row=json.loads(path.read_text())
        assert row['success'] is True and row['source_sha']==source and row['label']==side
        assert row['expected_os']==14 and re.match(r"^Version 14\.",row['os'])
        assert row['ci_run_id']==manifest['run_id'] and row['harness_sha']==manifest['harness_sha']
        assert row['collector_executable_sha256']==capture['sha256']
        assert row['app_executable_sha256']==expected_gui and row['cli_sha256']==expected_cli
        assert row['closed_only'] is True and row['row_ledger_enabled'] is False
        assert not any(k.startswith('row_ledger') and k!='row_ledger_enabled' for k in row)
        assert row['app_still_running_after_cleanup'] is False and row['app_termination_status']==0
        assert row['deadline_seconds']==75 and row['heartbeat_ci_only'] is True and row['heartbeat_mode']=='ci-own-active'
        assert row['system_preferences']=={'increase_contrast':False,'reduce_motion':False,'reduce_transparency':False}
        context=row['final_context']
        assert context['appearance']=='Light' and context['caption'] is True and context['volume']=='closed' and context['video']=='Paused0'
        assert row['bundled_tides_sha256']=='145a1b5e572bd3ce16207e2b341c0eecb04b4d1e765bf72f5fe3809a24f34957'
        assert len(row['captures'])==1
        shot=row['captures'][0]
        assert shot['png']=='frame-closed-light.png' and shot['stable_equal_comparisons']>=4 and shot['samples']>=5
        assert shot['canvas_screen_top_left_points']['width']==920 and shot['canvas_screen_top_left_points']['height']==668
        assert shot['icc_sha256']==gate['icc_sha256']
        png=(path.parent/shot['png']).resolve(strict=True)
        assert file_hash(png)==shot['png_sha256']==gate[side+'_png_sha256']
        inputs.append(png)
    return manifest,gate,gui,cli,inputs


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepare',action='store_true')
    parser.add_argument('--build-manifest-sha256',required=True)
    parser.add_argument('--color14-gate',required=True,type=Path)
    parser.add_argument('--color14-gate-sha256',required=True)
    parser.add_argument('--control14-report',required=True,type=Path)
    parser.add_argument('--candidate14-report',required=True,type=Path)
    parser.add_argument('candidate_app',type=Path)
    parser.add_argument('candidate_cli',type=Path)
    parser.add_argument('build_manifest',type=Path)
    parser.add_argument('fresh_work',type=Path)
    args=parser.parse_args()
    if not args.prepare:
        print('Draft plan only; no actual build/gate identity assumed and no preparation executed.')
        return 0
    original,cli,build_file=[v.resolve(strict=True) for v in [args.candidate_app,args.candidate_cli,args.build_manifest]]
    assert original.is_dir() and cli.is_file() and build_file.is_file()
    manifest,gate,gui_entry,cli_entry,contract_inputs=read_contract(build_file,args.build_manifest_sha256,args.color14_gate,args.color14_gate_sha256,args.control14_report,args.candidate14_report)
    gui_sha,cli_sha=gui_entry['sha256'],cli_entry['sha256']
    assert sha((original/'Contents/MacOS/Gallery').read_bytes())==gui_sha and (original/'Contents/MacOS/Gallery').stat().st_size==gui_entry['bytes']
    assert sha(cli.read_bytes())==cli_sha and cli.stat().st_size==cli_entry['bytes']
    original_info=plistlib.loads((original/'Contents/Info.plist').read_bytes())
    assert original_info['CFBundleIdentifier']=='dev.bern.gallery' and original_info['CFBundleExecutable']=='Gallery'
    assert original_info['LSMinimumSystemVersion']=='13.0'
    original_members=members(original)
    expected_members=manifest['app_members']
    assert original_members=={name:row['sha256'] for name,row in expected_members.items()}
    assert all((original/name).stat().st_size==row['bytes'] for name,row in expected_members.items())
    out=args.fresh_work.resolve()
    inputs=[original,cli,*contract_inputs]
    assert not out.exists() and all(out!=v and out not in v.parents and v not in out.parents for v in inputs),'Output and inputs must not overlap in either direction'
    pinned_inputs={str(v):file_hash(v) for v in contract_inputs}
    out.mkdir(parents=True)
    evidence=out/'candidate';evidence.mkdir()
    commands=[]
    def command(argv,log):
        result=subprocess.run([str(v) for v in argv],capture_output=True,timeout=30)
        log.write_bytes(result.stdout+result.stderr)
        commands.append({'argv':[str(v) for v in argv],'status':result.returncode,'log':str(log.relative_to(out))})
        assert result.returncode==0,str(log)
        return result.stdout
    original_machos=app_machos(original);original_cli_macho=macho(cli)
    command(['codesign','--verify','--deep','--strict',original],evidence/'original-signature.txt')
    command(['codesign','--verify','--strict',cli],evidence/'original-cli-signature.txt')
    for label,binary in [('gui',original/'Contents/MacOS/Gallery'),('cli',cli)]:
        metadata=command(['xcrun','vtool','-show-build',binary],evidence/('original-'+label+'-build.txt')).decode()
        assert re.findall(r'^\s*minos\s+(\S+)',metadata,re.M)==['13.0']
        assert re.findall(r'^\s*sdk\s+(\S+)',metadata,re.M)==['26.2']
    app=out/'runtime-work/candidate/Gallery.app';app.parent.mkdir(parents=True)
    command(['ditto',original,app],evidence/'copy.txt')
    assert members(app)==original_members
    identifier='dev.bern.frame13.candidate.'+uuid.uuid4().hex
    prefs=Path.home()/'Library/Preferences'/(identifier+'.plist')
    state=Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
    assert not any(v.exists() or v.is_symlink() for v in [prefs,state])
    info=app/'Contents/Info.plist';old_raw=info.read_bytes();old_plist=plistlib.loads(old_raw)
    assert old_plist==original_info
    changed_plist=dict(old_plist);changed_plist['CFBundleIdentifier']=identifier
    info.write_bytes(plistlib.dumps(changed_plist,fmt=plistlib.FMT_BINARY if old_raw.startswith(b'bplist') else plistlib.FMT_XML,sort_keys=False))
    command(['codesign','--force','--deep','--sign','-','--identifier',identifier,app],evidence/'resign.txt')
    command(['codesign','--verify','--deep','--strict',app],evidence/'signature.txt')
    private_members=members(app);private_machos=app_machos(app)
    assert original_members.keys()==private_members.keys() and original_machos.keys()==private_machos.keys()
    changed=[name for name in original_members if original_members[name]!=private_members[name]]
    assert set(changed)<=ALLOWED and plistlib.loads(info.read_bytes())==changed_plist
    for name,before in original_machos.items():
        assert before['sections']==private_machos[name]['sections']
        assert before['signature_storage_sizes_normalized_sha256']==private_machos[name]['signature_storage_sizes_normalized_sha256']
    assert members(original)==original_members and sha(cli.read_bytes())==cli_sha
    assert all(file_hash(Path(name))==digest for name,digest in pinned_inputs.items())
    shared={'kind':KIND,'source_sha':SOURCE,'baseline_sha':BASELINE,'build_manifest':str(build_file),'build_manifest_sha256':args.build_manifest_sha256,
            'color14_gate':str(args.color14_gate.resolve(strict=True)),'color14_gate_sha256':args.color14_gate_sha256,
            'control14_report':str(args.control14_report.resolve(strict=True)),'candidate14_report':str(args.candidate14_report.resolve(strict=True)),
            'ci_run_id':manifest['run_id'],'harness_sha':manifest['harness_sha']}
    receipt={**shared,'original_app':str(original),'private_app':str(app),'private_bundle_id':identifier,
             'original_gui_sha256':gui_sha,'private_gui_sha256':sha((app/'Contents/MacOS/Gallery').read_bytes()),
             'changed_members':changed,'original_members':original_members,'private_members':private_members,
             'original_machos':original_machos,'private_machos':private_machos,'original_cli_macho':original_cli_macho,
             'sections_and_signature_storage_sizes_normalized_equal':True,'whole_GUI_bytes_equal':False,'originals_unchanged':True,
             'cli':str(cli),'cli_sha256':cli_sha,'preferences_path':str(prefs),'saved_state_path':str(state)}
    receipt_file=evidence/'isolation.json';receipt_file.write_text(json.dumps(receipt,indent=2)+'\n')
    candidate={'app':str(app),'cli':str(cli),'bundle_id':identifier,'private_gui_sha256':receipt['private_gui_sha256'],
               'original_gui_sha256':gui_sha,'cli_sha256':cli_sha,'receipt':str(receipt_file)}
    locks={**shared,'schema':LOCKS_SCHEMA,'candidate':candidate,'commands':commands,
           'scope':'Unaccepted generic SplitButton color candidate13; actual14 color gate prerequisite. No UI executed; original candidate App/CLI unchanged; only private CFID/signature changes allowed.'}
    (out/'locks.json').write_text(json.dumps(locks,indent=2)+'\n')
    return 0


if __name__=='__main__':
    raise SystemExit(main())
