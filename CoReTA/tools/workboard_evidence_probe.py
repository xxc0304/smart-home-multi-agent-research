"""Three-condition public-excerpt diagnostic; hand focus is not autonomous retrieval."""
import argparse
import copy
import json
import os
import time
from pathlib import Path

from workboard_review_probe import read, hashes, packet_of
from coreta.handoff.__main__ import PROJECT, load_counter
from coreta.handoff.gateway import Journal, write_json
from coreta.handoff.contracts import HandoffContracts
from coreta.model_client import DeepSeekClient
from coreta.schemas import ProtocolError

PREVIOUS = PROJECT / 'runs/review-replacement-prepared-20261023-r1'
EXCERPTS = PROJECT / 'refine-logs/review-replacement-validation-20261023/EVIDENCE_VISIBILITY_DIAGNOSTIC.json'
DECISIONS = PROJECT / 'refine-logs/evidence-focus-validation-20261023/DECISIONS.md'
LOCAL_SCOPE = (
    'Local diagnostic scope: PUBLIC_VERSION_EXCERPTS contains partial verbatim public carrier text, '
    'not complete works or new source originals. Compare the supplied BEFORE and AFTER excerpts '
    'for changes in reported information, inferences, objects and evidential strength. Establish '
    'your own source access from SELF/SELF_MATERIALS. You cannot assess an omitted offer, full '
    'use_record, artifact or history; restrict finding and scope to the supplied excerpts. '
    'Identify any supported improvement or unsupported change, or say no issue within this scope; '
    'neither version is presumed true. Distinguish a report about an original from verification '
    'of that original. Do not infer which version to prefer merely from its position.'
)


def extract_payload(original, excerpts, local=False):
    p = packet_of(original)
    passages = copy.deepcopy(excerpts)
    old = p['BEFORE']['work_text']
    start = old.index('Cedar Station is therefore')
    end = old.index('Its drawbacks', start)
    passages.append({'version': p['BEFORE']['id'], 'author': p['BEFORE']['author'],
                     'field': 'work_text', 'access': 'visible_public_report_not_private_original',
                     'text': old[start:end].strip()})
    works = {w['id']: w for w in p['CANDIDATES']}
    for passage in passages:
        carrier = works[passage['version']]
        if passage['author'] != carrier['author'] or passage['text'] not in carrier['work_text']:
            raise ValueError('Excerpt not verbatim visible public work')
    prefix = original['instructions'].split('\nPACKET=', 1)[0]
    if local:
        version_pair = {'before': p['BEFORE']['id'], 'after': p['AFTER']['id']}
        p = {k: copy.deepcopy(p[k]) for k in ('TASK', 'SELF', 'SELF_MATERIALS', 'DIRECTORY', 'STAGE')}
        p['VERSION_PAIR'] = version_pair
        direct = ['T', *(m['ref'] for m in p['SELF_MATERIALS'])]
        public = sorted({x['version'] for x in passages})
        p['REFERENCE_INDEX'] = ([{'ref': r, 'kind': 'direct_original', 'access': 'direct_original'} for r in direct]
                                + [{'ref': r, 'kind': 'partial_public_work', 'access': 'public_report'} for r in public])
        p['SOURCE_ACCESS'] = {'direct_original_refs': sorted(direct), 'public_report_refs': public,
                              'reported_originals': [],
                              'partial_carriers_only': True}
        prefix += '\n' + LOCAL_SCOPE
    p['PUBLIC_VERSION_EXCERPTS'] = passages
    result = copy.deepcopy(original)
    schema_suffix = original['instructions'].split('\nOUTPUT_SCHEMA=', 1)[1]
    result['instructions'] = prefix + '\nPACKET=' + json.dumps(p, ensure_ascii=False) + '\nOUTPUT_SCHEMA=' + schema_suffix
    return result


def prepare(output):
    output = Path(output)
    if output.exists():
        raise ValueError('New preparation directory required')
    previous = read(PREVIOUS / 'manifest.json')
    for key in ('source_hashes', 'payload_hashes'):
        if hashes(previous[key]) != previous[key]:
            raise ValueError('Historical preparation changed')
    evidence = read(EXCERPTS)
    snippets = {row['input_id']: row['human_selected_public_excerpts'] for row in evidence['inputs']}
    config = previous['config']
    client = DeepSeekClient(config, lambda *args: None, token_counter=load_counter())
    items = [x for x in previous['inputs'] if '034' in x['task']]
    payloads = {}
    for item in items:
        original = read(PREVIOUS / (item['id'] + '--B.json'))
        payloads[item['id']] = {'F': original,
                               'H': extract_payload(original, snippets[item['id']]),
                               'L': extract_payload(original, snippets[item['id']], True)}
        item['input_estimates'] = {c: client.size(p) for c,p in payloads[item['id']].items()}
        if max(item['input_estimates'].values()) > config['generation']['max_input_tokens']:
            raise ValueError('Input exceeds configured limit')
    output.mkdir(parents=True, exist_ok=False)
    for item in items:
        for condition, payload in payloads[item['id']].items():
            write_json(output / f"{item['id']}--{condition}.json", payload)
    calls = []
    for ordinal, item in enumerate(items):
        for repeat in (1,2):
            shift = (ordinal + repeat - 1) % 3
            order = ('F','H','L')[shift:] + ('F','H','L')[:shift]
            for condition in order:
                calls.append({k: item[k] for k in ('id','task','system','stage','member')})
                calls[-1].update(condition=condition, repeat=repeat,
                                 payload_file=f"{item['id']}--{condition}.json")
    sources = [Path(__file__), PROJECT/'tools/workboard_review_probe.py', EXCERPTS, DECISIONS,
               PREVIOUS/'manifest.json', *map(Path,previous['source_hashes']),
               *[PREVIOUS/(item['id']+'--B.json') for item in items]]
    manifest = {'kind': 'human_focused_public_evidence_diagnostic', 'config': config,
                'scope': 'one_selected_task_correlated_inputs_not_efficacy',
                'conditions': ['F','H','L'], 'human_selected_evidence': True,
                'new_private_original_access': False, 'inputs':items,'calls':calls,
                'max_http_attempts':24,'max_output_tokens':73728,
                'transport_retries':0,'format_repairs':0,'sampling_seed_sent':False,
                'source_hashes': hashes(sources), 'payload_hashes': hashes(output.glob('*.json'))}
    write_json(output/'manifest.json',manifest)
    return manifest


def validate(prepared):
    manifest = read(Path(prepared)/'manifest.json')
    for key in ('source_hashes','payload_hashes'):
        if hashes(manifest[key]) != manifest[key]:
            raise ValueError('Frozen preparation changed: '+key)
    if (len(manifest['calls']),manifest['max_http_attempts'],manifest['max_output_tokens']) != (24,24,73728):
        raise ValueError('Unexpected diagnostic budget')
    return manifest


def run(prepared, output, transport=None):
    prepared, output = Path(prepared), Path(output)
    manifest = validate(prepared)
    if output.exists():
        raise ValueError('New output required; no resume')
    if transport is None and not os.environ.get('DEEPSEEK_API_KEY'):
        raise ValueError('Approved API credential unavailable')
    output.mkdir(parents=True,exist_ok=False)
    write_json(output/'manifest.json',manifest)
    journal=Journal(output)
    client=DeepSeekClient(manifest['config'],journal.log,transport=transport,token_counter=load_counter())
    progress={'kind':manifest['kind'],'status':'running',
              'transport_mode':'live' if transport is None else 'scripted_not_live',
              'completed':0,'actual_http_attempts':0,'transport_attempts':0,
              'input_tokens':0,'output_tokens':0,'unknown_usage_attempts':0,
              'rows':[dict(row,status='not_started') for row in manifest['calls']]}
    write_json(output/'progress.json',progress)
    for number,row in enumerate(progress['rows'],1):
        row['status']='running'
        journal.call_context={k:row[k] for k in ('task','system','stage','member','condition','repeat')}
        journal.call_context.update(logical_call=number,input_id=row['id'])
        write_json(output/'progress.json',progress)
        error=None
        try:
            if client.attempts>=24 or progress['output_tokens']+3072>73728:
                raise ProtocolError('BUDGET','Cannot reserve next request')
            payload=read(prepared/row['payload_file'])
            raw=client.complete(payload,deadline=time.monotonic()+120,logical_seed=16+row['repeat'])
            value=HandoffContracts.decode(raw,payload['text']['format']['schema'])
            if len(journal.usage)!=client.attempts or any(type(u.get(k)) is not int or u[k]<0
                for u in journal.usage for k in ('input_tokens','output_tokens')):
                raise ProtocolError('USAGE_UNKNOWN','Incomplete service usage')
            if journal.usage[-1]['output_tokens']>3072:
                raise ProtocolError('OUTPUT_BUDGET','Server stage cap exceeded')
            journal.log('stages.jsonl',{'output':value})
            journal.completed+=1
            row['status']='completed'
        except ProtocolError as exc:
            error={'code':exc.code,'detail':exc.detail}
        except Exception as exc:
            error={'code':'EXECUTION_ERROR','detail':type(exc).__name__}
        row['error']=error
        progress.update(completed=journal.completed,transport_attempts=client.attempts,
            actual_http_attempts=client.attempts if transport is None else 0,
            input_tokens=sum(u.get('input_tokens',0) for u in journal.usage if type(u.get('input_tokens')) is int),
            output_tokens=sum(u.get('output_tokens',0) for u in journal.usage if type(u.get('output_tokens')) is int),
            unknown_usage_attempts=client.attempts-sum(all(type(u.get(k)) is int and u[k]>=0
                for k in ('input_tokens','output_tokens')) for u in journal.usage))
        if error:
            row['status']='interrupted';progress['status']='stopped_on_first_error'
            write_json(output/'progress.json',progress)
            break
        write_json(output/'progress.json',progress)
    else:
        progress['status']='completed';write_json(output/'progress.json',progress)
    return progress


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action',choices=['prepare','run'])
    parser.add_argument('--prepared',type=Path)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if args.action=='prepare':
        result=prepare(args.output);keys=('kind','max_http_attempts','max_output_tokens')
    else:
        if not args.prepared or not args.live:parser.error('Explicit --prepared and --live required')
        result=run(args.prepared,args.output);keys=('kind','status','actual_http_attempts','completed')
    print(json.dumps({k:result[k] for k in keys}))
    return 2 if result.get('status')=='stopped_on_first_error' else 0


if __name__=='__main__':
    raise SystemExit(main())
