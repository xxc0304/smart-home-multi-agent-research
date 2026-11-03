"""Scripted engineering responses on a previously inspected original-source case."""
import json
from coreta.local_work.comparison import ComparisonFlow
from local_work_offline_trace import work, metadata, binding


def smoke_case(task, arm):
    case = dict(case_id='engineering-credit-not-evaluation', group='engineering', final_member='A1', task=task)
    flow = ComparisonFlow(case, arm, provenance='scripted_engineering_fixture_not_model_output')
    while flow.status == 'pending':
        pending = flow.pending_requests()
        replies = {}
        for actor, req in pending.items():
            reply = dict(message='Manually scripted engineering response, not model output')
            if req['final']:
                reply = dict(answer=None, result_id='W3' if arm == 'local_work' else 'C1', scale='million',
                             reasoning='Manually scripted delivery; not an autonomous team result')
            elif arm == 'local_work':
                if flow.wave == 0 and actor == 'A1':
                    reply['work'] = [work('total_available_credit', ['T1'], value=1344.1)]
                elif flow.wave == 0 and actor == 'A2':
                    reply['work'] = [work('committed_credit', ['P4'], value=1137.4),
                        work('uncommitted_credit', ['TASK'], expression='total - committed', inputs=[
                            dict(name='total', metadata=metadata('total_available_credit')),
                            dict(name='committed', metadata=metadata('committed_credit'))])]
                elif flow.wave == 1 and actor == 'A2':
                    reply['bindings'] = [binding('W3', 'total', 'W1'), binding('W3', 'committed', 'W2')]
            else:
                if flow.wave == 0:
                    reply['source_ids'] = ['T1'] if actor == 'A1' else ['P4']
                if (arm == 'single' and flow.wave == 0) or (arm == 'ordinary' and flow.wave == 1 and actor == 'A1'):
                    reply['calculations'] = [dict(expression='total - committed', values=dict(total=1344.1, committed=1137.4))]
            replies[actor] = json.dumps(reply)
        flow.submit(replies)
    assert flow.status == 'completed'
    assert flow.answer['delivered']['answer'] == 206.7
    return dict(artifact_type='scripted_engineering_only_not_model_results',
                summary=flow.summary(), requests=flow.requests, events=flow.events)
