"""Offline reconstruction of actual evidence-layer diagnostic requests/results."""
import copy
import json
import evidence_layer_probe as probe
import local_judgment_frontend as io
from prepare_evidence_layer_audit import restore

def audit():
    p=probe.PREPARED;out=probe.ROOT/'runs/evidence-layer-live-20261026-r1';probe.verify(p)
    state=io.read(out/'progress.json');review=io.read(out/'review.json')['rows']
    requests=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
    responses=list(map(io.strict_json,(out/'responses.jsonl').read_text(encoding='utf-8').splitlines()))
    assert state['status']=='completed' and len(requests)==len(responses)==state['attempts']==24
    assert all(r['retry']==0 for r in requests)
    groups={m:dict(requests=0,input_tokens=0,output_tokens=0) for m in ('nested','layered')};pairs={}
    for row in review:
        assert row['status']=='readable'
        req,packet=probe.request_for(p,row)
        assert req==io.read(out/'actual_requests'/f"{row['slot']:03d}.json")
        actual=requests[row['slot']-1]['payload']
        assert actual['instructions']==req['instructions'] and actual['text']['format']['schema']==req['schema'] and actual['max_output_tokens']==1536
        response=responses[row['slot']-1]['response']
        raw=(out/f"{row['slot']:03d}.raw.txt").read_text(encoding='utf-8')
        assert raw==''.join(c['text'] for item in response['output'] for c in item.get('content',[]) if c.get('type')=='output_text')
        assert probe.terminal.decode(raw,packet)==row['answer']
        pairs.setdefault((row['task'],row['receiver'],row['repeat']),{})[row['method']]=packet
        g=groups[row['method']];g['requests']+=1
        for field in ('input_tokens','output_tokens'):g[field]+=response['usage'][field]
    for packets in pairs.values():assert restore(packets['layered'])==packets['nested']
    for field in ('input_tokens','output_tokens'):assert state[field]==sum(g[field] for g in groups.values())
    scores=io.read(out/'SCORES.json')['rows'];table={}
    for task in ('030','033'):
        table[task]={method:dict(correct=sum(r['reference_match'] for r in scores if r['task']==task and r['method']==method),
            unresolved=sum(r['unresolved'] for r in scores if r['task']==task and r['method']==method),n=6) for method in ('nested','layered')}
    paired=[]
    for t,m,rep in pairs:
        pair={method:next(r for r in scores if r['task']==t and r['receiver']==m and r['repeat']==rep and r['method']==method) for method in ('nested','layered')}
        paired.append(dict(task=t,receiver=m,repeat=rep,**pair))
    io.write(out/'RECEIVER_PAIRS.json',paired)
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),actual_requests_reconstructed=24,raw_outputs_redecoded=24,
        lossless_pair_checks=12,groups=groups,reference_matches=table,quarantines=0,retries=0,unknown_usage=state['unknown_usage'],network_calls_by_audit=0)
    io.write(out/'TECHNICAL_AUDIT.json',result);print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':audit()
