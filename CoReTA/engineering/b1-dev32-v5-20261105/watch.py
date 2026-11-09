"""Read-only live check; returns once stage2 passes and stage8 starts generating."""
import json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];OUT=ROOT/'runs/b1-dev32-20261105-v5'
def read(p):
    try:return json.loads(p.read_text())
    except (FileNotFoundError,json.JSONDecodeError):return None
while True:
    status=read(OUT/'STATUS.json') or {};phase=status.get('stage',2)
    folder=OUT/f'stage{phase}';rows=[]
    if (folder/'responses.jsonl').exists():
        for line in (folder/'responses.jsonl').read_text().splitlines():
            try:rows.append(json.loads(line))
            except json.JSONDecodeError:pass
    done=sum(bool((read(p) or {}).get('complete')) for p in (folder/'trials').glob('*.json'))
    result=read(OUT/'PIPELINE_RESULT.json')
    new=sum(not r.get('inherited',False) for r in rows)
    print(json.dumps(dict(status=status,stage=phase,n_complete=done,n_recorded_requests=len(rows),new_stage_requests=new,result=result)),flush=True)
    if result or (phase>=8 and new>=1):break
    time.sleep(40)
