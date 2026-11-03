"""Local complete-history replay and synchronous routing/privacy/failure checks."""
import copy
import json
import urllib.error
from tokenizers import Tokenizer
import imp_adaptation_probe as run
import imp_router as router
import local_judgment_frontend as io

def check(p):
    run.verify(p);root=p/'local_validation'
    if root.exists():raise ValueError('new validation directory required')
    root.mkdir();tok=Tokenizer.from_file(str(run.TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    modes=('history','long','bad_initial','two_bad','bad_update','bad_final','null','transport','unknown_usage','over_output','input_cap')
    outcomes={};sizes=[]
    for mode in modes:
        out=root/mode;calls=[]
        def transport(payload,timeout):
            slot=max(int(f.stem) for f in (out/'actual_requests').glob('*.json'));row=run.schedule()[slot-1];calls.append(slot)
            packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1]);bundle=io.read(p/'tasks'/f"{row['task']}.json")
            assert 'shared_information' not in packet['task']
            assert not any(k in payload['instructions'] for k in ('correct_option_id','reference_match','rubric'))
            if row['method']=='full_information':assert packet['information_available']==list(bundle['documents'].values()) and 'previous_answer' not in packet
            else:
                assert [s['ref'] for s in packet['information_available']]==bundle['owned'][row['receiver']]
                if not row['round']:assert not set(packet)&{'messages_from_other_participants','previous_answer'}
                elif row['method']=='imp':
                    inbox=packet['messages_from_other_participants'];refs=[s['ref'] for s in inbox]
                    assert len(refs)==len(set(refs)) and not set(refs)&set(bundle['owned'][row['receiver']])
                    assert all(s==bundle['documents'][s['ref']] for s in inbox)
                    assert all(set(s)=={'ref','content'} for s in inbox)
                else:assert len(packet['messages_from_other_participants'])==2
            if mode=='transport':raise urllib.error.URLError('fixture only')
            carrier=14 if row['task']=='030' else 24
            raw=(run.ROOT/'runs/receiver-confirmation-live-20261026-r1'/f'{carrier:03d}.raw.txt').read_text(encoding='utf-8')
            if mode=='null':raw=(run.ROOT/'runs/confidence-visibility-live-20261026-r2/004.raw.txt').read_text(encoding='utf-8')
            if mode=='long':
                value=io.strict_json(raw)
                while count(json.dumps(value))<900:value['reasoning']+=' Synthetic length-only addition.'
                raw=json.dumps(value)
            if (mode=='bad_initial' and slot==1 or mode=='two_bad' and slot in (1,2) or mode=='bad_update' and slot==4 or mode=='bad_final' and slot==10):raw='{"choice":'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False))+256,output_tokens=count(raw));sizes.append(usage['input_tokens'])
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='over_output':usage['output_tokens']=1025
            if mode=='input_cap':usage['input_tokens']=16384
            return dict(status='completed',usage=usage,output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
        state=run.run(p,out,transport=transport,local=True);rows=io.read(out/'review.json')['rows'];assert len(rows)==64
        assert state['attempts']==len(calls)
        logs=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
        assert len(logs)==len(calls) and all(r['retry']==0 for r in logs)
        if mode in ('history','long','null','input_cap'):assert state['status']=='completed' and len(calls)==64,state
        elif mode=='bad_initial':assert state['status']=='completed_with_quarantine' and len(calls)==52
        elif mode=='bad_update':assert state['status']=='completed_with_quarantine' and len(calls)==61
        elif mode=='bad_final':assert state['status']=='completed_with_quarantine' and len(calls)==64
        elif mode=='two_bad':assert state['status']=='stopped' and len(calls)==2
        else:assert state['status']=='stopped' and len(calls)==1
        if mode=='input_cap':assert state['input_tokens']==run.LIMITS['input']
        if mode=='null':assert all(g['reference_score']==0 for g in io.read(out/'SCORES.json')['groups'])
        answers={}
        for row in rows:
            req,packet,audit=run.request_for(p,row,answers)
            file=out/'actual_requests'/f"{row['slot']:03d}.json"
            if file.exists():
                assert io.read(file)==req and io.read(out/'routing'/f"{row['slot']:03d}.json")==audit
            if row['status']=='readable':answers[run.key(row)]=row['answer']
        outcomes[mode]=dict(status=state['status'],attempts=state['attempts'])
    # Exact routing invariants without asking a model to judge relevance.
    docs={'S1':dict(ref='S1',content='Amber highway is closed.'),'S2':dict(ref='S2',content='Birch freezer is unavailable.'),'S3':dict(ref='S3',content='Cedar generator is restored.')}
    assert router.route(['S1'],{'A':['S1','S2'],'B':['S2','S3']},docs)==[docs['S2'],docs['S3']]
    assert router.route(['S1'],{},docs)==[]
    found,_=router.match('Birch freezer is unavailable.',['S2'],docs,'Choose a laboratory.')
    assert found==['S2']
    assert router.match('Birch freezer is unavailable.',['S1'],docs,'Choose a laboratory.')[0]==[]
    assert router.match('No substantive evidence mentioned.',['S2'],docs,'Choose a laboratory.')[0]==[]
    # Real historical member messages routed only to their own original records.
    history=run.ROOT/'runs/receiver-confirmation-live-20261026-r1';historical=[]
    for task,slots in [('030',(2,3,4)),('033',(18,19,20))]:
        bundle=io.read(p/'tasks'/f'{task}.json')
        for member,slot in zip(run.MEMBERS,slots):
            raw=io.strict_json((history/f'{slot:03d}.raw.txt').read_text(encoding='utf-8'))
            refs,details=router.match(raw['text'],bundle['owned'][member],bundle['documents'],bundle['task']['scenario']+' '+json.dumps(bundle['task']['choices']))
            assert set(refs)<=set(bundle['owned'][member])
            historical.append(dict(task=task,member=member,slot=slot,matched=refs,details=details))
    io.write(p/'HISTORICAL_ROUTING_REPLAY.json',historical)
    packet=io.read(p/'tasks/030.json');terminal_packet={'task':packet['task']}
    bad=['{}','null','{"choice":','{"choice":"bad","reasoning":"x"}','{"choice":true,"reasoning":"x"}',
        '{"choice":null,"reasoning":" "}','{"choice":null,"choice":null,"reasoning":"x"}','{"choice":NaN,"reasoning":"x"}']
    for raw in bad:
        try:run.terminal.decode(raw,terminal_packet)
        except ValueError:pass
        else:raise AssertionError('invalid response accepted')
    run.terminal.decode('{"choice":null,"reasoning":"Unknown","extra":1}',terminal_packet)
    try:run.gates(p)
    except (ValueError,FileNotFoundError):pass
    else:raise AssertionError('unauthorized launch passed')
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),network_calls=0,modes=outcomes,
        max_fixture_input_tokens=max(sizes),input_cap=16384,historical_member_messages_replayed=6,invalid_core_rejections=len(bad),
        invariants=['shared round-0','previous-round-only inputs','own-original matching only','no withheld original injected','unique missing source units only','received units do not mutate initial ownership','dependency blocking','no retry','full-information isolated'])
    io.write(p/'PREFLIGHT.json',result);return result

if __name__=='__main__':print(json.dumps(check(run.PREPARED),ensure_ascii=False))
