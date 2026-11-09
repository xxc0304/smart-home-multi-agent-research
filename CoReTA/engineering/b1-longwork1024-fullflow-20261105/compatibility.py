"""Read-only old V2/V4/V5 trace replay and official-score recomputation."""
import hashlib,json,os,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];os.chdir(ROOT);sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import load_json,development_data
from b1_controls import replay,summarize
from b0_answers import write_json
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
cases=(('runs/b1-dev32-final-20261104-v2',32),('runs/b1-dev32-20261105-v5/stage32',32),('runs/b1-batch2-fullflow-20261105-v1/serial',8),('runs/b1-batch2-fullflow-20261105-v1/batch2',8))
results=[];all_before={}
for name,n in cases:
    folder=ROOT/name;paths=list((folder/'trials').glob('*.json'))+[folder/'scores.json']
    all_before.update({p:sha(p) for p in paths});traces=[load_json(p) for p in sorted(paths[:-1])]
    assert all(replay(t).export()==t for t in traces)
    tasks,groups,targets=development_data(n,targets=True);saved=load_json(folder/'scores.json')
    result=summarize(traces,targets,[t['id'] for t in tasks],groups)
    if name.endswith(('/serial','/batch2')):result.update(primary_enabled=False,scope='TECHNICAL_FULL_HISTORY_D8_NOT_INDEPENDENT_CONFIRMATION')
    assert result==saved,'old_score_changed:'+name
    results.append(dict(folder=name,n_traces=len(traces),complete=saved['n_complete'],score_exact_match=True))
extra=[]
for name in ('runs/b1-concise-tech6-20261105-v1','runs/b1-concise-readable-tech6-20261105-v1'):
    for p in sorted((ROOT/name/'trials').glob('*.json')):
        all_before[p]=sha(p);t=load_json(p);assert replay(t).export()==t;extra.append(str(p.relative_to(ROOT)))
assert extra,'missing_real_V4_V5_technical_traces'
assert all(sha(p)==h for p,h in all_before.items()),'old_artifact_mutated'
out=dict(verdict='PASS',reviewer='assistant',independence='none/provisional',old_score_cases=results,extra_real_V4_V5_traces=len(extra),all_original_files_unchanged=True,new_model_generations=0,new_C_H_reads=False,scope='BACKWARD_COMPATIBILITY_NOT_MODEL_QUALITY')
write_json(Path(__file__).parent/'COMPATIBILITY.json',out);print(json.dumps(out),flush=True)
