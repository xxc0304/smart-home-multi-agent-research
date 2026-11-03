"""Check human-record structure and literal citations; never infer semantic labels."""
from pathlib import Path
from datetime import datetime, timezone
import argparse
import json

HERE=Path(__file__).resolve().parent
ROOT=HERE.parent.parent
DATA=ROOT/'data/expert-transfer-annotation-20261030-v0.1'
VERSION='expert-transfer-annotation-v0.1-20261030'
ENUMS={
 'source_validity':{'supported','partial','contradicted','underdetermined','not_available'},
 'sharing_fidelity':{'faithful','strengthened','weakened','changed','mixed','not_shared','unclear','not_applicable'},
 'receipt':{'observed','absent_from_recorded_input','unavailable_input','unclear','not_applicable'},
 'receiver_handling':{'used_with_support','acknowledged_not_applied','misstated','rejected_with_reason','rejected_without_visible_reason','no_visible_response','mixed','unclear','not_applicable'},
 'outcome_link':{'explicitly_used','explicitly_discarded','co_occurs','unclear','not_applicable'}}
BASIS={'calibrated_ability','information_access','item_correctness_only','role_label','insufficient','other'}


def pointer(doc,path):
    if not isinstance(path,str) or not path.startswith('/'): raise ValueError('Use a non-root JSON pointer')
    node=doc
    for part in path.split('/')[1:]:
        key=part.replace('~1','/').replace('~0','~')
        if isinstance(node,list):
            if not key.isdigit(): raise ValueError('Bad array pointer')
            node=node[int(key)]
        elif isinstance(node,dict): node=node[key]
        else: raise ValueError('Pointer continues after a scalar')
    return node


def citation(cite,docs,allowed):
    if not isinstance(cite,dict) or set(cite)!={'document','pointer','quote'}: raise ValueError('Citation needs document/pointer/quote')
    if cite['document'] not in allowed: raise ValueError('Citation uses a later/unavailable stage')
    value=pointer(docs[cite['document']],cite['pointer'])
    text=value if isinstance(value,str) else json.dumps(value,ensure_ascii=False,indent=2)
    if not isinstance(cite['quote'],str) or not cite['quote'].strip() or cite['quote'] not in text:
        raise ValueError('Quoted text not present at cited pointer')


def nonempty(value,name):
    if not isinstance(value,str) or not value.strip() or value.strip() in ('____','UNSET'):
        raise ValueError('Unfilled '+name)


def validate(form):
    if form.get('version')!=VERSION: raise ValueError('Wrong material version')
    cid=form.get('case_id')
    if cid not in {f'S{i:02}' for i in range(1,9)}: raise ValueError('Unknown case')
    docs={phase:json.loads((DATA/'participant/cases'/cid/(phase+'.json')).read_text(encoding='utf-8')) for phase in 'ABC'}
    # Validate even a partial record's supplied citations, but never count a draft as complete.
    for phase in 'abc':
        item=form.get('phase_'+phase,{})
        cites=list(item.get('citations',[]))
        if phase=='b':
            cites+=item.get('advantage_citations',[])
            cites += [c for claim in item.get('claims',[]) for c in claim.get('citations',[])]
        for cite in cites: citation(cite,docs,set('ABC'[:'abc'.index(phase)+1]))
    if form.get('completion_status')!='COMPLETE': return {'status':'DRAFT_NOT_COUNTED','case_id':cid}
    if form.get('reviewer_role')!='human': raise ValueError('Human completion requires declared human role')
    nonempty(form.get('reviewer_id'),'reviewer_id')
    if form.get('prior_exposure') not in {'yes','no','not_sure'}: raise ValueError('Declare prior exposure')
    if type(form.get('minutes_spent')) not in (int,float) or form['minutes_spent']<=0: raise ValueError('Record actual time')
    for phase in 'abc':
        p=form.get('phase_'+phase,{})
        if p.get('status')!='COMPLETE': raise ValueError('Incomplete phase '+phase)
        nonempty(p.get('saved_at'),'phase '+phase+' saved_at')
    a,b,c=[form['phase_'+phase] for phase in 'abc']
    nonempty(a.get('task_requirements'),'task requirements'); nonempty(a.get('fact_notes'),'fact notes')
    if a.get('answerability') not in {'supported_choice','multiple_plausible','insufficient','unclear'}: raise ValueError('Answerability unset')
    if not a.get('citations'): raise ValueError('A requires a factual citation')
    if not b.get('advantage_basis') or not set(b['advantage_basis'])<=BASIS: raise ValueError('Advantage basis unset')
    nonempty(b.get('advantage_evidence_notes'),'advantage basis/missing evidence')
    if not b.get('claims'): raise ValueError('Track at least one claim')
    claim_ids=[]
    for claim in b['claims']:
        nonempty(claim.get('claim_id'),'claim id');claim_ids.append(claim['claim_id'])
        nonempty(claim.get('claim_text'),'claim text')
        for field,options in ENUMS.items():
            if claim.get(field) not in options: raise ValueError('Invalid/unset '+field)
        if not claim.get('citations'): raise ValueError('Tracked claim needs a citation or cited missing-input notice')
        nonempty(claim.get('uncertainty_or_alternative'),'claim uncertainty/alternative; explicitly state none observed if appropriate')
    if len(set(claim_ids))!=len(claim_ids): raise ValueError('Duplicate claim IDs')
    for key in ('observable_summary','needed_comparison'): nonempty(b.get(key),key)
    if b.get('coverage') not in {'full_available_record','partial_read','missing_source'}: raise ValueError('Coverage unset')
    if b['coverage']!='full_available_record': nonempty(b.get('missing_material'),'partial coverage/missing material')
    if c.get('reference_assessment') not in {'accept','qualified','dispute','unclear'}: raise ValueError('Reference assessment unset')
    nonempty(c.get('reasoning_assessment'),'reasoning assessment')
    independence=form.get('independence',{})
    flags=[independence.get(key) for key in ('discussed_with_other_reviewer_before_save','opened_admin_before_save')]
    if any(type(v) is not bool for v in flags): raise ValueError('Independence declarations missing')
    return {'status':'REPORTED_COMPLETE_STRUCTURALLY_VALID','case_id':cid,'reviewer_id':form['reviewer_id'],
            'prior_exposure':form['prior_exposure'],'coverage':b['coverage'],
            'reported_independent_of_other_reviewer_and_admin':not any(flags),
            'meaning':'Format and citations validated; semantic correctness and actual human independence require review.'}


def main():
    parser=argparse.ArgumentParser();parser.add_argument('files',nargs='*');args=parser.parse_args()
    paths=[Path(p) for p in args.files] if args.files else sorted((DATA/'submissions').rglob('*.json'))
    results=[]; seen=set()
    for path in paths:
        try:
            row=validate(json.loads(path.read_text(encoding='utf-8-sig')))
            if row['status'].startswith('REPORTED_COMPLETE'):
                key=(row['reviewer_id'],row['case_id'])
                if key in seen: raise ValueError('Duplicate reviewer/case submission; archive superseded version outside submissions')
                seen.add(key)
            results.append({'file':str(path),**row})
        except (ValueError,KeyError,TypeError,IndexError) as exc:
            results.append({'file':str(path),'status':'INVALID_NOT_COUNTED','reason':str(exc)})
    complete=[r for r in results if r['status']=='REPORTED_COMPLETE_STRUCTURALLY_VALID']
    result={'checked_at_utc':datetime.now(timezone.utc).isoformat(),'submission_files':len(paths),
       'reported_complete_valid_records':len(complete),'distinct_cases':len({r['case_id'] for r in complete}),
       'human_agreement':None,'semantic_adjudication':'PENDING','records':results}
    if not args.files:
        (HERE/'HUMAN_REVIEW_STATUS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))
    if any(r['status']=='INVALID_NOT_COUNTED' for r in results): raise SystemExit(2)


if __name__=='__main__':main()
