"""Read-only descriptive summary; semantic judgements are separate."""
import json, re
from probe import HERE, ROOT, load, write, b, ACTORS, ARMS
c=load(HERE/'config.json'); out=ROOT/c['run_dir']
t=(out/'responses.jsonl').read_text(); rows=[json.loads(s) for s in t[:t.rfind('\n')+1].splitlines()]
entries=load(HERE/'INPUTS.json')['entries']; scores=load(out/'scores.json')
summary={'status':load(out/'STATUS.json'),'arms':{},'units':[]}
for arm in ARMS:
 ss=[s['arms'][arm] for s in scores if s['arms'][arm]['complete']]
 summary['arms'][arm]={'n':len(ss),'team_expected_em':sum(s['expected_em'] for s in ss)/len(ss) if ss else None,'expert_em':sum(s['members']['M1']['em'] for s in ss)/len(ss) if ss else None,'ordinary_em':sum(s['members'][a]['em'] for s in ss for a in ACTORS[1:])/(3*len(ss)) if ss else None}
for s in scores:
 e=next(e for e in entries if e['unit']==s['unit']); old=b.source(e)
 summary['units'].append({'unit':s['unit'],'index':s['index'],'rep':s['rep'],'old_finals':{a:old[(a,'final','B',3)]['raw_output'] for a in ACTORS},'arms':s['arms']})
write(HERE/'DESCRIPTIVE.json',summary)
print(json.dumps(summary,ensure_ascii=False))
lines=[]
for r in rows:
 if r['stage']=='review':lines += [f"## unit {r['unit']} {r['arm']} {r['actor']} call {r['call']}",r['raw_output'],'']
(HERE/'REVIEWS.md').write_text('\n'.join(lines))
