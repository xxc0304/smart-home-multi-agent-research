"""Post-run integrity and separate historical/control scoring. No model calls."""
import json
from pathlib import Path
import local_judgment_frontend as io
import minimal_final_answer_contract as terminal
import example_adaptation_probe as front
import run_example_adaptation as runner


def main():
    p=runner.DEFAULT;out=runner.ROOT/'runs/example-adaptation-live-20261026-r1'
    manifest,plan=runner.verify(p);state=io.read(out/'progress.json');review=io.read(out/'review.json')
    requests=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[io.strict_json(x) for x in (out/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['mode']=='live' and state['status'] in ['completed','completed_with_quarantine','stopped']
    assert len(requests)==len(responses)==state['attempts']<=72
    assert all(r['retry']==0 for r in requests)
    actual_rows={r['slot']:r for r in review['rows']}
    examples=io.read(p/'EXAMPLES.json')
    costs={m:dict(requests=0,input_tokens=0,output_tokens=0) for m in front.METHODS}
    for request,response in zip(requests,responses):
        slot=request['attempt'];assert response['attempt']==slot
        row=plan['schedule'][slot-1];case=io.read(p/'cases'/f"{row['case_id']}.json")
        req=front.request(case,row['method'],examples);actual=io.read(out/'actual_requests'/f'{slot:03d}.json')
        assert req==actual
        payload=runner.core.DeepSeekClient(runner.core.config(),lambda *a:None).payload(req['instructions'],req['schema'],1536)
        assert request['payload']==payload
        packet=front.packet(req);shown=packet.pop('worked_examples',None)
        assert shown==(None if row['method']=='no_examples' else examples[row['method']])
        assert packet==case['packet']
        def no_labels(value):
            if isinstance(value,dict):
                assert not set(value)&{'reference_match','correct_option_id','correct_answer','CONTROL_LABELS','case_rubric'}
                for v in value.values():no_labels(v)
            elif isinstance(value,list):
                for v in value:no_labels(v)
        no_labels(front.packet(req))
        bucket=costs[row['method']];bucket['requests']+=1
        if 'response' not in response:continue
        body=response['response'];raw=''.join(c['text'] for m in body.get('output',[]) for c in m.get('content',[]) if c.get('type')=='output_text')
        assert raw==(out/f'{slot:03d}.raw.txt').read_text(encoding='utf-8')
        if actual_rows[slot]['status']=='readable':
            assert body['status']=='completed'
            assert terminal.decode(raw,case['packet'])==actual_rows[slot]['answer']
        for key in ['input_tokens','output_tokens']:
            amount=body.get('usage',{}).get(key)
            if type(amount) is int:bucket[key]+=amount
    if not state['unknown_usage']:
        for key in ['input_tokens','output_tokens']:assert sum(c[key] for c in costs.values())==state[key]
    assert state['input_tokens']<=runner.LIMITS['input'] and state['output_tokens']<=runner.LIMITS['output']
    # Reference data is only loaded here, after generation. Demonstration labels are deliberately inputs.
    references={str(r['id']).zfill(3):r['correct_answer'] for r in io.read(runner.ROOT/'data/task-source-audit-20261021/hiddenbench.json')}
    control_labels=io.read(p/'offline_only/CONTROL_LABELS.json')
    scored=[]
    for row in review['rows']:
        case=io.read(p/'cases'/f"{row['case_id']}.json")
        names={x['text']:x['id'] for x in case['packet']['task']['choices']}
        reference=(names[references[row['case_id'][:3]]] if row['kind']=='historical_development_regression' else control_labels[row['case_id']]['choice'])
        old=case['packet']['historical_work']['artifact'];choice=row['answer']['choice'] if row['status']=='readable' else None
        scored.append(dict(row,reference_choice=reference,reference_match=(choice==reference if row['status']=='readable' else None),
            target_reference_match=old==reference,changed=(choice!=old if row['status']=='readable' else None),
            corrected=(old!=reference and choice==reference if row['status']=='readable' else None),
            damaged=(old==reference and choice!=reference if row['status']=='readable' else None),
            unresolved=(choice is None if row['status']=='readable' else None),semantic_application=None))
    totals={}
    for kind in ['historical_development_regression','authored_safety_control']:
        totals[kind]={}
        for method in front.METHODS:
            group=[r for r in scored if r['kind']==kind and r['method']==method]
            totals[kind][method]=dict(correct=sum(r['reference_match'] is True for r in group),planned=len(group),
                readable=sum(r['status']=='readable' for r in group),corrected=sum(r['corrected'] is True for r in group),
                damaged=sum(r['damaged'] is True for r in group),unresolved=sum(r['unresolved'] is True for r in group),
                by_repeat={str(rep):sum(r['reference_match'] is True for r in group if r['repeat']==rep) for rep in [1,2]})
    pairs=[]
    for cid in dict.fromkeys(r['case_id'] for r in plan['schedule']):
        for rep in [1,2]:
            group={r['method']:dict(slot=r['slot'],status=r['status'],choice=r['answer']['choice'] if r['status']=='readable' else None,reference_match=r['reference_match'])
                   for r in scored if r['case_id']==cid and r['repeat']==rep}
            pairs.append(dict(case_id=cid,repeat=rep,conditions=group))
    io.write(out/'SCORES.json',dict(scope='Historical regression and authored controls separately; no unseen benchmark claim.',totals=totals,rows=scored,pairs=pairs))
    io.write(out/'TECHNICAL_AUDIT.json',dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),run_status=state['status'],
        actual_requests=len(requests),planned_requests=72,retries=0,exact_packet_reconstructions=len(requests),
        readable=sum(r['status']=='readable' for r in review['rows']),quarantined=sum(r['status']=='quarantined' for r in review['rows']),
        not_run=sum(r['status']=='not_run' for r in review['rows']),unknown_usage=state['unknown_usage'],
        source_code_and_inputs_verified=True,evaluation_labels_not_in_requests=True,
        input_tokens=state['input_tokens'],output_tokens=state['output_tokens'],costs=costs))
    print(json.dumps(dict(status=state['status'],totals=totals,costs=costs),ensure_ascii=False))


if __name__=='__main__':main()
