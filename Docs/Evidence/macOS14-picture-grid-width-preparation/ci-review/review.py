#!/usr/bin/env python3
"""Independent static CI review: no product build, runtime UI or CI dispatch."""
from pathlib import Path
import ast,hashlib,json,subprocess,yaml

ROOT=Path(__file__).resolve().parent.parent.parent
PREP=ROOT/'work/picture-grid-width-ci-preparation'
OUT=Path(__file__).resolve().parent
REPO=ROOT/'outputs/Bern'
SOURCE='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
EXPECTED={
 '.github/scripts/picture-grid-width/build.py':'3ca51ca81333d20fd7512f6fe7093b14e14a3ef0efc5f4290342d3dc9d9b6812',
 '.github/scripts/picture-grid-width/patch.py':'06a8b12d24ede2bec754f297a9f3bc3ae1fd650c9831f6c6ab42e9f36e746914',
 '.github/scripts/picture-grid-width/GridWidthTrace.swift':'027c778fe272cf388e38ea0d2d5cab5089fa1d51b7b50768dca33da67227311b',
 '.github/workflows/macos14-picture-grid-width.yml':'687d69ce890cc0fd6e0bc0886b3f404accaa34ed911d4bf68ead4b281d9aff93'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_text())

def main():
    assert sha(PREP/'SHA256SUMS')=='7dbff4d25a9345ca7fd6aaf35040e5561ee2ce09c846cec34ced95b936856062'
    for line in (PREP/'SHA256SUMS').read_text().splitlines():
        digest,name=line.split('  ',1);assert sha(PREP/name)==digest
    for name,digest in EXPECTED.items():assert sha(PREP/name)==digest
    build_path=PREP/'.github/scripts/picture-grid-width/build.py'
    tree=ast.parse(build_path.read_text())
    ast.parse((PREP/'.github/scripts/picture-grid-width/patch.py').read_text())
    locked=next(ast.literal_eval(n.value)for n in tree.body if isinstance(n,ast.Assign)and any(isinstance(t,ast.Name)and t.id=='LOCKED_INPUTS'for t in n.targets))
    for name,digest in locked.items():
        base=PREP/'.github/scripts'if name.startswith('picture-grid-width/')else REPO/'.github/scripts'
        assert sha(base/name)==digest
    for name in ['patch.py','GridWidthTrace.swift']:
        assert (PREP/'.github/scripts/picture-grid-width'/name).read_bytes()==(ROOT/'work/picture-grid-width-preparation'/name).read_bytes()
    collector=REPO/'.github/scripts/macos14-reference.swift'
    assert sha(collector)=='3dcaaf994cd7b61655e202ac76f79cc0e0b7c161b608ed2800378652207f0ac6'
    workflow=PREP/'.github/workflows/macos14-picture-grid-width.yml'
    parsed=yaml.load(workflow.read_text(),Loader=yaml.BaseLoader)
    assert list(parsed['on'])==['workflow_dispatch']
    jobs=parsed['jobs'];assert jobs['build']['runs-on']=='macos-15'and jobs['capture']['runs-on']=='macos-14'
    assert jobs['capture']['needs']=='build'
    steps=[s for job in jobs.values()for s in job['steps']]
    assert not any(s.get('uses','').startswith('actions/cache/save@')for s in steps)
    assert len([s for s in steps if s.get('uses','').startswith('actions/cache/restore@')])==1
    shell=[]
    for job,body in jobs.items():
        for step in body['steps']:
            if 'run'in step:
                r=subprocess.run(['bash','-n'],input=step['run'],text=True,capture_output=True)
                assert r.returncode==0,r.stderr
                shell.append({'job':job,'step':step['name'],'bash_n_exit_code':0})
    uploads=[s for s in steps if s.get('uses','').startswith('actions/upload-artifact@')]
    downloads=[s for s in steps if s.get('uses','').startswith('actions/download-artifact@')]
    assert [s['with']['name']for s in uploads]==['picture-grid-width-build','picture-grid-width-on14']
    assert all(s['with']['retention-days']=='3'and s['if']=='always()'for s in uploads)
    assert len(downloads)==1 and downloads[0]['with']['name']=='picture-grid-width-build'and downloads[0]['with']['path']=='build'
    assert downloads[0]['with']['run-id']=='${{ github.run_id }}'
    source_rows=load(REPO/'Docs/Evidence/macOS14-picture-source-40136458675/raw/before.json')['inputs']
    for row in source_rows:
        raw=subprocess.check_output(['git','-C',str(REPO),'show',SOURCE+':'+row['path']])
        assert len(raw)==row['bytes']and hashlib.sha256(raw).hexdigest()==row['sha256']
    assert len(source_rows)==55
    author=load(PREP/'validation.json')
    assert author['prepare_path_check']['Git_HEAD_status_diff_boundary']=='substituted exact returns; not a real checkout guard test'
    assert author['actual_patch_sequence']['product_compile_or_run']is False
    report={
      'verdict':'static_source_CI_review_pass_with_root_owned_native_and_outer_digest_acceptance',
      'preparation_manifest_sha256':sha(PREP/'SHA256SUMS'),'core_inputs':[{'path':name,'bytes':(PREP/name).stat().st_size,'sha256':digest}for name,digest in EXPECTED.items()],
      'frozen_21_package_width_helpers_source_export_hashes_verified':locked,'all55_archived_input_rows_vs_Git9dd_verified':True,
      'collector_current_sha256':sha(collector),'collector_expected_SHA_asserted_in_workflow':False,
      'Python_AST_and_YAML_parsed':True,'independent_bash_n_checks':shell,
      'manual_source_review':{
       'source_and_hook':'prepare requires exact9dd and clean tracked checkout, compares55 source rows to fixed Git, accepts only expected original CLI hash and one target.plan needle, inserts env-gated diagnostic hook, then asserts CLI-only tracked diff. Generated subtree reset is bounded; Rust caches remain. No skip-target-plan return is introduced.',
       'patch':'original21 patcher and Observer are read from SHA-locked existing package; compiled Generated must be106494B/f4cac696…06d2. Actual Style must first be e1cad857…1c6f, then209558B/09d8f99a…987f with reversible patch proof. Original21Generated SHA is checked unchanged after width patch.',
       'build_exit_and_collect':'cargo command return code is saved and returned without a pipe. collect runs on always after successful prepare, checks rc0/one hook marker, fixedHEAD, soleCLI diff/hash, same package hashes, all55 inputs except deliberateCLI, both compiled source SHAs, release/min13 metadata and nonempty binaries. collect defaults false and returns nonzero on failure.',
       'failure_evidence':'build/capture artifacts upload on always and preserve partial metadata/logs; capture needs successful build. An artifact existing or job green does not establish trace coverage or visual acceptance. Bounded build.log records full-log byte/hash/truncation; full build log is excluded from artifact.',
       'capture':'capture uses same-run named build artifact, verifies fixedsource/harness SHA and internal tar checksum before extraction, preserves App/CLI signatures, and does not rebuild. It sets normal profile and precreates evidence/observer before invoking original collector. Original collector supplies en/en_US,920x668 and Layout0.8s; it has no selected13PNG equivalence gate.',
       'package_binding':'Six existing/baseline width inputs are hard SHA-locked. Newbuild.py selfSHA is recorded in prepare and rechecked patch/collect; harness commit and harness-inputs receipt bind workflow/collector. Baseline package is read-only. New wrapper is a sibling under .github/scripts after publication, preserving imports.'},
      'artifact_container_contract':{
       'build_artifact':'picture-grid-width-build','capture_artifact':'picture-grid-width-on14','same_run_download_root':'build/',
       'internal_payload':'build/showcase-grid-width.tar.gz','internal_checksum':'(cd build && shasum -a256 -c showcase-grid-width.tar.gz.sha256)',
       'internal_checksum_container_correct':True,'retention_days':3,
       'outer_artifact_digest_limit':'The artifact API digest identifies outer artifact ZIP bytes, not the contained tar, extracted directory or member hash list. The workflow delegates outer download to actions/download-artifact. Root must independently compare the downloaded outer ZIP bytes to its exact artifact API id/name/size/digest before extraction/deletion if claiming that gate.',
       'root_prepared_local_download_helper':{'path':'work/github-ci.py','sha256':'52d183af039474d51c728ba2a896049ecbcf8d9f3d34347d8d2343803a67719b','review_scope':'Read-only source/AST inspected after root update; not executed or network tested. Source now compares actual downloadedZIP SHA against available API digest before extraction/deletion, retains mismatchZIP, records unavailable digest honestly, and writes sibling receipt. Fresh unique artifact/path guards, member/count/size/type checks are present. Actual future download/receipt still required; old evidence is not retroactively validated.'}},
      'root_acceptance_still_required':[
       'Confirm actual committed/published4files and harnessSHA; actual remote generatedsource proofs and package/input receipts must match frozen inputs.',
       'Confirm collector receipt SHA3dcaaf99…0ac6. Workflow records it but has no independent expected-SHA pre-execution assertion.',
       'Confirm GUI and CLI Mach-O architecture, minimumOS13.0, exact tar members and strict original signatures. Workflow hardchecks GUIminos only; CLIvtool is recorded.',
       'Check effective increaseContrast false in actual result, alongside normal reduceMotion/reduceTransparency. Original collector profile guard checks the latter two and records contrast.',
       'Compare all13 selected original14PNG files against accepted baseline and confirm125/147 card heights, unchanged21-label coverage and ownPID/window/context before interpreting width trace.',
       'Require separate width packet bound to ownPID, finite/main-thread target120/192 rows and no written cap; optional140rows retained; prefix/end_not_observed limitations remain.',
       'Only after14 new diagnostic noninterference passes, run exact same binary on13 with locked route/timing and compare actual result; equal widths are not a causal diagnosis.'
      ],
      'author_fixture_scope':'Author check really applied old21patch+Observer and newwidthpatch to private retained/generated text. Git HEAD/status/diff and input_rows checks were explicit substitutes. It did not run cargo/target.plan, Swiftcompile, binary signing, UI, CI, artifact transfer or native acceptance.',
      'reviewer_execution_scope':'Read-only hashes/AST/YAML/Git blobs and nine bash -n checks. No fixture rerun, compiler/cache/UI/CI/repo/index/input mutation.',
      'future_runtime_result':'not_run_not_accepted'}
    p=OUT/'review.json'
    with p.open('x')as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(p),'sha256':sha(p),'verdict':report['verdict'],'bash_n_steps':len(shell)}))

if __name__=='__main__':main()
