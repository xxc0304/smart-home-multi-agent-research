"""Freeze development comparison offline; no live execution or credential loading."""
import argparse
import copy
import hashlib
import json
from pathlib import Path

from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import Journal, write_json
from coreta.workboard.access_ground import AccessRunner, AccessPrompts
from coreta.workboard.artifacts import ChoiceAdapter
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import input_sources, payload_for
from coreta.workboard.gateway import Gateway
from coreta.workboard.grounded import GroundContracts
from coreta.workboard.issue_loop import IssueRunner, IssuePrompts, IssueContracts, settings


DATA = PROJECT / 'data/task-packs/hiddenbench-grounded-dev-20261024-v1'
ARCHIVE = PROJECT / 'runs/grounded-three-arm-pilot-live-20261024-r1'
DOC = PROJECT / 'refine-logs/issue-loop-20261024'
METHODS = ('ground_access_only_v2', 'ground_issue_loop_v2')


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def source_snapshot():
    values = input_sources(DATA)
    paths = [Path(__file__), PROJECT/'tools/run_issue_loop_comparison.py',
             PROJECT/'tools/audit_issue_loop_load.py', PROJECT/'tools/export_issue_loop_review.py',
             DOC/'COMPARISON_PLAN.md', DOC/'DESIGN.md', DOC/'RUBRIC.md', DOC/'FINAL_AUDIT.md',
             DOC/'LOAD_AUDIT_DEDUP.json']
    paths += [ARCHIVE/(task+'-r1')/'initial/cache.json' for task in ('hb-dev-005', 'hb-dev-006')]
    values.update({str(path.resolve()): digest(path) for path in paths})
    return values


def budget(n, legacy):
    value = settings(n, legacy)
    out = value['max_output_tokens']
    cycle = (n-1)*out['observe'] + sum(out[s] for s in ('ground', 'try', 'check_use', 'choose'))
    closing = sum(out[s] for s in ('finalize', 'final_check_use', 'final_check_effect', 'final_choose'))
    value['limits']['max_network_attempts_total'] = (n+1)**2
    value['limits']['max_output_tokens_total'] = (n-1)*cycle + closing
    value['budget_status'] = 'issue_loop_comparison_v1'
    return value


def engine(folder, packets, config, legacy, method, ordinal, cache, counter, transport=None):
    if method not in METHODS:
        raise ValueError('Unexpected method')
    issue = method == METHODS[1]
    adapter = ChoiceAdapter(packets.task)
    contracts = IssueContracts(adapter) if issue else GroundContracts(adapter)
    prompts = IssuePrompts() if issue else AccessPrompts()
    gateway = Gateway(config, budget(len(packets.agents), legacy), contracts, prompts, Journal(folder),
                      token_counter=counter, transport=transport)
    cls = IssueRunner if issue else AccessRunner
    return cls(packets, gateway, gateway.journal, adapter, task_ordinal=ordinal,
               initial_cache=copy.deepcopy(cache))


def prepare(output, counter=None):
    if output.exists():
        raise ValueError('Use a new output directory')
    config, legacy = configure(PROJECT/'config/deepseek_flash_inspection.json', DESIGN/'runtime.defaults.json')
    counter = counter or load_counter()
    output.mkdir(parents=True)
    manifest = dict(kind='issue_loop_component_comparison_v1', status='frozen_not_run',
        network_requests=0, config=config, pairs=[], max_http_attempts=0, max_output_tokens=0,
        scope='historical_development_diagnostic_not_holdout', scoring_feedback=False,
        source_hashes=source_snapshot(), prepared_hashes={}, offline_evaluation_hashes={})
    for index, (task_id, ordinal) in enumerate((('hb-dev-005', 1), ('hb-dev-006', 2))):
        pair_id = task_id+'-r1'
        packets = ChoicePackets(DATA/task_id, 'distributed')
        n = len(packets.agents)
        evaluation = DATA/task_id/'offline/evaluation.json'
        manifest['offline_evaluation_hashes'][task_id] = digest(evaluation)
        archive_cache = ARCHIVE/pair_id/'initial/cache.json'
        cache = read(archive_cache)
        if cache['member_packet_hashes'] != packets.hashes or set(cache['candidates']) != set(packets.agents):
            raise ValueError('Archived initial cache does not match task packets')
        relative_cache = pair_id+'/initial_cache.json'
        (output/pair_id).mkdir()
        write_json(output/relative_cache, cache)
        manifest['source_hashes'][str(archive_cache.resolve())] = digest(archive_cache)
        manifest['prepared_hashes'][relative_cache] = digest(output/relative_cache)
        limits = budget(n, legacy)
        methods = list(METHODS if index == 0 else reversed(METHODS))
        manifest['pairs'].append(dict(id=pair_id, task_id=task_id, pack=str(DATA/task_id),
            ordinal=ordinal, editor=packets.agents[ordinal % n], members=n, methods=methods,
            initial_cache=relative_cache, settings=limits, preview_inputs={}))
        row = manifest['pairs'][-1]
        for method in methods:
            (output/pair_id/method).mkdir()
            runner = engine(output/pair_id/method, packets, config, legacy, method, ordinal, cache, counter)
            runner.initialize()  # Cached INITIAL only, verified through current contracts; no client call.
            runner.cycle = 1  # First live OBSERVE is emitted inside collaborate's first cycle.
            member = next(a for a in packets.agents if a != runner.editor)
            packet = runner.packet(member, 'OBSERVE')
            payload = payload_for(runner, 'OBSERVE', packet)
            relative = pair_id+'/'+method+'/first_observe.request.json'
            write_json(output/relative, payload)
            manifest['prepared_hashes'][relative] = digest(output/relative)
            row['preview_inputs'][method] = runner.gateway.client.size(payload)
        manifest['max_http_attempts'] += 2*limits['limits']['max_network_attempts_total']
        manifest['max_output_tokens'] += 2*limits['limits']['max_output_tokens_total']
    # Cached initialization creates state previews; protect every generated preparation file.
    manifest['prepared_hashes'] = {path.relative_to(output).as_posix(): digest(path)
        for path in output.rglob('*') if path.is_file()}
    write_json(output/'manifest.json', manifest)
    return manifest


def verify(output):
    manifest = read(output/'manifest.json')
    if manifest['kind'] != 'issue_loop_component_comparison_v1':
        raise ValueError('Unexpected manifest kind')
    expected = [('hb-dev-005-r1', 'hb-dev-005', 1, list(METHODS), 4),
                ('hb-dev-006-r1', 'hb-dev-006', 2, list(reversed(METHODS)), 3)]
    actual = [(p['id'], p['task_id'], p['ordinal'], p['methods'], p['members']) for p in manifest['pairs']]
    if actual != expected:
        raise ValueError('Changed schedule')
    if manifest['source_hashes'] != source_snapshot():
        raise ValueError('Source snapshot changed or incomplete')
    actual_files = {path.relative_to(output).as_posix() for path in output.rglob('*')
                    if path.is_file() and path != output/'manifest.json'}
    if actual_files != set(manifest['prepared_hashes']):
        raise ValueError('Prepared file list changed or incomplete')
    for pair in manifest['pairs']:
        if (Path(pair['pack']).resolve() != (DATA/pair['task_id']).resolve()
                or pair['initial_cache'] != pair['id']+'/initial_cache.json'):
            raise ValueError('Changed task/cache path')
    for path, sha in manifest['source_hashes'].items():
        if digest(Path(path)) != sha:
            raise ValueError('Stale source: '+path)
    for rel, sha in manifest['prepared_hashes'].items():
        path = (output/rel).resolve()
        if not path.is_relative_to(output.resolve()) or digest(path) != sha:
            raise ValueError('Changed prepared file: '+rel)
    if manifest['max_http_attempts'] != 82 or manifest['max_output_tokens'] != 225280:
        raise ValueError('Unexpected comparison budget')
    return manifest


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    manifest = verify(args.output) if args.verify else prepare(args.output)
    print(json.dumps({k: manifest[k] for k in
        ('status', 'network_requests', 'max_http_attempts', 'max_output_tokens')}))


if __name__ == '__main__':
    main()
