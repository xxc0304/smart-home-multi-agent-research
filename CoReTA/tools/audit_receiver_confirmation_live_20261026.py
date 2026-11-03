"""Offline integrity and stratified choice summary for the live confirmation batch."""
import json
from pathlib import Path
import run_receiver_confirmation as runner
import local_judgment_frontend as io
import prepare_receiver_baseline_20261026 as contract
import minimal_final_answer_contract as terminal

ROOT=runner.ROOT
PREPARED=ROOT/'runs/receiver-confirmation-prepared-20261026-r3'
LIVE=ROOT/'runs/receiver-confirmation-live-20261026-r1'


def main():
    runner.verify(PREPARED)
    state=io.read(LIVE/'progress.json');plan=io.read(PREPARED/'PLAN.json')['schedule']
    assert state['mode']=='live' and state['status']=='completed'
    reqs=[json.loads(x) for x in (LIVE/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[json.loads(x) for x in (LIVE/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(reqs)==len(responses)==state['attempts']==56
    assert all(r['retry']==0 and not r['seed_sent'] for r in reqs)
    rows={r['slot']:r for r in state['rows']};drafts,contributions,firsts={},{},{}
    usage={k:sum(r['response']['usage'][k] for r in responses) for k in ['input_tokens','output_tokens']}
    assert all(state[k]==v for k,v in usage.items())
    for row,request,response in zip(plan,reqs,responses):
        slot=row['slot'];assert rows[slot]['status']=='readable'
        assert request['slot']==response['slot']==request['attempt']==response['attempt']==slot
        expected,blocked=runner.request_for(PREPARED,row,drafts,contributions,firsts)
        assert not blocked and expected==io.read(LIVE/'actual_requests'/f'{slot:03d}.json')
        client=runner.DeepSeekClient(runner.config(),lambda *a:None)
        assert client.payload(expected['instructions'],expected['schema'],1536)==request['payload']
        packet=io.strict_json(expected['instructions'].split('PACKET=',1)[1])
        raw=(LIVE/f'{slot:03d}.raw.txt').read_text(encoding='utf-8')
        decoded=terminal.decode(raw,packet) if row['stage'] in {'draft','final'} else contract.decode_first(raw)
        assert decoded==rows[slot]['answer']
        if row['stage']=='draft':drafts[row['task']]=decoded
        elif row['stage']=='contribute':contributions.setdefault(row['task'],{})[row['receiver']]=decoded
        elif row['stage']=='first':firsts[row['unit']]=decoded
    scores=io.read(LIVE/'SCORES.json');summary=[]
    for task in runner.TASKS:
        subset=scores['benchmark'] if task in runner.TASKS[:2] else scores['controls']
        methods={}
        for method in ['ordinary','diagnose']:
            group=[r for r in subset if r['task']==task and r['method']==method]
            methods[method]=dict(matches=sum(r['choice_match'] is True for r in group),
                unresolved=sum(r['unresolved'] for r in group),total=len(group),
                choices={r['receiver']:r['answer']['choice'] for r in group})
        summary.append(dict(task=task,kind='benchmark' if task in runner.TASKS[:2] else 'control',**methods))
    costs=io.read(LIVE/'COSTS.json')['groups']
    assert costs['shared_setup']['requests']==8 and costs['ordinary']['requests']==costs['diagnose']['requests']==24
    assert all(sum(g[k] for g in costs.values())==v for k,v in usage.items())
    result=dict(mode='audit_of_live_results',manifest_sha256=io.digest(PREPARED/'manifest.json'),
        requests=56,retries=0,quarantines=0,unknown_usage=False,actual_requests_reconstructed=56,
        raw_responses_redecoded=56,usage=usage,costs=costs,stratified_choice_table=summary,
        public_drafts={t:dict(choice=a['choice'],reasoning=a['reasoning']) for t,a in drafts.items()},
        caveat='Public reference choices and synthetic control choices are separate, not one overall accuracy.',new_api_calls=0)
    io.write(LIVE/'TECHNICAL_AUDIT.json',result)
    print(json.dumps(result,ensure_ascii=False))


if __name__=='__main__':main()
