"""Offline actual IMP-adaptation trace reconstruction and descriptive metrics."""
import json
import imp_adaptation_probe as probe
import local_judgment_frontend as io

def audit():
    p=probe.PREPARED;out=probe.ROOT/'runs/imp-adaptation-live-20261026-r1';probe.verify(p)
    state=io.read(out/'progress.json');rows=io.read(out/'review.json')['rows']
    requests=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
    responses=list(map(io.strict_json,(out/'responses.jsonl').read_text(encoding='utf-8').splitlines()))
    assert state['status']=='completed' and state['attempts']==len(requests)==len(responses)==64
    assert all(r['retry']==0 for r in requests)
    answers={};groups={m:dict(requests=0,input_tokens=0,output_tokens=0) for m in ('shared','standard','imp','full_information')}
    delivered=[];words=[]
    for row in rows:
        assert row['status']=='readable'
        req,packet,route=probe.request_for(p,row,answers)
        assert req==io.read(out/'actual_requests'/f"{row['slot']:03d}.json")
        assert route==io.read(out/'routing'/f"{row['slot']:03d}.json")
        actual=requests[row['slot']-1]['payload']
        assert actual['instructions']==req['instructions'] and actual['text']['format']['schema']==req['schema'] and actual['max_output_tokens']==1024
        response=responses[row['slot']-1]['response']
        raw=(out/f"{row['slot']:03d}.raw.txt").read_text(encoding='utf-8')
        assert raw==''.join(c['text'] for item in response['output'] for c in item.get('content',[]) if c.get('type')=='output_text')
        decoded=probe.terminal.decode(raw,packet);assert decoded==row['answer'];answers[probe.key(row)]=decoded
        group=groups[row['method']];group['requests']+=1
        for f in ('input_tokens','output_tokens'):group[f]+=response['usage'][f]
        words.append(dict(slot=row['slot'],words=len(decoded['reasoning'].split())))
        if row['method']=='imp' and row['round']:
            bundle=io.read(p/'tasks'/f"{row['task']}.json")
            private=[ref for ref in bundle['documents'] if ref.startswith('PRIVATE.') and ref not in bundle['owned'][row['receiver']]]
            refs=route['delivered_refs']
            delivered.append(dict(slot=row['slot'],task=row['task'],repeat=row['repeat'],round=row['round'],receiver=row['receiver'],
                expected_other_private_refs=private,delivered_refs=refs,all_other_private_present=set(private)<=set(refs)))
            assert not set(refs)&set(bundle['owned'][row['receiver']])
            assert all(doc==bundle['documents'][doc['ref']] for doc in packet['messages_from_other_participants'])
    assert all(state[f]==sum(g[f] for g in groups.values()) for f in ('input_tokens','output_tokens'))
    scores=io.read(out/'SCORES.json');team=[g for g in scores['groups'] if g['round']==2]
    summary={t:{m:[g['reference_score'] for g in team if g['task']==t and g['method']==m] for m in ('standard','imp')} for t in ('030','033')}
    full=[dict(task=r['task'],repeat=r['repeat'],choice=r['answer']['choice'],match=r['reference_match']) for r in scores['individual'] if r['method']=='full_information']
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),request_reconstructions=64,raw_redecodes=64,
        routing_reconstructions=24,quarantines=0,retries=0,unknown_usage=state['unknown_usage'],groups=groups,
        round2_team_scores=summary,full_information=full,imp_receiver_rounds=len(delivered),
        receiver_rounds_with_all_other_private=sum(r['all_other_private_present'] for r in delivered),
        word_limit_exceeded=[r for r in words if r['words']>100],network_calls_by_audit=0)
    io.write(out/'TECHNICAL_AUDIT.json',result);io.write(out/'DELIVERY_AUDIT.json',delivered)
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':audit()
