from pathlib import Path
import hashlib,importlib.util,json,plistlib,subprocess,uuid
base=Path(__file__).resolve().parents[2];repo=base/'outputs/Bern';out=Path(__file__).resolve().parent
prior=repo/'Docs/Evidence/macOS13-toolbar-title-host-f6/capture-pair/run-pair.py'
spec=importlib.util.spec_from_file_location('previous_macho_receipt',prior);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cli=base/'work/picture-scene-observed14/exact/bin/showcase';assert sha(cli)=='963eb1f1fc5ab553ba8f46286c19746f65cdbb4cec9d255755f7d814818e3170'
inputs={'B3':(base/'work/picture-scene-observed14/exact/Showcase.app','c1d27a0435bd145f08a098adaaf22c6718c1192da15367456afb7ff151c4c12c')}
assert not (out/'runtime-work').exists()and not (out/'locks.json').exists()
commands=[];groups={}
def run(args,log):
 p=subprocess.run([str(a)for a in args],capture_output=True,timeout=30)
 log.write_bytes(p.stdout+p.stderr);commands.append({'argv':[str(a)for a in args],'status':p.returncode,'log':str(log.relative_to(out))});assert p.returncode==0,str(log)
for side,(original,expected)in inputs.items():
 assert sha(original/'Contents/MacOS/Showcase')==expected
 directory=out/'runtime-work'/side;directory.mkdir(parents=True);app=directory/'Showcase.app';evidence=out/side;evidence.mkdir()
 run(['codesign','--verify','--deep','--strict',original],evidence/'original-signature.txt')
 before_members=m.members(original);before_machos=m.app_machos(original)
 run(['ditto',original,app],evidence/'copy.txt');assert m.members(app)==before_members
 identifier='dev.bern.picture13.'+side.lower()+'.'+uuid.uuid4().hex
 prefs=Path.home()/'Library/Preferences'/(identifier+'.plist');state=Path.home()/'Library/Saved Application State'/(identifier+'.savedState')
 assert not any(p.exists()or p.is_symlink()for p in [prefs,state])
 info=app/'Contents/Info.plist';raw=info.read_bytes();old_plist=plistlib.loads(raw);data=dict(old_plist);data['CFBundleIdentifier']=identifier
 info.write_bytes(plistlib.dumps(data,fmt=plistlib.FMT_BINARY if raw.startswith(b'bplist')else plistlib.FMT_XML,sort_keys=False))
 run(['codesign','--force','--deep','--sign','-','--identifier',identifier,app],evidence/'resign.txt')
 run(['codesign','--verify','--deep','--strict',app],evidence/'signature.txt')
 after_members=m.members(app);after_machos=m.app_machos(app)
 assert before_members.keys()==after_members.keys()and before_machos.keys()==after_machos.keys()
 changed=[name for name in before_members if before_members[name]!=after_members[name]]
 assert set(changed)<=m.ALLOWED
 assert plistlib.loads(info.read_bytes())==data
 for name,before in before_machos.items():
  assert before['sections']==after_machos[name]['sections']
  assert before['signature_storage_sizes_normalized_sha256']==after_machos[name]['signature_storage_sizes_normalized_sha256']
 assert m.members(original)==before_members and sha(original/'Contents/MacOS/Showcase')==expected
 receipt={'variant':side,'source_sha':'9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0','observer_added':side.startswith('B'),'original_app':str(original),'private_app':str(app),'private_bundle_id':identifier,'original_gui_sha256':expected,'private_gui_sha256':sha(app/'Contents/MacOS/Showcase'),'changed_members':changed,'original_members':before_members,'private_members':after_members,'original_machos':before_machos,'private_machos':after_machos,'sections_and_signature_storage_sizes_normalized_equal':True,'whole_GUI_bytes_equal':False,'originals_unchanged':True,'cli':str(cli),'cli_sha256':sha(cli),'preferences_path':str(prefs),'saved_state_path':str(state),'compiled_original_entitlements':'Original CI and delivered apps have no entitlements; prior raw extraction0 bytes retained separately.'}
 (evidence/'isolation.json').write_text(json.dumps(receipt,indent=2)+'\n');groups[side]={'app':str(app),'cli':str(cli),'bundle_id':identifier,'receipt':str(evidence/'isolation.json')}
(out/'locks.json').write_text(json.dumps({'schema':1,'groups':groups,'macho_helper_source':str(prior),'macho_helper_source_sha256':sha(prior),'commands':commands,'scope':'Preparation only; no UI launched. Private signatures/IDs differ; Mach-O sections and signature-size-normalized non-signature bytes preserved. Original App/CLI unchanged. A/B share the exact unchanged CI CLI.'},indent=2)+'\n')
print('Prepared A/B private identities; all Mach-O sections/normalized bytes and original App/CLI hashes preserved; UI not launched')
