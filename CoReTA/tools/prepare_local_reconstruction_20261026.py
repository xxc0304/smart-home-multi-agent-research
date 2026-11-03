"""Build real historical case packets; no paid requests, no gold loading."""
import copy
import hashlib
import json
from pathlib import Path

import local_judgment_frontend as io
import local_reconstruction_probe as probe

ROOT = io.ROOT
OUT = ROOT/'research/isolated-reconstruction-20261026-v1'
HISTORY = {
    '004': 'candidate-004-probe-live-20261025-r2',
    '009': 'candidate-transfer-probe-live-20261025-r1',
    '011': 'candidate-screening-probe-live-20261025-r1',
    '023': 'candidate-screening-probe-live-20261025-r1',
}
# Deliberate, analyst-selected diagnostic targets, not autonomous discovery.
SPECS = [
    ('004-age-10', '004', 10, 7, 'A2', 'age', True),
    ('004-age-09', '004', 9, 7, 'A2', 'age', True),
    ('009-beds-11', '009', 11, 10, 'A4', 'beds', True),
    ('009-beds-06', '009', 6, 4, 'A4', 'beds', True),
    ('011-time-18', '011', 18, 14, 'A2', 'time', True),
    ('011-time-24', '011', 24, 20, 'A2', 'time', True),
    ('023-road-89', '023', 89, 85, 'A1', 'road', True),
    ('023-road-95', '023', 95, 91, 'A1', 'road', True),
    ('023-booking-89', '023', 89, 86, 'A2', 'booking', False),
    ('023-booking-95', '023', 95, 92, 'A2', 'booking', False),
]
QUESTIONS = {
    'age': 'What restrictions do your sources place on the culprit\'s age, and which listed ages are compatible? Distinguish age compatibility from establishing responsibility.',
    'beds': 'What do your sources establish about Hospital B\'s present critical-care bed availability, and how does that relate to the public description of its ICU?',
    'time': 'What timing and certainty do your sources give for School Gym restroom availability relative to the relocation window? Distinguish current state, expected future state, and confirmation.',
    'road': 'What do your sources establish about access to Lakeview Resort during the banquet\'s scheduled time? State the geographic scope and time limits of the report.',
    'booking': 'What do your sources establish about short-notice booking at Grand Oak Hotel for the task\'s scheduled event? State applicability conditions, how this relates to the public notice policy, and what remains unconfirmed.',
}
RUBRICS = {
    'age': ['Preserve less-than-30 and stated candidate ages; do not equate compatible age with guilt.',
            'Do not let drinking or an inferred passenger role defeat a stated age exclusion.'],
    'beds': ['Distinguish ICU infrastructure/staffing from present bed availability.',
             'Treat source as a current report; do not certify all other hospital requirements or invent a bypass.'],
    'time': ['Preserve expected restoration, within-one-hour wording, and two-hour relocation context.',
             'Neither certify completed repairs nor equate not ready now with impossible by the task window.'],
    'road': ['Preserve ONLY access road and closure through the weekend.',
             'Do not infer an available alternative route or establish all other venue requirements.'],
    'booking': ['Preserve this-week phone-booking exception and usual advance-notice policy.',
                'Can accept phone bookings is not confirmed reservation, catering permission, or capacity.'],
}


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def rows(run):
    path = ROOT/'runs'/run/'responses.jsonl'
    return {r['attempt']: r for r in map(io.strict_json, path.read_text(encoding='utf-8').splitlines())}


def response_text(row):
    return ''.join(c['text'] for item in row['response']['output'] for c in item.get('content', [])
                   if c.get('type') == 'output_text')


def historical_packet(row):
    return io.strict_json(row['response']['instructions'].split('PACKET=', 1)[1])


def main():
    if OUT.exists():
        raise ValueError('preparation exists; use a new version rather than overwriting it')
    sources = {}
    index, rubrics, schedule = [], [], []
    for number, (identifier, task, slot, checker_slot, checker, relation, scheduled) in enumerate(SPECS):
        run = HISTORY[task]
        records = rows(run)
        original = historical_packet(records[slot])
        checker_original = historical_packet(records[checker_slot])
        assert checker_original['member'] == checker
        assert checker_original['task'] == original['task']
        answer = io.strict_json(response_text(records[slot]))
        assert isinstance(answer.get('reason'), str) and 'artifact' in answer
        source_log = ROOT/'runs'/run/'responses.jsonl'
        raw = ROOT/'runs'/run/f'{slot:02d}.raw.txt'
        checker_raw = ROOT/'runs'/run/f'{checker_slot:02d}.raw.txt'
        assert raw.read_text(encoding='utf-8').strip() == response_text(records[slot]).strip()
        assert checker_raw.read_text(encoding='utf-8').strip() == response_text(records[checker_slot]).strip()
        # Original legacy answer is retained verbatim as data; no choice/reason rewriting.
        receiver = {k: copy.deepcopy(v) for k, v in original.items() if k != 'field_meanings'}
        receiver['historical_author'] = original['member']
        receiver['historical_work'] = copy.deepcopy(answer)
        local = {k: copy.deepcopy(checker_original[k]) for k in ('task','member','public_sources','own_sources')}
        case = dict(case_id=identifier, checker_context=local, receiver_context=receiver,
                    target_answer=answer, local_question=QUESTIONS[relation])
        io.write(OUT/'cases'/f'{identifier}.json', case)
        io.write(OUT/'archive'/f'{identifier}.json', dict(actual_received_packet=original, actual_answer=answer))
        for method in probe.METHODS:
            io.write(OUT/'request_examples'/f'{identifier}-{method}-local.json', probe.local_request(case, method))
        # Full real EXTRACT carrier, only for common text/packet replay, not semantic checking success.
        carrier = probe.decode_local(response_text(records[checker_slot]))
        io.write(OUT/'request_examples'/f'{identifier}-final-HISTORICAL-CARRIER.json', probe.final_request(case, carrier))
        for path in [source_log, raw, checker_raw]:
            sources[path.relative_to(ROOT).as_posix()] = sha(path)
        index.append(dict(case_id=identifier, task=task, relation=relation, target_slot=slot,
                          checker_slot=checker_slot, checker=checker, receiver=original['member'],
                          source_run=run, scheduled=scheduled,
                          selection='manual diagnostic target after historical outcomes; not autonomous or held-out',
                          common_change='field_meanings omitted from both arms; original retained in archive',
                          target_raw=raw.relative_to(ROOT).as_posix(),
                          carrier_raw=checker_raw.relative_to(ROOT).as_posix()))
        rubrics.append(dict(case_id=identifier, local_criteria=RUBRICS[relation],
                            final_criteria=['Check actual decision and consequence, not citation alone.',
                                            'Retain justified decisions; allow rejection of incorrect feedback.',
                                            'Record abstention separately from technical failure.'],
                            status='analyst rubric; no official answer loaded, not independent semantic gold'))
        if scheduled:
            order = probe.METHODS if number % 2 == 0 else probe.METHODS[::-1]
            for method in order:
                unit = f'{identifier}-{method}'
                schedule.extend([dict(case_id=identifier, method=method, stage='local', unit=unit, depends_on=None),
                                 dict(case_id=identifier, method=method, stage='final', unit=unit, depends_on=unit+'-local')])
    io.write(OUT/'CASE_INDEX.json', index)
    io.write(OUT/'offline_only/RUBRICS.json', rubrics)
    io.write(OUT/'DESIGN_CONFIG.json', dict(status='offline_spec_no_live_runner_or_authorization',
        max_proposed_requests=len(schedule), output_cap_per_request=probe.CAP,
        max_total_output_tokens=len(schedule)*probe.CAP, max_input_tokens_per_request=16384,
        max_total_input_tokens=524288, retries=0, no_auto_expand=True,
        repeats_per_historical_case=1, native_tasks=4, scheduled_historical_cases=8,
        walkthrough_only_cases=2, schedule=schedule,
        failure_policy=dict(local_unreadable='quarantine and block dependent final; other independent units may continue',
                            two_consecutive_unreadable='stop', transport_or_usage_or_budget_error='stop'),
        scope='analyst-targeted local-component diagnosis, not full architecture or new-instance confirmation'))
    code = [Path(__file__), Path(probe.__file__), ROOT/'tools/minimal_final_answer_contract.py',
            ROOT/'tools/local_judgment_frontend.py']
    sources.update({p.relative_to(ROOT).as_posix():sha(p) for p in code})
    io.write(OUT/'SOURCE_MANIFEST.json', dict(status='source_and_builder_snapshot_not_launch_manifest', sources=sources,
        case_sha256={p.relative_to(OUT).as_posix():sha(p) for p in sorted((OUT/'cases').glob('*.json'))}))
    print(json.dumps(dict(cases=len(index), scheduled_requests=len(schedule), new_api_calls=0)))


if __name__ == '__main__':
    main()
