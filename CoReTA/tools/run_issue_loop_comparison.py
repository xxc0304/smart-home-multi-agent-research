"""Execute exactly the frozen component schedule; scoring data never enters execution."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from prepare_issue_loop_comparison import verify, read, engine, budget, METHODS, digest
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import write_json
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import payload_for
from coreta.schemas import ProtocolError


def cache_digest(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode()).hexdigest()


def run(prepared, output, *, transport_factory=None, counter=None):
    manifest = verify(prepared)
    config, legacy = configure(PROJECT/'config/deepseek_flash_inspection.json', DESIGN/'runtime.defaults.json')
    if config != manifest['config']:
        raise ValueError('Configuration changed')
    if output.exists():
        raise ValueError('New output required; no overwrite or implicit resume')
    output.mkdir(parents=True)
    write_json(output/'manifest.json', manifest)
    counter = counter or load_counter()
    progress = dict(status='running', manifest_sha256=digest(prepared/'manifest.json'),
        http_attempts=0, input_tokens=0, output_tokens=0,
        format_repairs=0, unknown_usage=False, unknown_usage_attempts=0, units=[], completed_pairs=[],
        max_http_attempts=manifest['max_http_attempts'], max_output_tokens=manifest['max_output_tokens'])

    def persist():
        write_json(output/'progress.json', progress)

    persist()
    try:
        for pair in manifest['pairs']:
            packets = ChoicePackets(Path(pair['pack']), 'distributed')
            if (packets.task['task_id'] != pair['task_id'] or len(packets.agents) != pair['members']
                    or packets.agents[pair['ordinal'] % len(packets.agents)] != pair['editor']
                    or pair['settings'] != budget(len(packets.agents), legacy)
                    or set(pair['methods']) != set(METHODS) or len(pair['methods']) != 2):
                raise ValueError('Frozen roster/settings mismatch')
            cache = read(prepared/pair['initial_cache'])
            (output/pair['id']).mkdir(parents=True, exist_ok=True)
            write_json(output/pair['initial_cache'], cache)
            initial_sha = cache_digest(cache)
            for method in pair['methods']:
                folder = output/pair['id']/method
                folder.mkdir(parents=True)
                row = dict(pair=pair['id'], method=method, status='running', cache_sha256=initial_sha)
                progress['units'].append(row)
                persist()
                transport = transport_factory(pair['id'], method) if transport_factory else None
                runner = engine(folder, packets, config, legacy, method, pair['ordinal'], cache,
                                counter, transport=transport)
                original_call = runner.gateway.call
                first = True

                def bounded(stage, member, packet):
                    nonlocal first
                    cap = runner.gateway.outputs[stage.lower()]
                    if progress['unknown_usage']:
                        raise ProtocolError('USAGE_UNKNOWN', 'Cannot continue with unknown usage')
                    if progress['http_attempts'] >= manifest['max_http_attempts']:
                        raise ProtocolError('ATTEMPT_BUDGET', 'Batch request limit')
                    if progress['output_tokens'] + cap > manifest['max_output_tokens']:
                        raise ProtocolError('OUTPUT_BUDGET', 'Batch output reservation failed')
                    if first:
                        frozen = read(prepared/pair['id']/method/'first_observe.request.json')
                        if stage != 'OBSERVE' or payload_for(runner, stage, packet) != frozen:
                            raise ProtocolError('INPUT_ERROR', 'First request differs from frozen preview')
                        first = False
                    before = runner.gateway.client.attempts
                    offset = len(runner.journal.usage)
                    repairs = runner.journal.repairs
                    try:
                        return original_call(stage, member, packet)
                    finally:
                        count = runner.gateway.client.attempts-before
                        usage = runner.journal.usage[offset:]
                        progress['http_attempts'] += count
                        progress['format_repairs'] += runner.journal.repairs-repairs
                        known = (len(usage) == count and all(type(u.get(k)) is int and u[k] >= 0
                                 for u in usage for k in ('input_tokens', 'output_tokens')))
                        if not known:
                            progress['unknown_usage'] = True
                            progress['unknown_usage_attempts'] += count
                        else:
                            progress['input_tokens'] += sum(u['input_tokens'] for u in usage)
                            progress['output_tokens'] += sum(u['output_tokens'] for u in usage)
                        persist()

                runner.gateway.call = bounded
                result = runner.run()
                row.update(status=result['status'], http_attempts=result['http_attempts'], error=result['error'])
                if result['status'] != 'completed' or progress['unknown_usage']:
                    raise ProtocolError('DEVELOPMENT_STOP', 'Stop after technical interruption')
                if cache_digest(cache) != initial_sha:
                    raise ValueError('Shared cache mutated')
            progress['completed_pairs'].append(pair['id'])
            persist()
        progress['status'] = 'completed'
    except Exception as exc:
        if progress['units'] and progress['units'][-1]['status'] == 'running':
            progress['units'][-1]['status'] = 'interrupted'
        progress.update(status='stopped_on_first_technical_error',
                        error=dict(type=type(exc).__name__, detail=str(exc)))
        raise
    finally:
        persist()
    return progress


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--prepared', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--live', action='store_true')
    args = parser.parse_args()
    if not args.live or not os.environ.get('DEEPSEEK_API_KEY'):
        parser.error('Requires --live and configured API key')
    result = run(args.prepared, args.output)
    print(json.dumps(dict(status=result['status'], http_attempts=result['http_attempts'])))


if __name__ == '__main__':
    main()
