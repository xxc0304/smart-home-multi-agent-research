"""Full offline API-contract replay/failure simulation; zero network calls."""
import argparse
import json
import os
import subprocess
import sys
import urllib.error
from pathlib import Path
from tokenizers import Tokenizer
from coreta.constraint_commit import session_from_receiver
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import constraint_commit_probe as front
import run_constraint_commit as runner


def check(prepared):
    p=Path(prepared);manifest,plan=runner.verify(p);root=p/'local_validation'
    if root.exists():raise ValueError('preserve validation; freeze a new version after code changes')
    root.mkdir();index={r['case_id']:r for r in io.read(p/'CASE_INDEX.json')}
    tok=Tokenizer.from_file(str(runner.TOKENIZER));count=lambda x:len(tok.encode(x,add_special_tokens=False).ids)
    modes=['history','stress','one_bad_core','two_bad_core','extra_annotations','null_choice',
        'invalid_optional_action','valid_optional_action','incomplete','transport','unknown_usage','output_over_cap','input_budget']
    results={}
    for mode in modes:
        out=root/mode;calls=[]
        def transport(payload,timeout):
            slot=max(int(x.stem) for x in (out/'actual_requests').glob('*.json'));row=plan['schedule'][slot-1]
            calls.append(slot)
            if mode=='transport':raise urllib.error.URLError('offline simulated transport failure')
            text=(runner.ROOT/index[row['case_id']]['carrier_raw']).read_text(encoding='utf-8')
            value=io.strict_json(text)
            if mode=='stress':
                while count(json.dumps(value,ensure_ascii=False))<1400:value['reasoning']+=' Offline length stress only; no new evidence.'
                text=json.dumps(value,ensure_ascii=False)
            if mode=='extra_annotations':value['note']='OFFLINE extra metadata';text=json.dumps(value)
            if mode=='null_choice':value['choice']=None;text=json.dumps(value)
            if mode=='invalid_optional_action':value['updates']=[dict(entry_id='unknown')];text=json.dumps(value)
            if mode=='valid_optional_action':
                c=io.read(p/'cases'/(row['case_id']+'.json'));s=session_from_receiver(c['context'],c['field_types'])
                value['updates']=[dict(entry_id=next(iter(s.entries)),action='retire',reason='OFFLINE action carrier, not justified semantic revision.',evidence_ids=[next(iter(s.evidence))])]
                text=json.dumps(value)
            if (mode=='one_bad_core' and len(calls)==1) or (mode=='two_bad_core' and len(calls)<=2):text='{"choice":'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256,output_tokens=count(text))
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='output_over_cap':usage['output_tokens']=1537
            if mode=='input_budget':usage['input_tokens']=16384
            return dict(status='incomplete' if mode=='incomplete' else 'completed',
                output=[dict(type='message',content=[dict(type='output_text',text=text)])],usage=usage)
        state=runner.run(p,out,transport=transport,local_validation=True)
        review=io.read(out/'review.json');evaluation=io.read(out/'EVALUATION_TEMPLATE.json')
        assert state['attempts']==len(calls)
        assert len(review['rows'])==18 and len(evaluation['rows'])==18
        logs=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        assert all(r['retry']==0 for r in logs)
        assert all(r['final_quality'] is None and r['wrong_exclusion'] is None for r in evaluation['rows'])
        if mode in {'history','stress','extra_annotations','null_choice','invalid_optional_action','valid_optional_action'}:
            assert state['status']=='completed' and len(calls)==18,state['error']
            assert evaluation['summary']['technical_missing']==0
        elif mode=='one_bad_core':
            assert state['status']=='completed_with_quarantine' and len(calls)==18
            assert evaluation['summary']['technical_missing']==1
        elif mode in {'two_bad_core','incomplete'}:
            assert state['status']=='stopped' and len(calls)==2
        elif mode=='input_budget':assert state['status']=='stopped' and len(calls)==16 and 'budget' in state['error']
        else:assert state['status']=='stopped' and len(calls)==1
        for r in state['rows']:
            raw=out/f"{r['slot']:03d}.raw.txt"
            if r['status'] in {'readable','quarantined'}:assert raw.exists()
            if r['status']=='readable':
                case=io.read(p/'cases'/(r['case_id']+'.json'));session=session_from_receiver(case['context'],case['field_types'])
                rebuilt=front.process(raw.read_text(encoding='utf-8'),case['context'],session,r['method'],1)
                assert rebuilt==r['answer']
                if mode=='invalid_optional_action':assert r['answer']['action']['status']=='rejected_optional_action'
                if mode=='valid_optional_action':assert r['answer']['report']['version']==2
        for path in (out/'actual_requests').glob('*.json'):
            row=plan['schedule'][int(path.stem)-1];case=io.read(p/'cases'/(row['case_id']+'.json'))
            session=session_from_receiver(case['context'],case['field_types'])
            req=io.read(path);assert req==front.request(case['context'],session,row['method'])
            packet=front.packet(req)
            assert not set(packet)&{'correct_option_id','official_correct_text','control_purpose','historical_work'}
        results[mode]=dict(status=state['status'],attempts=len(calls),max_input_estimate=max(r['estimated_input_count'] for r in logs),
            reserved_input=state['reserved_input'],input_tokens=state['input_tokens'],error=state['error'])
    # Two arms share every packet field and response schema, not merely source IDs.
    for cid in index:
        c=io.read(p/'cases'/(cid+'.json'));s=session_from_receiver(c['context'],c['field_types'])
        a,b=[front.request(c['context'],s,m) for m in front.METHODS]
        assert front.packet(a)==front.packet(b) and a['schema']==b['schema']
    touched=[]
    try:runner.run(p,root/'no-authorization',transport=lambda *a:touched.append(True))
    except (FileNotFoundError,ValueError):pass
    else:raise AssertionError('authorization gate bypassed')
    try:runner.run(p,root/'implicit-live',local_validation=True)
    except ValueError:pass
    else:raise AssertionError('implicit live transport in local mode')
    assert not touched
    target=p/'cases/history-01.json';old=target.read_bytes()
    try:
        target.write_bytes(old+b' ')
        try:runner.verify(p)
        except ValueError:pass
        else:raise AssertionError('tamper accepted')
    finally:target.write_bytes(old)
    runner.verify(p)
    client=runner.DeepSeekClient(runner.config(),lambda *a:None,transport=lambda *a:touched.append(True),token_counter=count)
    try:client.complete(client.payload('input '*20000,dict(type='object'),1536),deadline=runner.time.monotonic()+5,logical_seed=1)
    except ProtocolError as exc:assert exc.code=='CONTEXT_OVERFLOW'
    else:raise AssertionError('long context reached transport')
    assert not touched
    # Instructions embed JSON text: dictionary order must be stable across fresh
    # Python hash seeds, not just structurally equal in this checker process.
    script=("import hashlib,json,sys;from pathlib import Path;import local_judgment_frontend as io;"
        "from coreta.constraint_commit import session_from_receiver;import constraint_commit_probe as f;"
        "c=io.read(Path(sys.argv[1])/'cases/history-01.json');s=session_from_receiver(c['context'],c['field_types']);"
        "r=f.request(c['context'],s,'constraint_commit');print(hashlib.sha256(json.dumps(r,sort_keys=True).encode()).hexdigest())")
    digests=[]
    for seed in ('101','202'):
        env=dict(os.environ,PYTHONHASHSEED=seed)
        digests.append(subprocess.check_output([sys.executable,'-c',script,str(p.resolve())],env=env,cwd=runner.ROOT,text=True).strip())
    assert len(set(digests))==1,'payload order varies across process hash seeds'
    evidence=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),new_api_calls=0,scenarios=results,
        exact_full_body_processing_replay=True,paired_packet_and_schema_equal=True,cross_process_payload_hash=digests[0],optional_action_failures_separate=True,
        incomplete_roster_exported=True,semantic_scores_unfilled=True,source_and_code_tamper_guard=True,transport_gates_untouched=True,
        carrier_scope='Three same-task modern real finals; controls reuse a real modern final from another task for interface only. No new model revisions or semantic success claimed.')
    io.write(p/'PREFLIGHT.json',evidence)
    print(json.dumps(dict(status='passed',manifest_sha256=evidence['manifest_sha256'],new_api_calls=0,
        scenarios={k:v['attempts'] for k,v in results.items()})))

if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepared',type=Path,default=runner.DEFAULT)
    check(parser.parse_args().prepared)
