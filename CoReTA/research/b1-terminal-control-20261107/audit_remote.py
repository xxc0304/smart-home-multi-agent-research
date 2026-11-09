import json
from collections import Counter
from runner import OUT,HERE,ROOT,load,sha,verify_freeze,decode,validate_pack,atomic
from b0_training import load_tokenizer
s=load(OUT/'STATUS.json');assert s['status']=='COMPLETE' and s['completed']==48
pack=load(OUT/'DIAGNOSTIC_INPUTS.json');validate_pack(pack);verify_freeze()
rs=[json.loads(x) for x in (OUT/'responses.jsonl').read_text().splitlines()]
attempts=[json.loads(x) for x in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()]
assert len(rs)==48 and len({r['request']['id'] for r in rs})==48
assert Counter(a['event'] for a in attempts)=={'START':48,'RETURN':48}
tok=load_tokenizer(load(OUT/'diagnostic_config.json'));byid={r['request']['id']:r for r in rs}
for q in pack['schedule']:
 r=byid[q['id']];assert r['request']==q
 u=r['response']['usage'];assert r['response']['status']=='OK' and u['ended_with_eos'] and u['finish_reason']=='EOS'
 assert u['batch_size']==1 and u['output_cap']==256 and u['output_tokens']==len(u['output_ids'])
 assert u['lora_layers']==252 and u['disabled_layers']==(0 if q['adapter']=='on' else 252)
 assert u['adapter_enabled']==(q['adapter']=='on')
 assert tok.decode(u['output_ids'],skip_special_tokens=True)==r['response']['raw_output']
 ids=tok.apply_chat_template([{'role':k,'content':q['payload'][k]} for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,enable_thinking=False)
 assert len(ids)==u['input_tokens'] and len(ids)+256<=16384
score=load(OUT/'scores.json');original=[r for r in score['rows'] if r['adapter']=='on' and r['rep']==0]
out={'verdict':'PASS','scope':'ACTUAL_REQUEST_ROUTE_TOKEN_AND_FREEZE_AUDIT_NOT_INDEPENDENT_HUMAN','attempts':48,'returns':48,'all_OK_EOS':True,'output_tokens':sum(r['response']['usage']['output_tokens'] for r in rs),'actual_on_off_routes':dict(Counter(r['request']['adapter'] for r in rs)),'on_original_seed_exact_matches':sum(r['originalFinalMatch'] for r in original),'on_original_seed_n':len(original),'source_and_freeze_unchanged':True,'max_input_plus_cap':max(r['response']['usage']['input_tokens']+256 for r in rs),'reviewer':'assistant','independence':'none/provisional'}
atomic(HERE/'POST_RUN_AUDIT.json',out);print(json.dumps(out))
