"""Read-only reconstruction of actual SBP requests, scores and token outputs."""
import json, sys
import pilot as p

cfg = p.load(p.HERE/'config.json'); out = p.ROOT/cfg['run_dir']
manifest = p.load(out/'manifest.json'); assert manifest['freeze'] == p.freeze()
rows = [json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines() if s.strip()]
attempts = [json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines() if s.strip()]
assert len(rows) <= len(attempts) <= len(rows)+1
task = p.load(p.HERE/'task.json'); gold = p.load(p.HERE/'labels.json')['ranking']
sys.path.insert(0,str(p.ROOT/'tools')); from b0_training import load_tokenizer
tok = load_tokenizer(cfg); max_length = 0; original = {}; history = {}
for i, row in enumerate(rows):
    assert row['call'] == i
    assert all(row[k] == attempts[i][k] for k in attempts[i])
    seed, arm, actor, stage = [row[k] for k in ('seed','arm','actor','stage')]
    initial_order, orders = p.schedule(seed)
    if stage == 'initial':
        own, public = [], []
        original.setdefault((seed,arm),{})[actor] = row['text']
    else:
        initial_arm = 'B_hidden' if arm in ['A_private','B_hidden','D_revealed'] else arm
        initials = original[(seed,initial_arm)]
        old = history.get((seed,arm),[])
        own = [initials[actor]] + [r['text'] for r in old if r['actor']==actor and r['stage']=='work']
        public = [] if arm == 'A_private' else [(a,initials[a]) for a in initial_order] + [(r['actor'],r['text']) for r in old if r['stage']=='work']
        if stage == 'work':
            previous_works = sum(r['stage']=='work' for r in old)
            assert row['round'] == previous_works//4+1
            assert actor == orders[row['round']-1][previous_works%4]
        history.setdefault((seed,arm),[]).append(row)
    expected = p.payload(task,actor,arm,seed,stage,own,public)
    assert row['payload'] == expected
    ids = tok.apply_chat_template([{'role':k,'content':expected[k]} for k in ('system','user')],
        tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs'])
    assert row['input_tokens'] == len(ids)
    assert row['output_tokens'] == len(row['output_ids']) <= row['cap']
    assert tok.decode(row['output_ids'],skip_special_tokens=True) == row['text']
    assert row['adapter_enabled'] is False
    assert p.parse(row['text']) == row['ranking']
    assert p.error(row['ranking'],gold) == row['l1']
    assert row['generation_seed'] == (seed*10000+{'initial':0,'work':1000,'final':9000}[stage]+row['round']*10+p.ACTORS.index(actor))%(2**32)
    p.check_length(len(ids),row['cap'],cfg['max_length']); max_length = max(max_length,len(ids)+row['cap'])
scores = p.load(out/'scores.json') if (out/'scores.json').exists() else []
for score in scores:
    if not score['complete']: continue
    selected = [r for r in rows if r['seed']==score['seed'] and r['arm']==score['arm'] and r['stage']=='final']
    assert len(selected)==4
    assert p.aggregate([r['ranking'] for r in selected],gold) == score['final_aggregate']
status = p.load(out/'STATUS.json')
result = {'result':'PASS','status':status['status'],'snapshot_responses':len(rows),'snapshot_attempts':len(attempts),
    'all_requests_reconstructed':True,'token_ids_decoded':True,'all_actual_lengths_within_context':True,
    'max_input_plus_cap':max_length,'complete_branches':len([s for s in scores if s['complete']]),
    'invalid_ranking_outputs':len([r for r in rows if r['ranking'] is None]),
    'non_eos_outputs':len([r for r in rows if r['status']!='OK']),
    'snapshot_output_tokens':sum(r['output_tokens'] for r in rows),
    'snapshot_generation_seconds':sum(r['elapsed_seconds'] for r in rows),
    'initials':[{'seed':r['seed'],'actor':r['actor'],'l1':r['l1'],'status':r['status']} for r in rows if r['stage']=='initial' and r['arm']=='B_hidden'],
    'freeze_unchanged':True,'scope':'assistant self-audit, not independent human or semantic process verification'}
p.write(p.HERE/('COMPLETION_AUDIT.json' if status['status']!='RUNNING' else 'START_VERIFICATION.json'),result)
print(json.dumps(result))
