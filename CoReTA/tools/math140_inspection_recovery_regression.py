"""One frozen seen-task engineering regression. No reruns or runtime gold feedback."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

from coreta.closure import digest
from coreta.scoring import docker_math_records
from coreta.state import write_json
from coreta.task_audit_binding import SourceBindingContracts


ROOT = Path(__file__).resolve().parents[1]
PLAN = ROOT / 'engineering/MATH140_INSPECTION_RECOVERY_PLAN_20261020.json'
OUT = ROOT / 'runs/math140-inspection-recovery-20261020'
JOB = OUT / '4276ec64c178dafa'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def verify():
    plan = read(PLAN)
    for path, expected in plan['source_hashes'].items():
        if sha(Path(path)) != expected:
            raise ValueError('Frozen source changed: ' + path)
    return plan


def build():
    if PLAN.exists() or OUT.exists():
        raise ValueError('Refuse to overwrite a previous plan/run')
    old = read(ROOT / 'engineering/MATH140_FORMAT_PLAN_20261019.json')
    job = old['jobs'][0]
    task_path = Path(job['task_path'])
    assert sha(task_path) == job['sha256']
    task = read(task_path)
    config_path = ROOT / 'config/deepseek_flash_closure.json'
    config = read(config_path)
    runtime_config_path = ROOT / 'config/deepseek_flash_inspection.json'
    runtime_config = read(runtime_config_path)
    old_without_budget = json.loads(json.dumps(config))
    old_without_budget['generation']['max_input_tokens'] = 32768
    old_without_budget['generation']['max_output_tokens']['inspect'] = 8192
    assert old_without_budget == runtime_config
    prompts = read(ROOT / 'design/source_binding_prompts.json')
    contracts = SourceBindingContracts(ROOT / 'design/v0.3/coreta.schema.json')
    bank_paths = []
    for actor, expected_payload in zip(('A0', 'A1', 'A2'), job['initial_hashes']):
        material = {'task': task, 'actor': actor, 'seed': 17, 'config': config,
                    'system_prompt': prompts['system'], 'draft_prompt': prompts['draft'],
                    'schema': contracts.schema('Candidate')}
        fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
        original = ROOT / 'runs/math-expanded-screen-20261019/draft-bank' / (fingerprint + '.json')
        saved = read(original)
        assert saved['fingerprint'] == fingerprint and digest(saved['candidate']) == expected_payload
        material['config'] = runtime_config
        new_fingerprint = hashlib.sha256(json.dumps(material, sort_keys=True).encode()).hexdigest()
        bank_paths.append((original, new_fingerprint, expected_payload))
    if not os.environ.get('DEEPSEEK_API_KEY'):
        raise RuntimeError('DEEPSEEK_API_KEY unavailable')
    image = (ROOT / 'engineering/SCORING_IMAGE_20261019.txt').read_text().strip()
    engine = subprocess.run(['docker', 'info', '--format', '{{.OSType}}'], capture_output=True, text=True, check=True)
    assert engine.stdout.strip() == 'linux'
    inspected = subprocess.run(['docker', 'image', 'inspect', image, '--format', '{{.Id}}'],
                               capture_output=True, text=True, check=True)
    assert inspected.stdout.strip() == image
    OUT.mkdir()
    bank = OUT / 'draft-bank'
    bank.mkdir()
    migration = []
    for original, new_fingerprint, expected_payload in bank_paths:
        saved = read(original)
        migrated = {**saved, 'fingerprint': new_fingerprint}
        destination = bank / (new_fingerprint + '.json')
        write_json(destination, migrated)
        assert digest(read(destination)['candidate']) == expected_payload
        migration.append({'original': str(original), 'original_sha256': sha(original),
                          'original_fingerprint': saved['fingerprint'], 'new_fingerprint': new_fingerprint,
                          'candidate_hash_unchanged': expected_payload, 'destination': str(destination),
                          'reason': 'Local input budget changed 24576 to 32768 and inspection output cap4096 to8192; cached original answer replay, not a new draft generation'})
    write_json(OUT / 'draft_migration.json', migration)
    tokenizer = ROOT / 'data/tokenizer-v4.1-flash-1017/tokenizer.json'
    source_names = ('revision.py', 'closure.py', 'closure_feedback.py', 'closure_diff.py', 'closure_format.py',
                    'task_audit.py', 'task_audit_binding.py', 'run_task_audit_binding.py', 'closure_reference.py', 'run_closure_reference.py', 'audit_delivery.py', 'run_audit_delivery.py', 'inspection_recovery.py', 'run_inspection_recovery.py', 'model_client.py', 'schemas.py', 'state.py', 'scoring.py')
    sources = [ROOT / 'src/coreta' / n for n in source_names] + [
        config_path, runtime_config_path, OUT / 'draft_migration.json', *[r[0] for r in bank_paths], ROOT / 'design/source_binding_prompts.json', ROOT / 'design/task_audit.schema.json', ROOT / 'design/source_binding.schema.json',
        ROOT / 'design/v0.3/coreta.schema.json', task_path, tokenizer, Path(__file__),
        ROOT / 'data/math-expanded-screen-20261019/evaluation/math_gold.json',
        ROOT / 'engineering/SCORING_IMAGE_20261019.txt', *bank.glob('*.json')]
    command = [sys.executable, '-m', 'coreta.run_inspection_recovery', '--task', str(task_path),
               '--output', str(JOB), '--draft-bank', str(bank), '--tokenizer', str(tokenizer), '--live']
    plan = {'protocol_variant': 'task_audit_inspection_v5', 'task_id': task['task_id'], 'seed_label': 17,
            'seed_supported': False, 'task_path': str(task_path), 'initial_scores': job['initial_scores'],
            'initial_hashes': job['initial_hashes'], 'draft_bank': str(bank), 'output': str(JOB),
            'normal_call_cap': 14, 'cached_draft_calls': 3, 'new_logical_stage_cap': 11,
            'http_attempt_upper_bound': 39, 'format_repair_cap': config['protocol']['max_format_repairs'],
            'scoring_image': image, 'command': command,
            'scope': 'One seen all-initial-fail engineering regression; no new-task effectiveness estimate',
            'failure_policy': 'One invocation only, retain degraded/failure; no rerun or protocol changes after launch',
            'runtime_material': 'Public task, frozen three drafts, and this trajectory only; no gold, old diagnostics or other trajectories',
            'score_policy': 'Offline fixed Docker Math-Verify; final delivered candidate, no best-of-history selection',
            'source_hashes': {str(p): sha(p) for p in sources}}
    write_json(PLAN, plan)
    print(json.dumps({'plan': str(PLAN), 'cached_initials': 3, 'initial_scores': plan['initial_scores'],
                      'normal_call_cap': 14, 'scoring_ready': True}), flush=True)


def run():
    plan = verify()
    if JOB.exists() or (OUT / 'launch.json').exists():
        raise ValueError('Single invocation only; run already started')
    write_json(OUT / 'launch.json', {'command': plan['command'], 'single_invocation': True})
    print(json.dumps({'starting': plan['task_id'], 'variant': plan['protocol_variant']}), flush=True)
    process = subprocess.run(plan['command'], cwd=ROOT, capture_output=True, text=True, encoding='utf-8', check=False)
    (OUT / 'stdout.txt').write_text(process.stdout, encoding='utf-8')
    (OUT / 'stderr.txt').write_text(process.stderr, encoding='utf-8')
    write_json(OUT / 'launcher_result.json', {'returncode': process.returncode})
    if process.returncode:
        raise RuntimeError('Entry failed; output retained, no rerun: ' + process.stderr[-1500:])
    result = read(JOB / 'result.json')
    verify()
    assert [digest(e['payload']) for e in lines(JOB / 'events.jsonl') if e['stage'] == 'draft'] == plan['initial_hashes']
    print(json.dumps({k: result[k] for k in ('status', 'stop_reason', 'normal_calls', 'http_attempts',
                                           'format_repairs', 'audit_record_count')}), flush=True)


def score():
    plan = verify()
    destination = ROOT / 'engineering/MATH140_INSPECTION_RECOVERY_SCORES_20261020.json'
    if destination.exists():
        raise ValueError('Refuse to overwrite scores')
    result = read(JOB / 'result.json')
    events = lines(JOB / 'events.jsonl')
    assert [digest(e['payload']) for e in events if e['stage'] == 'draft'] == plan['initial_hashes']
    gold = next(r for r in read(ROOT / 'data/math-expanded-screen-20261019/evaluation/math_gold.json')
                if r['task_id'] == plan['task_id'])
    # Keep generation in a separate finished process; gold is used only here.
    scores = docker_math_records([{**gold, 'artifact': result['artifact']}], plan['scoring_image'])
    summary = {'task_id': plan['task_id'], 'initial_scores': plan['initial_scores'], 'final_score': scores[0].get('score'),
               'score_detail': scores[0], 'status': result['status'], 'stop_reason': result['stop_reason'],
               'review_status': result['review_status'], 'normal_calls': result['normal_calls'],
               'http_attempts': result['http_attempts'], 'format_repairs': result['format_repairs'],
               'audit_record_count': result['audit_record_count'], 'errors': result['errors'],
               'stages': [e['stage'] for e in events], 'source_hashes_match': True,
               'scope': plan['scope'], **{k: result.get(k) for k in ('source_bindings_complete', 'declared_check_item_count', 'pipeline_completed', 'mechanism_evaluable')}}
    write_json(destination, summary)
    print(json.dumps(summary), flush=True)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('mode', choices=('build', 'run', 'score'))
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if args.mode == 'run' and not args.live:
        parser.error('Explicit --live is required to send requests')
    {'build': build, 'run': run, 'score': score}[args.mode]()
