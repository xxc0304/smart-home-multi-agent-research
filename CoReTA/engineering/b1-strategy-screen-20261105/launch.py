"""Wait for earlier technical batch, audit it, then start one finite screen."""
import hashlib,json,os,subprocess,sys,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,validate_runtime,development_data
from b1_controls import replay,summarize
from b0_answers import write_json
OUT=ROOT/'runs/b1-strategy-screen-20261105-v2';PRIOR=ROOT/'runs/b1-parallel-fullflow-20261105-v1'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()

def wait_and_dispatch():
    started=time.monotonic();f=load_json(OUT/'FREEZE.json')
    try:
        while not (PRIOR/'RESULTS.json').exists():
            if time.monotonic()-started>1800:raise RuntimeError('prior_wait_timeout')
            write_json(OUT/'STATUS.json',dict(status='WAITING_FOR_PRIOR',prior=str(PRIOR),wait_seconds=time.monotonic()-started));time.sleep(15)
        previous=load_json(PRIOR/'RESULTS.json')
        assert previous['status']=='COMPLETE' and previous['error'] is None
        assert previous['cross_engine_compared']==104 and all(previous['counts'][e]['n_calls']==104 and previous['counts'][e]['n_complete']==2 for e in ('serial','batch2'))
        tasks,groups,targets=development_data(2,targets=True)
        for engine in ('serial','batch2'):
            ts=[load_json(PRIOR/engine/f'trials/{i:03d}.json') for i in range(2)]
            assert all(replay(t).export()==t and t['complete'] for t in ts)
            score=summarize(ts,targets,[t['id'] for t in tasks],groups);score.update(primary_enabled=False,scope='TECHNICAL_EXECUTOR_COMPARISON_NOT_QUALITY_EQUIVALENCE')
            assert score==load_json(PRIOR/engine/'scores.json')
            rows=[json.loads(s) for s in (PRIOR/engine/'responses.jsonl').read_text().splitlines()]
            assert len(rows)==104 and all(r['record']['status']=='OK' and r['record']['usage']['finish_reason']=='EOS' and r['record']['usage']['adapter_enabled']==(r['record']['actor']=='M1') for r in rows)
            for i,t in enumerate(ts):assert [r['record'] for r in rows if r['item_index']==i]==t['records']
        assert all(sha(p)==h for p,h in f['files'].items())
        pre=load_json(OUT/'PREFLIGHT.json');assert pre['science']==pre['engineering']=='PASS' and pre['new_generations_max']==256
        validate_runtime(load_json(OUT/'config.json'))
        # Previous process may need a short moment to release its CUDA context.
        gpu=None
        for _ in range(12):
            gpu=subprocess.check_output(['nvidia-smi','--query-gpu=memory.used,utilization.gpu','--format=csv,noheader,nounits'],text=True).strip();used,util=map(int,gpu.split(','))
            if used<100 and util<5:break
            time.sleep(5)
        else:raise RuntimeError('GPU_not_idle_after_prior')
        (OUT/'DISPATCHED').touch(exist_ok=False)
        write_json(OUT/'APPROVAL.json',dict(verdict='RUN_ALLOWED',science='PASS',engineering='PASS',reviewer='assistant',independence='none/provisional',freeze_sha256=sha(OUT/'FREEZE.json'),prior_result_sha256=sha(PRIOR/'RESULTS.json'),prior_replayed_scored_and_journal_audited=True,gpu_before=gpu))
        with (OUT/'run.log').open('x') as log:
            p=subprocess.Popen(['timeout','--signal=TERM','--kill-after=30','2700',sys.executable,str(Path(__file__).with_name('screen.py')),'run'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        (OUT/'PID').write_text(str(p.pid)+'\n');write_json(OUT/'STATUS.json',dict(status='DISPATCHED_NOT_COMPLETE',pid=p.pid))
        print(json.dumps(dict(dispatched=True,pid=p.pid)),flush=True)
    except BaseException as exc:
        write_json(OUT/'STATUS.json',dict(status='BLOCKED_NO_GPU_RUN',error=type(exc).__name__+':'+str(exc)));raise

if __name__=='__main__':
    if len(sys.argv)>1 and sys.argv[1]=='wait':wait_and_dispatch()
    else:
        f=load_json(OUT/'FREEZE.json');assert all(sha(p)==h for p,h in f['files'].items())
        (OUT/'QUEUED').touch(exist_ok=False)
        with (OUT/'queue.log').open('x') as log:p=subprocess.Popen([sys.executable,str(Path(__file__)),'wait'],cwd=ROOT,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
        write_json(OUT/'QUEUE_PROCESS.json',dict(pid=p.pid,max_wait_seconds=1800));print(json.dumps(dict(queued=True,pid=p.pid,max_new_calls=256)))
