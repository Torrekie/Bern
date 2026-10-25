import hashlib
import importlib.util
import json
import os
from pathlib import Path
import plistlib
import subprocess
import sys
import uuid

sys.dont_write_bytecode=True
p=Path(__file__).resolve().parent
root=p.parents[1]
repo=root/'outputs/Bern'
seed=repo/'Docs/Evidence/macOS13-film-first-last-e48-20261025/preparation/driver/prepare-film13.py'
spec=importlib.util.spec_from_file_location('macho_receipt',seed)
m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
sha=lambda f:hashlib.sha256(f.read_bytes()).hexdigest()
original=root/'outputs/macOS13/Gallery.app';cli=root/'outputs/macOS13/bin/gallery'
assert sha(original/'Contents/MacOS/Gallery')==m.CONTROL_GUI and sha(cli)==m.CONTROL_CLI
guard=root/'work/native-logic-gallery13-tools/FocusGuard'
provenance=json.loads((guard.parent/'provenance.json').read_text())
assert sha(guard)==provenance['sha256']=='b4301b511a82a0d0eedb1e54d1dc507f573e5535d4015b123dd8424b17e9b561'
commands=[]
def run(args,label):
    r=subprocess.run([str(x) for x in args],capture_output=True,timeout=20)
    commands.append({'label':label,'argv':[str(x) for x in args],'returncode':r.returncode,'stdout':r.stdout.decode(),'stderr':r.stderr.decode()})
    assert r.returncode==0,label
run(['codesign','--verify','--deep','--strict',original],'original-signature')
run(['codesign','--verify','--strict',cli],'cli-signature')
run(['codesign','--verify','--strict',guard],'guard-signature')
app=p/'runtime/Gallery.app';assert not app.exists()
app.parent.mkdir()
before=m.members(original);binary_before=m.macho(original/'Contents/MacOS/Gallery')
run(['ditto',original,app],'private-copy');assert m.members(app)==before
identifier='dev.bern.native13.gallery.'+uuid.uuid4().hex
info=app/'Contents/Info.plist';old=plistlib.loads(info.read_bytes());new=dict(old,CFBundleIdentifier=identifier)
info.write_bytes(plistlib.dumps(new,sort_keys=False))
run(['codesign','--force','--deep','--sign','-','--identifier',identifier,app],'private-sign')
run(['codesign','--verify','--deep','--strict',app],'private-signature')
after=m.members(app);binary_after=m.macho(app/'Contents/MacOS/Gallery')
assert before.keys()==after.keys()
changed=[n for n in before if before[n]!=after[n]]
assert set(changed)<=m.ALLOWED
assert binary_before['sections']==binary_after['sections']
assert binary_before['signature_storage_sizes_normalized_sha256']==binary_after['signature_storage_sizes_normalized_sha256']
for q in [Path.home()/'Library/Preferences'/(identifier+'.plist'),Path.home()/'Library/Saved Application State'/(identifier+'.savedState'),Path(os.environ['TMPDIR'])/(identifier+'.savedState')]:assert not q.exists()
assert m.members(original)==before and sha(cli)==m.CONTROL_CLI
receipt={'source_sha':m.SOURCE,'app':str(app),'cli':str(cli),'identifier':identifier,'original_app':str(original),
    'original_gui_sha256':m.CONTROL_GUI,'cli_sha256':m.CONTROL_CLI,'private_gui_sha256':sha(app/'Contents/MacOS/Gallery'),
    'original_members':before,'private_members':after,'changed_members':changed,'macho_sections_unchanged':True,
    'normalized_non_signature_bytes_unchanged':True,'guard_path':str(guard),'guard_sha256':sha(guard),
    'guard_source_sha256':provenance['source_sha256'],'ipc':'/tmp/bern-response13-'+uuid.uuid4().hex[:12],
    'deadline_seconds':240,'commands':commands,'no_compile_or_module_cache':True,
    'macho_helper_source':str(seed),'macho_helper_sha256':sha(seed),
    'scope':'Existing source-bound e48 coupled Close/Light and Film/Frame response; no pixel gates or keyboard claims.'}
(p/'isolation.json').write_text(json.dumps(receipt,indent=2)+'\n')
print('Validated private e48 copy; active Guard reused, no compiler/cache')
