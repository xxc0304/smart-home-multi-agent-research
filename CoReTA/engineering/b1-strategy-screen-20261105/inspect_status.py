"""Read current states and archive a completed prior run, no model calls."""
import json,tarfile
from datetime import datetime,timezone
from pathlib import Path
root=Path(__file__).resolve().parents[2]
load=lambda p:json.loads(p.read_text())
snapshot=dict(checked_utc=datetime.now(timezone.utc).isoformat())
for label,name in (('prior','b1-parallel-fullflow-20261105-v1'),('screen','b1-strategy-screen-20261105-v2')):
    run=root/'runs'/name;snapshot[label]=dict(status=load(run/'STATUS.json'))
    if (run/'RESULTS.json').exists():
        r=load(run/'RESULTS.json')
        snapshot[label]['result']={k:r[k] for k in ('status','error','elapsed_seconds','n_generated','n_attempted_requests','timings','counts','engine_time_ratio','aggregate','cross_engine_same_text','cross_engine_same_tokens','cross_engine_compared') if k in r}
        if label=='prior':
            snapshot[label]['scores']={e:dict(initial=s['initial_baseline'],arms={a:{k:v[k] for k in ('expected_em','actual_em','expert_em')} for a,v in s['arms'].items()}) for e,s in r['scores'].items()}
            target=root/'runs'/f'{name}-evidence.tar.gz'
            with tarfile.open(target,'w:gz') as tar:tar.add(run,arcname=name)
            snapshot[label]['evidence_archive']=str(target)
(Path(__file__).parent/'LATEST_STATUS.json').write_text(json.dumps(snapshot,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(snapshot,ensure_ascii=False),flush=True)
