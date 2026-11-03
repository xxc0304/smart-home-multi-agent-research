"""Offline scoring. Uses upstream MuSiQue metrics, with explicit missing/invalid slots.

No missing record is removed from the expected denominator. Primary summaries
are disabled for an incomplete batch. Fixture results are labeled at their site.
"""
from pathlib import Path
from collections import Counter, defaultdict
import argparse
import json
import sys

from expert_mechanism_protocol import parse_output, ProtocolError

ROOT = Path(__file__).resolve().parent.parent
OFFICIAL = ROOT/'research/musique-data-preparation-20261030/official_scorer'
sys.path.insert(0, str(OFFICIAL))
from metrics.answer import compute_exact, compute_f1
from metrics.support import SupportMetric


def read_jsonl(path):
    return [json.loads(line) for line in Path(path).read_text(encoding='utf-8-sig').splitlines() if line.strip()]


def score_one(output, target):
    answer = output['answer'] if output['answer'] is not None else ''
    gold = [target['answer']] + target['answer_aliases']
    support = SupportMetric()
    support(output['support_idxs'], [p['idx'] for p in target['paragraphs'] if p['is_supporting']])
    return {'answer_em': max(compute_exact(g, answer) for g in gold),
            'answer_f1': max(compute_f1(g, answer) for g in gold),
            'support_em': support.get_metric()[0], 'support_f1': support.get_metric()[1],
            'abstained': output['answer'] is None or not answer.strip()}


def score_batch(requests, responses, targets, fixture=False, source_root=ROOT):
    req_ids = [r['request_id'] for r in requests]
    res_ids = [r['request_id'] for r in responses]
    if not requests or len(set(req_ids)) != len(req_ids):
        raise ProtocolError('empty_or_duplicate_expected_requests')
    if len(set(res_ids)) != len(res_ids) or set(res_ids)-set(req_ids):
        raise ProtocolError('duplicate_or_extra_response_ids')
    by_id = {r['request_id']: r for r in responses}
    records = []
    for req in requests:
        target = targets[req['task_id']]
        row = {'request_id': req['request_id'], 'task_id': req['task_id'],
               'condition': req.get('condition', req.get('stage')), 'actor': req.get('actor')}
        res = by_id.get(req['request_id'])
        if res is None:
            records.append({**row,'status':'MISSING','metrics':None}); continue
        if res.get('status') != 'ok':
            records.append({**row,'status':'TECHNICAL_FAILURE','raw_output':res.get('raw_output'),
                            'reason':res.get('status'),'metrics':None}); continue
        try:
            if not fixture:
                if res.get('source_kind') != 'ACTUAL_MODEL_RESPONSE':
                    raise ProtocolError('model_origin_not_declared')
                raw_path = Path(res.get('raw_response_path',''))
                if not raw_path.is_absolute(): raw_path=Path(source_root)/raw_path
                if not raw_path.is_file() or raw_path.read_text(encoding='utf-8') != res['raw_output']:
                    raise ProtocolError('raw_response_pointer_does_not_match')
            output = parse_output(res['raw_output'], {p['idx'] for p in target['paragraphs']})
            row.update({'status':'VALID','metrics':score_one(output,target),'output':output,
                        'raw_output':res['raw_output'],'usage':res.get('usage')})
        except (ProtocolError, KeyError) as exc:
            row.update({'status':'PROTOCOL_INVALID','reason':str(exc),'metrics':None,
                        'raw_output':res.get('raw_output')})
        records.append(row)
    valid=[r for r in records if r['status']=='VALID']
    complete=len(valid)==len(requests)
    summaries={}
    if complete:
        groups=defaultdict(list)
        for row in valid: groups[(row['condition'],row['actor'])].append(row)
        for (condition,actor),rows in groups.items():
            summaries[f'{condition}|{actor}']={'condition':condition,'actor':actor,'n':len(rows),**{key:sum(r['metrics'][key] for r in rows)/len(rows)
                            for key in ('answer_em','answer_f1','support_em','support_f1')}}
    return {'evidence_type':'HAND_AUTHORED_SCORING_FIXTURE_NOT_MODEL_RESULTS' if fixture else 'DECLARED_MODEL_OUTPUTS',
        'status':'COMPLETE_VALID' if complete else 'INCOMPLETE_NO_PRIMARY_SUMMARY',
        'n_expected':len(requests),'n_valid':len(valid),'status_counts':dict(Counter(r['status'] for r in records)),
        'primary_comparison_enabled':complete and not fixture,'condition_summaries':summaries if complete else None,
        'records':records,'scientific_limit':'Answer scores and citation overlap are not truth about causal use or expertise.'}


def paired_effects(scored):
    """Per-task factorial differences, only complete blocks. No independent-N claim."""
    by_task=defaultdict(dict)
    for row in scored['records']:
        if row['status']=='VALID' and row['condition'] in ('C00','C10','C01','C11','G','N0','N1'):
            if row['condition'] in by_task[row['task_id']]: raise ProtocolError('duplicate_task_condition')
            by_task[row['task_id']][row['condition']]=row
    effects=[]
    if scored['status']=='COMPLETE_VALID':
        for tid,rows in by_task.items():
            if not {'C00','C10','C01','C11','G','N0','N1'} <= rows.keys(): continue
            for metric in ('answer_em','answer_f1','support_f1'):
                y={k:v['metrics'][metric] for k,v in rows.items()}
                effects.append({'task_id':tid,'metric':metric,
                    'source_average_effect':((y['C10']-y['C00'])+(y['C11']-y['C01']))/2,
                    'application_average_effect':((y['C01']-y['C00'])+(y['C11']-y['C10']))/2,
                    'interaction':y['C11']-y['C10']-y['C01']+y['C00'],
                    'application_vs_generic':y['C01']-y['G'],
                    'message_application_minus_no_message_application':(y['C01']-y['C00'])-(y['N1']-y['N0'])})
    return {'complete_task_blocks':len({r['task_id'] for r in effects}), 'effects':effects,
            'fixture_math_only':scored['evidence_type'].startswith('HAND_AUTHORED'),
            'status':'DESCRIPTIVE_ONLY_NO_CAUSAL_MECHANISM_VERDICT',
            'note':'No p-values or effective sample size inferred from repeated arms; cluster-aware inference not implemented.'}


def transitions(initial_output, final_output, target):
    a,b=score_one(initial_output,target),score_one(final_output,target)
    return {'initial_correct':bool(a['answer_em']),'final_correct':bool(b['answer_em']),
            'direction':('correct_to_correct' if b['answer_em'] else 'correct_to_wrong') if a['answer_em'] else
                        ('wrong_to_correct' if b['answer_em'] else 'wrong_to_wrong')}


def main():
    p=argparse.ArgumentParser();p.add_argument('--requests',required=True);p.add_argument('--responses',required=True)
    p.add_argument('--targets',required=True);p.add_argument('--output',required=True);p.add_argument('--fixture',action='store_true')
    args=p.parse_args()
    targets={r['id']:r for r in read_jsonl(args.targets)}
    result=score_batch(read_jsonl(args.requests),read_jsonl(args.responses),targets,fixture=args.fixture)
    result['paired_effects']=paired_effects(result)
    Path(args.output).write_text(json.dumps(result,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    print(json.dumps({k:result[k] for k in ('evidence_type','status','n_expected','n_valid','primary_comparison_enabled')},ensure_ascii=False))
    if result['status']!='COMPLETE_VALID':raise SystemExit(2)


if __name__=='__main__':main()
