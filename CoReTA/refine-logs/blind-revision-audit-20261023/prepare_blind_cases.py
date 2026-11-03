"""Offline case selection: source content and artifacts only, no experimental labels or gold."""
import hashlib
import json
import random
from pathlib import Path

PROJECT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).parent
SELECTION=[
 ('hb-dev-034','runs/workboard-d0-natural-live-20261022-r2/hb-dev-034-r1-c2/d0_continuation/state.json','W4','W6'),
 ('hb-dev-050','runs/hiddenbench-development-live-20261022-r1/hb-dev-050-r1/coreta_workboard/state.json','W4','W5'),
 ('hb-dev-001','runs/hiddenbench-development-live-20261022-r1/hb-dev-001-r1/coreta_workboard/state.json','W6','W7'),
 ('hb-dev-001','runs/hiddenbench-development-live-20261022-r1/hb-dev-001-r2/coreta_workboard/state.json','W5','W6'),
 ('hb-dev-004','runs/hiddenbench-development-live-20261022-r1/hb-dev-004-r1/coreta_workboard/state.json','W3','W4'),
]


def read(p):return json.loads(p.read_text(encoding='utf-8'))


def main():
    selected=list(SELECTION);random.Random(53).shuffle(selected)
    cases=[];mapping=[]
    for i,(task,statepath,before,after) in enumerate(selected,1):
        state=read(PROJECT/statepath)
        root=PROJECT/'data/task-packs/hiddenbench-workboard-dev-v1'/task
        packets=[read(p) for p in sorted((root/'packets/distributed').glob('A*.json'))]
        works={w['id']:w for w in state['works']}
        def artifact(ref):
            w=works[ref]
            return {k:w[k] for k in ['author','artifact','work_text','open_points']}
        case={'case':f'CASE-{i:02}', 'task':packets[0]['TASK'],
              'materials':[{'holder':p['SELF']['agent_id'],'materials':p['SELF_MATERIALS']} for p in packets],
              'before':artifact(before),'after':artifact(after),
              'audit_access':'Auditor sees all listed originals; actual members only their own. No gold supplied.'}
        # Original artifact text may contain protocol-specific author language; preserve it verbatim.
        cases.append(case)
        mapping.append({'case':case['case'],'task':task,'state':statepath,'before':before,'after':after,
                        'state_sha256':hashlib.sha256((PROJECT/statepath).read_bytes()).hexdigest()})
    (OUT/'BLIND_CASES.json').write_text(json.dumps({'kind':'masked_conditions_not_fully_anonymized_text',
        'selection':'purposive_diagnostic_not_random_sample','cases':cases},ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (OUT/'PRIVATE_MAPPING.json').write_text(json.dumps(mapping,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({'cases':len(cases),'unique_tasks':len({r['task'] for r in mapping}),'http_calls':0}))


if __name__=='__main__':main()
