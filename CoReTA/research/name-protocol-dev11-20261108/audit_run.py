"""Read-only reconstruction of prompts, selected fact routing, token IDs, and scores."""
import json, sys
import experiment as e

def read_prefix(path):
    text=path.read_text(encoding='utf-8')
    return [json.loads(s) for s in text[:text.rfind('\n')+1].splitlines() if s.strip()]

cfg=e.load(e.HERE/'config.json');out=e.ROOT/cfg['run_dir']
manifest=e.load(out/'manifest.json');assert manifest['freeze']==e.freeze()
snapshot_status=e.load(out/'STATUS.json')
rows=read_prefix(out/'responses.jsonl');attempts=read_prefix(out/'attempts.jsonl')
assert len(rows)<=len(attempts)
cache=e.cache_index(cfg);verified_reused=0
tasks={t['id']:t for t in e.load(e.HERE/'tasks.json')};labels=e.load(e.HERE/'labels.json')
sys.path.insert(0,str(e.ROOT/'tools'));from b0_training import load_tokenizer
tok=load_tokenizer(cfg)
initials={};prep={};hist={};selected={};largest=0;reference_rows=[]
for i,r in enumerate(rows):
    assert r['call']==i and all(r[k]==v for k,v in attempts[i].items())
    if r.get('inherited'):
        original=cache[e.key(r)]
        e.check_cached({k:r[k] for k in ['task_id','actor','stage','arm','round','generation_seed','cap','payload']},original)
        for k in ['text','output_ids','input_tokens','output_tokens','status','elapsed_seconds','ended_with_eos','adapter_enabled']:
            assert r[k]==original[k]
        assert r['source_cache_call']==original['call'];verified_reused+=1
    number,actor,stage,arm=[r[k] for k in ['task_id','actor','stage','arm']]
    task=tasks[number];first,orders=e.order(task,cfg)
    initial=initials.get(number,{});prior=hist.get((number,arm),[])
    own=[];public=[];initial_text=''
    if stage!='initial':initial_text=initial[actor]['text']
    if stage in ['work','final']:
        parent='FACTS_SHARED' if arm.startswith(('E_','F_')) else arm
        own=[prep[(number,parent)][actor]['text']]+[x['text'] for x in prior if x['stage']=='work' and x['actor']==actor]
        if arm=='B_ordinary':public=[(a,prep[(number,arm)][a]['text']) for a in first]
        elif arm.startswith(('E_','F_')):
            public=e.public_facts(task,selected[number],{a:initial[a]['text'] for a in e.ACTORS},arm=='F_facts_opinions')
        public += [] if arm=='A_private' else [(x['actor'],x['text']) for x in prior if x['stage']=='work']
        if stage=='work':
            n=sum(x['stage']=='work' for x in prior)
            assert r['round']==n//4+1 and actor==orders[r['round']-1][n%4]
    expected=e.packet(task,actor,stage,arm,initial_text,own,public)
    assert expected==r['payload']
    ids=tok.apply_chat_template([{'role':k,'content':expected[k]} for k in ['system','user']],
         tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
    assert len(ids)==r['input_tokens']
    e.backend_module.check_length(len(ids),r['cap'],cfg['max_length']);largest=max(largest,len(ids)+r['cap'])
    assert len(r['output_ids'])==r['output_tokens']<=r['cap']
    assert tok.decode(r['output_ids'],skip_special_tokens=True)==r['text']
    assert r['adapter_enabled'] is False
    stage_code={'initial':0,'exchange':100,'facts':200,'work':1000,'final':9000}[stage]
    assert r['generation_seed']==(cfg['seed']+number*100000+stage_code+r['round']*10+e.ACTORS.index(actor))%(2**32)
    if stage=='facts':
        parsed=e.refs(r['text'],e.visible(task,actor));assert parsed==r['references']
        selected.setdefault(number,{})[actor]=parsed
        reference_rows.append({'task_id':number,'actor':actor,**parsed})
    else:assert e.answer(r['text'],task)==r['answer']
    if stage=='initial':initials.setdefault(number,{})[actor]=r
    elif stage in ['exchange','facts']:prep.setdefault((number,arm),{})[actor]=r
    else:hist.setdefault((number,arm),[]).append(r)
scores=e.load(out/'scores.json') if (out/'scores.json').exists() else []
checked=0
for s in scores:
    if not s['complete']:continue
    final=[r for r in rows if r['task_id']==s['task_id'] and r['arm']==s['arm'] and r['stage']=='final']
    if len(final)<4:continue # Live snapshot may end just before atomic score write.
    gold=labels[str(s['task_id'])]['correct']
    assert s['final_vote']==e.expected_vote([r['answer'] for r in final],gold)
    assert s['final_answers']=={r['actor']:r['answer'] for r in final}
    checked+=1
status=snapshot_status
if status['status']=='COMPLETED':assert len(rows)==len(attempts)==status['calls'] and checked==status['complete_arms']
summary={'result':'PASS','status':status['status'],'snapshot_responses':len(rows),'snapshot_attempts':len(attempts),
         'max_input_plus_cap':largest,'complete_arms_checked':checked,'all_requests_reconstructed':True,
         'all_output_ids_decoded':True,'source_permissions_checked':True,'fact_selection_requests':reference_rows,
         'non_eos':sum(r['status']!='OK' for r in rows),'unreadable_finals':sum(r['answer'] is None for r in rows if r['stage']=='final'),
         'output_tokens':sum(r['output_tokens'] for r in rows),'generation_seconds':sum(r['elapsed_seconds'] for r in rows),
         'freeze_unchanged':True,'scope':'assistant provisional audit; not independent human or semantic correctness certification'}
summary['unreadable_initials']=sum(r['answer'] is None for r in rows if r['stage']=='initial')
summary['unreadable_nonfact_outputs']=sum(r['answer'] is None for r in rows if r['stage']!='facts')
summary['legacy_option_ids_emitted']=sum(bool(e.re.search(r'\boption_\d+\b',r['text'])) for r in rows if r['stage']!='facts')
summary['initial_probe']=e.load(out/'INITIAL_PROBE.json') if (out/'INITIAL_PROBE.json').exists() else None
summary['stage_max_output_tokens']={stage:max((r['output_tokens'] for r in rows if r['stage']==stage),default=0) for stage in ['initial','exchange','facts','work','final']}
summary['not_confirmatory_evidence']=True
summary['inherited_records']=sum(bool(r.get('inherited')) for r in rows)
summary['new_generation_records']=len(rows)-summary['inherited_records']
summary['parse_modes']=dict(e.collections.Counter(e.answer_mode(r['text'],tasks[r['task_id']]) for r in rows if r['stage']!='facts'))
summary['generation_seconds_excluding_inherited']=sum(r['elapsed_seconds'] for r in rows if not r.get('inherited'))
summary['reused_records_verified_exactly']=verified_reused
summary['new_initial_records']=sum(r['stage']=='initial' and not r.get('inherited') for r in rows)
if status['status']=='COMPLETED':
    assert summary['inherited_records']<=208 and summary['new_generation_records']<=848
    summary['original_planned_tasks']=11
    summary['all_11_four_arm_complete']=checked==44
e.write(e.HERE/('COMPLETION_AUDIT.json' if status['status'] in ['COMPLETED','FAILED'] else 'START_VERIFICATION.json'),summary)
print(json.dumps(summary))
