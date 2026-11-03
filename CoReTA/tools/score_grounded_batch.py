"""Offline exact-match + evidence bundle export; semantic labels require review."""
import argparse
import hashlib
import json
from pathlib import Path
from coreta.handoff.gateway import write_json


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))


def export(prepared, runs, output):
    if output.exists(): raise ValueError('New export directory required')
    m=read(prepared/'manifest.json');sha=hashlib.sha256((prepared/'manifest.json').read_bytes()).hexdigest()
    roots={}
    for run in runs:
        progress=read(run/'progress.json')
        if progress['manifest_sha256']!=sha: raise ValueError('Different freeze')
        for row in progress['units']:
            if row['method']=='initial': continue
            key=(row['pair'],row['method'])
            if key in roots: raise ValueError('Duplicate trajectory export')
            roots[key]=run
    output.mkdir(parents=True);rows=[];mapping=[];review=[];initials=[]
    for pair in m['pairs']:
        # Only the offline scorer opens gold; no protocol runtime imports this module.
        gold=read(Path(pair['pack'])/'offline/evaluation.json')['correct_option_id']
        pair_root=next((root for (pid,method),root in roots.items() if pid==pair['id']),None)
        cache_path=pair_root/pair['id']/'initial/cache.json' if pair_root else None
        cache=read(cache_path) if cache_path and cache_path.exists() else None
        for member in ('A'+str(i) for i in range(1,pair['members']+1)):
            candidate=cache['candidates'].get(member) if cache else None
            initials.append(dict(pair=pair['id'],member=member,artifact=candidate['artifact'] if candidate else None,
                                 exact_match=int(candidate['artifact']==gold) if candidate else None))
        for method in pair['methods']:
            alias='unit_'+hashlib.sha256((pair['id']+'|'+method).encode()).hexdigest()[:12]
            root=roots.get((pair['id'],method))
            folder=root/pair['id']/method if root else None
            result=read(folder/'result.json') if folder and (folder/'result.json').exists() else None
            rows.append(dict(pair=pair['id'],method=method,task_id=pair['task_id'],unit_id=alias,
                status=result['status'] if result else 'missing',
                http_attempts=result.get('http_attempts') if result else None,
                usage=result.get('usage') if result else None,
                artifact=result['selected_work']['artifact'] if result and result.get('selected_work') else None,
                exact_match=int(result['selected_work']['artifact']==gold) if result and result.get('selected_work') and result['status']=='completed' else None))
            mapping.append(dict(unit_id=alias,pair=pair['id'],method=method,path=str(folder) if folder else None))
            if folder and (folder/'state.json').exists():
                state=read(folder/'state.json')
                events=[json.loads(line) for line in (folder/'events.jsonl').read_text(encoding='utf-8').splitlines()]
                review.append(dict(unit_id=alias,task_id=pair['task_id'],works=state['works'],
                    offers=state['offers'],checks=state['checks'],feedback=state['feedback'],events=events,
                    selected=result.get('selected_work_id') if result else state['current'],
                    note='Method identifiers hidden; structure can reveal method. Not guaranteed blind.'))
    write_json(output/'EXACT_MATCH.json',dict(rows=rows,note='Null means missing/interrupted, not success; no exclusion from roster.'))
    write_json(output/'PRIVATE_METHOD_MAP.json',mapping)
    write_json(output/'INITIAL_EXACT_MATCH.json',initials)
    write_json(output/'PROCESS_EVIDENCE.json',review)
    write_json(output/'ANNOTATIONS.json',read(prepared/'ANNOTATION_TEMPLATE.json'))
    return rows


if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--prepared',type=Path,required=True);p.add_argument('--runs',nargs='+',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True);a=p.parse_args()
    export(a.prepared,a.runs,a.output)
