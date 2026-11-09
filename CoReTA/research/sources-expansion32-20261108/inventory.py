"""Metadata/content-exposure inventory; no model calls or score-based selection."""
import json, hashlib
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parents[1]
source=ROOT/'research/name-protocol-dev11-20261108/benchmark.json'
tasks=json.loads(source.read_text());hits={t['id']:set() for t in tasks}
def texts(x):
    if isinstance(x,str):
        if len(x)>200:yield x
    elif isinstance(x,dict):
        for v in x.values():yield from texts(v)
    elif isinstance(x,list):
        for v in x:yield from texts(v)
files=0;records=0
for p in (ROOT/'runs').rglob('*.jsonl'):
    if not any(s in p.name.lower() for s in ['attempt','request','response']):continue
    files+=1
    with p.open(encoding='utf-8') as f:
        for line in f:
            if not line.strip():continue
            try:r=json.loads(line)
            except json.JSONDecodeError:continue
            records+=1
            for s in texts(r):
                if len(s)<200:continue
                for t in tasks:
                    if t['description'] in s:hits[t['id']].add(str(p.relative_to(ROOT)))
result={'files_scanned':files,'records_scanned':records,'full_description_matches':{str(k):sorted(v) for k,v in hits.items() if v},
        'matched_ids':sorted(k for k,v in hits.items() if v),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
        'limitations':'Available run logs only, exact full-description matches; no claim of never viewed, no pretraining exposure, or recovered historical split.'}
(HERE/'REMOTE_EXPOSURE_AUDIT.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n')
print(json.dumps({k:v for k,v in result.items() if k!='full_description_matches'}))
