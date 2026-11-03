"""Explicit audit-reference v3 entry; no requests on import or --help."""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import uuid
from pathlib import Path

from .closure_format import FormatClosureClient
from .state import write_json
from .task_audit import TASK_FACTS_OUTPUT_TOKENS
from .task_audit_binding import SourceBindingContracts, VERSION
from .protocol_stability import StabilityRunner, StabilityClient, VARIANT


PROJECT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description='Run task audit with program-resolved exact source bindings')
    parser.add_argument('--task', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--config', type=Path, default=PROJECT / 'config/deepseek_flash_inspection.json')
    parser.add_argument('--tokenizer', type=Path)
    parser.add_argument('--draft-bank', type=Path)
    parser.add_argument('--seed', type=int, default=17)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if not args.live:
        parser.error('No requests sent. Explicit --live is required.')
    if not os.environ.get('DEEPSEEK_API_KEY'):
        parser.error('DEEPSEEK_API_KEY is not configured.')
    config = json.loads(args.config.read_text(encoding='utf-8'))
    if config['model'] != 'deepseek-flash' or config['base_url'] != 'https://api.deepseek.com':
        parser.error('This entry uses the approved official deepseek-flash endpoint.')
    if config['protocol']['max_work_turns'] != 2:
        parser.error('This protocol has one bootstrap and at most two further work cycles.')
    legacy = PROJECT / 'design/v0.3/coreta.schema.json'
    prompt_path = PROJECT / 'design/source_binding_prompts.json'
    contracts = SourceBindingContracts(legacy)
    task = json.loads(args.task.read_text(encoding='utf-8'))
    contracts.validate('PublicTask', task)
    prompts = json.loads(prompt_path.read_text(encoding='utf-8'))
    token_counter = None
    if args.tokenizer:
        from tokenizers import Tokenizer
        tokenizer = Tokenizer.from_file(str(args.tokenizer))
        token_counter = lambda value: len(tokenizer.encode(value, add_special_tokens=False).ids)
    args.output.mkdir(parents=True, exist_ok=False)
    runner = StabilityRunner(task, args.output, 'coreta-source-binding-' + uuid.uuid4().hex[:12],
                                   contracts, None, config, prompts, args.seed, draft_bank=args.draft_bank)
    runner.client = StabilityClient(config, runner.log, token_counter=token_counter)
    source_names = ('revision.py', 'closure.py', 'closure_feedback.py', 'closure_diff.py', 'closure_format.py',
                    'task_audit.py', 'task_audit_binding.py', 'closure_reference.py', 'audit_delivery.py', 'run_audit_delivery.py', 'inspection_recovery.py', 'run_inspection_recovery.py', 'protocol_stability.py', 'run_protocol_stability.py',
                    'model_client.py', 'schemas.py', 'state.py')
    sources = [legacy, prompt_path, args.config] + [Path(__file__).with_name(n) for n in source_names]
    write_json(args.output / 'manifest.json', {
        'run_id': runner.run_id, 'protocol_variant': VARIANT, 'schema_version': VERSION,
        'public_task_sha256': hashlib.sha256(args.task.read_bytes()).hexdigest(),
        'normal_call_cap': 14, 'scheduler_cap': 15, 'final_stage_used': False,
        'config': config, 'task_facts_output_tokens': config['generation']['max_output_tokens'].get(
            'task_facts', TASK_FACTS_OUTPUT_TOKENS),
        'draft_bank': str(args.draft_bank) if args.draft_bank else None,
        'seed': args.seed, 'seed_supported': False, 'input_count_mode': runner.client.count_mode,
        'source_hashes': {str(p.resolve().relative_to(PROJECT)) if p.resolve().is_relative_to(PROJECT)
                          else str(p.resolve()): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
        'tokenizer_sha256': hashlib.sha256(args.tokenizer.read_bytes()).hexdigest() if args.tokenizer else None})
    write_json(args.output / 'contract_snapshot.json', contracts.document)
    write_json(args.output / 'public_task.json', task)
    try:
        result = runner.run()
    except Exception as exc:
        write_json(args.output / 'implementation_error.json', {'type': type(exc).__name__, 'message': str(exc)})
        raise
    print(json.dumps({k: result[k] for k in ('run_id', 'status', 'stop_reason', 'normal_calls', 'http_attempts',
                                           'format_repairs', 'audit_record_count', 'source_bindings_complete',
                                           'pipeline_completed', 'mechanism_evaluable')}))


if __name__ == '__main__':
    main()
