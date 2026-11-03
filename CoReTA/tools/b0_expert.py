"""Entry point for bounded answer-only expert preparation and explicit runs."""
import argparse
import json
from pathlib import Path

from b0_answers import (ROOT, read_jsonl, write_json, smoke, score_run,
                        compare_runs, select_candidate)
from b0_training import dependencies, require_config, load_tokenizer, encode_row, train, generate


DATA = ROOT/'data/expert-training-answer-only-20261031'
PACKAGE = ROOT/'implement-stage/expert-answer-only-20261101'


def prepare_metadata(output):
    """C IDs/relationships only, no C questions/targets and no H bodies."""
    from prepare_expert_training import dependency_groups
    source=ROOT/'data/external/musique-v1.0-20261030'
    manifest=json.loads((ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json').read_text(encoding='utf-8'))
    expected=set(manifest['roles']['C_calibration']['ids'])
    index=[r for r in read_jsonl(source/'corpus_index.jsonl') if r['id'] in expected]
    groups=dependency_groups(index)
    mapping={task_id:i for i,group in enumerate(groups) for task_id in group}
    if set(mapping)!=expected:raise ValueError('C_metadata_missing_ids')
    result=dict(role='C',expected_ids=sorted(expected),groups=mapping,
        n_groups=len(groups),largest_group_n=max(map(len,groups)),
        bootstrap_repeats=10000,seed=20261102,ci='percentile_95',
        grouping='shared question/component/support, including support in peer context; no answers',
        C_question_and_target_bodies_read=False,H_bodies_read=False)
    write_json(output,result)
    return {k:result[k] for k in ('role','n_groups','largest_group_n')}


def check_data():
    from prepare_answer_only_expert import SYSTEM
    train_rows=read_jsonl(DATA/'train.messages.jsonl')
    validation=read_jsonl(DATA/'validation.messages.jsonl')
    assert (len(train_rows),len(validation))==(1796,200)
    assert not {r['id'] for r in train_rows}&{r['id'] for r in validation}
    for r in train_rows+validation:
        assert [m['role'] for m in r['messages']]==['system','user','assistant']
        assert r['messages'][0]['content']==SYSTEM and r['messages'][2]['content'].strip()
    return dict(status='DATA_INTERFACE_CHECK_ONLY',n_train=len(train_rows),n_validation=len(validation),
                no_C_D_H_bodies_read=True,dependencies=dependencies())


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    sub=parser.add_subparsers(dest='command',required=True)
    for name in ('check-data','smoke','prepare-metadata'):
        p=sub.add_parser(name);p.add_argument('--output',type=Path,required=True)
    for name in ('tokenize-check','train','generate'):
        p=sub.add_parser(name);p.add_argument('--config',type=Path,required=True)
        p.add_argument('--output',type=Path,required=True)
        if name=='train':p.add_argument('--technical-steps',type=int)
        if name=='generate':
            p.add_argument('--role',choices=['V','C'],required=True)
            p.add_argument('--condition',choices=['B','E'],required=True)
            p.add_argument('--adapter',type=Path)
    p=sub.add_parser('score');p.add_argument('--run',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('compare');p.add_argument('--baseline',type=Path,required=True)
    p.add_argument('--expert',type=Path,required=True);p.add_argument('--groups',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    p=sub.add_parser('select');p.add_argument('--reports',nargs='+',type=Path,required=True)
    p.add_argument('--output',type=Path,required=True)
    args=parser.parse_args()
    if args.command=='smoke':result=smoke(args.output)
    elif args.command=='check-data':result=check_data();write_json(args.output,result)
    elif args.command=='prepare-metadata':result=prepare_metadata(args.output)
    elif args.command=='score':
        manifest=json.loads((args.run/'manifest.json').read_text(encoding='utf-8'))
        if manifest['role'] not in ('V','C'):raise ValueError('role_not_allowed')
        target_path=(ROOT/'data/expert-training-20261030-v1/validation.targets.jsonl'
            if manifest['role']=='V' else ROOT/'data/external/musique-v1.0-20261030/scoring/C_calibration.jsonl')
        result=score_run(args.run,{r['id']:r for r in read_jsonl(target_path)})
        write_json(args.output,result)
    elif args.command=='compare':
        a,b=[json.loads(p.read_text(encoding='utf-8')) for p in (args.baseline,args.expert)]
        groupmeta=json.loads(args.groups.read_text(encoding='utf-8'))
        if a['manifest']['role']!=groupmeta['role']:raise ValueError('group_role_mismatch')
        result=compare_runs(a,b,groupmeta['groups'],groupmeta['bootstrap_repeats'],groupmeta['seed'])
        write_json(args.output,result)
    elif args.command=='select':
        result=select_candidate([json.loads(p.read_text(encoding='utf-8')) for p in args.reports])
        write_json(args.output,result)
    else:
        config=json.loads(args.config.read_text(encoding='utf-8'))
        if args.command=='generate':
            result=generate(config,args.role,args.condition,args.adapter,args.output)
        elif args.command=='tokenize-check':
            # No model weights needed, but use the exact chosen tokenizer/template.
            require_config(config)
            tok=load_tokenizer(config)
            features=[encode_row(tok,r,config['max_length'],config['template_kwargs'])
                      for r in read_jsonl(DATA/'train.messages.jsonl')+read_jsonl(DATA/'validation.messages.jsonl')]
            result=dict(status='FULL_TRAIN_V_LENGTH_CHECK',n=len(features),
                max_tokens=max(len(f['input_ids']) for f in features),
                total_tokens=sum(len(f['input_ids']) for f in features),truncation=False)
            write_json(args.output,result)
        else:
            if args.technical_steps is not None:
                if args.technical_steps<1:raise ValueError('positive_technical_steps_required')
                config['purpose']='technical_preflight'
            train(config,read_jsonl(DATA/'train.messages.jsonl'),args.output,max_steps=args.technical_steps)
            result=dict(output=str(args.output),purpose=config['purpose'])
    print(json.dumps({k:v for k,v in result.items() if k not in ('records','manifest','example')},ensure_ascii=False))


if __name__=='__main__':main()
