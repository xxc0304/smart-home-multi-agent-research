"""Bounded V20 precision diagnostic. No training, adapters, C/H, or downloads."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tools'))
from b0_answers import read_jsonl, write_json, answer_score, score_run
from b0_training import load_tokenizer, load_base, require_config
from prepare_answer_only_expert import SYSTEM
from expert_mechanism_protocol import task_data

OUT = ROOT / 'runs/baseline-health-v20-20261103-v1'
HERE = Path(__file__).resolve().parent
INPUT = ROOT / 'data/expert-training-20261030-v1/validation.inputs.jsonl'
TARGET = ROOT / 'data/expert-training-20261030-v1/validation.targets.jsonl'
CONFIG = ROOT / 'config/b0_lab3090_V_v2_20261103.json'
OLD = ROOT / 'runs/b0-first-run-20261103-v2/V_B'


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def messages(task, config):
    return [dict(role='system', content=SYSTEM), dict(role='user', content='TASK_DATA\n' +
        json.dumps(task_data(task), ensure_ascii=False, indent=2) + config['evaluation_answer_suffix'])]


def check_freeze():
    freeze = json.loads((OUT / 'FREEZE.json').read_text())
    for path, sha in freeze['files'].items():
        if digest(path) != sha:
            raise ValueError('frozen_file_changed:' + path)
    return freeze


def preflight():
    config = json.loads(CONFIG.read_text())
    require_config(config)
    assert config['quantization'] == '4bit' and config['dtype'] == 'bfloat16'
    assert config['generation'] == dict(do_sample=False, max_new_tokens=256)
    assert config['template_kwargs'] == dict(enable_thinking=False)
    assert config['revision'] == '1cfa9a7208912126459214e8b04321603b3df60c'
    tasks = read_jsonl(INPUT)
    assert len(tasks) == 200 and len({t['id'] for t in tasks}) == 200
    tasks = tasks[:20]
    ids = [t['id'] for t in tasks]
    old_manifest = json.loads((OLD / 'manifest.json').read_text())
    old_rows = {r['id']: r for r in read_jsonl(OLD / 'responses.jsonl')}
    assert old_manifest['expected_ids'][:20] == ids
    for key, value in old_manifest['inference'].items():
        assert config[key] == value, key
    tokenizer = load_tokenizer(config)
    lengths = []
    prompt_hashes = []
    for task in tasks:
        prompt = messages(task, config)
        tokens = tokenizer.apply_chat_template(prompt, tokenize=True, add_generation_prompt=True,
            return_dict=False, **config['template_kwargs'])
        assert len(tokens) == old_rows[task['id']]['input_tokens']
        assert len(tokens) + 256 <= config['max_length']
        lengths.append(len(tokens))
        prompt_hashes.append(hashlib.sha256(json.dumps(tokens).encode()).hexdigest())
    targets = {t['id']: t for t in read_jsonl(TARGET)}
    old_score = json.loads((OLD.parent / 'V_B_score.json').read_text())
    score_by_id = {r['id']: r for r in old_score['records']}
    for task_id in ids:
        assert answer_score(old_rows[task_id]['raw_output'], targets[task_id]) == score_by_id[task_id]['metrics']
    # Real full old responses replay through scorer; explicit missing/failure export check.
    assert answer_score('Answer: x', dict(answer='x'))['em'] == 1
    OUT.mkdir(exist_ok=False, parents=True)
    failure_dir = OUT / 'failure-export-fixture'
    failure_dir.mkdir()
    write_json(failure_dir / 'manifest.json', dict(expected_ids=ids[:2], fixture=True))
    (failure_dir / 'responses.jsonl').write_text(json.dumps(dict(id=ids[0], status='OUTPUT_LIMIT', raw_output='unfinished')) + '\n')
    fail = score_run(failure_dir, targets)
    assert fail['status'] == 'INCOMPLETE' and fail['metrics'] is None and fail['n_valid'] == 0
    write_json(failure_dir / 'scored.json', fail)
    for arm, quantization in [('NF4', '4bit'), ('BF16', 'none')]:
        candidate = dict(config, quantization=quantization, wall_seconds=600,
                         purpose='V20_precision_diagnostic', reviewed_for_run=False)
        write_json(OUT / (arm + '.json'), candidate)
    import torch
    free, total = torch.cuda.mem_get_info()
    assert free >= 20 * 1024**3, 'GPU_not_idle_enough'
    paths = [CONFIG, INPUT, TARGET, HERE/'diagnostic.py', HERE/'PLAN.md',
        ROOT/'tools/b0_training.py', ROOT/'tools/b0_answers.py',
        ROOT/'tools/prepare_answer_only_expert.py', ROOT/'tools/expert_mechanism_protocol.py',
        OLD/'manifest.json', OLD/'responses.jsonl', OLD.parent/'V_B_score.json',
        OUT/'NF4.json', OUT/'BF16.json']
    paths += list((ROOT/'research/musique-data-preparation-20261030/official_scorer/metrics').glob('*.py'))
    model_dir = Path(config['model_path'])
    paths += [p for p in model_dir.iterdir() if p.is_file() and p.suffix in ('.json', '.jinja')]
    freeze = dict(expected_ids=ids, selected_order='first20_in_existing_V200_order',
        files={str(p): digest(p) for p in paths}, prompt_token_sha256=prompt_hashes,
        input_lengths=lengths, n_generations_max=40, no_C_H_read=True,
        arm_order=['NF4', 'BF16'], per_arm_wall_seconds=600, total_wall_seconds=1800)
    write_json(OUT/'FREEZE.json', freeze)
    report = dict(status='PREPARED_NOT_LAUNCHED', n=20, max_input_tokens=max(lengths),
        historic_prompt_lengths_equal=True, historical_raw_score_replay_equal=True,
        missing_and_output_limit_export='PASS', GPU_free_bytes=free, GPU_total_bytes=total,
        torch=torch.__version__, cuda=torch.version.cuda, freeze_sha256=digest(OUT/'FREEZE.json'))
    write_json(OUT/'PREFLIGHT.json', report)
    print(json.dumps(report), flush=True)


def arm_run(arm):
    freeze = check_freeze()
    review = json.loads((OUT/'APPROVAL.json').read_text())
    assert review['science'] == review['readiness'] == 'PASS'
    assert review['freeze_sha256'] == digest(OUT/'FREEZE.json')
    config = json.loads((OUT/(arm+'.json')).read_text())
    config['reviewed_for_run'] = True  # Effective only after the bound review gate above.
    require_config(config)
    tasks = read_jsonl(INPUT)[:20]
    assert [t['id'] for t in tasks] == freeze['expected_ids']
    dest = OUT / arm
    dest.mkdir(exist_ok=False)
    write_json(dest/'manifest.json', dict(expected_ids=freeze['expected_ids'], fixture=False,
        technical_preflight=True, role='V', condition='B', diagnostic=True, arm=arm, config=config))
    response = dest/'responses.jsonl'
    response.touch()
    import torch
    from transformers import set_seed
    started = time.monotonic()
    error = None
    try:
        tokenizer = load_tokenizer(config)
        model = load_base(config)
        model.eval()
        model.config.use_cache = True
        for i, task in enumerate(tasks):
            remaining = 600 - (time.monotonic()-started)
            if remaining <= 0:
                break
            row = dict(id=task['id'], status='TECHNICAL_FAILURE', raw_output=None)
            try:
                tokens = tokenizer.apply_chat_template(messages(task,config), tokenize=True,
                    add_generation_prompt=True, return_dict=False, **config['template_kwargs'])
                assert hashlib.sha256(json.dumps(tokens).encode()).hexdigest() == freeze['prompt_token_sha256'][i]
                set_seed(config['seed'])
                x = torch.tensor([tokens], device=config['device'])
                begin = time.monotonic()
                with torch.inference_mode():
                    generated = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                        **config['generation'], max_time=remaining, pad_token_id=tokenizer.pad_token_id)
                tail = generated[0, len(tokens):].tolist()
                eos = model.generation_config.eos_token_id
                eos = eos if isinstance(eos,list) else [eos if eos is not None else tokenizer.eos_token_id]
                row.update(status='OK' if tail and tail[-1] in eos else 'OUTPUT_LIMIT',
                    raw_output=tokenizer.decode(tail,skip_special_tokens=True), input_tokens=len(tokens),
                    output_tokens=len(tail), elapsed_seconds=time.monotonic()-begin)
            except Exception as exc:
                row['reason'] = type(exc).__name__ + ':' + str(exc)
            with response.open('a') as f:
                f.write(json.dumps(row,ensure_ascii=False)+'\n')
                f.flush()
            print(arm, i+1, row['status'], flush=True)
            if row['status'] == 'TECHNICAL_FAILURE':
                break
    except Exception as exc:
        error = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        write_json(dest/'execution.json', dict(elapsed_seconds=time.monotonic()-started,
            fatal_error=error, peak_allocated_bytes=torch.cuda.max_memory_allocated(),
            peak_reserved_bytes=torch.cuda.max_memory_reserved(),
            allocator_retries=torch.cuda.memory_stats().get('num_alloc_retries'),
            num_ooms=torch.cuda.memory_stats().get('num_ooms')))


def report():
    freeze = check_freeze()
    targets = {t['id']:t for t in read_jsonl(TARGET)}
    reports = {}
    for arm in freeze['arm_order']:
        dest = OUT/arm
        if (dest/'manifest.json').exists():
            reports[arm] = score_run(dest, targets)
            write_json(dest/'score.json', reports[arm])
    result = dict(status='INCOMPLETE', n_expected=20, primary_enabled=False,
        conditions={a:{k:r[k] for k in ('status','n_valid','metrics')} for a,r in reports.items()})
    if len(reports)==2 and all(r['status']=='COMPLETE' for r in reports.values()):
        a,b = reports['NF4']['records'],reports['BF16']['records']
        old = {r['id']:r for r in read_jsonl(OLD/'responses.jsonl')}
        result.update(status='COMPLETE_DIAGNOSTIC', paired_counts=dict(
            both_correct=sum(x['metrics']['em']==y['metrics']['em']==1 for x,y in zip(a,b)),
            only_NF4=sum(x['metrics']['em']>y['metrics']['em'] for x,y in zip(a,b)),
            only_BF16=sum(x['metrics']['em']<y['metrics']['em'] for x,y in zip(a,b)),
            both_wrong=sum(x['metrics']['em']==y['metrics']['em']==0 for x,y in zip(a,b))),
            raw_answer_agreement=sum(x['raw_output']==y['raw_output'] for x,y in zip(a,b)),
            NF4_historical_raw_agreement=sum(x['raw_output']==old[x['id']]['raw_output'] for x in a),
            em_difference_BF16_minus_NF4=reports['BF16']['metrics']['em']-reports['NF4']['metrics']['em'])
    write_json(OUT/'RESULTS.json',result)
    print(json.dumps(result),flush=True)


def pipeline():
    check_freeze()
    (OUT/'LAUNCHED').touch(exist_ok=False)
    started = time.monotonic()
    exit_code = 0
    try:
        for arm in ('NF4','BF16'):
            try:
                proc = subprocess.run([sys.executable,str(Path(__file__).resolve()),'arm','--arm',arm],
                    timeout=min(660, 1740-(time.monotonic()-started)), check=False)
                if proc.returncode:
                    exit_code=proc.returncode
                    break
                scored=score_run(OUT/arm,{t['id']:t for t in read_jsonl(TARGET)})
                write_json(OUT/arm/'score.json',scored)
                if scored['status']!='COMPLETE':
                    exit_code=2
                    break
            except subprocess.TimeoutExpired:
                exit_code=124
                break
    finally:
        report()
        write_json(OUT/'PIPELINE_STATUS.json',dict(exit_code=exit_code,elapsed_seconds=time.monotonic()-started))
    if exit_code:
        raise SystemExit(exit_code)


if __name__=='__main__':
    parser=argparse.ArgumentParser()
    parser.add_argument('command',choices=['preflight','arm','run','report'])
    parser.add_argument('--arm',choices=['NF4','BF16'])
    args=parser.parse_args()
    if args.command=='arm':
        if not args.arm: parser.error('--arm required')
        arm_run(args.arm)
    else:
        {'preflight':preflight,'run':pipeline,'report':report}[args.command]()
