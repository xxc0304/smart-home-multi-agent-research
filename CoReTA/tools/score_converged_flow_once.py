import json
from pathlib import Path
from coreta.scoring import docker_math_records
from coreta.state import write_json
root=Path('runs/converged-flow-20261020');result=json.loads((root/'result.json').read_text(encoding='utf-8'))
gold=json.loads(Path('data/math-expanded-screen-20261019/evaluation/math_gold.json').read_text(encoding='utf-8'))
record=next(r for r in gold if r['task_id']==result['task_id'])
score=docker_math_records([{**record,'artifact':result['artifact']}],'sha256:841f8763c03c5cc688a811a90e13e82541d3350cdaccf3bba64aefb627be5cf6')
write_json(root/'score.json',score);print(json.dumps(score))
