"""Offline historical-mechanism inventory. No model client or network imports."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/bottleneck-selection-20261026'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    inventory = {'kind': 'offline_mechanism_inventory', 'new_model_requests': 0,
                 'source_hash_checks': [], 'historical_instructions': [],
                 'older_live_loop_events': [], 'walkthroughs': []}
    for run in ['local-application-probe-live-20261025-r1',
                'candidate-screening-probe-live-20261025-r1']:
        manifest = read(ROOT / 'runs' / run / 'manifest.json')
        for name, frozen_hash in manifest['code_sha256'].items():
            path = ROOT / name
            current = digest(path) if path.exists() else None
            inventory['source_hash_checks'].append(dict(run=run, path=name,
                frozen_sha256=frozen_hash, current_sha256=current, matches=current == frozen_hash))
    run = 'evidence-first-live-20261025-r1'
    base = ROOT / 'runs' / run
    for name, frozen_hash in read(base / 'frozen_source/SHA256.json').items():
        frozen = base / 'frozen_source' / name
        assert digest(frozen) == frozen_hash, name
        inventory['source_hash_checks'].append(dict(run=run, path=name,
            frozen_sha256=frozen_hash, snapshot_verified=True,
            current_sha256=digest(ROOT / name) if (ROOT / name).exists() else None))

    selections = {
        'candidate-screening-probe-live-20261025-r1': [5, 6, 18, 89, 90, 113, 114, 119, 120],
        'local-application-probe-live-20261025-r1': [1, 4, 5, 8],
        'evidence-first-live-20261025-r1': [16, 17, 18],
    }
    packets = {}
    for run, slots in selections.items():
        rows = [json.loads(x) for x in (ROOT/'runs'/run/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
        selected = {row['attempt']: row for row in rows}
        for slot in slots:
            response = selected[slot]['response']
            instructions = response['instructions']
            prompt, packet_text = instructions.split('PACKET=', 1)
            packet = json.loads(packet_text)
            texts = [c['text'] for message in response['output'] for c in message.get('content', [])
                     if c.get('type') == 'output_text']
            inventory['historical_instructions'].append(dict(run=run, slot=slot,
                instruction_prefix=prompt, packet_keys=list(packet), output_text=texts))
            packets[(run, slot)] = packet

    # Cases are manual design checks; neither model outcomes nor new truth labels.
    cases = [(6, '010', 'C道路信息已提供却称未建立', 'Check supplied C road evidence before claiming absence; do not infer all risks resolved.'),
             (89, '023', '唯一道路及预订例外被弱化', 'Preserve only-road scope and distinguish usual booking policy from a specific exception; retain actual uncertainties.'),
             (119, '027', '旧通路描述盖过有条件的新更新', 'Compare old and updated road evidence while retaining the monitoring condition; risk ranking remains contestable.'),
             (18, '011', '错误的当前状态编码导致排除', 'Question the ready=false abstraction against restoration and task windows; do not force agreement with the report.')]
    run = 'candidate-screening-probe-live-20261025-r1'
    for slot, task, issue, target in cases:
        packet = packets[(run, slot)]
        raw = ROOT / 'runs' / run / f'{slot:02d}.raw.txt'
        inventory['walkthroughs'].append(dict(task=task, origin_run=run, origin_slot=slot,
            origin_raw_sha256=digest(raw), draft=read(raw), actual_received_packet=packet,
            analyst_design_issue=issue, analyst_design_target=target,
            labels_must_not_be_sent_to_model=True, model_tested=False,
            note='Preserve this receiver information boundary; no inaccessible private original pooling.'))

    events = ROOT/'runs/issue-loop-comparison-live-20261024-r2/hb-dev-005-r1/ground_issue_loop_v2/events.jsonl'
    for row in map(json.loads, events.read_text(encoding='utf-8').splitlines()):
        if row.get('kind') in {'ground_review', 'trial_created', 'check_observation'}:
            inventory['older_live_loop_events'].append(row)
    inventory['scope_limits'] = [
        'Current older architecture code is an implementation inventory, not proof that every component ran in recent batches.',
        'Live issue-loop run stopped at CHOOSE before repair/recheck; no completed paired benefit claim.',
        'Manual walkthrough targets are not test outcomes and must remain offline.',
    ]
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT/'MECHANISM_EVIDENCE.json').write_text(json.dumps(inventory, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(dict(historical_instructions=len(inventory['historical_instructions']),
                         walkthroughs=len(inventory['walkthroughs']),
                         verified_frozen_sources=sum(x.get('snapshot_verified', False) for x in inventory['source_hash_checks']),
                         changed_source_entries=sum(x.get('matches') is False for x in inventory['source_hash_checks']),
                         new_model_requests=0), ensure_ascii=False))


if __name__ == '__main__':
    main()
