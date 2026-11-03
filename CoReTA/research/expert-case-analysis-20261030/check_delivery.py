"""Check evidence, report links and preservation of unused human-review surfaces."""
from pathlib import Path
import hashlib
import json
import re

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent


def main():
    proof=json.loads((HERE/'EVIDENCE.json').read_text(encoding='utf-8'))
    assert proof['case_units']==8 and proof['unique_tasks']==7
    assert proof['literal_evidence_items']==len(proof['events'])==56
    previous=ROOT/'research/expert-annotation-pilot-20261030'
    manifest=json.loads((previous/'PACK_MANIFEST.json').read_text(encoding='utf-8'))
    for item in manifest['files']+manifest['reviewer_work_surfaces']:
        assert hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()==item['sha256'],item['path']
    submissions=list((ROOT/'data/expert-transfer-annotation-20261030-v0.1/submissions').rglob('*.json'))
    assert not submissions,'Unexpected human submissions: do not overwrite state or assume none'
    anchors={item['id'].lower() for item in proof['events']}
    checked=0
    for path in HERE.glob('*.md'):
        for target in re.findall(r'\]\(([^)]+)\)',path.read_text(encoding='utf-8')):
            if '://' in target or target.startswith('#'):continue
            filename,_,anchor=target.partition('#')
            # This function writes its own diagnostics after all checks succeed.
            if (path.parent/filename).resolve()!=(HERE/'STAGE_CHECKS.json').resolve():
                assert (path.parent/filename).exists(),(str(path),target)
            if filename=='EVIDENCE.md' and anchor:assert anchor in anchors,target
            checked+=1
    s=proof['structural_comparisons']
    assert all(s[c]['history_present_in_both'] and s[c]['history_same'] and s[c]['packet_different_keys']==['local_reconstruction'] for c in ('C05','C06'))
    result={'date':'2026-10-30','verdict':'PASS_ASSISTANT_QUALITATIVE_ANALYSIS_ONLY',
       'evidence_items':56,'cases_analyzed':8,'unique_tasks':7,'existing_output_events_reviewed':205,
       'analysis_identity':'assistant','human_records_filled':0,'human_agreement':None,
       'frozen_annotation_files_unchanged':len(manifest['files']),'reviewer_surfaces_unchanged':len(manifest['reviewer_work_surfaces']),
       'relative_links_checked':checked,'model_experiment_calls':0,'training_runs':0,'new_case_sampling':0,
       'important_revisions':['C02 slot29 choice/justification inconsistency confirmed.',
            'C05/C06 final historical_work unchanged; only local_reconstruction differs.',
            'C08 correct candidate appears in round1 before EOC claim; Fact3 has divergent referents.'],
       'limits':['Literal checks do not independently validate assistant semantic interpretation.',
                 'Purposive old cases do not estimate prevalence or causal effect.',
                 'Human review scope follows intended paper claims; not a prerequisite to this analysis.']}
    (HERE/'STAGE_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':main()
