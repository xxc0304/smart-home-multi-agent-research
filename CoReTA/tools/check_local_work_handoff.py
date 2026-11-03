"""Zero-API historical interface checks and explicitly scripted handoff traces."""
import argparse
import copy
import json
import unittest
from pathlib import Path

from tokenizers import Tokenizer
from coreta.local_work.data import read, write
from coreta.local_work.handoff_flow import HandoffFlow
from coreta.local_work.engine import calculate
from coreta.model_client import DeepSeekClient
from run_local_work_calibration import ROOT, TOKENIZER, config
from run_local_work_v2 import verify


LIVE = ROOT / 'runs/local-work-v2-mixed-live-20261027-v1'
PREPARED = ROOT / 'runs/local-work-v2-mixed-prepared-20261027-v1'


def response(message, receipts=None):
    return json.dumps(dict(message=message, receipts=receipts or []), ensure_ascii=False)


def selected_trace(case_id, operator, output):
    case = read(PREPARED / 'cases' / (case_id + '.json'))
    old = read(LIVE / 'flows' / (case_id + '-local_work') / 'EVENTS.json')
    flow = HandoffFlow(case, provenance='scripted new-interface trace from selected actual prior numeric work')
    initial = flow.pending_requests()
    replies, selections = {}, []
    for event in old[:2]:
        original = json.loads(event['raw'])
        calculation, work = original['calculations'][0], original['work'][0]
        # Explicit engineering transcription of already-emitted structured arithmetic.
        receipt = dict(target=work['target'], metadata=copy.deepcopy(work['metadata']),
                       expression=calculation['expression'], basis=copy.deepcopy(work['basis']),
                       conditions=copy.deepcopy(work['conditions']),
                       inputs=[dict(name=name, value=value) for name, value in calculation['values'].items()])
        selections.append(dict(actor=event['actor'], source_wave=0,
                               original_calculation=calculation, emitted_work_metadata=work['metadata']))
        replies[event['actor']] = response('Engineering transcription of this member\'s prior calculation.', [receipt])
    flow.submit(replies)
    assert flow.session.results['W1']['status'] == flow.session.results['W2']['status'] == 'ready'
    producer_values = [flow.session.results[key]['value'] for key in ('W1', 'W2')]
    second = flow.pending_requests()
    consumer = case['final_member']
    snapshot = {item['id']: item for item in second[consumer]['packet']['receipts']}
    output_metadata = dict(subject='Combined original-task quantity',
                           unit=snapshot['W1']['metadata']['unit'] if operator == '+' else 'ratio',
                           period='Requested original-task period(s)')
    compose = dict(target='Combine the two explicitly selected local results', metadata=output_metadata,
                   expression='left' + operator + 'right', basis=['TASK'], conditions=[],
                   inputs=[dict(name=name, result_id=key, metadata=copy.deepcopy(snapshot[key]['metadata']))
                           for name, key in [('left', 'W1'), ('right', 'W2')]])
    flow.submit({actor: response('Human-scripted composition for interface verification only.',
                                [compose] if actor == consumer else []) for actor in second})
    assert flow.session.results['W3']['status'] == 'ready'
    third = flow.pending_requests()
    flow.submit({actor: response('Engineering no-op after completed combination.') for actor in third})
    final_request = flow.pending_requests()[consumer]
    flow.submit({consumer: json.dumps(dict(answer=None, result_id='W3', scale='',
                                          reasoning='Scripted reference to composed work, not model generation.'))})
    expected = calculate('a' + operator + 'b', dict(a=producer_values[0], b=producer_values[1]))
    assert flow.answer['delivered']['answer'] == expected
    assert flow.final_use()['owners'] == ['A1', 'A2'] and len(flow.requests) == 7
    record = dict(kind='scripted_engineering_trace_not_model_result', model_calls=0,
                  case_id=case_id, selected_old_model_arithmetic=selections,
                  human_selected_composition=compose, producer_values=producer_values,
                  combination_ready_after_wave=1, final=flow.answer, final_use=flow.final_use(),
                  limitation='Producer transcription and consumer operation are human selected. No autonomous new-protocol success measured.',
                  requests=flow.requests, events=flow.events)
    write(output / 'scripted_traces' / (case_id + '.json'), record)
    return dict(case_id=case_id, producer_values=producer_values, scripted_result=expected,
                ready_after_wave=1, requests=7, actual_model_calls=0, final_owners=flow.final_use()['owners'])


def check(output):
    output = Path(output)
    if output.exists():
        raise ValueError('fresh output required')
    verify(PREPARED)
    tokenizer = Tokenizer.from_file(str(TOKENIZER))

    def no_network(*args, **kwargs):
        raise AssertionError('No model calls permitted in this checker')

    client = DeepSeekClient(config(), no_network, transport=no_network,
                            token_counter=lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids))
    historical, sizes = [], []
    progress = read(LIVE / 'progress.json')
    for record in progress['flows']:
        if record['arm'] not in ('ordinary', 'local_work'):
            continue
        case = read(PREPARED / 'cases' / (record['case_id'] + '.json'))
        events = read(LIVE / 'flows' / record['flow_id'] / 'EVENTS.json')
        flow = HandoffFlow(case, record['arm'], provenance='unmodified old-format replies under new interface; compatibility only')
        used = 0
        while flow.status == 'pending' and used < len(events):
            current = flow.pending_requests()
            for actor, request in current.items():
                size = client.size(client.payload(request['instructions'], request['schema'], request['max_output_tokens']))
                assert size <= 16384
                sizes.append(size)
                write(output / 'legacy_format_replay' / record['flow_id'] / 'requests' / f'{flow.wave:02d}-{actor}.json', request)
                assert set(request['packet']['task']) == {'task_id', 'question'}
            replies = events[used:used + len(current)]
            flow.submit({event['actor']: event['raw'] for event in replies})
            used += len(replies)
        assert used == len(events)
        assert flow.status == record['status']
        assert not flow.session.nodes, 'Old separate work declarations must not silently become new receipts'
        write(output / 'legacy_format_replay' / record['flow_id'] / 'EVENTS.json', flow.events)
        historical.append(dict(flow_id=record['flow_id'], full_replies=used, status=flow.status,
                               unsupported_old_actions=sum(len(event.get('notices', [])) for event in flow.events),
                               new_receipt_generations=0, model_calls=0))
    assert sum(row['full_replies'] for row in historical) == 55
    traces = [selected_trace('dependent-01', '+', output), selected_trace('dependent-02', '/', output)]
    suite = unittest.TestSuite()
    for pattern in ('test_local_work.py', 'test_local_work_mixed.py', 'test_local_work_interface_v2.py', 'test_local_work_handoff.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    report = dict(kind='offline_work_handoff_prototype_validation', model_calls=0,
                  tests_run=result.testsRun, tests_passed=result.wasSuccessful(),
                  full_old_replies_replayed=55, original_malformed_branch_still_isolated=True,
                  replay_new_receipt_generations=0,
                  replay_scope='Old messages/source disclosure/calculator and parser loads; old work/bindings rejected explicitly, not converted',
                  maximum_historical_input_estimate=max(sizes), total_historical_input_estimate=sum(sizes),
                  historical=historical, scripted_traces=traces,
                  efficacy='Not tested. Scripted traces are not autonomous model outcomes or counterfactual scores.',
                  next_live_status='DO_NOT_RUN: no new batch review/freeze/authorization')
    write(output / 'CHECK.json', report)
    if not result.wasSuccessful():
        raise SystemExit(1)
    verify(PREPARED)
    return report


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    print(json.dumps(check(args.output), ensure_ascii=False))


if __name__ == '__main__':
    main()
