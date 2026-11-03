"""CLI for the revised second experiment; real runs are explicit and gated."""
import argparse
import json
from pathlib import Path
from b1_controls import smoke
from b0_answers import write_json
from b1_runtime import development_data, load_json, run_batch, score_batch, validate_runtime


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--smoke', type=Path)
    sub=parser.add_subparsers(dest='command')
    check=sub.add_parser('check', help='D inputs/relationship metadata only; zero model calls')
    check.add_argument('--n',type=int,choices=[1,2,8,32],required=True)
    check.add_argument('--output',type=Path,required=True)
    check.add_argument('--config',type=Path)
    run=sub.add_parser('run',help='Explicit local model execution, requires qualified B0 expert')
    run.add_argument('--n',type=int,choices=[1,2,8,32],required=True)
    run.add_argument('--config',type=Path,required=True)
    run.add_argument('--output',type=Path,required=True)
    run.add_argument('--resume-from',type=Path)
    score=sub.add_parser('score',help='Read D labels only after execution')
    score.add_argument('--run',type=Path,required=True)
    args = parser.parse_args()
    if args.smoke:
        if args.command:
            parser.error('choose smoke or a subcommand')
        result=smoke(args.smoke)
    elif args.command=='check':
        tasks,groups,_=development_data(args.n)
        result=dict(status='OFFLINE_INPUT_CHECK_ONLY',expected_ids=[t['id'] for t in tasks],
            n=len(tasks),n_groups=len(set(groups.values())),groups=groups,
            expected_generations=52*len(tasks),model_calls=0,targets_read=False,
            C_H_question_target_bodies_read=False)
        if args.config:
            try:
                validate_runtime(load_json(args.config))
                result['runtime_configuration']='RESOLVED_NOT_GPU_VERIFIED'
            except (ValueError,OSError) as exc:
                result['runtime_configuration']='BLOCKED'
                result['runtime_reason']=str(exc)
        write_json(args.output,result)
    elif args.command=='run':
        config=load_json(args.config)
        if config['fixture']:
            parser.error('CLI run is real D only; fixture execution is isolated in tests')
        validate_runtime(config)
        tasks,groups,_=development_data(args.n)
        result=run_batch(config,tasks,groups,args.output,resume_from=args.resume_from)
    elif args.command=='score':
        result=score_batch(args.run)
    else:
        parser.error('choose --smoke, check, run, or score')
    print(json.dumps({k:v for k,v in result.items() if k not in ('reports','expected_ids','groups','config')},ensure_ascii=False))


if __name__ == '__main__':
    main()
