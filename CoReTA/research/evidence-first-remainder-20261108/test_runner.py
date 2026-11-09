"""Real execution state machine with explicit fake model, never scientific data."""
import contextlib, importlib.util, io, json, re, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def execute(case):
    spec=importlib.util.spec_from_file_location('ef_fixture_'+case,HERE/'experiment.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory(prefix='ef-fixture-') as directory:
        original_tasks=m.load(HERE/'tasks.json')[:2]
        m.ROOT=Path(directory);m.HERE=m.ROOT/'research/fixture';m.HERE.mkdir(parents=True)
        cfg=m.load(HERE/'config.json');cfg.update(fixture=True,run_dir='run')
        m.write(m.HERE/'config.json',cfg);m.write(m.HERE/'tasks.json',original_tasks)
        m.write(m.HERE/'labels.json',{str(t['id']):{'correct':'option_1'} for t in original_tasks})
        m.freeze=lambda:{'fixture':'not_generation_evidence'}
        m.write(m.HERE/'FREEZE.json',m.freeze());m.write(m.HERE/'PREFLIGHT.json',{'result':'PASS'})
        (m.HERE/'EXPERIMENT_REVIEW.md').write_text('RUN_ALLOWED explicit fake fixture')
        class Fake:
            def __init__(self,cfg):self.n=0
            def respond(self,payload,cap,seed):
                self.n+=1
                if case=='system_failure' and self.n==3:raise RuntimeError('injected_failure')
                text='Reason based on evidence.\nANSWER: option_1'
                if 'Output only their IDs' in payload['user']:
                    text=','.join(dict.fromkeys(re.findall(r'\[(H\d{2})\]',payload['user']))) or 'NONE'
                    if case in ['invalid_reference','two_independent_failures'] and self.n==13:text='H99'
                if 'Output ONLY one option ID' in payload['user']:text='option_1'
                if case=='ambiguous_final' and 'Output ONLY one option ID' in payload['user']:text='option_1 or option_2'
                limited=((case=='single_branch_failure' and self.n==17) or (case=='two_independent_failures' and self.n==14)
                         or (case=='common_initial_failure' and self.n==1)
                         or (case=='two_common_failures' and self.n in [1,2]))
                return {'text':text,'status':'OUTPUT_LIMIT' if limited else 'OK','output_ids':[1,2],
                        'input_tokens':50,'output_tokens':2,'elapsed_seconds':0.,'adapter_enabled':False,'ended_with_eos':not limited}
        try:m.run(backend_factory=Fake)
        except SystemExit:pass
        out=m.ROOT/'run';status=m.load(out/'STATUS.json')
        responses=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines()]
        attempts=[json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines()]
        assert len(responses)==status['calls']
        if case=='normal':
            assert status['status']=='COMPLETED' and status['calls']==192 and status['complete_arms']==8
            # Finals do not expose other finals; E/F start with exactly the same fact bodies.
            finals=[r for r in responses if r['task_id']==original_tasks[0]['id'] and r['arm']=='E_facts' and r['stage']=='final']
            assert len(finals)==4
            for r in finals:assert 'Submit your final answer privately' in r['payload']['user']
            task=original_tasks[0];selected={a:m.refs(','.join(m.visible(task,a)),m.visible(task,a)) for a in m.ACTORS}
            initial={a:'INITIAL_'+a for a in m.ACTORS}
            ef=m.public_facts(task,selected,initial,False);ff=m.public_facts(task,selected,initial,True)
            assert [s for _,s in ef]==[s.split('\n\nInitial individual opinion:')[0] for _,s in ff]
        elif case=='single_branch_failure':assert status['status']=='COMPLETED' and status['calls']==173
        elif case=='invalid_reference':assert status['status']=='COMPLETED' and status['calls']==149
        elif case=='two_independent_failures':assert status['status']=='FAILED' and status['calls']==34
        elif case=='system_failure':assert status['status']=='FAILED' and len(responses)==2 and len(attempts)==3
        elif case=='common_initial_failure':
            assert status['status']=='COMPLETED' and status['calls']==97 and status['complete_arms']==4
            assert sum(not s['complete'] for s in m.load(out/'scores.json'))==4
        elif case=='two_common_failures':assert status['status']=='FAILED' and status['calls']==2
        else:
            assert status['status']=='COMPLETED' and status['calls']==192
            assert all(s['final_vote'] is None for s in m.load(out/'scores.json'))
        return {'case':case,'pass':True,'attempts':len(attempts),'responses':len(responses),'state':status['status']}

if __name__=='__main__':
    with contextlib.redirect_stdout(io.StringIO()):
        results=[execute(c) for c in ['normal','single_branch_failure','invalid_reference','two_independent_failures','system_failure','ambiguous_final','common_initial_failure','two_common_failures']]
    (HERE/'RUNNER_TESTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results))
