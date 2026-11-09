"""Exploratory baseline contrasts; official paired group bootstrap, no run edits."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import paired_interval
RUN=ROOT/'runs/b1-independent-first-work-20261106-v1';HERE=Path(__file__).resolve().parent
s=json.loads((RUN/'scores.json').read_text());p=json.loads((RUN/'INPUTS.json').read_text());rows=[r for r in s['rows'] if r['coverage']]
defs={
'Bteam-Ateam':lambda r:r['conditions']['B']['expected_em']-r['conditions']['A']['expected_em'],
'Dteam-Cteam':lambda r:r['conditions']['D']['expected_em']-r['conditions']['C']['expected_em'],
'Bteam-EprivateA':lambda r:r['conditions']['B']['expected_em']-r['conditions']['A']['expert_em'],
'Bdelayteam-EprivateA':lambda r:r['conditions']['B_delay']['expected_em']-r['conditions']['A']['expert_em'],
'Bteam-Einitial':lambda r:r['conditions']['B']['expected_em']-r['initial']['M1']['em'],
'Bdelayteam-Einitial':lambda r:r['conditions']['B_delay']['expected_em']-r['initial']['M1']['em'],
'BdelayExpert-Bexpert':lambda r:r['conditions']['B_delay']['expert_em']-r['conditions']['B']['expert_em']}
out={}
for k,fn in defs.items():
 v={f'{r["id"]}/r{r["rep"]}':fn(r) for r in rows};g={f'{r["id"]}/r{r["rep"]}':p['groups'][r['id']] for r in rows}
 out[k]=dict(difference=sum(v.values())/len(v),cluster_ci95=paired_interval(v,g,10000,20261107),scope='EXPLORATORY_SECONDARY_NOT_PREREGISTERED_PRIMARY')
(HERE/'BASELINE_CONTRASTS.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out),flush=True)
