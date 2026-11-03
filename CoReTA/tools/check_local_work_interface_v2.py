"""Zero-network regression and full real-response replay for the versioned interface."""
import argparse
import json
import unittest
from pathlib import Path

from tokenizers import Tokenizer
from coreta.local_work.comparison_v2 import ComparisonFlowV2
from coreta.local_work.data import read, write
from coreta.model_client import DeepSeekClient
from run_local_work_calibration import config, TOKENIZER


ROOT = Path(__file__).resolve().parents[1]


def check(output):
    output = Path(output)
    live = ROOT / 'runs/local-work-calibration-live-20261027-v1'
    prepared = ROOT / 'runs/local-work-calibration-prepared-20261027-v1'
    progress = read(live / 'progress.json')
    tokenizer = Tokenizer.from_file(str(TOKENIZER))

    def no_network(*args, **kwargs):
        raise AssertionError('This checker must never make network requests')

    client = DeepSeekClient(config(), no_network, transport=no_network,
                            token_counter=lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids))
    rows, sizes = [], []
    for original in progress['flows']:
        events = read(live / 'flows' / original['flow_id'] / 'EVENTS.json')
        case = read(prepared / 'cases' / (original['case_id'] + '.json'))
        flow = ComparisonFlowV2(case, original['arm'], provenance='unchanged real v1 replies under new v2 packets')
        consumed = 0
        while flow.status == 'pending':
            pending = flow.pending_requests()
            for actor, req in pending.items():
                assert req['packet']['tool_feedback'] is None or req['packet']['tool_feedback']['from_wave'] < flow.wave
                assert set(req['packet']['task']) == {'task_id', 'question'}
                payload = client.payload(req['instructions'], req['schema'], req['max_output_tokens'])
                size = client.size(payload)
                assert size <= 16384
                sizes.append(size)
                write(output / 'replay' / original['flow_id'] / 'requests' / f'{flow.wave:02d}-{actor}.json', req)
            selected = events[consumed:consumed + len(pending)]
            flow.submit({event['actor']: event['raw'] for event in selected})
            consumed += len(selected)
        assert consumed == 7
        assert flow.answer == original['final'], 'Do not rewrite old results as if generated under v2'
        old_engine = [event.get('engine_event') for event in events]
        new_engine = [event.get('engine_event') for event in flow.events]
        assert old_engine == new_engine, 'Interface feedback must not silently repair old work or bindings'
        write(output / 'replay' / original['flow_id'] / 'EVENTS.json', flow.events)
        trace = flow.final_use()
        rows.append(dict(flow_id=original['flow_id'], replies=consumed, final_unchanged=True,
                         engine_events_unchanged=True, final_use=trace))
    suite = unittest.TestSuite()
    for pattern in ('test_local_work.py', 'test_local_work_mixed.py', 'test_local_work_interface_v2.py'):
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / 'tests'), pattern=pattern))
    result = unittest.TextTestRunner(verbosity=1).run(suite)
    report = dict(kind='offline_interface_validation_not_new_model_results', model_calls=0,
                  original_replies_replayed=sum(row['replies'] for row in rows),
                  old_answers_and_optional_rejections_preserved=True,
                  tests_run=result.testsRun, tests_passed=result.wasSuccessful(),
                  tokenizer_max_input_with_margin=max(sizes), tokenizer_total_input_with_margin=sum(sizes),
                  replay_scope='Actual complete v1 replies. Models cannot react to newly exposed feedback in a replay.',
                  flows=rows)
    write(output / 'CHECK.json', report)
    if not result.wasSuccessful():
        raise SystemExit(1)
    return report


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    print(json.dumps(check(parser.parse_args().output), ensure_ascii=False))


if __name__ == '__main__':
    main()
