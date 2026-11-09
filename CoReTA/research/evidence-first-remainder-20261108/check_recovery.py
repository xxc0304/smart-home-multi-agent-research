"""Verify exact unattempted suffix and unchanged scientific configuration."""
import experiment as e
original=e.HERE.parent/'evidence-first-dev-20261108'
cfg=e.load(e.HERE/'config.json');old_cfg=e.load(original/'config.json')
assert {k:v for k,v in cfg.items() if k not in ['run_dir','purpose']}=={k:v for k,v in old_cfg.items() if k not in ['run_dir','purpose']}
old=e.load(original/'tasks.json');new=e.load(e.HERE/'tasks.json')
assert new==old[3:] and [t['id'] for t in old[:3]]==[1,4,7]
run=e.ROOT/old_cfg['run_dir'];rows=[e.json.loads(s) for s in (run/'responses.jsonl').read_text().splitlines()]
assert len(rows)==193 and rows[-1]['task_id']==7 and rows[-1]['stage']=='initial'
assert rows[-1]['status']=='OUTPUT_LIMIT' and rows[-1]['output_tokens']==rows[-1]['cap']==256
assert not set(t['id'] for t in new)&set(r['task_id'] for r in rows)
scores=e.load(run/'scores.json');assert len(scores)==8 and all(s['complete'] for s in scores)
assert set(s['task_id'] for s in scores)=={1,4}
for relative,digest in e.load(run/'manifest.json')['freeze'].items():assert e.sha(e.ROOT/relative)==digest
result={'result':'PASS','original_attempts':193,'original_complete_task_ids':[1,4],
        'original_failed_task_id':7,'unattempted_suffix':[t['id'] for t in new],
        'scientific_config_and_tasks_identical':True,'old_freeze_unchanged':True,'no_retries':True,
        'max_combined_calls':193+96*len(new),'original_analysis_denominator':11}
e.write(e.HERE/'RECOVERY_CHECK.json',result);print(e.json.dumps(result))
