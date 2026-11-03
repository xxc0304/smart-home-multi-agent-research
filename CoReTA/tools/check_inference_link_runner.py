"""Full offline runner replay and failure simulation; fixtures are not new model results."""
import argparse
import json
import urllib.error
from pathlib import Path

from tokenizers import Tokenizer
from coreta.schemas import ProtocolError
import local_judgment_frontend as io
import inference_link_probe_v1 as front
import local_reconstruction_probe as decoder
import minimal_final_answer_contract as terminal
import run_inference_link as runner


def check(prepared):
    p=Path(prepared)
    manifest,plan=runner.verify(p)
    validation=p/'local_validation'
    if validation.exists():
        raise ValueError('validation exists; preserve it and freeze a new version after changes')
    validation.mkdir()
    tokenizer=Tokenizer.from_file(str(runner.TOKENIZER))
    count=lambda text:len(tokenizer.encode(text,add_special_tokens=False).ids)
    index={row['case_id']:row for row in io.read(p/'CASE_INDEX.json')}
    outcomes={}
    # Core validity is deliberately separate from truth or unknown judgments.
    case=io.read(p/'cases'/f"{plan['schedule'][0]['case_id']}.json")
    for bad in ['{}','{"text":null}','{"text":1}','{"text":" "}','{"text":"a","text":"b"}','{"text":NaN}']:
        try:decoder.decode_local(bad)
        except ValueError:pass
        else:raise AssertionError('invalid first-stage core accepted')
    for bad in ['{}','{"choice":1,"reasoning":"x"}','{"choice":"unknown-id","reasoning":"x"}',
                '{"choice":null,"reasoning":""}','{"choice":null,"reasoning":7}',
                '{"choice":null,"choice":null,"reasoning":"x"}']:
        try:terminal.decode(bad,case['receiver_context'])
        except ValueError:pass
        else:raise AssertionError('invalid final core accepted')
    for entry in index.values():
        c=io.read(p/'cases'/f"{entry['case_id']}.json");v=c['receiver_context'];selected=c['selected_statement']
        assert v['historical_work']['reasoning'][selected['start']:selected['end']]==selected['text']
        assert 'local_question' not in v and v['prior_local_question']['addressed_member']==v['local_reconstruction']['author']
        assert front.packet(front.first_request(c,front.METHODS[0]))==front.packet(front.first_request(c,front.METHODS[1]))
        for a in c['visible_anchors']:
            value=v
            for key in a['pointer']:value=value[key]
            assert value==a['text']
    for mode in ['history','stress','one_bad_local','two_bad_local','one_bad_final','extra_annotations',
                 'unresolved','incomplete','transport','unknown_usage','output_over_cap','input_budget']:
        out=validation/mode
        calls=[]
        def transport(payload,timeout):
            current=max(int(x.stem) for x in (out/'actual_requests').glob('*.json'))
            row=plan['schedule'][current-1]
            case=io.read(p/'cases'/f"{row['case_id']}.json")
            calls.append(current)
            if mode=='transport':
                raise urllib.error.URLError('offline simulated transport failure')
            if row['stage']=='local':
                text=(runner.ROOT/index[row['case_id']]['carrier_raw']).read_text(encoding='utf-8')
                if mode=='stress':
                    decoded=decoder.decode_local(text)
                    while count(json.dumps(dict(text=decoded['text']),ensure_ascii=False))<1400:
                        decoded['text']+=' Synthetic length stress only; no new task evidence.'
                    text=json.dumps(dict(text=decoded['text']),ensure_ascii=False)
            else:
                text=(runner.ROOT/index[row['case_id']]['answer_path']).read_text(encoding='utf-8')
            if mode=='extra_annotations':
                value=io.strict_json(text)
                value['optional_note']='fixture annotation, not evidence'
                text=json.dumps(value,ensure_ascii=False)
            if mode=='unresolved' and row['stage']=='final':
                text='{"choice":null,"reasoning":"Cannot offer a defensible answer from this fixture."}'
            if (mode=='one_bad_local' and len(calls)==1) or (mode=='two_bad_local' and len(calls)<=2):
                text='{"text":'
            if mode=='one_bad_final' and len(calls)==2:
                text='{"choice":null}'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False,separators=(',',':')))+256,
                       output_tokens=count(text))
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='output_over_cap':usage['output_tokens']=1537
            if mode=='input_budget':usage['input_tokens']=16384
            return dict(status='incomplete' if mode=='incomplete' else 'completed',
                output=[dict(type='message',content=[dict(type='output_text',text=text)])],usage=usage)
        state=runner.run(p,out,transport=transport,local_validation=True)
        review=io.read(out/'review.json')
        exported=io.read(out/'EVALUATION_TEMPLATE.json')['summary']
        assert len(review['rows'])==24 and exported['final_units']==12
        assert state['attempts']==len(calls)
        requests=[io.strict_json(x) for x in (out/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
        assert all(row['retry']==0 for row in requests)
        assert all(r['semantic_application'] is None for pair in io.read(out/'EVALUATION_TEMPLATE.json')['pairs']
                   for r in pair['conditions'].values())
        if mode in {'history','stress','extra_annotations','unresolved'}:
            assert state['status']=='completed' and len(calls)==24,state
            assert exported['technical_missing']==0
            assert exported['unresolved']==(12 if mode=='unresolved' else 0)
        elif mode=='one_bad_local':
            assert state['status']=='completed_with_quarantine' and len(calls)==23
            assert review['rows'][1]['status']=='blocked_upstream'
            assert exported['technical_missing']==1
        elif mode=='one_bad_final':
            assert state['status']=='completed_with_quarantine' and len(calls)==24
            assert exported['technical_missing']==1
        elif mode in {'two_bad_local','incomplete'}:
            assert state['status']=='stopped' and len(calls)==2
            assert exported['technical_missing']==12
        elif mode=='input_budget':
            assert state['status']=='stopped' and len(calls)<24 and 'budget' in state['error']
        else:
            assert state['status']=='stopped' and len(calls)==1
            assert exported['technical_missing']==12
        done={row['slot']:row for row in review['rows']}
        for path in (out/'actual_requests').glob('*.json'):
            slot=int(path.stem)
            row=plan['schedule'][slot-1]
            case=io.read(p/'cases'/f"{row['case_id']}.json")
            req=io.read(path)
            packet=front.packet(req)
            def labels_absent(value):
                if isinstance(value,dict):
                    assert not set(value)&{'local_criteria','final_criteria','correct_option_id','reference_match','case_rubric'}
                    for v in value.values():labels_absent(v)
                elif isinstance(value,list):
                    for v in value:labels_absent(v)
            labels_absent(packet)
            if row['stage']=='local':
                assert req==front.first_request(case,row['method'])
            else:
                previous=done[slot-1]
                assert previous['status']=='readable'
                assert req==front.final_request(case,previous['answer'])
                assert packet['inference_link_review']['text']==previous['answer']['text']
                assert set(packet['inference_link_review'])=={'author','text'}
        outcomes[mode]=dict(status=state['status'],attempts=len(calls),export=exported,
            error=state['error'],max_input_estimate=max(r['estimated_input_count'] for r in requests),
            reserved_input=state['reserved_input'],actual_input=state['input_tokens'])
    # Missing preflight/review/authorization cannot reach even an injected transport.
    touched=[]
    try:
        runner.run(p,validation/'unauthorized',transport=lambda *args:touched.append(True))
    except (FileNotFoundError,ValueError):pass
    else:raise AssertionError('live gates bypassed')
    assert not touched
    try:
        runner.run(p,validation/'implicit-local',local_validation=True)
    except ValueError:pass
    else:raise AssertionError('local validation could use live transport')
    # Frozen context tampering fails before transport. Restore the exact original bytes.
    target=p/'cases'/f"{plan['schedule'][0]['case_id']}.json"
    data=target.read_bytes()
    try:
        target.write_bytes(data+b' ')
        try:runner.verify(p)
        except ValueError:pass
        else:raise AssertionError('tampering accepted')
    finally:target.write_bytes(data)
    runner.verify(p)
    # Direct client context overflow must be rejected without invoking its transport.
    client=runner.DeepSeekClient(runner.config(),lambda *a:None,
        transport=lambda *a:touched.append(True),token_counter=count)
    payload=client.payload('source '*20000,dict(type='object'),1536)
    try:client.complete(payload,deadline=runner.time.monotonic()+5,logical_seed=1)
    except ProtocolError as exc:assert exc.code=='CONTEXT_OVERFLOW'
    else:raise AssertionError('context guard bypassed')
    assert not touched
    evidence=dict(status='passed',mode='local_fixture_only',manifest_sha256=io.digest(p/'manifest.json'),
        new_api_calls=0,scenarios=outcomes,exact_downstream_packet_reconstruction=True,
        offline_labels_absent=True,core_type_and_duplicate_key_boundaries=True,exact_source_anchor_and_target_offsets=True,explicit_role_addressee=True,frozen_source_and_input_tamper_guard=True,
        gated_transport_untouched=True,context_overflow_before_transport=True,
        interpretation='Real full EXTRACT text carriers and unmodified modern final outputs; interface replay only, not new inference-review results.',
        code_sha256=manifest['code_sha256'])
    io.write(p/'PREFLIGHT.json',evidence)
    print(json.dumps(dict(status='passed',manifest_sha256=evidence['manifest_sha256'],
                         scenarios={k:v['attempts'] for k,v in outcomes.items()},new_api_calls=0)))


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('--prepared',type=Path,default=runner.DEFAULT)
    check(parser.parse_args().prepared)
