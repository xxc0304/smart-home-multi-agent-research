"""Verify real exported files and scoring edge cases; fixtures are NOT model results."""
from pathlib import Path
from collections import Counter
from copy import deepcopy
import hashlib
import json
import tempfile
from audit_corpus import ROOT, DATA, HERE, sanitize, paragraph_hash
from score_predictions import score, validate, official


def read(path):
    return [json.loads(s) for s in Path(path).open(encoding='utf-8') if s.strip()]


def dump(path, rows):
    path.write_text(''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in rows),encoding='utf-8')


def main():
    m=json.loads((HERE/'SPLIT_MANIFEST.json').read_text(encoding='utf-8'))
    for entry in m['files']:
        assert hashlib.sha256((ROOT/entry['path']).read_bytes()).hexdigest()==entry['sha256'],entry['path']
    for name,expected in m['code_sha256'].items():
        assert hashlib.sha256((HERE/name).read_bytes()).hexdigest()==expected,name
    source_manifest=json.loads((HERE/'SOURCE_MANIFEST.json').read_text(encoding='utf-8'))
    assert hashlib.sha256((HERE/'SOURCE_MANIFEST.json').read_bytes()).hexdigest()==m['source_manifest_sha256']
    assert hashlib.sha256((ROOT/'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json').read_bytes()).hexdigest()==m['tokenizer_sha256']
    for item in source_manifest['extracted']:
        assert hashlib.sha256((DATA/item['file']).read_bytes()).hexdigest()==item['sha256'],item['file']
    originals={}
    required=set().union(*(set(r['ids']) for r in m['roles'].values()))
    for source in ('train','dev'):
        for row in read(DATA/f'musique_ans_v1.0_{source}.jsonl'):
            if row['id'] in required: originals[row['id']]=row
    inputs_by_role={}
    for role, info in m['roles'].items():
        inputs=read(DATA/'inputs'/(role+'.jsonl'))
        targets=read(DATA/'scoring'/(role+'.jsonl'))
        assert [r['id'] for r in inputs]==info['ids']==[r['id'] for r in targets]
        assert len(set(info['ids']))==info['n']
        for inp,target in zip(inputs,targets):
            raw=originals[inp['id']]
            assert inp==sanitize(raw)
            assert set(inp)=={'id','question','paragraphs'}
            assert all(set(p)=={'idx','title','paragraph_text'} for p in inp['paragraphs'])
            assert target['answer']==raw['answer'] and target['answer_aliases']==raw['answer_aliases']
            assert target['question_decomposition']==raw['question_decomposition']
            assert target['paragraphs']==[{'idx':p['idx'],'is_supporting':p['is_supporting']} for p in raw['paragraphs']]
        inputs_by_role[role]=inputs
    exposed_ids={r['official_id'] for r in read(HERE/'exposure_mapping.jsonl')}
    assert not exposed_ids & set(m['roles']['H_confirmation_candidate']['ids'])
    old_inputs=read(ROOT/'data/external/musique-inspection-20261030/dev_inputs.jsonl')
    official_exposed={r['id']:r for r in read(DATA/'musique_ans_v1.0_dev.jsonl') if r['id'] in exposed_ids}
    exposure_mapping={r['raw_id']:r['official_id'] for r in read(HERE/'exposure_mapping.jsonl')}
    prior_visible_matches=0
    for old in old_inputs:
        mapped=exposure_mapping[old['raw_id']]
        # These exposed records are outside exported H; retrieve by source ID.
        raw=official_exposed[mapped]
        from audit_corpus import digest
        assert {digest(p['text']) for p in old['paragraphs']}=={paragraph_hash(p) for p in raw['paragraphs']}
        prior_visible_matches+=1
    for left in inputs_by_role:
        for right in inputs_by_role:
            if left==right: continue
            right_text={paragraph_hash(p) for r in inputs_by_role[right] for p in r['paragraphs']}
            for row in inputs_by_role[left]:
                assert not {paragraph_hash(p) for p in originals[row['id']]['paragraphs'] if p['is_supporting']} & right_text
    target=read(HERE/'examples/targets.jsonl')[0]
    supports=[p['idx'] for p in target['paragraphs'] if p['is_supporting']]
    exact={'id':target['id'],'predicted_answer':target['answer'],
           'predicted_support_idxs':supports,'predicted_answerable':True}
    alias=deepcopy(exact); alias['predicted_answer']=target['answer_aliases'][0]
    wrong_answer=deepcopy(exact); wrong_answer['predicted_answer']='zzzzzznonanswerzzzzzz'
    wrong_support=deepcopy(exact); wrong_support['predicted_support_idxs']=[next(p['idx'] for p in target['paragraphs'] if not p['is_supporting'])]
    partial=deepcopy(exact); partial['predicted_support_idxs']=supports[:1]
    valid_cases={'exact_gold_fixture':(exact,{'answer_em':1.,'answer_f1':1.,'support_f1':1.}),
                 'alias_fixture':(alias,{'answer_em':1.,'answer_f1':1.,'support_f1':1.}),
                 'wrong_answer_correct_support_fixture':(wrong_answer,{'answer_em':0.,'answer_f1':0.,'support_f1':1.}),
                 'correct_answer_wrong_support_fixture':(wrong_support,{'answer_em':1.,'answer_f1':1.,'support_f1':0.}),
                 'partial_support_fixture':(partial,{'answer_em':1.,'answer_f1':1.,'support_f1':round(2/(len(supports)+1),3)})}
    outcomes={}
    with tempfile.TemporaryDirectory(prefix='coreta-musique-fixtures-') as folder:
        folder=Path(folder); gold=folder/'gold.jsonl'; dump(gold,[target])
        for name,(prediction,expected) in valid_cases.items():
            pred=folder/(name+'.jsonl'); dump(pred,[prediction])
            actual=score(pred,gold)
            assert actual['metrics']==expected==official.evaluate(str(pred),str(gold)),name
            outcomes[name]={'status':'MATCH_OFFICIAL_AND_EXPECTED','metrics':actual['metrics']}
            dump(HERE/'examples'/(name+'.jsonl'),[prediction])
        # Mixed set: macro averaging and ID alignment, not just single-perfect rows.
        tg=[]; ps=[]
        for i,(p,_) in enumerate(valid_cases.values()):
            t=deepcopy(target); t['id']=str(i); tg.append(t)
            p=deepcopy(p); p['id']=str(i); ps.append(p)
        dump(gold,tg); mixed=folder/'mixed.jsonl'; dump(mixed,list(reversed(ps)))
        expected_macro={k:round(sum(v[1][k] for v in valid_cases.values())/len(valid_cases),3) for k in ('answer_em','answer_f1','support_f1')}
        actual=score(mixed,gold); assert actual['metrics']==expected_macro
        outcomes['mixed_macro_and_reordered_ID_join']={'status':'MATCH_EXPECTED','metrics':actual['metrics']}
    invalid={}
    invalid['missing_prediction']=[]
    invalid['duplicate_prediction_id']=[deepcopy(exact),deepcopy(exact)]
    for label,value in [('out_of_range',20),('float_index',1.0),('bool_index',True),('string_index','1')]:
        p=deepcopy(exact); p['predicted_support_idxs']=[value]; invalid[label]=[p]
    p=deepcopy(exact); p['predicted_support_idxs']=supports+supports; invalid['duplicate_support_index']=[p]
    p=deepcopy(exact); p['gold_answer']='forbidden'; invalid['extra_prediction_field']=[p]
    for name,preds in invalid.items():
        try: validate(preds,[target])
        except ValueError as exc: outcomes[name]={'status':'REJECTED_NO_AGGREGATE','reason':str(exc)}
        else: raise AssertionError('Invalid fixture accepted: '+name)
    # Native source blacklist IDs are a different namespace from numeric MuSiQue IDs.
    blacklist=json.loads((DATA/'dev_test_singlehop_questions_v1.0.json').read_text(encoding='utf-8'))
    source_counts={k:len(v) for k,v in blacklist.items()}
    scorer_files=[]
    for path in sorted((HERE/'official_scorer').rglob('*')):
        if path.is_file() and '__pycache__' not in str(path):
            scorer_files.append({'path':str(path.relative_to(HERE)).replace('\\','/'),
                                 'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
    (HERE/'OFFICIAL_SCORER_MANIFEST.json').write_text(json.dumps({'retrieved_date':'2026-10-30',
       'source_repository':'https://github.com/StonyBrookNLP/musique',
       'source_ref':'main at retrieval, content hashes frozen locally; commit not asserted',
       'license':'CC BY 4.0; upstream LICENSE preserved',
       'files':scorer_files,'local_addition':'empty metrics/__init__.py; upstream algorithm unchanged'},indent=2)+'\n',encoding='utf-8')
    result={'status':'PASS_OFFLINE_DATA_AND_SCORER_ONLY','model_calls':0,'training_runs':0,
        'file_hashes_verified':len(m['files']),'rows_verified_against_raw':len(required),
        'schema_gold_isolation':'allowlisted input keys, exact comparison to raw inputs; targets in separate scoring directory',
        'cross_role_gold_to_context_overlap_rows':0,'direct_exposed_dev_in_H':0,
        'prior_dev_visible_paragraph_sets_matched_to_official':prior_visible_matches,
        'official_blacklist_native_source_counts':source_counts,
        'scoring_checks':outcomes,
        'warning':'ALL scores above are hand-constructed metric fixtures using gold, NOT model predictions or scientific results.',
        'limits':['Text can naturally contain answers; gold isolation means no answer labels/decomposition/support flags are exported as extra model fields.',
                  'Neither human annotation agreement nor model-generation end-to-end readiness has been checked.',
                  'Metric parity is against the downloaded official scorer, not against an external evaluator service.']}
    (HERE/'STAGE_CHECKS.json').write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__': main()
