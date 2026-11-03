"""Deterministic, outcome-independent, purged data preparation (no model calls)."""
from pathlib import Path
from collections import Counter, defaultdict
from itertools import combinations
import hashlib
import json
from audit_corpus import DATA, ROOT, HERE, sanitize, prompt, keys, overlaps, components, summary, digest

SEED = 'coreta-musique-20261030-v1'


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def frozen_keys(row):
    # Also protect single-hop answer strings, as in paper section S5.
    return keys(row) | {('a',v) for v in row['component_answer_hashes']} | {('a',row['final_answer_hash'])}


def guard(rows):
    return {'keys': set().union(*(frozen_keys(r) for r in rows)),
            'gold': {v for r in rows for v in r['support_hashes']},
            'visible': {v for r in rows for v in r['context_hashes']}}


def reasons(row, protected):
    hits = frozen_keys(row) & protected['keys']
    out = sorted({k[0] for k in hits})
    if set(row['context_hashes']) & protected['gold']: out.append('protected_gold_in_candidate_context')
    if set(row['support_hashes']) & protected['visible']: out.append('candidate_gold_in_protected_context')
    return out


def ranked(rows, tag):
    return sorted(rows, key=lambda r:hashlib.sha256((SEED+'|'+tag+'|'+r['id']).encode()).hexdigest())


def select(rows, n, tag):
    # Shape-stratified proportional quotas; no model scores or answer correctness.
    if len(rows) < n: raise ValueError(f'{tag}: only {len(rows)} candidates for target {n}')
    groups = defaultdict(list)
    for row in ranked(rows,tag): groups[row['shape']].append(row)
    ideal = {s:n*len(v)/len(rows) for s,v in groups.items()}
    quotas = {s:int(v) for s,v in ideal.items()}
    for shape in sorted(groups,key=lambda s:(-(ideal[s]-quotas[s]),s))[:n-sum(quotas.values())]: quotas[shape]+=1
    selected, questions = [], set()
    for shape in sorted(groups):
        count=0
        for row in groups[shape]:
            if count == quotas[shape]: break
            if row['question_hash'] in questions: continue
            selected.append(row); questions.add(row['question_hash']); count+=1
    ids={r['id'] for r in selected}
    for row in ranked(rows,tag+'|fill'):
        if len(selected)==n: break
        if row['id'] not in ids and row['question_hash'] not in questions:
            selected.append(row); ids.add(row['id']); questions.add(row['question_hash'])
    if len(selected)!=n: raise ValueError(f'{tag}: not enough distinct composed questions')
    return ranked(selected,tag+'|order')


def write_jsonl(path, rows):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('w',encoding='utf-8') as handle:
        for row in rows: handle.write(json.dumps(row,ensure_ascii=False)+'\n')


def main():
    audit=json.loads((HERE/'CORPUS_AUDIT.json').read_text(encoding='utf-8'))
    if any(audit[s]['schema_issues'] or audit[s]['duplicate_ids'] for s in ('train','dev')):
        raise ValueError('Unresolved schema/ID issues')
    indexed=[json.loads(s) for s in (DATA/'corpus_index.jsonl').open(encoding='utf-8')]
    train=[r for r in indexed if r['source_split']=='train']
    dev=[r for r in indexed if r['source_split']=='dev']
    by_id={r['id']:r for r in indexed}
    old=[json.loads(s) for s in (ROOT/'data/external/musique-inspection-20261030/dev_inspected_ids.jsonl').open(encoding='utf-8')]
    mapping={'double':'2hop','triple_ii':'3hop1','triple_io':'3hop2','quadruple_iii':'4hop1',
             'quadruple_iot':'4hop2','quadruple_ioh1':'4hop3','quadruple_ioh2':'4hop4'}
    mapped=[]
    for entry in old:
        prefix,tail=entry['raw_id'].split('__',1)
        official=mapping[prefix]+'__'+tail
        if official not in by_id or by_id[official]['question_hash']!=digest(entry['question']):
            raise ValueError('Prior exposure ID/question mismatch: '+official)
        mapped.append({'raw_id':entry['raw_id'],'official_id':official,'normalized_question_match':True})
    exposed=[by_id[e['official_id']] for e in mapped]
    exposure_guard=guard(exposed)
    H, exclusions, h_questions=[],{},set()
    for row in ranked(dev,'H_dedup'):
        why=reasons(row,exposure_guard)
        if row['id'] in {r['id'] for r in exposed}: why=['directly_exposed']+why
        if row['question_hash'] in h_questions: why.append('duplicate_composed_question')
        if why: exclusions[row['id']]=why
        else: H.append(row); h_questions.add(row['question_hash'])
    H=ranked(H,'H_order')
    hg=guard(H)
    pool=[r for r in train if not reasons(r,hg)]
    C=select(pool,160,'C'); cg=guard(C); cids={r['id'] for r in C}
    dp=[r for r in pool if r['id'] not in cids and not reasons(r,cg)]
    D=select(dp,80,'D'); dg=guard(D); dids={r['id'] for r in D}
    tp=[r for r in dp if r['id'] not in dids and not reasons(r,dg)]
    T=select(tp,min(2000,len(tp)),'T_optional')
    roles={'C_calibration':C,'D_development':D,'H_confirmation_candidate':H,'T_optional_training':T}
    groups={k:guard(v) for k,v in roles.items()}
    checks={}
    for left,right in combinations(roles,2):
        fields={field:overlaps(roles[left],roles[right],field) for field in
            ('id','question_hash','component_ids','standalone_component_question_hashes','component_answer_hashes','support_hashes','context_hashes')}
        cross1=sum(bool(set(r['support_hashes'])&groups[right]['visible']) for r in roles[left])
        cross2=sum(bool(set(r['support_hashes'])&groups[left]['visible']) for r in roles[right])
        if any(v['shared_keys'] for f,v in fields.items() if f!='context_hashes') or cross1 or cross2:
            raise ValueError('Protected overlap: '+left+'/'+right)
        checks[left+'__'+right]={'overlaps':fields,'left_gold_in_right_visible_rows':cross1,'right_gold_in_left_visible_rows':cross2}
    role_ids={k:{r['id'] for r in v} for k,v in roles.items()}
    assignment=[]
    for row in indexed:
        assigned=next((k for k,ids in role_ids.items() if row['id'] in ids),None)
        why={}
        if not assigned:
            if row['source_split']=='dev':
                assigned='DEV_EXCLUDED_EXPOSURE_OR_DUPLICATE'; why={'exposure_or_dedup':exclusions[row['id']]}
            else:
                why={k:reason for k,g in groups.items() if k!='T_optional_training' and (reason:=reasons(row,g))}
                assigned='TRAIN_PURGED_FROM_ACTIVE_ROLES' if why else 'TRAIN_UNUSED_ELIGIBLE_RESERVE'
        assignment.append({'id':row['id'],'source_split':row['source_split'],'role':assigned,'reasons':why})
    write_jsonl(DATA/'split_assignments.jsonl',assignment)
    role_of={r['id']:r['role'] for r in assignment}
    handles={}
    for role in roles:
        for kind in ('inputs','scoring'):
            folder=DATA/kind; folder.mkdir(exist_ok=True)
            handles[role,kind]=(folder/(role+'.jsonl')).open('w',encoding='utf-8')
    source_rows={}
    # Export in frozen manifest order, not incidental source order.
    needed=set().union(*role_ids.values())|{r['id'] for r in exposed}
    for source in ('train','dev'):
        for line in (DATA/f'musique_ans_v1.0_{source}.jsonl').open(encoding='utf-8'):
            row=json.loads(line)
            if row['id'] in needed: source_rows[row['id']]=row
    for role,records in roles.items():
        for record in records:
            row=source_rows[record['id']]
            inp=sanitize(row)
            assert set(inp)=={'id','question','paragraphs'}
            assert all(set(p)=={'idx','title','paragraph_text'} for p in inp['paragraphs'])
            target={k:row[k] for k in ('id','answer','answer_aliases','answerable')}
            target['paragraphs']=[{'idx':p['idx'],'is_supporting':p['is_supporting']} for p in row['paragraphs']]
            target['question_decomposition']=row['question_decomposition']
            handles[role,'inputs'].write(json.dumps(inp,ensure_ascii=False)+'\n')
            handles[role,'scoring'].write(json.dumps(target,ensure_ascii=False)+'\n')
    for handle in handles.values(): handle.close()
    # Only already-exposed dev examples used in scorer demonstration.
    demo=next((source_rows[r['id']] for r in exposed if source_rows[r['id']]['answer_aliases']),source_rows[exposed[0]['id']])
    (HERE/'examples').mkdir(exist_ok=True)
    (HERE/'examples/input.json').write_text(json.dumps(sanitize(demo),ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    (HERE/'examples/prompt.txt').write_text(prompt(sanitize(demo))+'\n',encoding='utf-8')
    demo_target={k:demo[k] for k in ('id','answer','answer_aliases','answerable')}
    demo_target['paragraphs']=[{'idx':p['idx'],'is_supporting':p['is_supporting']} for p in demo['paragraphs']]
    write_jsonl(HERE/'examples/targets.jsonl',[demo_target])
    write_jsonl(HERE/'exposure_mapping.jsonl',mapped)
    files=[DATA/'corpus_index.jsonl',DATA/'split_assignments.jsonl']
    files += [DATA/kind/(role+'.jsonl') for role in roles for kind in ('inputs','scoring')]
    stats={k:{'n':len(v),'hops':dict(Counter(r['hops'] for r in v)),
               'shapes':dict(Counter(r['shape'] for r in v)), 'tokens':summary([r['input_tokens'] for r in v]),
               'dependency_components_without_answer_strings':components(v),
               'ids':[r['id'] for r in v]} for k,v in roles.items()}
    result={'version':SEED,'date':'2026-10-30','model_calls':0,'training_runs':0,
        'code_sha256':{name:sha(HERE/name) for name in ('audit_corpus.py','build_pack.py','score_predictions.py')},
        'source_manifest_sha256':sha(HERE/'SOURCE_MANIFEST.json'),
        'tokenizer_sha256':sha(ROOT/'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json'),
        'status':'OFFLINE_DATA_PREPARATION_ONLY_NOT_EXPERIMENT_READY',
        'selection':'Stable SHA256 order and proportional shape quotas; H excludes direct/related exposure and duplicate composed questions; train roles purged against protected roles. No model outcomes used.',
        'protected': ['composed question exact normalized text','published single-hop IDs','standalone component question text without #N references','normalized single-hop/final answer strings','support paragraph normalized text','support paragraph visible as context in another role (both directions)'],
        'not_protected':['distractor-to-distractor overlap','generic uninstantiated single-hop question templates','semantic paraphrases','external pretraining contamination'],
        'candidate_pool_sizes':{'train_after_H_guard':len(pool),'D_after_C_guard':len(dp),'T_after_C_D_H_guard':len(tp)},
        'roles':stats,'assignment_counts':dict(Counter(r['role'] for r in assignment)),
        'pairwise_checks':checks,'prior_exposed_dev':len(exposed),'H_excluded_dev':len(exclusions),
        'H_exclusion_reason_counts':dict(Counter(reason for reasons_list in exclusions.values() for reason in reasons_list)),
        'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'bytes':p.stat().st_size,'sha256':sha(p)} for p in files],
        'limits':['H is an internal holdout derived from public official dev, not the official test or an externally secret test.',
                  'Machine gold access was used only for outcome-independent splitting/scoring; no manual H content inspection or model outputs for selection.',
                  'Purging changes the distribution; compare the provided hop/shape/length profiles and do not call this the complete official benchmark.',
                  'Rows within a role can share components. Row count is not an independent-sample count. Statistical design still needs cluster-aware analysis.',
                  'T is an optional training branch; no GPU, existing model endpoint, calibration advantage, team effect or scientific result is established.']}
    (HERE/'SPLIT_MANIFEST.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('candidate_pool_sizes','assignment_counts','H_exclusion_reason_counts')},ensure_ascii=False,indent=2))


if __name__=='__main__': main()
