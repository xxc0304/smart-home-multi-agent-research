"""Full historical carrier replay and synthetic annotation boundary tests; no network."""
import copy
import json
import urllib.error
from pathlib import Path
from tokenizers import Tokenizer
import confidence_visibility_probe as probe
import local_judgment_frontend as io

def check(p):
    probe.verify(p);root=p/'local_validation'
    if root.exists():raise ValueError('new local validation required')
    root.mkdir();tok=Tokenizer.from_file(str(probe.previous.TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    outcomes={};max_input=0
    modes=['history','stress','one_bad_annotation','two_bad_annotations','one_bad_final','transport','unknown_usage','over_output','input_budget']
    for mode in modes:
        out=root/mode;trace=[]
        def transport(payload,timeout):
            nonlocal max_input
            slot=max(int(f.stem) for f in (out/'actual_requests').glob('*.json'))
            row=probe.schedule()[slot-1];trace.append(slot)
            request=io.read(out/'actual_requests'/f'{slot:03d}.json')
            packet=io.strict_json(request['instructions'].split('PACKET=',1)[1])
            assert not any(key in request['instructions'] for key in ['correct_option_id','expected_choice','reference_match','rubric'])
            if mode=='transport':raise urllib.error.URLError('local fixture only')
            if row['stage']=='annotate':
                assert not set(packet)&{'contributor_reports','target_answer'}
                assert [s['ref'] for s in packet['own_sources']]==['PRIVATE.'+row['receiver']]
                # New annotation contract has no real historical responses. Synthetic marks only;
                # actual original full contributions are retained and used downstream.
                quote=packet['fixed_contribution']['text']
                value=dict(local_judgment=dict(quote=quote,confidence=80),overall_recommendation=dict(quote=quote,confidence=50.0))
                raw=json.dumps(value,ensure_ascii=False)
            else:
                carrier=14 if row['method']=='hidden' else 16
                raw=(probe.HISTORY/f'{carrier:03d}.raw.txt').read_text(encoding='utf-8')
                if mode=='stress':
                    value=io.strict_json(raw)
                    while count(json.dumps(value))<1400:value['reasoning']+=' Synthetic length extension only.'
                    raw=json.dumps(value)
            if mode=='one_bad_annotation' and slot==1 or mode=='two_bad_annotations' and slot in (1,2) or mode=='one_bad_final' and slot==4:raw='{"text":'
            size=count(json.dumps(payload,ensure_ascii=False))+256;max_input=max(max_input,size)
            usage=dict(input_tokens=size,output_tokens=count(raw))
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='over_output':usage['output_tokens']=1537
            if mode=='input_budget':usage['input_tokens']=16384
            return dict(status='completed',usage=usage,output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
        state=probe.run(p,out,transport=transport,local=True)
        review=io.read(out/'review.json')['rows'];assert len(review)==18
        assert state['attempts']==len(trace)
        logs=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
        assert len(logs)==len(trace) and all(r['retry']==0 for r in logs)
        if mode in ('history','stress'):assert state['status']=='completed' and len(trace)==18,state
        elif mode=='one_bad_annotation':
            assert state['status']=='completed_with_quarantine' and len(trace)==12
            assert all(r['status']=='blocked_annotation' for r in review[3:9])
        elif mode=='two_bad_annotations':assert state['status']=='stopped' and len(trace)==2
        elif mode=='one_bad_final':assert state['status']=='completed_with_quarantine' and len(trace)==18
        elif mode in ('transport','unknown_usage','over_output'):assert state['status']=='stopped' and len(trace)==1
        else:
            # 18 * per-input cap equals this batch's total cap: exactly the cap is valid.
            assert state['status']=='completed' and len(trace)==18 and state['input_tokens']==probe.LIMITS['input']
        # Reassemble from full outputs, verify that only confidence visibility changes paired input.
        annotations={}
        for row in review:
            if row['stage']=='annotate' and row['status']=='readable':annotations[row['task'],row['receiver']]=row['answer']
        if mode=='history':
            for t in probe.TASKS:
                for m in probe.MEMBERS:
                    hidden,ph=probe.request_for(p,dict(task=t,receiver=m,stage='final',method='hidden'),annotations)
                    shown,ps=probe.request_for(p,dict(task=t,receiver=m,stage='final',method='shown'),annotations)
                    stripped=copy.deepcopy(ps)
                    for report in stripped['contributor_reports']:
                        for field in probe.FIELDS:report['judgment_annotations'][field].pop('confidence')
                    assert ph==stripped
                    assert hidden['instructions'].split('PACKET=')[0]==shown['instructions'].split('PACKET=')[0]
                    assert len(ps['contributor_reports'])==3
        outcomes[mode]=dict(status=state['status'],attempts=state['attempts'])
    packet=io.read(p/'members/030/A1.json');packet['fixed_contribution']=io.read(p/'contributions/030/A1.json')
    quote=packet['fixed_contribution']['text'];valid={k:dict(quote=quote,confidence=50) for k in probe.FIELDS}
    probe.decode_annotation(json.dumps(valid),packet)
    probe.decode_annotation(json.dumps({k:dict(quote=None,confidence=None) for k in probe.FIELDS}),packet)
    bad=['{}','null','{"local_judgment":','{"x":1,"x":2}']
    for field,value in [('confidence',True),('confidence','80'),('confidence',101),('confidence',-1),('confidence',None),('quote','invented quote')]:
        v=copy.deepcopy(valid);v['local_judgment'][field]=value;bad.append(json.dumps(v))
    v=copy.deepcopy(valid);v['extra']=1;bad.append(json.dumps(v))
    bad.append(json.dumps(valid).replace('50','NaN',1))
    for raw in bad:
        try:probe.decode_annotation(raw,packet)
        except ValueError:pass
        else:raise AssertionError('bad annotation accepted: '+raw)
    final_packet=io.read(p/'members/030/A1.json')
    probe.terminal.decode('{"choice":null,"reasoning":"Unresolved"}',final_packet)
    probe.terminal.decode('{"choice":"option_1","reasoning":"Explanation","extra":1}',final_packet)
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),modes=outcomes,
        annotation_boundary_rejections=len(bad),max_fixture_input_tokens=max_input,input_cap=16384,
        real_carriers='Full historical 030/033 contributions, original member packets and 014/016 final responses',
        gap='No real confidence annotation responses yet; marks are synthetic fixtures, not model results or calibration evidence.',
        network_calls=0)
    io.write(p/'PREFLIGHT.json',result);return result

if __name__=='__main__':print(json.dumps(check(probe.PREPARED),ensure_ascii=False))
