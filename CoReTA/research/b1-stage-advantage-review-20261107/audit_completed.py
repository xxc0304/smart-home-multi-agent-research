"""Read-only actual-run audit and archive. No generation or rewriting old scores."""
import json,hashlib,tarfile
from collections import Counter
from repeat import ROOT,HERE,OUT,load,sha,verify_freeze,validate_pack,RepeatTrial,ARMS,ACTORS,atomic
from b1_controls import vote,vote_scores
from b0_answers import answer_score
from b0_training import load_tokenizer
verify_freeze();pack=load(OUT/'REPEAT_INPUTS.json');entries=validate_pack(pack)
status=load(OUT/'STATUS.json');assert status['status']=='COMPLETE'
scores=load(OUT/'scores.json');labels=load(OUT/'REPEAT_LABELS.json')['targets'];config=load(OUT/'repeat_config.json');tok=load_tokenizer(config)
flat=[json.loads(x) for x in (OUT/'responses.jsonl').read_text().splitlines()]
attempts=[json.loads(x) for x in (OUT/'ATTEMPTS.jsonl').read_text().splitlines()]
assert len(flat)==2855 and Counter(x['event'] for x in attempts)=={'START':2855,'RETURN':2855}
assert len({r['request_id'] for r in flat})==2855
byid={r['request_id']:r for r in flat};failures=[];cost={};maximum=0;recomputed=0
for e in entries:
 t=load(OUT/'trials'/f'{e["index"]:03d}.json');replay=RepeatTrial(e)
 for z in t['records']:
  req=replay.next_request();assert req and all(z[k]==v for k,v in req.items());assert byid[z['request_id']]==z
  u=z['usage'];assert u and u['batch_size']==1 and u['lora_layers']==252
  assert u['disabled_layers']==(0 if z['actor']=='M1' else 252) and u['adapter_enabled']==(z['actor']=='M1')
  assert u['output_cap']==z['max_new_tokens'] and u['output_tokens']==len(u['output_ids'])
  assert tok.decode(u['output_ids'],skip_special_tokens=True)==z['raw_output']
  n=len(tok.apply_chat_template([dict(role=k,content=z['payload'][k]) for k in ('system','user')],tokenize=True,add_generation_prompt=True,return_dict=False,**config['template_kwargs']))
  assert n==u['input_tokens'];maximum=max(maximum,n+z['max_new_tokens']);assert n+z['max_new_tokens']<=16384
  if z['status']=='OK':assert u['ended_with_eos'] and u['finish_reason']=='EOS'
  else:
   assert z['status']=='OUTPUT_LIMIT' and u['output_tokens']==z['max_new_tokens']
   failures.append(dict(index=e['index'],actor=z['actor'],arm=z['arm'],stage=z['stage'],round=z['round'],tokens=u['output_tokens'],output=z['raw_output'],seed=z['seed']))
  key=f'{z["arm"]}/{z["stage"]}/{"expert" if z["actor"]=="M1" else "ordinary"}'
  if key not in cost:cost[key]=dict(calls=0,output_tokens=0,seconds=0)
  cost[key]['calls']+=1;cost[key]['output_tokens']+=u['output_tokens'];cost[key]['seconds']+=u['elapsed_seconds']
  replay.submit(req['request_id'],z['raw_output'],status=z['status'],usage=u,source_kind=z['source_kind'])
 assert replay.next_request() is None and replay.export()==t
 row=next(r for r in scores['rows'] if r['id']==e['id']);assert row['complete']==t['complete']
 if len(t['initials'])==4:assert row['initial']=={a:answer_score(v,labels[e['id']]) for a,v in t['initials'].items()}
 else:assert row['initial'] is None
 for c in ARMS:
  if c in t['failed'] or len(t['finals'][c])!=4:assert row['arms'][c]=={'complete':False};continue
  members={a:answer_score(v,labels[e['id']]) for a,v in t['finals'][c].items()};v=vote(t['finals'][c],replay.base_seed+1001)
  assert row['arms'][c]==dict(complete=True,members=members,vote=v,**vote_scores(v,labels[e['id']]),expert_em=members['M1']['em']);recomputed+=1
assert len(failures)==2 and sum(x['usage']['output_tokens'] for x in flat)==status['output_tokens']
assert [z['request'] for z in attempts if z['event']=='START']==[{k:r[k] for k in ('request_id','arm','stage','round','actor','seed','max_new_tokens','payload')} for r in flat]
out=dict(verdict='PASS',scope='ACTUAL_REQUEST_REPLAY_ROUTE_LENGTH_TOKEN_SCORE_FREEZE_AUDIT',reviewer='assistant',independence='none/provisional',new_model_calls=0,status=status,records=len(flat),complete_four_arm_tasks=sum(t['complete'] for t in scores['rows']),arms_scored=recomputed,max_actual_input_plus_cap=maximum,failures=failures,cost=cost,freeze_sha256=sha(OUT/'FREEZE.json'),all_frozen_sources_unchanged=True)
atomic(HERE/'COMPLETION_AUDIT.json',out)
archive=HERE/'seed1-completed-run.tar.gz'
with tarfile.open(archive,'w:gz') as tar:tar.add(OUT,arcname=OUT.name)
atomic(HERE/'ARCHIVE.json',dict(archive_sha256=sha(archive),files={str(p.relative_to(OUT)):sha(p) for p in OUT.rglob('*') if p.is_file()}))
print(json.dumps({k:v for k,v in out.items() if k not in ('failures','cost')},ensure_ascii=False));print(json.dumps(dict(archive_sha256=sha(archive),archive_bytes=archive.stat().st_size)),flush=True)
