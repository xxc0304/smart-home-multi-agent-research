"""Read only the already-used first eight D labels for offline process audit."""
import hashlib,json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b1_runtime import development_data
tasks,groups,targets=development_data(8,targets=True)
trace_root=ROOT/'runs/b1-longwork1024-fullflow-20261105-v1'
for i,t in enumerate(tasks):
    for engine in ('serial','batch2'):
        old=json.loads((trace_root/engine/f'trials/{i:03d}.json').read_text())
        assert old['task']==t
source=ROOT/'data/external/musique-v1.0-20261030/scoring/D_development.jsonl'
output=dict(scope='ALREADY_VIEWED_D8_LABELS_NOT_NEW_C_H',source=str(source),source_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),ids=[t['id'] for t in tasks],targets=targets,groups=groups,new_generations=0)
(Path(__file__).parent/'D8_TARGETS.json').write_text(json.dumps(output,ensure_ascii=False,indent=2)+'\n')
print(json.dumps(output,ensure_ascii=False))
