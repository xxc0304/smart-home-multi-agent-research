"""Manually scripted work on original task data. NOT an autonomous model run."""
import json
from coreta.local_work.engine import WorkSession
from coreta.local_work.prompts import request, final_request


def metadata(subject, period='2019-12-31', unit='USD_million'):
    return dict(subject=subject, unit=unit, period=period)


def work(subject, basis, value=None, expression=None, inputs=None, conditions=None,
         replaces=None, expected_revision=None):
    return dict(replaces=replaces, expected_revision=expected_revision, target='original question',
                metadata=metadata(subject), value=value, expression=expression, inputs=inputs or [],
                basis=basis, conditions=conditions or [])


def response(message='Scripted engineering reply, not model output', work=None, bindings=None):
    return json.dumps(dict(message=message, work=work or [], bindings=bindings or []))


def binding(work_id, input, result_id, revision=1):
    return dict(work_id=work_id, input=input, result_id=result_id, expected_revision=revision)


def trace(task):
    if task['task_id'] != '0aa035e4-f009-4067-9904-b7d249900f1f':
        raise ValueError('scripted engineering trace only applies to the declared original task')
    originals = {s['id']: s['content'] for s in task['sources']}
    if '$ 1,344.1' not in originals['T1'] or '$1,137.4 million' not in originals['P4']:
        raise ValueError('original source changed; scripted fixture must be reviewed')
    s = WorkSession(task)
    requests, snapshots = [], []
    # All requests in a wave are prepared before any reply is processed.
    initial = {a: request(s, a, 0) for a in task['members']}
    requests.extend(initial.values())
    total = work('total_available_credit', ['T1'], value=1344.1)
    committed = work('committed_credit', ['P4'], value=1137.4)
    difference = work('uncommitted_credit', ['TASK', 'P4'], expression='total - committed',
                      inputs=[dict(name='total', metadata=metadata('total_available_credit')),
                              dict(name='committed', metadata=metadata('committed_credit'))])
    # A2 can finish the local operation definition without access to the table.
    s.apply('A2', response(work=[committed, difference]), initial['A2']['packet'])
    snapshots.append(dict(point='A2_operation_waits', results=s.results.copy()))
    s.apply('A1', response(work=[total]), initial['A1']['packet'])
    continuation = {a: request(s, a, 1) for a in task['members']}
    requests.extend(continuation.values())
    s.apply('A1', response(), continuation['A1']['packet'])
    s.apply('A2', response(bindings=[binding('W2', 'total', 'W3'), binding('W2', 'committed', 'W1')]),
            continuation['A2']['packet'])
    snapshots.append(dict(point='A2_binds_actual_inputs', results=s.results.copy()))
    final = final_request(s, 'A1')
    requests.append(final)
    delivered = s.deliver(json.dumps(dict(answer=None, result_id='W2', scale='million',
                                         reasoning='Scripted total minus committed; engineering trace only.')),
                          final['packet'])
    assert s.results['W2']['value'] == 206.7
    assert delivered['delivered']['answer'] == 206.7
    return dict(artifact_type='scripted_engineering_trace_not_model_result', task_id=task['task_id'],
                scripted_operations=True, autonomous_generations=0, model_calls=0,
                requests=requests, snapshots=snapshots, events=s.events, final=delivered)
