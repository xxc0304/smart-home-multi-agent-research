"""Network-free, real-carrier replay and failure-path checks for the receiver runner."""
import argparse
import copy
import json
import urllib.error
from pathlib import Path

from tokenizers import Tokenizer
import run_receiver_baseline as runner
import prepare_receiver_baseline_20261026 as front
import minimal_final_answer_contract as terminal
import local_judgment_frontend as io


def check(prepared):
    p=Path(prepared)
    _,plan=runner.verify(p)
    validation=p/'local_validation'
    if validation.exists():
        raise ValueError('validation already exists; freeze a new batch after changes')
    validation.mkdir()
    tok=Tokenizer.from_file(str(runner.TOKENIZER))
    count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    full=[]
    originals=io.read(runner.ROOT/'research/bottleneck-selection-20261026/MECHANISM_EVIDENCE.json')['walkthroughs']
    historical_log=runner.ROOT/'runs/candidate-screening-probe-live-20261025-r1/responses.jsonl'
    historical_rows={r['attempt']:r for r in map(json.loads,historical_log.read_text(encoding='utf-8').splitlines())}
    lineage=[]
    for case in originals:
        base=copy.deepcopy(case['actual_received_packet'])
        base['historical_work']=copy.deepcopy(case['draft'])
        base.pop('field_meanings')
        base['historical_author']=base['member']
        first_slot={'010':1,'023':85,'027':115,'011':13}[case['task']]
        common_contexts=[]
        for mi,member in enumerate(runner.MEMBERS):
            extract=io.strict_json(historical_rows[first_slot+mi]['response']['instructions'].split('PACKET=',1)[1])
            expected=copy.deepcopy(base)
            expected['member']=member
            expected['own_sources']=extract['own_sources']
            actual=io.read(p/'contexts'/case['task']/f'{member}.json')
            assert actual==expected and actual['member']==member
            assert actual['historical_author']=={'010':'A1','023':'A1','027':'A2','011':'A1'}[case['task']]
            assert 'field_meanings' not in actual
            for method in ('ordinary','diagnose'):
                req=front.first_request(actual,method)
                assert io.strict_json(req['instructions'].split('PACKET=',1)[1])==expected
            common_contexts.append({k:v for k,v in actual.items() if k not in {'member','own_sources'}})
            lineage.append(dict(task=case['task'],receiver=member,historical_author=actual['historical_author'],
                                own_sources_match_actual_extraction=True))
        assert all(c==common_contexts[0] for c in common_contexts)
    assert len(lineage)==16
    assert sum(r['method']=='ordinary' for r in plan['schedule'][::4])==8
    def fixture(mode):
        calls=[]
        def transport(payload, timeout):
            packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
            task=packet['task']['task_id'].split('-')[-1]
            stage='final' if 'prior_analysis' in packet else 'first'
            calls.append((task,stage))
            if mode=='transport': raise urllib.error.URLError('local fixture transport failure')
            # Matching-task real complete first carrier; the final is an explicitly
            # schema-adapted historical output, not a claimed real new-protocol response.
            slot={'010':1,'023':85,'027':115,'011':13}[task]+runner.MEMBERS.index(packet['member'])
            base=runner.ROOT/'runs/candidate-screening-probe-live-20261025-r1'
            if stage=='first':
                text=(base/f'{slot:02d}.raw.txt').read_text(encoding='utf-8')
                if mode=='stress':
                    raw=io.strict_json(text)
                    while count(json.dumps(raw,ensure_ascii=False))<1400:
                        raw['text']+=' This is a synthetic length stress extension, not additional task evidence.'
                    text=json.dumps(raw,ensure_ascii=False)
            else:
                final_slot={'010':6,'023':89,'027':119,'011':18}[task]
                old=io.read(base/f'{final_slot:02d}.raw.txt')
                ids={c['text']:c['id'] for c in packet['task']['choices']}
                text=json.dumps(dict(choice=ids.get(old['artifact'],old['artifact']),reasoning=old['reason']),ensure_ascii=False)
            if (mode=='one_bad_first' and len(calls)==1) or (mode=='two_bad_first' and stage=='first' and len(calls)<=2):
                text='{"text":'
            if mode=='one_bad_final' and len(calls)==2: text='{"choice":null}'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256,
                       output_tokens=count(text))
            if mode=='input_budget': usage['input_tokens']=16384
            if mode=='over_output': usage['output_tokens']=1537
            if mode=='unknown_usage': usage.pop('input_tokens')
            response=dict(status='completed',output=[dict(type='message',content=[dict(type='output_text',text=text)])],usage=usage)
            full.append(dict(mode=mode,task=task,stage=stage,fixture_output_tokens=count(text)))
            return response
        return transport,calls

    outcomes={}
    for mode in ['history','stress','one_bad_first','two_bad_first','one_bad_final',
                 'transport','unknown_usage','over_output','input_budget']:
        transport,calls=fixture(mode)
        out=validation/mode
        state=runner.run(p,out,transport=transport,local_validation=True)
        exported=runner.export(p,out)
        review=io.read(out/'review.json')
        assert len(review['rows'])==64
        assert state['attempts']==len(calls)
        reqs=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        assert all(r['retry']==0 for r in reqs)
        assert len(reqs)==len(calls)
        if mode in {'history','stress'}:
            assert state['status']=='completed' and len(calls)==64,state
            assert all(r['status']=='readable' for r in review['rows'])
            assert exported['missing_or_unresolved']==0
        elif mode=='one_bad_first':
            assert state['status']=='completed_with_quarantine' and len(calls)==63
            assert review['rows'][1]['status']=='blocked_upstream'
            assert exported['missing_or_unresolved']==1
        elif mode=='two_bad_first':
            assert state['status']=='stopped' and len(calls)==2
            assert exported['missing_or_unresolved']==32
        elif mode=='one_bad_final':
            assert state['status']=='completed_with_quarantine' and len(calls)==64
            assert exported['missing_or_unresolved']==1
        elif mode in {'transport','unknown_usage','over_output'}:
            assert state['status']=='stopped' and len(calls)==1
            assert exported['missing_or_unresolved']==32
        else:
            assert state['status']=='stopped' and len(calls)<64 and 'budget' in state['error']
        # Every actual second-stage input carries exactly the accepted first text for its unit.
        rows_by_slot={r['slot']:r for r in state['rows']}
        for request_path in (out/'actual_requests').glob('*.json'):
            slot=int(request_path.stem)
            row=plan['schedule'][slot-1]
            req=io.read(request_path)
            packet=io.strict_json(req['instructions'].split('PACKET=',1)[1])
            def no_labels(value):
                if isinstance(value,dict):
                    assert not set(value)&{'correct_option_id','official_correct_text','analyst_design_issue',
                        'analyst_design_target','case_rubric','reference_match','primary_checks'}
                    for nested in value.values():no_labels(nested)
                elif isinstance(value,list):
                    for nested in value:no_labels(nested)
            no_labels(packet)
            assert 'field_meanings' not in packet
            context=io.read(p/'contexts'/row['task']/f"{row['receiver']}.json")
            if row['stage']=='first': assert packet==context
            else:
                expected=copy.deepcopy(context)
                expected['prior_analysis']=rows_by_slot[slot-1]['answer']['text']
                assert packet==expected
        outcomes[mode]=dict(status=state['status'],attempts=state['attempts'],export=exported,
            maximum_input_estimate=max(r['estimated_input_count'] for r in reqs),
            total_input_estimate=sum(r['estimated_input_count'] for r in reqs),error=state['error'])

    # Modern real finals use their original actual task context, including missing optional metadata.
    history=runner.ROOT/'runs/evidence-first-live-20261025-r1'
    responses={r['attempt']:r for r in map(json.loads,(history/'responses.jsonl').read_text(encoding='utf-8').splitlines())}
    for slot in [18,36,63]:
        packet=io.strict_json(responses[slot]['response']['instructions'].split('PACKET=',1)[1])
        terminal.decode((history/f'{slot:03d}.raw.txt').read_text(encoding='utf-8'),packet)
    # No paid execution is possible with only an available transport: gates run first.
    touched=[]
    try:
        runner.run(p,validation/'unauthorized',transport=lambda *a:touched.append(True))
    except (FileNotFoundError,ValueError): pass
    else: raise AssertionError('live gates bypassed')
    assert not touched
    tamper_path=p/'contexts/010/A1.json'
    original=tamper_path.read_bytes()
    try:
        tamper_path.write_bytes(original+b' ')
        try: runner.verify(p)
        except ValueError: pass
        else: raise AssertionError('tamper accepted')
    finally: tamper_path.write_bytes(original)
    runner.verify(p)
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),live_model_requests=0,
        scenarios=outcomes,modern_real_final_replays=3,trace=full,
        receiver_and_context_lineage=lineage,offline_rubrics_not_sent=True,
        gates_block_unauthorized=True,tamper_rejected=True,
        limitations=['First stage replays full real matching-task EXTRACT carriers, not new diagnosis semantics.',
                    'Same-task legacy final reason/artifact renamed only in explicit fixture adapter; no claim of unmodified replay.',
                    'Long outputs have synthetic extensions; local checks cannot guarantee provider compliance.',
                    'Local fixture scores are not research results.'])
    io.write(p/'PREFLIGHT.json',result)
    return result


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('--prepared',type=Path,default=runner.DEFAULT)
    args=parser.parse_args();result=check(args.prepared)
    print(json.dumps({k:v for k,v in result.items() if k not in {'trace','limitations'}},ensure_ascii=False))
