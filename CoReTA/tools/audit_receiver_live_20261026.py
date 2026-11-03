"""Offline integrity and choice summary; never invokes model transport."""
import json
from collections import Counter
from pathlib import Path
import run_receiver_baseline as runner
import prepare_receiver_baseline_20261026 as front
import minimal_final_answer_contract as terminal

ROOT=runner.ROOT
PREPARED=ROOT/'runs/receiver-baseline-prepared-20261026-r3'
LIVE=ROOT/'runs/receiver-baseline-live-20261026-r1'


def main():
    runner.verify(PREPARED)
    plan=runner.io.read(PREPARED/'PLAN.json')['schedule']
    state=runner.io.read(LIVE/'progress.json')
    requests=[json.loads(x) for x in (LIVE/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[json.loads(x) for x in (LIVE/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['mode']=='live' and state['status']=='completed'
    assert len(requests)==len(responses)==state['attempts']==64
    assert [r['attempt'] for r in requests]==list(range(1,65))
    assert all(r['retry']==0 and not r['seed_sent'] for r in requests)
    sums={key:sum(r['response']['usage'][key] for r in responses) for key in ['input_tokens','output_tokens']}
    assert all(state[key]==value for key,value in sums.items())
    assert not state['unknown_usage'] and not state['over_cap']
    by_slot={r['slot']:r for r in state['rows']}
    costs={method:dict(requests=0,input_tokens=0,output_tokens=0) for method in front.FIRST}
    for schedule,req,res in zip(plan,requests,responses):
        slot=schedule['slot']
        assert by_slot[slot]['status']=='readable'
        context=runner.io.read(PREPARED/'contexts'/schedule['task']/f"{schedule['receiver']}.json")
        expected=(front.first_request(context,schedule['method']) if schedule['stage']=='first'
                  else front.final_request(context,by_slot[slot-1]['answer']))
        assert expected==runner.io.read(LIVE/'actual_requests'/f'{slot:03d}.json')
        fake=runner.DeepSeekClient(runner.config(),lambda *a:None)
        assert fake.payload(expected['instructions'],expected['schema'],1536)==req['payload']
        raw=(LIVE/f'{slot:03d}.raw.txt').read_text(encoding='utf-8')
        decoded=front.decode_first(raw) if schedule['stage']=='first' else terminal.decode(raw,context)
        assert decoded==by_slot[slot]['answer']
        assert res['attempt']==slot and res['response']['status']=='completed'
        cost=costs[schedule['method']];cost['requests']+=1
        for key in sums:cost[key]+=res['response']['usage'][key]
    rows=runner.io.read(LIVE/'SCORES.json')['rows']
    table=[]
    for task in runner.TASKS:
        entries={}
        for method in front.FIRST:
            subset=[r for r in rows if r['task']==task and r['method']==method]
            entries[method]=dict(matches=sum(r['reference_match'] is True for r in subset),
                                 unresolved=sum(r['unresolved'] for r in subset),total=len(subset))
        table.append(dict(task=task,**entries))
    pairs=runner.io.read(LIVE/'RECEIVER_PAIRS.json')['pairs']
    counts=Counter()
    for row in pairs:
        a,b=(row[m]['reference_match'] is True for m in ['ordinary','diagnose'])
        counts['both_match' if a and b else 'ordinary_only' if a else 'diagnose_only' if b else 'neither_match']+=1
    result=dict(mode='offline_audit_of_live_results',manifest_sha256=runner.io.digest(PREPARED/'manifest.json'),
        request_count=64,zero_retries=True,format_quarantines=0,unknown_usage=False,
        actual_requests_reconstructed=64,raw_outputs_redecoded=64,usage=sums,method_costs=costs,
        choice_table=table,choice_pair_counts=dict(counts),
        limitations=['Choice matches are secondary, especially for disputed 027.',
                    'Single sample per task/receiver/method; receiver contrasts are not pure causal effects.',
                    'New model calls by this audit: zero.'])
    runner.io.write(LIVE/'TECHNICAL_AUDIT.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
