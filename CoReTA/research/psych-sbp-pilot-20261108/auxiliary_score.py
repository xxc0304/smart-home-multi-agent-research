"""Explicit post-observation identity normalization; original strict scores untouched."""
import collections, json, re
import pilot as p

RULE = {'version':'SBP_LETTER_ID_AUX_V1', 'status':'post_observation_exploratory',
        'exposure':'First pilot responses inspected before introducing this auxiliary metric; not preregistered.',
        'mapping':{c:'Candidate '+c for c in 'ABCD'},
        'allowed':'Exactly four numbered lines 1..4, each one uppercase A..D or exact Candidate A..D; no duplicates.',
        'unchanged':'No facts, rank order, gold, prompts, original parser, generation, or strict score files changed.'}

def normalized(text):
    matches = re.findall(r'^\s*([1-4])[.)]\s*(?:Candidate )?([A-D])\s*$',text,re.M)
    if len(matches)!=4 or [int(n) for n,_ in matches]!=[1,2,3,4]: return None
    names = ['Candidate '+c for _,c in matches]
    return names if len(set(names))==4 else None

def main():
    assert normalized('1. D\n2. C\n3. A\n4. B') == ['Candidate '+c for c in 'DCAB']
    assert normalized('1. D\n2. D\n3. A\n4. B') is None
    assert normalized('1. D or C\n2. C\n3. A\n4. B') is None
    cfg=p.load(p.HERE/'config.json'); out=p.ROOT/cfg['run_dir']; gold=p.load(p.HERE/'labels.json')['ranking']
    rows=[json.loads(s) for s in (out/'responses.jsonl').read_text().splitlines() if s.strip()]
    groups=collections.defaultdict(list)
    for r in rows: groups[(r['seed'],r['arm'],r['stage'])].append(r)
    result=[]
    for seed in cfg['seeds']:
        for arm in p.ARMS:
            ia='B_hidden' if arm in ['A_private','B_hidden','D_revealed'] else arm
            initial=groups[(seed,ia,'initial')]; final=groups[(seed,arm,'final')]
            item={'seed':seed,'arm':arm,'initials':{r['actor']:p.error(normalized(r['text']),gold) for r in initial},
                  'finals':{r['actor']:p.error(normalized(r['text']),gold) for r in final},
                  'complete':len(final)==4 and all(r['status']=='OK' for r in final),
                  'initial_aggregate':p.aggregate([normalized(r['text']) for r in initial],gold),
                  'final_aggregate':p.aggregate([normalized(r['text']) for r in final],gold)}
            result.append(item)
    evidence={'rule':RULE,'snapshot_rows':len(rows),'original_strict_invalid':sum(r['ranking'] is None for r in rows),
              'aux_invalid':sum(normalized(r['text']) is None for r in rows), 'results':result,
              'source_status':p.load(out/'STATUS.json')['status']}
    p.write(p.HERE/'AUXILIARY_RULE.json',RULE); p.write(p.HERE/'AUXILIARY_RESULTS.json',evidence)
    print(json.dumps(evidence))

if __name__=='__main__':main()
