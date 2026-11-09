"""Build and tokenize fixed-prefix counterfactual payloads; NO generation entry point."""
import copy,hashlib,importlib.util,json
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
s=importlib.util.spec_from_file_location('composition',HERE.parent/'expert-composition100-20261109/experiment.py');b=importlib.util.module_from_spec(s);s.loader.exec_module(b)
IDS=[0,1,2,6,9,13,15,17,24,31,43,49,51,54]
ARMS=['N_self','E_expert_final','O_ordinary_finals','EO_all_finals','P_expert_public_repeat']
INSTRUCTION='The previous discussion has ended. Your own sealed answer and any additional peer records are provided below. Reconsider privately using the supplied material and these records. A peer answer can be wrong; repeated agreement is not independent evidence. Return only your best short answer.'

def build(entry,index,arm):
 result=[]
 for actor in b.ACTORS:
  old=index[(actor,'final','B',3)];payload=copy.deepcopy(old['payload']);suffix=entry['trial_config']['answer_suffix']
  assert payload['user'].startswith('TASK_DATA\n') and payload['user'].endswith(suffix)
  data=json.loads(payload['user'][10:-len(suffix)])
  data['own_sealed_answer']=old['raw_output'];peers=[]
  for sender in b.ACTORS:
   if sender==actor:continue
   include=(sender=='M1' and arm in ['E_expert_final','EO_all_finals']) or (sender!='M1' and arm in ['O_ordinary_finals','EO_all_finals'])
   if include:peers.append(dict(sender=sender,source_stage='sealed_final',text=index[(sender,'final','B',3)]['raw_output']))
   elif sender=='M1' and arm=='P_expert_public_repeat':peers.append(dict(sender=sender,source_stage='previous_public_work',text=index[('M1','work','B',2)]['raw_output']))
  data['additional_peer_records']=peers;data['revision_instruction']=INSTRUCTION
  payload['user']='TASK_DATA\n'+json.dumps(data,ensure_ascii=False,indent=2)+suffix
  result.append(dict(task_id=entry['id'],index=entry['source_index'],rep=entry['rep'],arm=arm,actor=actor,stage='additional_private_final',seed=old['seed']+200000000,max_new_tokens=old['max_new_tokens'],payload=payload,adapter_enabled=actor=='M1'))
 return result

def main():
 from b0_training import load_tokenizer
 c=b.load(HERE.parent/'expert-composition100-20261109/config.json');tok=load_tokenizer(c)
 entries=[e for e in b.load(HERE.parent/'expert-composition100-20261109/INPUTS.json')['units'] if e['cohort']=='fresh' and e['source_index'] in IDS]
 assert len(entries)==28 and len({e['id'] for e in entries})==14
 rows=[];maximum=0;reuse=0;sources={}
 for e in entries:
  idx=b.source(e);assert all(idx[(a,'final','B',3)]['status']=='OK' for a in b.ACTORS)
  t=b.Team(e)
  while (r:=t.next_request()) is not None:
   z=idx[(r['actor'],r['stage'],r['arm'],r['round'])];assert b.equal(r,z)
   t.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
  assert t.complete
  original={a:copy.deepcopy(idx[(a,'final','B',3)]['payload']) for a in b.ACTORS};cache=set()
  for arm in ARMS:
   for r in build(e,idx,arm):
    data=json.loads(r['payload']['user'][10:-len(e['trial_config']['answer_suffix'])]);seen={p['sender'] for p in data['additional_peer_records']}
    expected=({'M1'} if arm=='E_expert_final' else set(b.ACTORS[1:]) if arm=='O_ordinary_finals' else set(b.ACTORS) if arm=='EO_all_finals' else {'M1'} if arm=='P_expert_public_repeat' else set())-{r['actor']}
    assert seen==expected and data['own_sealed_answer']==idx[(r['actor'],'final','B',3)]['raw_output']
    assert not any(k in data for k in ['gold','correct','correct_answer','target','label'])
    ids=tok.apply_chat_template([dict(role=k,content=r['payload'][k]) for k in ['system','user']],tokenize=True,add_generation_prompt=True,return_dict=False,**c['template_kwargs'])
    n=len(ids)+r['max_new_tokens'];assert n<=c['max_length'];maximum=max(maximum,n)
    key=json.dumps({k:r[k] for k in ['payload','seed','max_new_tokens','adapter_enabled']},sort_keys=True)
    reused=key in cache;reuse+=int(reused);cache.add(key);rows.append(dict(r,input_plus_cap=n,exact_within_unit_reuse_possible=reused))
  assert all(original[a]==idx[(a,'final','B',3)]['payload'] for a in b.ACTORS)
  sources[e['source_path']]=b.sha(ROOT/e['source_path'])
 assert len(rows)==560 and reuse==84
 b.write(HERE/'SELECTION.json',dict(indices=IDS,n_distinct_questions=14,n_task_seed_units=28,core_candidate_indices=[1,6,17,24,31,49,54],expert_wrong_ordinary_correct=[43],measurement_controls=[9,51],both_correct_controls=[0,2],both_wrong_controls=[13,15],both_seeds_required=True,development_outcome_selected_not_population_estimate=True,boundary_flags={1:'multiple same-title songs',24:'we/UK referent not explicit',31:'author organization vs publication and hedged public answer',49:'multiple Collegian institutions',54:'performer label vs album attribution',43:'language-used inference and kinship binding'}))
 b.write(HERE/'REQUESTS.json',rows)
 b.write(HERE/'DESIGN_CHECK.json',dict(result='PASS_PAYLOAD_DESIGN_ONLY_NOT_RUNTIME_READY',source_complete_units_replayed=28,old_requests_replayed=784,logical_extra_calls=560,exact_duplicate_requests=84,max_unique_extra_calls=476,max_input_plus_cap=maximum,model_calls=0,source_sha256=sources,request_file_sha256=b.sha(HERE/'REQUESTS.json'),arms=ARMS,code_sha256=b.sha(HERE/'build_design.py')))
 print(json.dumps({k:v for k,v in b.load(HERE/'DESIGN_CHECK.json').items() if k!='source_sha256'}))

if __name__=='__main__':main()
