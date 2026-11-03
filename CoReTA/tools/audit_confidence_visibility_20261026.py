"""Offline actual-request and usage audit; no model invocation."""
import copy
import json
from pathlib import Path
import confidence_visibility_probe as probe
import local_judgment_frontend as io

def audit():
    p=probe.PREPARED;out=probe.ROOT/'runs/confidence-visibility-live-20261026-r2'
    probe.verify(p)
    state=io.read(out/'progress.json');rows=io.read(out/'review.json')['rows']
    annotations={};pairs={};requests=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
    responses=list(map(io.strict_json,(out/'responses.jsonl').read_text(encoding='utf-8').splitlines()))
    assert len(requests)==len(responses)==state['attempts']==18
    assert all(r['retry']==0 for r in requests)
    usage={k:sum(r['response']['usage'][k] for r in responses) for k in ('input_tokens','output_tokens')}
    assert all(state[k]==v for k,v in usage.items())
    groups={name:dict(requests=0,input_tokens=0,output_tokens=0) for name in ('shared','hidden','shown')}
    for row in rows:
        assert row['status']=='readable'
        req,packet=probe.request_for(p,row,annotations)
        assert req==io.read(out/'actual_requests'/f"{row['slot']:03d}.json")
        recorded=requests[row['slot']-1]['payload']
        for field in ('instructions','max_output_tokens'):assert recorded[field]==req[field]
        assert recorded['text']['format']['schema']==req['schema']
        raw=(out/f"{row['slot']:03d}.raw.txt").read_text(encoding='utf-8')
        response=responses[row['slot']-1]['response']
        assert raw==''.join(c['text'] for item in response['output'] for c in item.get('content',[]) if c.get('type')=='output_text')
        decoded=probe.decode_annotation(raw,packet) if row['stage']=='annotate' else probe.terminal.decode(raw,packet)
        assert decoded==row['answer']
        if row['stage']=='annotate':annotations[row['task'],row['receiver']]=decoded
        else:pairs.setdefault((row['task'],row['receiver']),{})[row['method']]=packet
        g=groups[row['method']];g['requests']+=1
        for field in usage:g[field]+=response['usage'][field]
    for pair in pairs.values():
        stripped=copy.deepcopy(pair['shown'])
        for report in stripped['contributor_reports']:
            for field in probe.FIELDS:report['judgment_annotations'][field].pop('confidence')
        assert pair['hidden']==stripped
    scores=io.read(out/'SCORES.json')['rows'];table={}
    for task in probe.TASKS:
        table[task]={method:sum(r['reference_match'] for r in scores if r['task']==task and r['method']==method) for method in ('hidden','shown')}
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),requests=18,real_retries=0,
        quarantines=0,unknown_usage=state['unknown_usage'],actual_request_reconstructions=18,raw_redecodes=18,
        paired_packets_identical_except_confidence=6,usage=usage,groups=groups,reference_matches=table,
        historical_interrupted_run=dict(attempts=1,model_outputs=0,usage='unknown; not asserted zero cost'),cumulative_attempts=19)
    io.write(out/'TECHNICAL_AUDIT.json',result)
    io.write(out/'RECEIVER_PAIRS.json',[dict(task=t,receiver=m,**{method:next(r for r in scores if r['task']==t and r['receiver']==m and r['method']==method) for method in ('hidden','shown')}) for t in probe.TASKS for m in probe.MEMBERS])
    print(json.dumps(result,ensure_ascii=False))

if __name__=='__main__':audit()
