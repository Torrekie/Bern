from pathlib import Path
import hashlib
import json
import shutil
import subprocess

w = Path(__file__).resolve().parent
local = w/'local13'
build = w/'build'
workspace = w.parents[1]
source = 'e48fff46b3a92a28465ad74295bd273a9d69af7d'
harness = '25e18cbc7cd760c1c399042f1d7364c3d755a9dc'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# This is a clearly attributed confirmation, not a fabricated GitHub API response.
confirmation = dict(run_id=40070407306,job_id=120802424623,status='completed',conclusion='success',
    build_source_sha=source,build_harness_sha=harness,
    verification_source='Parent agent explicitly confirmed final build completed/success after checking this exact run/job.')
(build/'ci-confirmation.json').write_text(json.dumps(confirmation,indent=2)+'\n')
base = workspace/'work/film-followup13-f9-baseline'
cleanup = (base/'cleanup-observer.py').read_text().replace("root/'direct-last-resize'", "root/'all-inactive13'")
(local/'cleanup-observer.py').write_text(cleanup)
s = (base/'RUN-BY-PARENT.sh').read_text()
changes = [
 ('app_root="$run_root/isolated/Gallery.app"', 'build_root="$run_root/../build"\napp_root="$run_root/isolated/Gallery.app"'),
 ('cli="$run_root/bin/gallery"', 'cli="$build_root/exact/bin/gallery"'),
 ('result_root="$run_root/direct-last-resize"', 'result_root="$run_root/all-inactive13"'),
 ('f8dacbfe1df00c68bad4465516c69b4c975f8ea1ace17cd0f047977e22409000', '6248546901e8f2f3341d30e9d07b0af867052155e3845a046575f72aa133db5d'),
 ('dev.bern.gallery.filmbaseline.925b37e2b4f944a3bf7be7394e02942d','dev.bern.gallery.filmclean.9697c3c5499d42df80b9bdfd0f43f986'),
 ('export BERN_SOURCE_SHA=f9e08b1d55bed4b9d880b19934abe48281057bb3','export BERN_SOURCE_SHA='+source),
 ('export FILM_BUILD_RUN=39991406873','export FILM_BUILD_RUN=40070407306'),
 ('export BERN_FILM_SCENARIO=direct','export BERN_FILM_SCENARIO=all'),
 ('export BERN_FILM_FOLLOWUP=last-resize','export BERN_FILM_FOLLOWUP=none'),
 ('# The exact f9 build has no diagnostic logger. Do not request or synthesize a trace.','# Clean production code has no logger. Never wait for a diagnostic trace.'),
 ('codesign --verify --deep --strict "$app_root"','codesign --verify --deep --strict "$build_root/exact/Gallery.app"\ncodesign --verify --deep --strict "$app_root"'),
 ('cp "$run_root/gallery-film-probe.swift" "$run_root/provenance.json" "$run_root/validation.json" "$run_root/startup-gate-validation.json" "$run_root/README.md" "$run_root/RUN-BY-PARENT.sh" "$run_root/cleanup-observer.py" "$result_root/"',
  'cp "$run_root/gallery-film-probe.swift" "$run_root/isolation-provenance.json" "$run_root/validation.json" "$run_root/startup-gate-validation.json" "$run_root/README.md" "$run_root/RUN-BY-PARENT.sh" "$run_root/cleanup-observer.py" "$build_root/provenance.json" "$build_root/ci-confirmation.json" "$build_root/artifact.json" "$build_root/build.json" "$build_root/gallery.tar.gz.sha256" "$result_root/"\ncp "$build_root/environment.txt" "$result_root/build-environment.txt"\ncp "$build_root/binary.txt" "$result_root/build-binary.txt"'),
]
for old,new in changes:
    assert s.count(old)==1,old
    s=s.replace(old,new)
marker="printf '%s  %s\\n' 6248546901e8f2f3341d30e9d07b0af867052155e3845a046575f72aa133db5d"
assert s.count(marker)==1
s=s.replace(marker,"printf '%s  %s\\n' d44f051c6b8ca5ab573d9a479ffc4a13eec01f452ad419687b8c0ab13749126c \"$build_root/exact/Gallery.app/Contents/MacOS/Gallery\" | shasum -a 256 -c -\n"+marker)
(local/'RUN-BY-PARENT.sh').write_text(s)
(local/'README.md').write_text('''# Clean e48 Gallery: prepared macOS 13 three-scenario check

Build 40070407306 completed successfully (parent-confirmed job 120802424623). App source is e48fff46b3a92a28465ad74295bd273a9d69af7d, distinct from build harness 25e18cbc7cd760c1c399042f1d7364c3d755a9dc and later documentation commits. The build used SDK 26.2, Swift 6.2.4, ARM64, min13 and real SwiftUI-modern. Source Style is 3912ecdb… and existing 9dd Runtime is 255bacb4…; diagnostic logger/nativeSnapshot code is absent.

Artifact 12550744117 was downloaded once. Its ZIP digest matched GitHub metadata; ZIP/TAR paths, member types, top-level names and package SHA were checked before extraction. Exact app and CLI remain in build/exact for later delivery. Only redundant ZIP/TAR compression layers were removed after recording their hashes. Existing outputs/macOS13 delivery was untouched.

The local run copy uses unique bundleID dev.bern.gallery.filmclean.9697c3c5499d42df80b9bdfd0f43f986 and a local ad-hoc signature. All Mach-O section records/hashes and normalized signature-storage payload match the exact executable. The full signed executable hash differs. This is the same built code with a different bundle/signature environment, not byte-identical signed apps.

The parent may execute RUN-BY-PARENT.sh once. It compiles the unchanged collector 3f434cf / SHA79da4a84… ahead of time, then runs inactive13, scenario=all, followup=none and trace explicitly unset. Three fresh processes exercise Inspector immediate-close→Film, wait-static-close→Film and direct-Film. It never activates/restores focus or changes preferences, history or TCC. Normal accessibility flags are checked without mutation. The startup gate has a 15-second overall deadline plus an 8-second per-CLI-call cap; it does not promise every cold call the full 15 seconds.

This preparation has not launched the app or CLI. CI success and offline signature/hash/architecture/minOS checks do not constitute actual runtime acceptance. Any future successful run must retain raw PNG/AX/CLI results and distinguish inactive13/2x from active14/1x references. Last/resize followups and physical gestures are outside this run.

On exit, only this observer executable/module cache is removed and a cleanup receipt is written. Exact artifact and isolated app remain until later ownership-scoped cleanup. A pre-existing output directory blocks re-execution, preserving partial evidence.
''')
shutil.copy2(workspace/'work/film-startup-gate-check/validation.json',local/'startup-gate-validation.json')
subprocess.run(['bash','-n',str(local/'RUN-BY-PARENT.sh')],check=True)
compile(cleanup,str(local/'cleanup-observer.py'),'exec')
validation = dict(prepared_only=True,app_or_cli_launched=False,ci_success_confirmation=confirmation,
    source_sha=source,build_harness_sha=harness,observer_commit='3f434cf0313d5657a136b1f98d0ac1293b60f169',
    observer_sha256=sha(local/'gallery-film-probe.swift'),exact_gui_sha256=sha(build/'exact/Gallery.app/Contents/MacOS/Gallery'),
    isolated_gui_sha256=sha(local/'isolated/Gallery.app/Contents/MacOS/Gallery'),cli_sha256=sha(build/'exact/bin/gallery'),
    wrapper_sha256=sha(local/'RUN-BY-PARENT.sh'),shell_syntax='PASS: bash -n, not executed',
    python_syntax='PASS: compile(), no pycache',observer_prior_typecheck='Unchanged source; parent Swift5.9.2/SDK14.2 target13 warnings-as-errors validation retained',
    observation='inactive13',scenario='all',followup='none',trace='explicitly unset',runtime_acceptance=False,
    exact_app_cli_retained=True,existing_delivery_untouched=True)
assert validation['observer_sha256']=='79da4a84909a07a6d975cf7606a0cae6d4c22c1c1979a3fdbb0ce0e29aeb0755'
(local/'validation.json').write_text(json.dumps(validation,indent=2)+'\n')
(w/'PREPARATION-SHA256SUMS').write_text(''.join(f'{sha(p)}  {p.relative_to(w).as_posix()}\n' for p in sorted(w.rglob('*')) if p.is_file() and not any(part in ['exact','isolated'] for part in p.relative_to(w).parts) and p.name!='PREPARATION-SHA256SUMS'))
print(json.dumps(validation,indent=2))
