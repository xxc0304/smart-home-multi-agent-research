"""Network-free historical replay, representation checks, and failure/cost tests."""
import copy
import json
import urllib.error
from tokenizers import Tokenizer
import evidence_layer_probe as run
import local_judgment_frontend as io
from prepare_evidence_layer_audit import restore

def check(p):
    run.verify(p);root=p/'local_validation'
    if root.exists():raise ValueError('new validation directory required')
    root.mkdir();tok=Tokenizer.from_file(str(run.TOKENIZER));count=lambda s:len(tok.encode(s,add_special_tokens=False).ids)
    outcomes={};sizes=[]
    for task in ('030','033'):
        for m in ('A1','A2','A3'):
            nested=io.read(p/'packets'/f'{task}-{m}'/'nested.json');layered=io.read(p/'packets'/f'{task}-{m}'/'layered.json')
            assert restore(layered)==nested
            occurrences=nested['public_sources']+nested['own_sources']+[s for r in nested['contributor_reports'] for s in r['disclosed_originals']]
            assert occurrences==layered['available_original_documents']
    for mode in ('history','long','one_bad','two_bad','null','transport','unknown_usage','over_output','input_cap'):
        out=root/mode;calls=[]
        def transport(payload,timeout):
            slot=max(int(f.stem) for f in (out/'actual_requests').glob('*.json'));row=run.schedule()[slot-1];calls.append(slot)
            assert payload['instructions'].split('PACKET=')[0]==run.PROMPT.split('PACKET=')[0]
            packet=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
            def no_gold(v):
                if isinstance(v,dict):
                    assert not set(v)&{'correct_option_id','expected_choice','reference_match','rubric','purpose'}
                    for x in v.values():no_gold(x)
                elif isinstance(v,list):
                    for x in v:no_gold(x)
            no_gold(packet)
            if mode=='transport':raise urllib.error.URLError('local fixture only')
            raw=(run.ROOT/'runs/confidence-visibility-live-20261026-r2'/f"{(7 if row['task']=='030' else 14):03d}.raw.txt").read_text(encoding='utf-8')
            if mode=='long':
                value=io.strict_json(raw)
                while count(json.dumps(value))<1400:value['reasoning']+=' Synthetic long-response test only.'
                raw=json.dumps(value)
            if mode=='null':raw=(run.ROOT/'runs/confidence-visibility-live-20261026-r2/004.raw.txt').read_text(encoding='utf-8')
            if mode=='one_bad' and slot==1 or mode=='two_bad' and slot in (1,2):raw='{"choice":'
            usage=dict(input_tokens=count(json.dumps(payload,ensure_ascii=False))+256,output_tokens=count(raw));sizes.append(usage['input_tokens'])
            if mode=='unknown_usage':usage.pop('input_tokens')
            if mode=='over_output':usage['output_tokens']=1537
            if mode=='input_cap':usage['input_tokens']=16384
            return dict(status='completed',usage=usage,output=[dict(type='message',content=[dict(type='output_text',text=raw)])])
        state=run.run(p,out,transport=transport,local=True);review=io.read(out/'review.json')['rows']
        assert len(review)==24 and state['attempts']==len(calls)
        assert len(io.read(out/'SCORES.json')['rows'])==24
        logs=list(map(io.strict_json,(out/'requests.jsonl').read_text(encoding='utf-8').splitlines()))
        assert all(r['retry']==0 for r in logs) and len(logs)==len(calls)
        if mode in ('history','long','null','input_cap'):assert state['status']=='completed' and len(calls)==24,state
        elif mode=='one_bad':assert state['status']=='completed_with_quarantine' and len(calls)==24
        elif mode=='two_bad':assert state['status']=='stopped' and len(calls)==2
        else:assert state['status']=='stopped' and len(calls)==1
        if mode=='input_cap':assert state['input_tokens']==run.LIMITS['input']
        if mode=='null':assert all(r['unresolved'] and not r['reference_match'] for r in io.read(out/'SCORES.json')['rows'])
        for row in review:
            file=out/'actual_requests'/f"{row['slot']:03d}.json"
            if file.exists():assert io.read(file)==run.request_for(p,row)[0]
        outcomes[mode]=dict(status=state['status'],attempts=state['attempts'])
    packet=io.read(p/'packets/030-A1/nested.json')
    bad=['{}','null','{"choice":','{"choice":"unknown","reasoning":"x"}',
         '{"choice":true,"reasoning":"x"}','{"choice":"option_1","reasoning":1}',
         '{"choice":"option_1","reasoning":" "}','{"choice":null,"choice":null,"reasoning":"x"}',
         '{"choice":NaN,"reasoning":"x"}']
    for raw in bad:
        try:run.terminal.decode(raw,packet)
        except ValueError:pass
        else:raise AssertionError('invalid core accepted')
    run.terminal.decode('{"choice":null,"reasoning":"Unknown","extra":1}',packet)
    try:run.gates(p)
    except (ValueError,FileNotFoundError):pass
    else:raise AssertionError('unauthorized launch gate passed')
    result=dict(status='passed',manifest_sha256=io.digest(p/'manifest.json'),network_calls=0,modes=outcomes,
        invalid_core_rejections=len(bad),max_fixture_input_tokens=max(sizes),per_input_cap=16384,
        source_occurrence_preserving_roundtrips=6,real_full_carriers='030/033 complete historical source packets, original member contributions and actual 004/007/014 final outputs',
        scope='local technical validation, not scientific results; synthetic length extensions identified',
        pair_prompt_identical=True)
    io.write(p/'PREFLIGHT.json',result);return result

if __name__=='__main__':print(json.dumps(check(run.PREPARED),ensure_ascii=False))
