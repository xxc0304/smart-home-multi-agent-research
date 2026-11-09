"""Exercise the production state machine using explicit fake backend fixtures."""
import importlib.util, json, tempfile
from pathlib import Path

path = Path(__file__).with_name('pilot.py')

def execute(case):
    spec = importlib.util.spec_from_file_location('pilot_test_'+case, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
    with tempfile.TemporaryDirectory(prefix='sbp-fixture-') as tmp:
        m.ROOT = Path(tmp); m.HERE = m.ROOT/'research/pilot'; m.HERE.mkdir(parents=True)
        cfg = json.loads(path.with_name('config.json').read_text())
        cfg['seeds'] = [11,12]; cfg['fixture'] = True; cfg['run_dir'] = 'run'
        m.write(m.HERE/'config.json',cfg)
        m.write(m.HERE/'task.json',{'items':['Candidate '+c for c in 'ABCD'],'shared':'Fixture shared facts','private':[]})
        m.write(m.HERE/'labels.json',{'ranking':['Candidate '+c for c in 'DCAB']})
        m.freeze = lambda: {'fixture':'explicit_test_not_model_evidence'}
        m.write(m.HERE/'FREEZE.json',m.freeze()); m.write(m.HERE/'PREFLIGHT.json',{'result':'PASS'})
        (m.HERE/'EXPERIMENT_REVIEW.md').write_text('RUN_ALLOWED fixture only')
        class Fake:
            def __init__(self,config): self.n = 0
            def respond(self,p,cap,seed):
                self.n += 1
                if case == 'system_failure' and self.n == 3: raise RuntimeError('injected_backend_failure')
                limited = ((case == 'one_branch_failure' and self.n == 5) or
                           (case == 'two_branch_failure' and self.n in [5,6]))
                text = 'MY RANKING:\n1. Candidate D\n2. Candidate C\n3. Candidate A\n4. Candidate B'
                return {'text':text,'status':'OUTPUT_LIMIT' if limited else 'OK','output_ids':[1,2],
                        'input_tokens':100,'output_tokens':2,'elapsed_seconds':0.,'ended_with_eos':not limited}
        m.Backend = Fake
        try: m.run()
        except SystemExit: pass
        out = m.ROOT/'run'; status = m.load(out/'STATUS.json')
        responses = [json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines()]
        attempts = [json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines()]
        assert len(responses) == status['calls']
        if case == 'normal':
            assert status['status']=='COMPLETED' and status['calls']==224
            assert len(m.load(out/'scores.json'))==10
            # Finals all see same transcript; never another member's final.
            finals = [r for r in responses if r['seed']==11 and r['arm']=='B_hidden' and r['stage']=='final']
            assert len(finals)==4 and len({r['payload']['user'].split('Committee transcript')[1] for r in finals})==1
        elif case == 'one_branch_failure':
            assert status['status']=='COMPLETED' and status['calls']==205
            assert [s['arm'] for s in status['scores'] if not s['complete']]==['A_private']
        elif case == 'two_branch_failure':
            assert status['status']=='FAILED' and status['calls']==74
            assert not (out/'seed-12.json').exists()
        else:
            assert status['status']=='FAILED' and len(responses)==2 and len(attempts)==3
        return {'case':case,'status':status['status'],'attempts':len(attempts),'responses':len(responses),'pass':True}

if __name__ == '__main__':
    # Keep runner console noise out of the summary artifact.
    import contextlib, io
    with contextlib.redirect_stdout(io.StringIO()):
        results = [execute(c) for c in ['normal','one_branch_failure','two_branch_failure','system_failure']]
    path.with_name('RUNNER_TESTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(results))
