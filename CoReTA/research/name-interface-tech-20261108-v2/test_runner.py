"""Bounded technical-gate state machine and full-name field interface tests."""
import contextlib, importlib.util, io, json, re, tempfile
from pathlib import Path
HERE=Path(__file__).resolve().parent

def module(name):
    spec=importlib.util.spec_from_file_location(name,HERE/'experiment.py')
    m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);return m

def parser_tests():
    m=module('names_parser');t={'options':{'Mr. X':'Mr. X',"Mr. X's son":"Mr. X's son",'Mrs. Y':'Mrs. Y'}}
    assert m.answer("Reason mentions Mr. X.\nANSWER: Mr. X's son",t)=="Mr. X's son"
    assert m.answer("ANSWER: Mr. X\nANSWER: Mr. X's son",t) is None
    assert m.answer("ANSWER: Mr. X or Mr. X's son",t) is None
    assert m.answer("**ANSWER:** `Mr. X’s son`",t)=="Mr. X's son"
    assert m.answer('mr.   x.',t)=='Mr. X'
    assert m.answer('Mr. X is guilty',t) is None
    assert m.answer("Reason discusses Mrs. Y.\nMr. X's son",t)=="Mr. X's son"
    assert m.answer("Reason\nMr. X or Mr. X's son",t) is None
    assert m.answer("ANSWER: Unknown\nMr. X",t) is None
    assert m.answer('ANSWER: option_1',t) is None
    root=HERE.parents[1];tasks=m.load(root/'research/evidence-first-dev-20261108/tasks.json')
    old_tasks={t['id']:t for t in tasks};proof=[]
    for run in ['evidence-first-dev-20261108-v1','evidence-first-remainder-20261108-v1']:
        rows=[json.loads(s) for s in (root/'runs'/run/'responses.jsonl').read_text().splitlines()]
        for r in rows:
            if r['stage']=='initial' and r['status']=='OK' and r['answer'] is None:
                fields=m.answer_fields(r['text']);assert len(fields)==1
                name=old_tasks[r['task_id']]['options'][fields[0]]
                derived=re.sub(r'(?m)^ANSWER:.*$', 'ANSWER: '+name,r['text'])
                projected={'options':{s:s for s in old_tasks[r['task_id']]['options'].values()}}
                assert m.answer(derived,projected)==name
                proof.append({'task_id':r['task_id'],'actor':r['actor'],'original_answer_field':fields[0],
                    'derived_name':name,'kind':'actual field extraction plus explicit derived name fixture, not new generated output'})
    assert len(proof)==3
    m.write(HERE/'PARSER_REPLAY.json',{'pass':True,'three_real_field_cases':proof,'prefix_collision_test':True,'unknown_and_multiple_rejected':True})

def execute(case):
    m=module('names_fixture_'+case)
    original_tasks=m.load(HERE/'tasks.json')[:2]
    with tempfile.TemporaryDirectory(prefix='names-tech-') as directory:
        m.ROOT=Path(directory);m.HERE=m.ROOT/'research/fixture';m.HERE.mkdir(parents=True)
        cfg=m.load(HERE/'config.json');cfg.update(fixture=True,run_dir='run',flow_task_ids=[t['id'] for t in original_tasks])
        cfg.pop('initial_cache',None);cfg.pop('initial_cache_sha256',None)
        m.write(m.HERE/'config.json',cfg);m.write(m.HERE/'tasks.json',original_tasks)
        m.write(m.HERE/'labels.json',{str(t['id']):{'correct':next(iter(t['options']))} for t in original_tasks})
        m.freeze=lambda:{'fixture':'not_real_generation'}
        m.write(m.HERE/'FREEZE.json',m.freeze());m.write(m.HERE/'PREFLIGHT.json',{'result':'PASS'})
        (m.HERE/'EXPERIMENT_REVIEW.md').write_text('RUN_ALLOWED explicit fake fixture')
        class Fake:
            def __init__(self,cfg):self.n=0
            def respond(self,payload,cap,seed):
                self.n+=1
                if case=='system_failure' and self.n==3:raise RuntimeError('injected_failure')
                names=re.search(r'ALLOWED CHOICES.*?:\n(.*?)\n\nYOUR ORIGINAL',payload['user'],re.S).group(1).splitlines()
                name=names[0][2:];text='Reason mentioning alternatives as appropriate.\nANSWER: '+name
                if 'Output only their IDs' in payload['user']:
                    text=','.join(dict.fromkeys(re.findall(r'\[(H\d{2})\]',payload['user']))) or 'NONE'
                    if case in ['invalid_reference','two_independent_failures'] and self.n==17:text='H99'
                if 'Output ONLY one exact full choice name' in payload['user']:
                    text=name
                    if case=='ambiguous_final':text=name+' or '+names[1][2:]
                if case=='bad_initial_name' and self.n==1:text='ANSWER: Unknown person'
                limited=((case=='single_branch_failure' and self.n==21) or
                         (case=='two_independent_failures' and self.n==18) or
                         (case=='probe_length_failure' and self.n==1))
                return {'text':text,'status':'OUTPUT_LIMIT' if limited else 'OK','output_ids':[1,2],
                        'input_tokens':50,'output_tokens':2,'elapsed_seconds':0.,'adapter_enabled':False,'ended_with_eos':not limited}
        if case=='cached_initials':
            cached=[]
            for t in original_tasks:
                first,_=m.order(t,cfg)
                for actor in first:
                    name=next(iter(t['options']))
                    cached.append({'call':len(cached),'task_id':t['id'],'actor':actor,'stage':'initial','arm':'COMMON','round':0,
                        'generation_seed':(cfg['seed']+t['id']*100000+m.ACTORS.index(actor))%(2**32),
                        'cap':cfg['initial_tokens'],'payload':m.packet(t,actor,'initial','COMMON'),
                        'text':'Reason with no tag.\n'+name,'status':'OK','output_ids':[1,2],'input_tokens':50,
                        'output_tokens':2,'elapsed_seconds':0.,'ended_with_eos':True,'adapter_enabled':False,'answer':None})
            cache_path=m.ROOT/'cache.jsonl'
            for r in cached:m.append(cache_path,r)
            cfg.update(initial_cache='cache.jsonl',initial_cache_sha256=m.sha(cache_path));m.write(m.HERE/'config.json',cfg)
        try:m.run(backend_factory=Fake)
        except SystemExit:pass
        out=m.ROOT/'run';status=m.load(out/'STATUS.json')
        responses=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines()]
        attempts=[json.loads(s) for s in (out/'attempts.jsonl').read_text().splitlines()]
        assert len(responses)==status['calls']
        if case in ['normal','cached_initials']:
            assert status['status']=='COMPLETED' and status['calls']==192 and status['complete_arms']==8
            assert len([r for r in responses if r['stage']=='initial'])==8
            assert m.load(out/'INITIAL_PROBE.json')['gate']=='PASS'
            if case=='cached_initials':assert status['inherited_records']==8 and status['new_generation_calls']==184
        elif case=='single_branch_failure':assert status['status']=='COMPLETED' and status['calls']==173
        elif case=='invalid_reference':assert status['status']=='COMPLETED' and status['calls']==149
        elif case=='two_independent_failures':assert status['status']=='FAILED' and status['calls']==38
        elif case=='system_failure':assert status['status']=='FAILED' and len(responses)==2 and len(attempts)==3
        elif case=='probe_length_failure':
            assert status['status']=='FAILED' and status['calls']==5
            assert not any(r['stage']!='initial' for r in responses)
        elif case=='bad_initial_name':
            assert status['status']=='FAILED' and status['calls']==8
            assert not any(r['stage']!='initial' for r in responses)
        else:
            assert status['status']=='COMPLETED' and status['calls']==192
            assert all(s['final_vote'] is None for s in m.load(out/'scores.json'))
        return {'case':case,'pass':True,'attempts':len(attempts),'responses':len(responses),'state':status['status']}

if __name__=='__main__':
    parser_tests()
    with contextlib.redirect_stdout(io.StringIO()):
        results=[execute(c) for c in ['normal','single_branch_failure','invalid_reference','two_independent_failures','system_failure','ambiguous_final','probe_length_failure','bad_initial_name','cached_initials']]
    (HERE/'RUNNER_TESTS.json').write_text(json.dumps(results,indent=2)+'\n',encoding='utf-8');print(json.dumps(results))
