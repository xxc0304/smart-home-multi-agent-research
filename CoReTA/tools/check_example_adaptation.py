"""Offline real-response replay, input matching and failure simulation."""
import argparse
import copy
import json
import urllib.error
from pathlib import Path
from tokenizers import Tokenizer
import local_judgment_frontend as io
import minimal_final_answer_contract as terminal
import example_adaptation_probe as front
import run_example_adaptation as runner


def check(p):
    p=Path(p);manifest,plan=runner.verify(p)
    validation=p/'local_validation'
    if validation.exists():raise ValueError('preserve previous validation; freeze a new version')
    validation.mkdir()
    tok=Tokenizer.from_file(str(runner.core.TOKENIZER));count=lambda text:len(tok.encode(text,add_special_tokens=False).ids)
    examples=io.read(p/'EXAMPLES.json');index=io.read(p/'CASE_INDEX.json')
    assert len(examples['positive_examples'])==len(examples['contrastive_examples'])==4
    for positive,contrast in zip(examples['positive_examples'],examples['contrastive_examples']):
        assert positive['scenario']==contrast['scenario'] and positive['correct_application']==contrast['correct_application']
    lengths=[]
    for entry in index:
        case=io.read(p/'cases'/f"{entry['case_id']}.json")
        if entry['kind']=='historical_development_regression':
            original=io.read(runner.ROOT/entry['source'])
            assert front.packet(original)==case['packet'] and io.digest(runner.ROOT/entry['source'])==entry['source_sha256']
        views=[]
        for method in front.METHODS:
            req=front.request(case,method,examples);view=front.packet(req)
            supplied=view.pop('worked_examples',None)
            assert supplied==(None if method=='no_examples' else examples[method])
            assert view==case['packet'];views.append(view)
            payload=runner.core.DeepSeekClient(runner.core.config(),lambda *a:None).payload(req['instructions'],req['schema'],1536)
            length=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256
            assert length<16384
            lengths.append(dict(case_id=entry['case_id'],method=method,input_estimate=length))
            forbidden={'correct_answer','correct_option_id','reference_match','CONTROL_LABELS','primary_checks'}
            def inspect(value):
                if isinstance(value,dict):
                    assert not set(value)&forbidden
                    for v in value.values():inspect(v)
                elif isinstance(value,list):
                    for v in value:inspect(v)
            inspect(front.packet(req))
        assert views[0]==views[1]==views[2]
    lookup={(x['case_id'],x['method']):x['input_estimate'] for x in lengths}
    assert sum(lookup[(r['case_id'],r['method'])] for r in plan['schedule'])<runner.LIMITS['input']
    history=runner.ROOT/'runs/local-reconstruction-live-20261026-r1'
    hist_rows=io.read(history/'review.json')['rows']
    final_slots={r['case_id']:r['slot'] for r in hist_rows if r['stage']=='final' and r['method']=='visible_draft'}
    outcomes={}
    for mode in ['history','stress','one_bad','two_bad','extra_annotations','unresolved','incomplete','transport','unknown_usage','over_output','input_budget']:
        out=validation/mode;calls=[]
        def transport(payload,timeout):
            slot=max(int(x.stem) for x in (out/'actual_requests').glob('*.json'));row=plan['schedule'][slot-1];calls.append(slot)
            if mode=='transport':raise urllib.error.URLError('offline fixture transport failure')
            # Exact same-context historical response when available; new controls use an explicitly
            # cross-task real final carrier with a legal choice, not a claimed control solution.
            carrier_slot=final_slots.get(row['case_id'],14)
            text=(history/f'{carrier_slot:03d}.raw.txt').read_text(encoding='utf-8')
            if mode=='stress':
                value=io.strict_json(text)
                while count(json.dumps(value,ensure_ascii=False))<1400:value['reasoning']+=' Synthetic length stress only; no new evidence.'
                text=json.dumps(value,ensure_ascii=False)
            if mode=='extra_annotations':
                value=io.strict_json(text);value['optional_note']='Fixture annotation';text=json.dumps(value,ensure_ascii=False)
            if mode=='unresolved':text='{"choice":null,"reasoning":"No defensible answer in this fixture."}'
            if (mode=='one_bad' and len(calls)==1) or (mode=='two_bad' and len(calls)<=2):text='{"choice":'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256,output_tokens=count(text))
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='over_output':usage['output_tokens']=1537
            if mode=='input_budget':usage['input_tokens']=16384
            return dict(status='incomplete' if mode=='incomplete' else 'completed',output=[dict(type='message',content=[dict(type='output_text',text=text)])],usage=usage)
        state=runner.run(p,out,transport=transport,local_validation=True)
        review=io.read(out/'review.json')
        assert len(review['rows'])==72 and state['attempts']==len(calls)
        requests=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        assert all(r['retry']==0 for r in requests)
        if mode in {'history','stress','extra_annotations','unresolved'}:assert state['status']=='completed' and len(calls)==72
        elif mode=='one_bad':assert state['status']=='completed_with_quarantine' and len(calls)==72
        elif mode in {'two_bad','incomplete'}:assert state['status']=='stopped' and len(calls)==2
        elif mode=='input_budget':assert state['status']=='stopped' and len(calls)<72 and 'budget' in state['error']
        else:assert state['status']=='stopped' and len(calls)==1
        for path in (out/'actual_requests').glob('*.json'):
            row=plan['schedule'][int(path.stem)-1];case=io.read(p/'cases'/f"{row['case_id']}.json")
            assert io.read(path)==front.request(case,row['method'],examples)
        evaluation=io.read(out/'EVALUATION_TEMPLATE.json')
        assert len(evaluation['rows'])==72 and all(r['reference_match'] is None for r in evaluation['rows'])
        outcomes[mode]=dict(status=state['status'],attempts=len(calls),missing=sum(r['status']!='readable' for r in review['rows']),
            unresolved=sum(r['status']=='readable' and r['answer']['choice'] is None for r in review['rows']),
            max_input_estimate=max(r['estimated_input_count'] for r in requests),error=state['error'])
    sample=io.read(p/'cases'/f"{index[0]['case_id']}.json")['packet']
    bad=['{}','[]','{"choice":null}','{"choice":"illegal","reasoning":"x"}',
         '{"choice":null,"reasoning":" "}','{"choice":null,"reasoning":4}',
         '{"choice":null,"choice":null,"reasoning":"x"}','{"choice":null,"reasoning":"x"} trailing']
    for raw in bad:
        try:terminal.decode(raw,sample)
        except ValueError:pass
        else:raise AssertionError('invalid core accepted')
    touched=[]
    try:runner.run(p,validation/'unauthorized',transport=lambda *a:touched.append(True))
    except (FileNotFoundError,ValueError):pass
    else:raise AssertionError('launch gate bypassed')
    assert not touched
    try:runner.run(p,validation/'implicit_network',local_validation=True)
    except ValueError:pass
    else:raise AssertionError('fixture transport missing')
    target=p/'cases'/f"{index[0]['case_id']}.json";old=target.read_bytes()
    try:
        target.write_bytes(old+b' ')
        try:runner.verify(p)
        except ValueError:pass
        else:raise AssertionError('tamper accepted')
    finally:target.write_bytes(old)
    runner.verify(p)
    examples_tokens={method:count(json.dumps(examples[method],ensure_ascii=False)) for method in ['positive_examples','contrastive_examples']}
    io.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),new_api_calls=0,
        scenarios=outcomes,case_input_matching=12,example_facts_and_correct_actions_match=True,
        raw_historical_replay_contexts=8,cross_task_real_carrier_controls=4,synthetic_stress_labelled=True,
        invalid_core_rejections=len(bad),offline_labels_absent=True,source_access_and_fixed_finding_preserved=True,
        frozen_tamper_guard=True,transport_untouched_without_gates=True,input_estimates=lengths,
        total_input_estimate=sum(lookup[(r['case_id'],r['method'])] for r in plan['schedule']),
        example_tokens=examples_tokens,code_sha256=manifest['code_sha256'],
        caveat='Engineering replay only; no new method outputs or semantic performance generated.'))
    print(json.dumps(dict(status='passed',scenarios={k:v['attempts'] for k,v in outcomes.items()},example_tokens=examples_tokens,
        max_input=max(r['input_estimate'] for r in lengths),total_input_estimate=sum(lookup[(r['case_id'],r['method'])] for r in plan['schedule']),new_api_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepared',type=Path,default=runner.DEFAULT);check(parser.parse_args().prepared)
