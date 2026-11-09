"""Production state machine, cache reuse, and independent dependency fault tests."""
import contextlib,importlib.util,io,json,re,tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def execute(case):
    spec=importlib.util.spec_from_file_location('dev_fixture_'+case,HERE/'experiment.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
    originals=m.load(HERE/'tasks.json')[:2]
    with tempfile.TemporaryDirectory(prefix='dev11-fixture-') as d:
        m.ROOT=Path(d);m.HERE=m.ROOT/'research/fixture';m.HERE.mkdir(parents=True)
        cfg=m.load(HERE/'config.json');cfg.update(fixture=True,run_dir='run',flow_task_ids=[t['id'] for t in originals])
        cfg.pop('initial_cache',None);cfg.pop('initial_cache_sha256',None)
        m.write(m.HERE/'config.json',cfg);m.write(m.HERE/'tasks.json',originals)
        m.write(m.HERE/'labels.json',{str(t['id']):{'correct':next(iter(t['options']))} for t in originals})
        m.freeze=lambda:{'fixture':'not_real_model_evidence'}
        m.write(m.HERE/'FREEZE.json',m.freeze());m.write(m.HERE/'PREFLIGHT.json',{'result':'PASS'})
        (m.HERE/'EXPERIMENT_REVIEW.md').write_text('RUN_ALLOWED fixture only')
        class Fake:
            def __init__(self,cfg):self.n=0
            def respond(self,payload,cap,seed):
                self.n+=1
                if case=='system_failure' and self.n==3:raise RuntimeError('injected_failure')
                names=re.search(r'ALLOWED CHOICES.*?:\n(.*?)\n\nYOUR ORIGINAL',payload['user'],re.S).group(1).splitlines()
                name=names[0][2:];text='Reason.\nANSWER: '+name
                if 'Output only their IDs' in payload['user']:
                    text=','.join(dict.fromkeys(re.findall(r'\[(H\d{2})\]',payload['user']))) or 'NONE'
                    if case in ['invalid_reference','two_independent_failures'] and self.n==13:text='H99'
                if 'Output ONLY one exact full choice name' in payload['user']:
                    text=name if case!='ambiguous_final' else name+' or '+names[1][2:]
                limited=((case=='single_branch_failure' and self.n==17) or
                         (case=='two_independent_failures' and self.n==14) or
                         (case=='common_failure' and self.n==1) or
                         (case=='two_common_failures' and self.n in [1,2]))
                return {'text':text,'status':'OUTPUT_LIMIT' if limited else 'OK','output_ids':[1,2],
                        'input_tokens':50,'output_tokens':2,'elapsed_seconds':0.,'adapter_enabled':False,'ended_with_eos':not limited}
        try:m.run(backend_factory=Fake)
        except SystemExit:pass
        out=m.ROOT/'run';status=m.load(out/'STATUS.json')
        rows=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines()]
        attempts=[json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines()]
        assert len(rows)==status['calls']
        if case in ['normal','complete_cache','initial_cache','mismatched_cache']:
            assert status['status']=='COMPLETED' and status['calls']==192 and status['complete_arms']==8
            if case!='normal':
                cached=[r for r in rows if case!='initial_cache' or r['stage']=='initial']
                if case=='mismatched_cache':cached[0]=dict(cached[0],payload={'system':'different','user':'bad'})
                cache_file=m.ROOT/'cache.jsonl'
                for r in cached:m.append(cache_file,r)
                cfg.update(run_dir='reuse_run',initial_cache='cache.jsonl',initial_cache_sha256=m.sha(cache_file))
                m.write(m.HERE/'config.json',cfg)
                class NoCall(Fake):
                    def respond(self,*args):raise AssertionError('cache_fallback_must_not_generate')
                try:m.run(backend_factory=Fake if case=='initial_cache' else NoCall)
                except SystemExit:pass
                status=m.load(m.ROOT/'reuse_run/STATUS.json')
                if case=='mismatched_cache':assert status['status']=='FAILED' and status['calls']==0
                elif case=='complete_cache':assert status['status']=='COMPLETED' and status['new_generation_calls']==0 and status['inherited_records']==192
                else:assert status['status']=='COMPLETED' and status['new_generation_calls']==184 and status['inherited_records']==8
        elif case=='single_branch_failure':assert status['status']=='COMPLETED' and status['calls']==173
        elif case=='invalid_reference':assert status['status']=='COMPLETED' and status['calls']==149
        elif case=='two_independent_failures':assert status['status']=='FAILED' and status['calls']==34
        elif case=='system_failure':assert status['status']=='FAILED' and len(rows)==2 and len(attempts)==3
        elif case=='common_failure':assert status['status']=='COMPLETED' and status['calls']==97
        elif case=='two_common_failures':assert status['status']=='FAILED' and status['calls']==2
        else:
            assert status['status']=='COMPLETED' and status['calls']==192
            assert all(s['final_vote'] is None for s in m.load(out/'scores.json'))
        return {'case':case,'pass':True,'state':status['status'],'logical_calls':status['calls'],
                'new_calls':status['new_generation_calls'],'inherited':status['inherited_records']}

if __name__=='__main__':
    with contextlib.redirect_stdout(io.StringIO()):
        cases=['normal','complete_cache','initial_cache','mismatched_cache','single_branch_failure','invalid_reference',
               'two_independent_failures','system_failure','ambiguous_final','common_failure','two_common_failures']
        results=[execute(c) for c in cases]
    (HERE/'RUNNER_TESTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');print(json.dumps(results))
