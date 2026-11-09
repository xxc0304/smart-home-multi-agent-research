import collections,json
import experiment as e
cfg=e.load(e.HERE/'config.json');old_cfg=e.load(e.HERE.parent/'name-interface-tech-20261108/config.json')
ignored={'run_dir','purpose','initial_cache','initial_cache_sha256'}
assert {k:v for k,v in cfg.items() if k not in ignored}=={k:v for k,v in old_cfg.items() if k not in ignored}
tasks={t['id']:t for t in e.load(e.HERE/'tasks.json')}
assert e.load(e.HERE/'tasks.json')==e.load(e.HERE.parent/'name-interface-tech-20261108/tasks.json')
source=e.ROOT/cfg['initial_cache'];assert e.sha(source)==cfg['initial_cache_sha256']
rows=[json.loads(s) for s in source.read_text().splitlines()];assert len(rows)==24
for r in rows:
    t=tasks[r['task_id']]
    assert r['stage']=='initial' and r['status']=='OK' and r['ended_with_eos']
    assert r['payload']==e.packet(t,r['actor'],'initial','COMMON')
    assert r['cap']==cfg['initial_tokens'] and e.answer(r['text'],t) is not None
    assert r['generation_seed']==(cfg['seed']+t['id']*100000+e.ACTORS.index(r['actor']))%(2**32)
    assert not e.re.search(r'\boption_\d+\b',r['text'])
result={'result':'PASS','real_initials':24,'fresh_initial_gpu_calls':0,
        'parse_modes':dict(collections.Counter(e.answer_mode(r['text'],tasks[r['task_id']]) for r in rows)),
        'max_initial_output_tokens':max(r['output_tokens'] for r in rows),
        'original_strict_gate':'FAILED and preserved; amendment not preregistered for these originals',
        'payloads_seeds_caps_config_tasks_unchanged':True,'cache_sha256':e.sha(source),
        'remaining_new_generation_upper_bound':184,'combined_new_generation_upper_bound':208}
e.write(e.HERE/'CACHE_CHECK.json',result);print(json.dumps(result))
