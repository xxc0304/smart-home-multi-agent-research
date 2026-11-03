"""Network-free end-to-end replay, dependency, privacy and budget checks."""
import argparse
import copy
import json
import urllib.error
from pathlib import Path
from tokenizers import Tokenizer
import run_receiver_confirmation as run
import receiver_target_view as view
import local_judgment_frontend as io


def preflight(prepared):
    p=Path(prepared);_,plan=run.verify(p);root=p/'local_validation'
    if root.exists():raise ValueError('new validation directory required')
    root.mkdir()
    tok=Tokenizer.from_file(str(run.TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    history=run.ROOT/'runs/receiver-baseline-live-20261026-r1'
    trace=[];outcomes={}
    modes=['history','stress','bad_draft','bad_contribution','one_bad_first','two_bad_first',
           'two_bad_setup','one_bad_final','null_draft','transport','unknown_usage','over_output','input_budget']
    for mode in modes:
        out=root/mode;calls=[]
        def transport(payload,timeout):
            slot=max(int(f.stem) for f in (out/'actual_requests').glob('*.json'))
            row=plan['schedule'][slot-1];calls.append(slot)
            if mode=='transport':raise urllib.error.URLError('local fixture only')
            raw_slot=(2 if row['stage']=='draft' else 1 if row['stage']=='contribute' else 17 if row['stage']=='first' else 24)
            if row['task']=='control-genuinely-underdetermined' and row['stage']=='final':raw_slot=4
            raw=(history/f'{raw_slot:03d}.raw.txt').read_text(encoding='utf-8')
            if mode=='null_draft' and row['stage']=='draft':raw=(history/'004.raw.txt').read_text(encoding='utf-8')
            if mode=='stress':
                value=io.strict_json(raw);key='reasoning' if 'reasoning' in value else 'text'
                while count(json.dumps(value,ensure_ascii=False))<1400:
                    value[key]+=' Synthetic length extension for local testing, not new task evidence.'
                raw=json.dumps(value,ensure_ascii=False)
            bad=((mode=='bad_draft' and slot==1) or (mode=='bad_contribution' and slot==2)
                or (mode=='one_bad_first' and slot==5) or (mode=='two_bad_first' and slot in [5,7])
                or (mode=='two_bad_setup' and slot in [1,2]) or (mode=='one_bad_final' and slot==6))
            if bad:raw='{"text":'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256,
                       output_tokens=count(raw))
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='over_output':usage['output_tokens']=1537
            if mode=='input_budget':usage['input_tokens']=16384
            trace.append(dict(mode=mode,slot=slot,stage=row['stage'],historical_carrier=raw_slot,
                synthetic_length=mode=='stress',fixture_output_tokens=count(raw)))
            return dict(status='completed',usage=usage,output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
        state=run.run(p,out,transport=transport,local_validation=True)
        summary=run.export(p,out);review=io.read(out/'review.json')
        assert len(review['rows'])==56 and summary['final_units']==24
        assert summary['benchmark_units']==12 and summary['control_units']==12
        assert len(calls)==state['attempts']
        costs=io.read(out/'COSTS.json')['groups']
        assert sum(g['requests'] for g in costs.values())==len(calls)
        for quantity in ['input_tokens','output_tokens']:
            assert sum(g[quantity] for g in costs.values())==state[quantity]
        reqs=[io.strict_json(s) for s in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        assert len(reqs)==len(calls) and all(r['retry']==0 for r in reqs)
        if mode in {'history','stress','null_draft'}:
            assert state['status']=='completed' and len(calls)==56,state
            assert summary['missing_final_units']==0
        elif mode in {'bad_draft','bad_contribution'}:
            assert state['status']=='completed_with_quarantine' and len(calls)==44
            assert summary['missing_final_units']==6
            assert all(r['status']=='blocked_setup' for r in review['rows'][4:16])
        elif mode=='one_bad_first':
            assert state['status']=='completed_with_quarantine' and len(calls)==55
            assert review['rows'][5]['status']=='blocked_upstream' and summary['missing_final_units']==1
        elif mode in {'two_bad_first','two_bad_setup'}:
            assert state['status']=='stopped' and len(calls)==(6 if mode=='two_bad_first' else 2)
            assert summary['missing_final_units']==24
        elif mode=='one_bad_final':
            assert state['status']=='completed_with_quarantine' and len(calls)==56 and summary['missing_final_units']==1
        elif mode in {'transport','unknown_usage','over_output'}:
            assert state['status']=='stopped' and len(calls)==1 and summary['missing_final_units']==24
        else:
            assert state['status']=='stopped' and len(calls)<56 and 'budget' in state['error']
        # Replay actual generation and dependencies from saved decoded outputs.
        drafts,contributions,firsts={},{},{}
        actual={r['slot']:r for r in state['rows']}
        pair_contexts={}
        for row in plan['schedule']:
            result=actual.get(row['slot'])
            if result is None:continue
            req,blocked=run.request_for(p,row,drafts,contributions,firsts)
            file=out/'actual_requests'/f"{row['slot']:03d}.json"
            if file.exists():
                assert req==io.read(file)
                packet=io.strict_json(req['instructions'].split('PACKET=',1)[1])
                def check_no_labels(v):
                    if isinstance(v,dict):
                        assert not set(v)&{'expected_choice','correct_option_id','rubric','checks','purpose','evaluation'}
                        for item in v.values():check_no_labels(item)
                    elif isinstance(v,list):
                        for item in v:check_no_labels(item)
                check_no_labels(packet)
                assert 'correct-with-wrong-report' not in packet['task']['task_id']
                assert 'genuinely-underdetermined' not in packet['task']['task_id']
                if row['stage']=='draft':assert set(packet)=={'task','public_sources'}
                elif row['stage']=='contribute':
                    assert set(packet)=={'task','member','public_sources','own_sources'}
                    assert packet['member']==row['receiver'] and len(packet['own_sources'])==1
                    assert packet['own_sources'][0]['ref']=='PRIVATE.'+row['receiver']
                else:
                    context=view.restore(packet)
                    assert context['member']==row['receiver']
                    key=(row['task'],row['receiver'])
                    if row['stage']=='first':pair_contexts.setdefault(key,[]).append(context)
                    else:assert packet['prior_analysis']==firsts[row['unit']]['text']
                    if row['kind']=='benchmark':
                        assert context['historical_work']==drafts[row['task']]
                        assert context['historical_author']=='PUBLIC_SOLVER'
                        for member in run.MEMBERS:
                            original=io.read(p/'members'/row['task']/f'{member}.json')
                            assert context['shared_contributions'][member]['disclosed_originals']==original['own_sources']
            if result['status']=='readable':
                a=result['answer']
                if row['stage']=='draft':drafts[row['task']]=a
                elif row['stage']=='contribute':contributions.setdefault(row['task'],{})[row['receiver']]=a
                elif row['stage']=='first':firsts[row['unit']]=a
        assert all(len(c)<2 or c[0]==c[1] for c in pair_contexts.values())
        if mode in {'history','stress','null_draft'}:
            assert len(pair_contexts)==12 and all(len(c)==2 for c in pair_contexts.values())
            scores=io.read(out/'SCORES.json')
            unknown=[r for r in scores['controls'] if r['task']=='control-genuinely-underdetermined']
            assert all(r['unresolved'] and r['choice_match'] is True for r in unknown)
        if mode=='unknown_usage':
            assert io.read(out/'EXPORT_SUMMARY.json')['unknown_usage'] is True
            assert costs['shared_setup']['unknown_usage'] is True
        outcomes[mode]=dict(status=state['status'],attempts=len(calls),missing_final_units=summary['missing_final_units'],
            max_input_estimate=max(r['estimated_input_count'] for r in reqs),
            total_input_estimate=sum(r['estimated_input_count'] for r in reqs),error=state['error'])
    assert max(t['fixture_output_tokens'] for t in trace if t['mode']=='stress')<=1536
    # Live gating precedes even a supplied transport.
    touched=[]
    try:run.run(p,root/'unauthorized',transport=lambda *a:touched.append(True))
    except (ValueError,FileNotFoundError):pass
    else:raise AssertionError('unapproved live execution accepted')
    assert not touched
    path=p/'public/030.json';original=path.read_bytes()
    try:
        path.write_bytes(original+b' ')
        try:run.verify(p)
        except ValueError:pass
        else:raise AssertionError('frozen change accepted')
    finally:path.write_bytes(original)
    run.verify(p)
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),live_model_requests=0,
        scenarios=outcomes,full_historical_carrier_trace=trace,
        unauthorized_transport_blocked=True,tamper_rejected=True,
        setup_privacy_and_generated_context_reconstruction=True,control_labels_not_sent=True,
        limitations=['Historical full response carriers are from old tasks; these replays verify interface/load, not new semantics.',
                    'Stress extensions and faults are synthetic; local_fixture scores are not model results.',
                    'No new task generation has occurred; live service may still violate schema.'])
    io.write(p/'PREFLIGHT.json',result)
    return result


if __name__=='__main__':
    a=argparse.ArgumentParser();a.add_argument('--prepared',type=Path,default=run.DEFAULT)
    args=a.parse_args();r=preflight(args.prepared)
    print(json.dumps({k:v for k,v in r.items() if k not in {'full_historical_carrier_trace','limitations'}},ensure_ascii=False))
