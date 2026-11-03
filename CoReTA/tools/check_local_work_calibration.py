"""Local-only transport fixtures, preflight and release preparation. No model calls."""
import argparse
import copy
import json
import http.client
import tempfile
import urllib.error
from unittest.mock import patch
from pathlib import Path

from tokenizers import Tokenizer
from coreta.local_work.data import read, write
from coreta.local_work.comparison import ComparisonFlow
from coreta.model_client import DeepSeekClient
from coreta.handoff.contracts import HandoffContracts
from coreta.local_work.engine import obj, TEXT
import run_local_work_calibration as runner
from replay_local_work_history import replay


class FixtureTransport:
    """Handwritten engineering results, not agent-produced local work."""
    def __init__(self, mode='valid', history=None):
        self.calls = 0
        self.mode = mode
        self.history = history

    def __call__(self, payload, timeout):
        self.calls += 1
        if self.mode == 'transport_error' and self.calls == 2:
            raise urllib.error.URLError('engineering transport fixture')
        packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1])
        final = 'reasoning' in payload['text']['format']['schema']['properties']
        actor, wave = packet['member'], packet['wave']
        if final:
            ready = [key for key, value in packet['results'].items() if value['status'] == 'ready']
            raw = json.dumps(dict(answer=None if ready else 0, scale='', reasoning='Engineering fixture, not semantic evidence',
                                  result_id=ready[-1] if ready else None))
        else:
            message = self.history or 'Engineering fixture only; not a model-generated response'
            answer = dict(message=message)
            local = 'Begin local work' in payload['instructions'] or 'Supply an input, continue your local work' in payload['instructions']
            if local:
                meta = dict(subject='fixture_quantity', unit='unit', period='fixture_period')
                base = dict(replaces=None, expected_revision=None, target='engineering flow', metadata=meta,
                            value=10, expression=None, inputs=[], basis=['TASK'], conditions=[])
                if wave == 0 and actor == 'A1':
                    answer['work'] = [base]
                elif wave == 0 and actor == 'A2':
                    operation = copy.deepcopy(base)
                    operation.update(value=None, expression='x + 1', inputs=[dict(name='x', metadata=meta)])
                    answer['work'] = [operation]
                elif wave == 1 and actor == 'A2':
                    answer['bindings'] = [dict(work_id='W2', expected_revision=1, input='x', result_id='W1')]
            else:
                answer['source_ids'] = [s['id'] for s in packet['sources']]
                if wave == 0:
                    answer['calculations'] = [dict(expression='x+1', values=dict(x=10))]
            raw = json.dumps(answer)
        if self.mode == 'one_bad_core' and self.calls == 1:
            raw = '{"message":'
        if self.mode == 'two_bad_cores' and self.calls in (1, 2):
            raw = '{"message":'
        result = dict(status='completed', output=[dict(type='message', content=[dict(type='output_text', text=raw)])],
                      usage=dict(input_tokens=100, output_tokens=100))
        if self.mode == 'missing_usage' and self.calls == 2:
            del result['usage']
        if self.mode == 'over_output' and self.calls == 2:
            result['usage']['output_tokens'] = payload['max_output_tokens'] + 1
        if self.mode == 'over_input' and self.calls == 2:
            result['usage']['input_tokens'] = runner.LIMITS['per_input'] + 1
        if self.mode == 'incomplete_envelope' and self.calls == 1:
            result['status'] = 'incomplete'
        return result


def install_local_gate(prepared):
    """Fixture-only gate in scratch input; final release gate written after checks."""
    sha = runner.digest(prepared / 'manifest.json')
    write(prepared / 'PREFLIGHT.json', dict(status='PASS', manifest_sha256=sha, scope='local_fixture_only'))
    write(prepared / 'EXPERIMENT_REVIEW.json', dict(manifest_sha256=sha, science='PASS', readiness='PASS',
          scope='local_fixture_only'))


def checks(output):
    output = Path(output)
    if output.exists():
        raise ValueError('fresh check directory required; previous records retained')
    output.mkdir(parents=True)
    scratch = output / 'fixture_prepared'
    runner.freeze(scratch)
    runner.verify(scratch, require_preflight=False)
    install_local_gate(scratch)
    records = []
    for mode in ('valid', 'one_bad_core', 'two_bad_cores', 'transport_error', 'missing_usage', 'over_output', 'over_input', 'incomplete_envelope'):
        transport = FixtureTransport(mode)
        state = runner.run(scratch, output / mode, local_fixture=True, transport=transport)
        if mode == 'valid':
            assert state['status'] == 'completed' and state['attempts'] == 42
            assert all(r['status'] == 'completed' and r['network_calls'] == 0 for r in state['flows'])
            local = [r for r in state['flows'] if r['arm'] == 'local_work']
            assert all(r['final']['delivered']['answer'] == 11 for r in local)
        elif mode in ('one_bad_core', 'incomplete_envelope'):
            assert state['status'] == 'completed_with_incomplete_flows' and state['attempts'] == 37
            assert state['flows'][0]['status'] == 'technical_incomplete'
            assert state['flows'][1]['status'] == 'completed'
        else:
            assert state['status'] == 'stopped' and state['attempts'] == 2
            assert all(r['status'] == 'not_run' for r in state['flows'][1:])
        if mode in ('transport_error', 'missing_usage'):
            assert state['unknown_usage']
        if mode == 'transport_error':
            assert len(read(output / mode / 'flows/main-01-ordinary/EVENTS.json')) == 2
            assert (output / mode / 'flows/main-01-ordinary/requests/00-A2.json').exists()
        records.append(dict(mode=mode, status=state['status'], attempts=state['attempts'],
                            unknown_usage=state['unknown_usage'], network_calls=0))
    # A fixture-only gate must never pass live verification, even with authorization.
    try:
        runner.verify(scratch)
    except ValueError as exc:
        assert 'scope' in str(exc)
    else:
        raise AssertionError('fixture-only scope accepted for live verification')
    sha = runner.digest(scratch / 'manifest.json')
    write(scratch / 'PREFLIGHT.json', dict(status='PASS', manifest_sha256=sha, scope='bounded_protocol_calibration'))
    write(scratch / 'EXPERIMENT_REVIEW.json', dict(manifest_sha256=sha, science='PASS', readiness='PASS',
          scope='bounded_protocol_calibration'))
    # No live authorization: must fail before attempt/output creation.
    try:
        try:
            runner.run(scratch, output / 'unauthorized')
        except ValueError as exc:
            assert 'authorization' in str(exc)
        else:
            raise AssertionError('live path accepted missing authorization')
    finally:
        # Even a failed assertion cannot leave a checker-generated live gate.
        install_local_gate(scratch)
    assert not (output / 'unauthorized').exists()
    # Invalid outer HTTP JSON must leave the bytes available for forensic review.
    class MockHTTP:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def read(self):
            return b'{"status":"completed","output":['
    with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'local_mock_value_not_a_real_credential'}), \
            patch('urllib.request.urlopen', return_value=MockHTTP()):
        try:
            runner.official_transport({}, 1, output / 'invalid_http', 1)
        except json.JSONDecodeError:
            pass
        else:
            raise AssertionError('invalid HTTP JSON accepted')
    assert (output / 'invalid_http/http_bodies/001.bytes').read_bytes() == MockHTTP().read()
    class PartialHTTP(MockHTTP):
        def read(self):
            raise http.client.IncompleteRead(b'partial received bytes', 99)
    with patch.dict('os.environ', {'DEEPSEEK_API_KEY': 'local_mock_value_not_a_real_credential'}), \
            patch('urllib.request.urlopen', return_value=PartialHTTP()):
        try:
            runner.official_transport({}, 1, output / 'partial_http', 1)
        except http.client.IncompleteRead:
            pass
        else:
            raise AssertionError('partial HTTP body accepted')
    assert (output / 'partial_http/http_bodies/001.bytes').read_bytes() == b'partial received bytes'
    # Bind integrity is checked independently from model format.
    case_path = scratch / 'cases/main-01.json'
    original = case_path.read_bytes()
    case_path.write_bytes(original + b' ')
    try:
        runner.verify(scratch, allow_fixture_gate=True)
    except ValueError as exc:
        assert 'changed' in str(exc)
    else:
        raise AssertionError('changed frozen source accepted')
    case_path.write_bytes(original)
    runner.verify(scratch, allow_fixture_gate=True)
    history = replay(runner.ROOT / 'runs/local-rule-confirmation-live-20261025-r1')
    write(output / 'HISTORY_REPLAY.json', history)
    assert history['all_refs_visible']
    history_raw = Path(history['rows'][1]['raw_file']).read_text(encoding='utf-8')
    state = runner.run(scratch, output / 'full_historical_carrier', local_fixture=True,
                       transport=FixtureTransport(history=history_raw))
    assert state['status'] == 'completed' and state['attempts'] == 42
    # Validate every schema and packet actually produced by the dynamic workflows.
    tokenizer = Tokenizer.from_file(str(runner.TOKENIZER))
    client = DeepSeekClient(runner.config(), lambda *args: None,
        token_counter=lambda text: len(tokenizer.encode(text, add_special_tokens=False).ids))
    sizes = []
    for path in (output / 'full_historical_carrier/actual_requests').glob('*.json'):
        req = read(path)
        from jsonschema import Draft202012Validator
        Draft202012Validator.check_schema(req['schema'])
        assert json.loads(req['instructions'].split('\nPACKET=', 1)[1]) == req['packet']
        assert set(req['packet']['task']) == {'task_id', 'question'}
        sizes.append(client.size(client.payload(req['instructions'], req['schema'], req['max_output_tokens'])))
    assert max(sizes) <= runner.LIMITS['per_input'] and sum(sizes) <= runner.LIMITS['input']
    result = dict(status='PASS', check_scope='offline orchestration/envelope/old-contract carriers only',
                  fixtures=records, full_historical_carrier_calls=42, old_contract_replays=12,
                  max_fixture_estimated_input=max(sizes), total_fixture_estimated_input=sum(sizes),
                  estimator='existing local tokenizer +256 per serialized payload',
                  no_authorization_blocks=True, fixture_gate_blocks_live=True, malformed_http_body_preserved=True,
                  partial_http_bytes_preserved=True,
                  tamper_blocks=True, natural_new_schema_generations=0,
                  model_network_calls=0, method_effectiveness=None,
                  limitations='first live natural work/format remains unqualified; fixture budget fit is not a universal upper bound')
    write(output / 'CHECKS.json', result)
    return result


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--stage', choices=('runner', 'all'), default='all')
    args = parser.parse_args()
    result = checks(args.output)
    print(json.dumps(result, ensure_ascii=False))


if __name__ == '__main__':
    main()
