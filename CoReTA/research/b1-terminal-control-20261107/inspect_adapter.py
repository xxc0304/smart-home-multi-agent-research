import json,hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
c=json.loads((HERE/'diagnostic_config.json').read_text())
e=json.loads(Path(c['expert_C_score']).read_text())['manifest']
o=json.loads((Path(c['adapter_path'])/'b0_origin.json').read_text())
out={'config_adapter':c['adapter_path'],'qualified_adapter':e['adapter'],'origin':o,'config_resolved':str(Path(c['adapter_path']).resolve()),'qualified_resolved':str(Path(e['adapter']).resolve()),'path_files':{}}
for s in {c['adapter_path'],e['adapter']}:
 p=Path(s);out['path_files'][s]={q.name:{'bytes':q.stat().st_size,'sha256':hashlib.sha256(q.read_bytes()).hexdigest()} for q in p.glob('*') if q.is_file()}
for n in ('b1_runtime.py','b1_multi_backend.py'):
 p=ROOT/'tools'/n;out[n]=hashlib.sha256(p.read_bytes()).hexdigest()
print(json.dumps(out,ensure_ascii=False,indent=2))
