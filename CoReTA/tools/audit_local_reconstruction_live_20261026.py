"""Offline post-run lineage and reference scoring; never imported by live runner."""
import json
from pathlib import Path

import local_judgment_frontend as io
import local_reconstruction_probe as front
import minimal_final_answer_contract as terminal
import prepare_local_reconstruction_20261026 as history
import run_local_reconstruction as runner


def main():
    p=runner.DEFAULT
    out=runner.ROOT/'runs/local-reconstruction-live-20261026-r1'
    _,plan=runner.verify(p)
    state=io.read(out/'progress.json')
    review=io.read(out/'review.json')
    requests=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[io.strict_json(x) for x in (out/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['mode']=='live' and state['status']=='completed'
    assert len(requests)==len(responses)==state['attempts']==32
    assert all(r['retry']==0 for r in requests)
    assert all(r['status']=='readable' for r in review['rows'])
    assert not state['unknown_usage'] and not state['over_cap']
    rows={r['slot']:r for r in review['rows']}
    costs={m:dict(requests=0,input_tokens=0,output_tokens=0) for m in front.METHODS}
    max_input=max_output=0
    for row,request,response in zip(plan['schedule'],requests,responses):
        slot=row['slot']
        assert request['attempt']==response['attempt']==slot
        case=io.read(p/'cases'/f"{row['case_id']}.json")
        expected=(front.local_request(case,row['method']) if row['stage']=='local' else
                  front.final_request(case,rows[slot-1]['answer']))
        actual=io.read(out/'actual_requests'/f'{slot:03d}.json')
        assert expected==actual
        cfg=runner.config()
        payload=runner.DeepSeekClient(cfg,lambda *a:None).payload(expected['instructions'],expected['schema'],1536)
        assert request['payload']==payload
        def no_labels(value):
            if isinstance(value,dict):
                assert not set(value)&{'correct_answer','correct_option_id','local_criteria','final_criteria','reference_match'}
                for v in value.values():no_labels(v)
            elif isinstance(value,list):
                for v in value:no_labels(v)
        no_labels(front.packet(actual))
        raw=(out/f'{slot:03d}.raw.txt').read_text(encoding='utf-8')
        assert raw==history.response_text(response)
        decoded=(front.decode_local(raw) if row['stage']=='local' else terminal.decode(raw,case['receiver_context']))
        assert decoded==rows[slot]['answer']
        usage=response['response']['usage']
        bucket=costs[row['method']]
        bucket['requests']+=1
        for key in ['input_tokens','output_tokens']:
            assert type(usage[key]) is int and usage[key]>=0
            bucket[key]+=usage[key]
        max_input=max(max_input,usage['input_tokens'])
        max_output=max(max_output,usage['output_tokens'])
    assert sum(v['input_tokens'] for v in costs.values())==state['input_tokens']<=runner.LIMITS['input']
    assert sum(v['output_tokens'] for v in costs.values())==state['output_tokens']<=runner.LIMITS['output']
    assert max_input<=runner.LIMITS['per_input'] and max_output<=runner.LIMITS['per_output']
    # Only post-run scoring loads benchmark reference fields.
    ref_file=runner.ROOT/'data/task-source-audit-20261021/hiddenbench.json'
    references={r['id']:r for r in io.read(ref_file)}
    pairs=[]
    for identifier in dict.fromkeys(r['case_id'] for r in plan['schedule']):
        case=io.read(p/'cases'/f'{identifier}.json')
        task=int(identifier.split('-')[0])
        choice_map={c['text']:c['id'] for c in case['receiver_context']['task']['choices']}
        correct=choice_map[references[task]['correct_answer']]
        group={row['method']:row for row in review['rows'] if row['case_id']==identifier and row['stage']=='final'}
        values={method:dict(slot=row['slot'],choice=row['answer']['choice'],reference_match=row['answer']['choice']==correct,
                            changed_from_target=row['answer']['choice']!=case['target_answer']['artifact'],
                            semantic_application=None) for method,row in group.items()}
        pairs.append(dict(case_id=identifier,task=task,reference_choice=correct,
            target_choice=case['target_answer']['artifact'],target_reference_match=case['target_answer']['artifact']==correct,
            conditions=values))
    totals={method:dict(correct=sum(pair['conditions'][method]['reference_match'] for pair in pairs),denominator=8,
        corrected=sum(not pair['target_reference_match'] and pair['conditions'][method]['reference_match'] for pair in pairs),
        damaged=sum(pair['target_reference_match'] and not pair['conditions'][method]['reference_match'] for pair in pairs),
        changed=sum(pair['conditions'][method]['changed_from_target'] for pair in pairs)) for method in front.METHODS}
    io.write(out/'SCORES.json',dict(scope='reference choices only; manually targeted archived drafts, not independent new tasks',
        pairs=pairs,totals=totals,reference_source_sha256=io.digest(ref_file),
        semantic_review_status='separate exploratory manual review; no numeric semantic gold inferred from reference choice'))
    io.write(out/'TECHNICAL_AUDIT.json',dict(status='passed',mode='live',manifest_sha256=io.digest(p/'manifest.json'),
        requests=32,retries=0,quarantined=0,blocked=0,transport_errors=0,unresolved_finals=sum(
            row['answer']['choice'] is None for row in review['rows'] if row['stage']=='final'),
        exact_actual_packet_reconstructions=32,raw_response_and_decoder_checks=32,offline_labels_absent=True,
        input_tokens=state['input_tokens'],output_tokens=state['output_tokens'],max_actual_input=max_input,
        max_actual_output=max_output,costs=costs,source_and_code_hashes_verified=True))
    print(json.dumps(dict(totals=totals,costs=costs,input_tokens=state['input_tokens'],output_tokens=state['output_tokens']),ensure_ascii=False))


if __name__=='__main__':main()
