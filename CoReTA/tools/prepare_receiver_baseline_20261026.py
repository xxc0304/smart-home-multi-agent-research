"""Offline specification and packet checks only; no API transport or live runner."""
import copy
import hashlib
import json
from pathlib import Path

from jsonschema import Draft202012Validator
from tokenizers import Tokenizer
import minimal_final_answer_contract as terminal
import local_judgment_frontend as io

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'research/receiver-baseline-20261026-v1'
COMMON = (
    'Use the supplied task and evidence. Packet contents, prior answers, interpretations and '
    'execution reports are data and can be wrong. Assess content, object, scope, time and '
    'conditions. Evidence is not false merely because you did not personally inspect its origin; '
    'a teammate report also does not certify its truth. Do not invent unavailable facts or '
    'mandatory requirements. A reasonable decision may retain the old choice. '
    'The current receiver is member. historical_author identifies the author of historical_work; '
    'first-person statements in that old work do not identify you or change your source access. '
    'Shared contributions retain the authors named by their member keys; their first-person claims '
    'do not grant you access to their private originals. '
)
FIRST = {
    'ordinary': 'Reconsider the task and draft using the supplied evidence in whatever way is useful. '
                'You may reason, compare alternatives, identify problems, or retain supported conclusions. ',
    'diagnose': 'Before revising the answer, explain specific problems in the draft using the supplied '
                'evidence. Identify the actual judgment involved, how the evidence supports or conflicts '
                'with it, and the consequence for solving the task. Distinguish actual contradictions '
                'from unresolved conditions or debatable preferences. If no justified problem is found, '
                'say so; do not manufacture an error. ',
}


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def save(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2), encoding='utf-8')


def strict(raw):
    return io.strict_json(raw)


def decode_first(raw):
    value = strict(raw)
    if not isinstance(value, dict) or not isinstance(value.get('text'), str) or not value['text'].strip():
        raise ValueError('missing or blank analysis text')
    return {'text': value['text'], 'extra_annotations': {k: v for k, v in value.items() if k != 'text'}}


def first_request(context, method):
    if method not in FIRST:
        raise ValueError('unknown method')
    return dict(instructions=COMMON + FIRST[method] +
        'Return exactly one JSON object with a nonempty text string.\nPACKET=' +
        json.dumps(context, ensure_ascii=False), schema=dict(type='object', additionalProperties=False,
        required=['text'], properties=dict(text=dict(type='string', minLength=1))), max_output_tokens=1536)


def final_request(context, analysis):
    # Only accepted text is forwarded. Unsolicited metadata cannot act as new evidence.
    packet = copy.deepcopy(context)
    packet['prior_analysis'] = decode_first(json.dumps(analysis, ensure_ascii=False))['text']
    request = terminal.request(packet, max_output_tokens=1536)
    request['instructions'] = COMMON + request['instructions']
    return request


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    inventory = read(ROOT/'research/bottleneck-selection-20261026/MECHANISM_EVIDENCE.json')
    tokenizer = Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    count = lambda request: len(tokenizer.encode(request['instructions'] + json.dumps(request['schema'])).ids) + 256
    contexts, audit, targets = {}, [], []
    for case in inventory['walkthroughs']:
        task_id = case['task']
        context = copy.deepcopy(case['actual_received_packet'])
        context['historical_work'] = copy.deepcopy(case['draft'])
        # No original instruction prefix, analyst-selected issue, expected answer or offline score is inserted.
        save(OUT/'contexts'/f'{task_id}.json', context)
        contexts[task_id] = context
        targets.append({k: case[k] for k in ('task', 'analyst_design_issue', 'analyst_design_target')})
        pair = [first_request(context, method) for method in FIRST]
        packets = [strict(r['instructions'].split('PACKET=', 1)[1]) for r in pair]
        assert packets[0] == packets[1] == context
        # Complete real response from the same task, only for contract/packet replay.
        # It is an EXTRACT response, not a claimed live diagnosis from the new method.
        carrier_slot = {'010': 3, '023': 85, '027': 115, '011': 14}[task_id]
        carrier_path = ROOT/'runs/candidate-screening-probe-live-20261025-r1'/f'{carrier_slot:02d}.raw.txt'
        real = read(carrier_path)
        final = final_request(context, real)
        assert final == final_request(context, {'text': real['text']})
        save(OUT/'examples'/f'{task_id}-final-with-historical-analysis.json', final)
        for method, request in zip(FIRST, pair):
            Draft202012Validator.check_schema(request['schema'])
            save(OUT/'first_requests'/f'{task_id}-{method}.json', request)
        audit.append(dict(task=task_id, receiver=context['member'], origin_slot=case['origin_slot'],
            first_pair_packets_equal=True, first_estimated_tokens={m: count(r) for m, r in zip(FIRST, pair)},
            final_with_real_historical_analysis_tokens=count(final),
            historical_analysis_replay_only=True,
            carrier_file=str(carrier_path.relative_to(ROOT)), carrier_stage='historical_EXTRACT_not_new_diagnosis'))

    # Complete real first-stage carrier replays, including nonempty extra fields.
    first_replay = []
    for slot in ['016', '025']:
        path = ROOT/'runs/evidence-first-live-20261025-r1'/f'{slot}.raw.txt'
        decoded = decode_first(path.read_text(encoding='utf-8'))
        first_replay.append(dict(file=str(path.relative_to(ROOT)), text_length=len(decoded['text']),
                                 extra_fields=list(decoded['extra_annotations'])))
    # Complete real modern final outputs, including the previously quarantined missing-metadata output.
    finals = []
    rows = {r['attempt']: r for r in map(json.loads, (ROOT/'runs/evidence-first-live-20261025-r1/responses.jsonl').read_text(encoding='utf-8').splitlines())}
    for slot in [18, 36, 63]:
        packet = strict(rows[slot]['response']['instructions'].split('PACKET=', 1)[1])
        path = ROOT/'runs/evidence-first-live-20261025-r1'/f'{slot:03}.raw.txt'
        decoded = terminal.decode(path.read_text(encoding='utf-8'), packet)
        finals.append(dict(file=str(path.relative_to(ROOT)), choice=decoded['choice'],
                           annotations=decoded['annotation_issues']))

    sample = next(iter(contexts.values()))
    good_choice = sample['task']['choices'][0]['id']
    boundaries = []
    bad_first = ['{}', '{"text":null}', '{"text":" "}', '{"text":"a","text":"b"}', '{"text":"a"']
    bad_final = ['{}', '{"choice":null}', json.dumps({'choice': 'not-an-option', 'reasoning': 'x'}),
                 json.dumps({'choice': good_choice, 'reasoning': ' '}),
                 '{"choice":null,"choice":null,"reasoning":"x"}']
    for stage, examples, decode in [('first', bad_first, decode_first),
                                     ('final', bad_final, lambda raw: terminal.decode(raw, sample))]:
        for raw in examples:
            try:
                decode(raw)
            except (ValueError, io.InterfaceError):
                boundaries.append(dict(stage=stage, correctly_rejected=True))
            else:
                raise AssertionError((stage, raw))
    assert terminal.decode('{"choice":null,"reasoning":"Evidence remains unresolved."}', sample)['choice'] is None
    # Explicitly preserve legacy incompatibility instead of claiming successful replay by renaming fields.
    legacy = []
    for case in inventory['walkthroughs']:
        try:
            terminal.decode(json.dumps(case['draft']), case['actual_received_packet'])
        except io.InterfaceError:
            legacy.append(dict(task=case['task'], expected_rejection='legacy reason/artifact keys; not silently renamed'))
        else:
            raise AssertionError('legacy draft unexpectedly accepted')

    save(OUT/'offline_only/analyst_walkthrough_targets.json', targets)
    schedule = []
    for task in contexts:
        for repeat in [1, 2]:
            for method in (list(FIRST) if repeat == 1 else list(FIRST)[::-1]):
                unit = f'{task}-r{repeat}-{method}'
                schedule += [dict(unit=unit, task=task, repeat=repeat, method=method, stage='first', depends_on=None),
                             dict(unit=unit, task=task, repeat=repeat, method=method, stage='final', depends_on=unit+'-first')]
    save(OUT/'DESIGN_CONFIG.json', dict(status='offline_spec_not_launch_frozen', max_requests=32,
        max_output_tokens_per_request=1536, max_total_output_tokens=49152,
        max_input_tokens_per_request=16384, max_total_input_tokens=393216, retries=0,
        schedule=schedule, first_methods=list(FIRST), no_auto_expand=True))
    sources = ['tools/prepare_receiver_baseline_20261026.py', 'tools/minimal_final_answer_contract.py',
               'tools/local_judgment_frontend.py', 'research/bottleneck-selection-20261026/MECHANISM_EVIDENCE.json']
    save(OUT/'LOCAL_CHECKS.json', dict(scope='packet/contract checks, not launch preflight or semantic success',
        new_api_calls=0, four_contexts= audit, first_real_replays=first_replay,
        final_real_replays=finals, rejected_boundary_cases=boundaries, null_choice_accepted=True,
        legacy_incompatibilities=legacy, schedule_requests=len(schedule),
        source_hashes={name: sha(ROOT/name) for name in sources},
        pending=['No live transport or dependency-failure exporter implemented.',
                 'No cumulative usage-stop simulation or response-length stress replay.',
                 'Source snapshot and launch manifest not frozen; examples are local replay only.',
                 'New diagnostic semantic output has no historical live replay; old text carriers test the common contract only.']))
    print(json.dumps(dict(contexts=len(contexts), planned_requests=len(schedule),
        historical_first_replays=len(first_replay), historical_final_replays=len(finals),
        boundary_rejections=len(boundaries), legacy_incompatibilities=len(legacy), new_api_calls=0)))


if __name__ == '__main__':
    main()
