#!/usr/bin/env python3
"""Independent source-only review. No compilation, UI, CI or input writes."""
from pathlib import Path
import hashlib,importlib.util,json,re,subprocess

ROOT=Path(__file__).resolve().parent.parent.parent
OUT=Path(__file__).resolve().parent
PACKAGE=ROOT/'work/picture-grid-width-preparation'
SOURCE='9dd99b76cc5600043a37b3cf8ec46e046c0c1ec0'
def sha(b):return hashlib.sha256(b).hexdigest()
def git(path):return subprocess.check_output(['git','-C',str(ROOT/'outputs/Bern'),'show',SOURCE+':'+path])
def load(p):return json.loads(p.read_text())

def main():
    manifest=(PACKAGE/'SHA256SUMS').read_bytes()
    for line in manifest.decode().splitlines():
        expected,name=line.split('  ',1)
        assert sha((PACKAGE/name).read_bytes())==expected
    spec=importlib.util.spec_from_file_location('width_patch',PACKAGE/'patch.py')
    patch=importlib.util.module_from_spec(spec);spec.loader.exec_module(patch)
    original=git('crates/bern-backend-swiftui/templates/BernStyle.swift')
    helper=(PACKAGE/'GridWidthTrace.swift').read_bytes()
    result,proof=patch.candidate(original,helper)
    assert len(original)==205764 and sha(original)==patch.STYLE_SHA
    assert len(result)==209558 and sha(result)=='09d8f99a26a73498e7ef4d7d597eca646be751f32b4fe99f63482b944a81987f'
    begin=original.index(patch.BLOCK);head_end=patch.BLOCK.index(b'\n')+1
    expected=original[:begin+head_end]+patch.INSERT+original[begin+head_end:]+patch.DELIMITER+helper
    assert result==expected
    assert result.count(patch.INSERT)==1 and result.count(patch.ANCHOR)==1
    assert result[:-len(patch.DELIMITER+helper)].replace(patch.INSERT,b'',1)==original
    negatives={}
    for label,src,h in [('wrong_source',original+b'\n',helper),('wrong_helper',original,helper+b'\n'),('reapplication',result,helper)]:
        try:patch.candidate(src,h)
        except AssertionError:negatives[label]=True
        else:raise AssertionError('negative input accepted: '+label)
    lib=git('crates/bern-backend-swiftui/src/lib.rs')
    target=git('crates/bern-target-api/src/lib.rs')
    assert lib.count(b'const STYLE: &str = include_str!("../templates/BernStyle.swift");')==1
    assert lib.count(b'GeneratedFile::text("Sources/BernStyle.swift", STYLE)')==1
    assert b'contents: contents.into().into_bytes(),'in target
    before=load(ROOT/'outputs/Bern/Docs/Evidence/macOS14-picture-source-40136458675/raw/before.json')
    # An archived source input hash is provenance for the exact template, not
    # an actual generated Style export; that distinction remains explicit.
    assert any(row.get('path')=='crates/bern-backend-swiftui/templates/BernStyle.swift' and row.get('sha256')==sha(original) for row in before['inputs'])
    measured=(ROOT/'work/picture-scene-observed14/build/picture-patch/BernGenerated.measured.swift').read_bytes()
    observer=(ROOT/'outputs/Bern/.github/scripts/picture-scene-observer/Observer.swift').read_bytes()
    combined=measured+b'\n// Diagnostic observer; original Scene and layout declarations above.\n'+observer
    assert len(combined)==patch.GENERATED_BYTES==106494 and sha(combined)==patch.GENERATED_SHA
    generated=(ROOT/'outputs/Bern/Docs/Evidence/macOS14-picture-source-40136458675/raw/BernGenerated.swift').read_text()
    callsites=[{'line':i,'declaration':line.strip()}for i,line in enumerate(generated.splitlines(),1)if 'BernAdaptiveGrid('in line]
    assert [x['line']for x in callsites]==[1280,1314,1376]
    packet_contract={
      'source_only_no_runtime_execution':True,'Foundation_helper_typecheck_not_repeated':True,
      'logger_event_cap':64,'logger_file_byte_cap':65536,
      'output_requires_preexisting_external_directory':True,'first_write_without_overwriting':True,'later_writes_atomic':True,
      'sequence_means_lock_serialized_append_order':True,'no_instance_id_or_terminal_snapshot':True,
      'nonfinite_widths':'JSON null plus exact Double bit string; measured_is_finite and guard predicate are recorded',
      'caps_and_IO':'At64 successful events the written event_limit_reached flag is true. A later event/byte cap or thrown serialization/write stops silently; the last successful prefix may remain. No packet success/error/terminal completeness flag exists.',
      'timestamp_order':'entry uptime is sampled after reading old width and before original guard; recorded-after-action uptime is after lock acquisition and before JSON serialization/write. Neither is a presentation timestamp or callback-return time.',
      'timing_effect':'defer runs for guard rejection and successful assignments before callback returns. NSLock, allocation, serialization and synchronous I/O can perturb callbacks/layout timing, despite retaining original state-update order.'}
    findings=[
      {'severity':'scope','text':'All existing BernAdaptiveGrid uses are instrumented. The real generated page has120/16/16,192/16/16 and140/12/12 callsites. Configuration distinguishes these source callsites in this cohort; it is not runtime identity or remount history. The lower140 grid may be absent from the bounded prefix.'},
      {'severity':'interpretation','text':'columns_captured_from_body is a lexical body-evaluation capture. The action reads live old stored width separately. Recomputing columns from that old width or measured width gives a derived prediction, not the observed body capture or settled render. At measured719 the formulas predict5 and3 for the target configurations, but a stale body capture may differ without identifying a cause.'},
      {'severity':'timing','text':'Original guard, zero-width Transaction and both width writes stay contiguous exact bytes and retain order. Added entry captures precede them; defer logging follows them, including guard return. Source equivalence of state statements does not establish temporal noninterference.'},
      {'severity':'evidence','text':'The actual generated Style file has not been read in this local preparation. Git source and direct generator mapping establish its expected bytes. The patch must compare the actual generated remote Style SHA and unique action context before writing; the21-point BernGenerated source is independently SHA/length-locked and checked unchanged after.'},
      {'severity':'coverage','text':'Finite main-thread target120/192 rows, own PID, route/uptime binding and no written cap are necessary future bounded-prefix gates. They do not prove uninterrupted logging, absence of a later I/O failure or zero callbacks outside the prefix. Missing/unknown coverage cannot be interpreted as no width action.'},
      {'severity':'acceptance','text':'Previously accepted21-point observed14 captures and same13 A2/B3 exact PNGs are baseline evidence only. Every new width-trace product must independently retain original14 PNG/card125/147 and21 labels before interpreting traces, then use the same binary on13 with the locked route/timing. Equal width histories cannot establish root cause or full UI equivalence.'}
    ]
    report={
      'verdict':'source_review_pass_no_blocking_changes_with_explicit_runtime_and_timing_gates',
      'source_sha':SOURCE,'preparation_manifest_sha256':sha(manifest),
      'inputs':[{'name':p.name,'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}for p in sorted(PACKAGE.iterdir())if p.is_file()],
      'independent_source_proof':proof,'negative_candidate_inputs_rejected':negatives,
      'generator_source_files':[{'path':p,'sha256':sha(git(p))}for p in ['crates/bern-backend-swiftui/src/lib.rs','crates/bern-target-api/src/lib.rs']],
      'actual_generated_Style_read':False,'candidate_constructed_in_memory_only':True,
      'reconstructed_21point_source':{'bytes':len(combined),'sha256':sha(combined),'unchanged_by_width_candidate':True},
      'real_generated_grid_callsites':callsites,'packet_contract':packet_contract,'findings':findings,
      'no_compilation_UI_CI_repo_index_or_input_mutation':True,
      'future_runtime_result':'not_run_not_accepted'}
    p=OUT/'review.json'
    with p.open('x')as f:json.dump(report,f,indent=2,ensure_ascii=False);f.write('\n')
    print(json.dumps({'report':str(p),'sha256':sha(p.read_bytes()),'verdict':report['verdict']}))

if __name__=='__main__':main()
