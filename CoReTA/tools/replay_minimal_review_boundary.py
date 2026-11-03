"""Compatibility rejection inventory; does not relabel old model outputs as success."""
import hashlib
import json
from pathlib import Path
from coreta.minimal_review import ReviewAdapter
ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'runs/minimal-review-boundary-20261020'
def main():
    if OUT.exists():raise ValueError('Refuse overwrite')
    example=json.loads((ROOT/'design/convergence/example_same_object.json').read_text(encoding='utf-8'))
    adapter=ReviewAdapter(OUT,ROOT/'design/convergence/minimal_review.schema.json',token_counter=lambda s:len(s)//4)
    names=['task-audit','source-binding','closure-reference','audit-delivery','inspection-recovery','inspection-component','correct-repair-review-v2','correct-repair-review-v3','attribution-review']
    seen=set();receipts=[];sources={}
    for name in names:
        directory=ROOT/f'runs/math140-{name}-20261020'
        for f in directory.rglob('responses.jsonl'):
            sources[str(f)]=hashlib.sha256(f.read_bytes()).hexdigest()
            for line in f.read_text(encoding='utf-8').splitlines():
                row=json.loads(line);response=row.get('response',{})
                raw=''.join(c.get('text','') for o in response.get('output',[]) if o.get('type')=='message' for c in o.get('content',[]) if c.get('type')=='output_text')
                if not raw:continue
                h=hashlib.sha256(raw.encode()).hexdigest()
                if h in seen:continue
                seen.add(h)
                request=adapter.request(example['input_packet'])
                result=adapter.consume(request['request_id'],raw,example['input_packet']['candidate_identity'],response.get('status','completed'))
                receipts.append({'source':str(f),'raw_sha256':h,'original_response_status':response.get('status'),
                    'new_protocol_acceptance':not bool(result['global_errors']),
                    'all_issues_resolved':result['all_issues_resolved'],'global_errors':result['global_errors']})
    result={'scope':'Old-format compatibility rejection only, using a human design packet; not semantic replay, model recovery, or new task evidence',
        'unique_original_outputs':len(receipts),'unexpected_acceptances':sum(r['new_protocol_acceptance'] for r in receipts),
        'old_results_relabelled':False,'external_api_requests':0,'source_hashes':sources,'receipts':receipts}
    (ROOT/'engineering/MINIMAL_REVIEW_BOUNDARY_REPLAY_20261020.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:result[k] for k in ['unique_original_outputs','unexpected_acceptances','external_api_requests']}))
if __name__=='__main__':main()
