"""Complete two off-diagonal cells with independently assigned sampling/order."""
import argparse,copy,hashlib,importlib.util,json,math,os,random,sys,time
from collections import Counter
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
OLD_HERE=ROOT/'research/b1-independent-first-work-20261106'
spec=importlib.util.spec_from_file_location('frozen_first_work_20261106',OLD_HERE/'experiment.py');old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
from b1_runtime import validate_runtime
from b1_multi_backend import MultiBackend
from b1_controls import vote,vote_scores
from b0_answers import answer_score,paired_interval
HERE=Path(__file__).resolve().parent;SOURCE=old.OUT;OUT=ROOT/'runs/b1-sampling-order-cross-20261107-v1'
ACTORS=('M1','M2','M3','M4');CONDITIONS=('B','B_delay');CELLS=((0,1),(1,0));OFFSETS=(0,100000000);MAX_CALLS=1200
load,sha,atomic,append,decode,length=old.load,old.sha,old.atomic,old.append,old.decode,old.length

def source_trace(e,s):return load(SOURCE/f'trials/{e["index"]:03d}-r{s}.json')

class CrossBranch(old.Branch):
    def __init__(self,e,c,s,o,condition,source_initials,order_branch):
        assert s in (0,1) and o in (0,1) and condition in CONDITIONS
        self.sampling=s;self.order_setting=o
        super().__init__(e,c,s,condition,source_initials)
        self.initial_order=copy.deepcopy(order_branch['initial_order']);self.orders=copy.deepcopy(order_branch['orders'])
        self.schedule=self.schedule[:4]+[('work','B',rn+1,a) for rn,order in enumerate(self.orders) for a in order]+[('final','B',3,a) for a in ACTORS]
        self.config.update(order_seed=c['seed']+OFFSETS[o],sampling_setting=s,order_setting=o)
        assert self.cursor==4 and len(self.schedule)==16

    def next_request(self):
        r=super().next_request()
        if r is None:return None
        self.pending['request_id']=f'{self.task["id"]}/S{self.sampling}O{self.order_setting}/{self.condition}/{self.cursor-4:02d}'
        return copy.deepcopy(self.pending)

    def export(self):
        value=super().export();value.update(protocol='B1_SAMPLING_ORDER_CROSS_V1',sampling=self.sampling,order_setting=self.order_setting)
        return value

def make_branch(e,c,s,o,cond):
    src=source_trace(e,s);order=source_trace(e,o)['branches']['B']
    return CrossBranch(e,c,s,o,cond,src['initial_records'],order)

def verify_sources(pack):
    assert len(pack['tasks'])==25 and sum(e['coverage'] for e in pack['tasks'])==24 and sum(e['mechanism'] for e in pack['tasks'])==8
    assert load(SOURCE/'RESULTS.json')['status']=='COMPLETE'
    assert load(ROOT/'research/b1-independent-first-analysis-20261107/POST_RUN_AUDIT.json')['verdict']=='PASS_RECORDS_REQUESTS_AND_SCORES'
    old.verify_freeze()
    for p,h in load(ROOT/'research/b1-independent-first-analysis-20261107/POST_RUN_AUDIT.json')['original_run_file_hashes'].items():assert sha(p)==h,('source_changed',p)
    for e in pack['tasks']:
        for s in (0,1):
            t=source_trace(e,s);assert t['status']=='COMPLETE' and t['initials']=={r['actor']:r['raw_output'] for r in t['initial_records']}
            rng=random.Random(20261102+OFFSETS[s]+e['index']*10000)
            assert t['branches']['B']['initial_order']==rng.sample(['M1','M2','M3','M4'],4)
            assert t['branches']['B']['orders']==[rng.sample(['M1','M2','M3','M4'],4) for _ in range(2)]

def evaluate(e,s,o,branches,initials,target):
    initial={a:answer_score(v,target) for a,v in initials.items()};row=dict(index=e['index'],id=e['id'],sampling=s,order_setting=o,coverage=e['coverage'],mechanism=e['mechanism'],origin='INHERITED_DIAGONAL' if s==o else 'NEW_CROSSED_CELL',initial=initial,conditions={})
    for cond in CONDITIONS:
        b=branches.get(cond)
        if not b or not b['complete']:row['conditions'][cond]=dict(complete=False);continue
        members={a:answer_score(v,target) for a,v in b['finals'].items()};voted=vote(b['finals'],20261102+OFFSETS[s]+e['index']*10000+1001)
        row['conditions'][cond]=dict(complete=True,members=members,vote=voted,**vote_scores(voted,target),expert_em=members['M1']['em'],expert_harm=int(initial['M1']['em']==1 and members['M1']['em']==0),expert_correction=int(initial['M1']['em']==0 and members['M1']['em']==1))
    row['paired_complete']=all(z['complete'] for z in row['conditions'].values())
    row['delta']=row['conditions']['B_delay']['expected_em']-row['conditions']['B']['expected_em'] if row['paired_complete'] else None
    return row

def score():
    pack=load(OUT/'INPUTS.json');targets=load(OUT/'LABELS.json')['targets'];rows=[]
    for e in pack['tasks']:
        for s in (0,1):
            src=source_trace(e,s)
            for o in (0,1):
                if s==o:branches={c:src['branches'][c] for c in CONDITIONS}
                else:
                    f=OUT/f'trials/{e["index"]:03d}-S{s}O{o}.json';branches=load(f)['branches'] if f.exists() else {}
                rows.append(evaluate(e,s,o,branches,src['initials'],targets[e['id']]))
    summaries={}
    for name,es in [('coverage',[e for e in pack['tasks'] if e['coverage']]),('mechanism',[e for e in pack['tasks'] if e['mechanism']]),('union',pack['tasks'])]:
        ids={e['id'] for e in es};subset=[r for r in rows if r['id'] in ids]
        complete_ids={i for i in ids if all(r['paired_complete'] for r in subset if r['id']==i)}
        sm=dict(expected_unique_questions=len(ids),four_cell_complete_questions=len(complete_ids),cells={},four_cell_common={},factorial_contrasts={})
        for s in (0,1):
            for o in (0,1):
                valid=[r for r in subset if r['sampling']==s and r['order_setting']==o and r['paired_complete']]
                cell=dict(n_expected=len(ids),paired_complete=len(valid),origin='INHERITED_DIAGONAL' if s==o else 'NEW_CROSSED_CELL')
                if valid:
                    cell['conditions']={c:dict(team_expected_em=sum(r['conditions'][c]['expected_em'] for r in valid)/len(valid),team_expected_f1=sum(r['conditions'][c]['expected_f1'] for r in valid)/len(valid),expert_em=sum(r['conditions'][c]['expert_em'] for r in valid)/len(valid)) for c in CONDITIONS}
                    values={r['id']:r['delta'] for r in valid};groups={i:pack['groups'][i] for i in values}
                    cell['delta']=sum(values.values())/len(values);cell['cluster_ci95']=paired_interval(values,groups,10000,20261107)
                sm['cells'][f'S{s}O{o}']=cell
                common=[r for r in valid if r['id'] in complete_ids]
                if common:sm['four_cell_common'][f'S{s}O{o}']=dict(n=len(common),B=sum(r['conditions']['B']['expected_em'] for r in common)/len(common),B_delay=sum(r['conditions']['B_delay']['expected_em'] for r in common)/len(common),delta=sum(r['delta'] for r in common)/len(common))
        if complete_ids:
            deltas={i:{(r['sampling'],r['order_setting']):r['delta'] for r in subset if r['id']==i} for i in complete_ids}
            fn={'average_intervention_delta':lambda d:sum(d.values())/4,
                'sampling_at_O0':lambda d:d[1,0]-d[0,0],'sampling_at_O1':lambda d:d[1,1]-d[0,1],
                'order_at_S0':lambda d:d[0,1]-d[0,0],'order_at_S1':lambda d:d[1,1]-d[1,0],
                'sampling_main_on_delta':lambda d:(d[1,0]+d[1,1]-d[0,0]-d[0,1])/2,
                'order_main_on_delta':lambda d:(d[0,1]+d[1,1]-d[0,0]-d[1,0])/2,
                'interaction_on_delta':lambda d:d[1,1]-d[1,0]-d[0,1]+d[0,0]}
            for k,f in fn.items():
                values={i:f(d) for i,d in deltas.items()};groups={i:pack['groups'][i] for i in values}
                sm['factorial_contrasts'][k]=dict(difference=sum(values.values())/len(values),cluster_ci95=paired_interval(values,groups,10000,20261107),n_questions=len(values))
        summaries[name]=sm
    result=dict(scope='TWO_FIXED_SAMPLING_AND_ORDER_LEVELS_REUSED_DEVELOPMENT_NOT_VARIANCE_COMPONENT_ESTIMATE',rows=rows,summaries=summaries)
    atomic(OUT/'scores.json',result);return result

def prepare():
    from b0_training import load_tokenizer
    tests=load(HERE/'TESTS.json');assert tests['verdict']=='PASS' and tests['code_sha256']==sha(HERE/'experiment.py') and tests['tests_sha256']==sha(HERE/'test_experiment.py')
    review=(HERE/'EXPERIMENT_REVIEW.md').read_text();assert 'SCIENCE_PASS' in review and 'ENGINEERING_PENDING_PREPARE' in review
    pack=load(SOURCE/'INPUTS.json');verify_sources(pack);c=load(SOURCE/'config.json');q=validate_runtime(c);c['purpose']='DEVELOPMENT_SAMPLING_X_ORDER_CROSS_DIAGNOSTIC'
    tok=load_tokenizer(c);lengths=[];exact=0;crossed=0;logical=0;shared=0;refs=[];records=[]
    for e in pack['tasks']:
        for s in (0,1):
            src=source_trace(e,s);sourcefile=SOURCE/f'trials/{e["index"]:03d}-r{s}.json';refs.append(dict(index=e['index'],sampling=s,path=str(sourcefile),sha256=sha(sourcefile)))
            for o in (0,1):
                if s!=o:shared+=source_trace(e,o)['branches']['B']['orders'][0].index('M1')
                for cond in CONDITIONS:
                    b=make_branch(e,c,s,o,cond);bykey={(r['stage'],r['round'],r['actor']):r for r in src['branches'][cond]['records']}
                    while (r:=b.next_request()) is not None:
                        oldr=bykey[r['stage'],r['round'],r['actor']]
                        if s==o:
                            for k in ('payload','actor','arm','stage','round','seed','max_new_tokens'):assert r[k]==oldr[k]
                            exact+=1
                        else:crossed+=1;logical+=1
                        n=length(tok,c,r)+r['max_new_tokens'];assert n<=c['max_length']
                        lengths.append(dict(index=e['index'],sampling=s,order_setting=o,condition=cond,input_plus_cap=n))
                        b.submit(r['request_id'],oldr['raw_output'],status=oldr['status'],usage=oldr['usage'],source_kind=oldr['source_kind']);records.append(oldr)
                    assert b.complete
    assert exact==crossed==logical==1200 and shared==67
    long=max((r for r in records if r['stage']=='work'),key=lambda r:r['usage']['output_tokens'])['raw_output'];pressure=[]
    for e in pack['tasks']:
        for s,o in CELLS:
            for cond in CONDITIONS:
                b=make_branch(e,c,s,o,cond)
                while (r:=b.next_request()) is not None:
                    pressure.append(length(tok,c,r)+r['max_new_tokens']);b.submit(r['request_id'],long if r['stage']=='work' else 'short replay stress',source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
    assert max(pressure)<=c['max_length'],('pressure_context_overflow',max(pressure))
    OUT.mkdir(parents=True,exist_ok=False)
    atomic(OUT/'config.json',c);atomic(OUT/'INPUTS.json',pack);atomic(OUT/'LABELS.json',load(SOURCE/'LABELS.json'));atomic(OUT/'DIAGONAL_REFERENCES.json',refs);atomic(OUT/'LENGTHS.json',dict(replays=lengths,actual_long_response_pressure=max(pressure)))
    budget=dict(unique_questions=25,coverage_questions=24,mechanism_questions=8,new_crossed_cells=50,new_branches=100,inherited_diagonal_branches=100,inherited_initial_generations=200,max_calls=MAX_CALLS,expected_complete_physical_calls=logical-shared,max_output_tokens=921600,wall_clock_cutoff=None,legacy_config_wall_seconds_unused=True,generation_retry=False,execution='ALL_SINGLETON_WITH_FROZEN_SHARED_INITIALS_AND_NEW_WITHIN_CELL_UPSTREAM',reuse_policy='Only audited diagonal cells and source initial responses, no old downstream substituted into crossed cells.')
    atomic(OUT/'BUDGET.json',budget)
    pf=dict(science='PASS',engineering='PASS',exact_diagonal_response_replays=exact,crossed_actual_text_reassemblies=crossed,source_initials_exactly_reused=True,sampling_order_decoupled=True,max_replay_input_plus_cap=max(x['input_plus_cap'] for x in lengths),actual_long_response_pressure=max(pressure),context=c['max_length'],expected_new_physical_calls=1133,qualification=q['qualification'],new_model_calls=0,reviewer='assistant',independence='none/provisional')
    atomic(OUT/'PREFLIGHT.json',pf)
    files=[HERE/n for n in ('experiment.py','launch.py','test_experiment.py','run_checks.py','TESTS.json','BRIEF.md','EXPERIMENT_REVIEW.md')]
    files += [OUT/n for n in ('config.json','INPUTS.json','LABELS.json','DIAGONAL_REFERENCES.json','LENGTHS.json','BUDGET.json','PREFLIGHT.json')]
    files += [Path(p) for p in load(SOURCE/'FREEZE.json')['files']]
    files += [SOURCE/'FREEZE.json',SOURCE/'scores.json',SOURCE/'RESULTS.json',SOURCE/'INPUTS.json',SOURCE/'LABELS.json',ROOT/'research/b1-independent-first-analysis-20261107/POST_RUN_AUDIT.json']
    files += [Path(r['path']) for r in refs]
    atomic(OUT/'FREEZE.json',dict(files={str(p):sha(p) for p in dict.fromkeys(files)}));atomic(OUT/'STATUS.json',dict(status='PREPARED_NOT_LAUNCHED',calls=0,max_calls=MAX_CALLS))
    print(json.dumps(pf),flush=True)

def verify_freeze():
    for p,h in load(OUT/'FREEZE.json')['files'].items():assert sha(p)==h,('frozen_input_changed',p)

def run():
    import fcntl
    lock=(OUT/'run.lock').open('a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    verify_freeze();a=load(OUT/'APPROVAL.json');assert a['verdict']=='RUN_ALLOWED' and a['freeze_sha256']==sha(OUT/'FREEZE.json');(OUT/'STARTED').touch(exist_ok=False)
    c=load(OUT/'config.json');pack=load(OUT/'INPUTS.json');begin=time.monotonic();calls=0;done=0;error=None
    atomic(OUT/'STATUS.json',dict(status='LOADING_MODEL',calls=0,max_calls=MAX_CALLS))
    try:
        backend=MultiBackend(c)
        def generate(r):
            nonlocal calls
            n=length(backend.tokenizer,c,r)
            if n+r['max_new_tokens']>c['max_length']:
                z=dict(status='INPUT_TOO_LONG',raw_output=None,usage=dict(input_tokens=n,output_tokens=0,host_no_generation=True));append(OUT/'host_failures.jsonl',dict(request=r,response=z));return z
            assert calls<MAX_CALLS;append(OUT/'ATTEMPTS.jsonl',dict(attempt_index=calls,request=r));calls+=1
            z=backend.respond_many([r],math.inf)[0]
            if z['status']=='OK' and (not isinstance(z['raw_output'],str) or not z['raw_output'].strip()):z['status']='EMPTY_OR_NON_TEXT'
            append(OUT/'responses.jsonl',dict(request=r,response=z,source_kind='ACTUAL_LOCAL_MODEL_RESPONSE',fixture=False))
            u=z['usage'];assert u['adapter_enabled']==(r['actor']=='M1') and u['disabled_layers']==(0 if r['actor']=='M1' else 252) and u['lora_layers']==252 and u['batch_size']==1
            return z
        for pos,e in enumerate(pack['tasks']):
            cells=CELLS if pos%2==0 else CELLS[::-1]
            for s,o in cells:
                src=source_trace(e,s);item=dict(index=e['index'],id=e['id'],sampling=s,order_setting=o,source_initial_path=str(SOURCE/f'trials/{e["index"]:03d}-r{s}.json'),initial_records=src['initial_records'],initials=src['initials'],branches={},status='RUNNING');f=OUT/f'trials/{e["index"]:03d}-S{s}O{o}.json';atomic(f,item)
                bs={cond:make_branch(e,c,s,o,cond) for cond in CONDITIONS}
                while (r:=bs['B'].next_request()) is not None and not (r['stage']=='work' and r['actor']=='M1' and r['round']==1):
                    rd=bs['B_delay'].next_request();assert rd['payload']==r['payload'] and rd['seed']==r['seed'];z=generate(r)
                    for cond,request in [('B',r),('B_delay',rd)]:
                        rec=bs[cond].submit(request['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE')
                        if cond=='B_delay':rec['shared_prefix_from']=r['request_id']
                        item['branches'][cond]=bs[cond].export()
                    atomic(f,item)
                    atomic(OUT/'STATUS.json',dict(status='RUNNING',phase='SHARED_PRE_EXPERT_PREFIX',index=e['index'],sampling=s,order_setting=o,calls=calls,max_calls=MAX_CALLS,completed_crossed_cells=done,total_crossed_cells=len(pack['tasks'])*2,elapsed_seconds=time.monotonic()-begin))
                order=CONDITIONS if (pos+s+o)%2==0 else CONDITIONS[::-1]
                for cond in order:
                    b=bs[cond]
                    while (r:=b.next_request()) is not None:
                        z=generate(r);b.submit(r['request_id'],z['raw_output'],status=z['status'],usage=z['usage'],source_kind='ACTUAL_LOCAL_MODEL_RESPONSE');item['branches'][cond]=b.export();atomic(f,item)
                        atomic(OUT/'STATUS.json',dict(status='RUNNING',index=e['index'],question_number=e['index']+1,position=pos+1,total_questions=len(pack['tasks']),sampling=s,order_setting=o,condition=cond,calls=calls,max_calls=MAX_CALLS,completed_crossed_cells=done,total_crossed_cells=len(pack['tasks'])*2,elapsed_seconds=time.monotonic()-begin))
                    item['branches'][cond]=b.export();atomic(f,item)
                item['status']='COMPLETE' if all(b.complete for b in bs.values()) else 'INCOMPLETE_BRANCHES';done+=1;atomic(f,item)
                atomic(OUT/'STATUS.json',dict(status='RUNNING',calls=calls,max_calls=MAX_CALLS,completed_crossed_cells=done,total_crossed_cells=len(pack['tasks'])*2,elapsed_seconds=time.monotonic()-begin))
        state='FINISHED'
    except BaseException as exc:state='STOPPED_SYSTEM_FAULT';error=type(exc).__name__+':'+str(exc)
    scored=score();responses=[json.loads(x) for x in (OUT/'responses.jsonl').read_text().splitlines()] if (OUT/'responses.jsonl').exists() else []
    failures=[]
    for e in pack['tasks']:
        for s,o in CELLS:
            f=OUT/f'trials/{e["index"]:03d}-S{s}O{o}.json';v=load(f) if f.exists() else None
            if not v or v['status']!='COMPLETE':failures.append(dict(index=e['index'],sampling=s,order_setting=o,status=v['status'] if v else 'MISSING'))
    if state=='FINISHED':state='COMPLETE' if not failures else 'COMPLETED_WITH_INCOMPLETE_BRANCHES'
    result=dict(status=state,error=error,calls=calls,confirmed_returns=len(responses),max_calls=MAX_CALLS,completed_crossed_cells=done,total_crossed_cells=len(pack['tasks'])*2,incomplete_or_missing_cells=failures,elapsed_seconds=time.monotonic()-begin,no_wall_cutoff=True,statuses=dict(Counter(x['response']['status'] for x in responses)),output_tokens=sum(x['response']['usage'].get('output_tokens',0) for x in responses),new_training=False,scope='TWO_FIXED_LEVEL_FACTORIAL_DEVELOPMENT_DIAGNOSTIC')
    atomic(OUT/'RESULTS.json',result);atomic(OUT/'STATUS.json',result);lock.close();print(json.dumps(result),flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('command',choices=['prepare','run','score']);args=p.parse_args();{'prepare':prepare,'run':run,'score':score}[args.command]()
