"""Frozen three-arm batches. Scoring files are never opened by this executor."""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path

from prepare_grounded_batch import engine, variant_settings, METHODS
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import write_json
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import payload_for
from coreta.schemas import ProtocolError


def read(path): return json.loads(Path(path).read_text(encoding='utf-8'))
def digest(path): return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(prepared):
    manifest=read(prepared/'manifest.json')
    if manifest['kind']!='grounded_three_arm_development_v3': raise ValueError('Expected v3 batch')
    for name,sha in manifest['source_hashes'].items():
        if digest(name)!=sha: raise ValueError('Stale source/input: '+name)
    for name,sha in manifest['prepared_hashes'].items():
        target=(prepared/name).resolve()
        if not target.is_relative_to(prepared.resolve()): raise ValueError('Prepared path escapes root')
        if digest(target)!=sha: raise ValueError('Changed prepared input: '+name)
    config,legacy=configure(PROJECT/'config/deepseek_flash_inspection.json',DESIGN/'runtime.defaults.json')
    if config!=manifest['config']: raise ValueError('Configuration changed')
    for n,values in manifest['settings'].items():
        if values!={m:variant_settings(int(n),legacy,m) for m in METHODS+('initial',)}:
            raise ValueError('Frozen budgets do not match engine')
    return manifest,config,legacy


def run(prepared, output, *, phase, prior=None, transport_factory=None, counter=None):
    prepared=Path(prepared).resolve();output=Path(output).resolve()
    manifest,config,legacy=verify(prepared)
    if phase not in ('pilot','remainder'): raise ValueError('Explicit phase required')
    sha=digest(prepared/'manifest.json')
    if phase=='remainder':
        if prior is None: raise ValueError('Remainder requires completed pilot directory')
        receipt=read(Path(prior)/'progress.json')
        if (receipt.get('status')!='completed' or receipt.get('phase')!='pilot'
                or receipt.get('manifest_sha256')!=sha): raise ValueError('Pilot receipt mismatch')
        expected=[p['id'] for p in manifest['pairs'] if p['phase']=='pilot']
        if receipt.get('completed_pairs')!=expected: raise ValueError('Pilot pair roster incomplete')
        if receipt.get('unknown_usage'): raise ValueError('Pilot usage incomplete')
        for pair in (p for p in manifest['pairs'] if p['phase']=='pilot'):
            rows=[r for r in receipt.get('units',[]) if r.get('pair')==pair['id']]
            if (len(rows)!=4 or {r.get('method') for r in rows}!={'initial',*METHODS}
                    or any(r.get('status')!='completed' for r in rows)):
                raise ValueError('Pilot unit roster incomplete')
            cache=read(Path(prior)/pair['id']/'initial/cache.json')
            cache_sha=hashlib.sha256(json.dumps(cache,sort_keys=True).encode()).hexdigest()
            if any(r.get('cache_sha256')!=cache_sha for r in rows): raise ValueError('Pilot cache changed')
            for method in METHODS:
                result=read(Path(prior)/pair['id']/method/'result.json')
                if result.get('status')!='completed' or result.get('incomplete_or_unknown_usage_attempts')!=0:
                    raise ValueError('Pilot result incomplete')
        # No reuse of model outputs between pairs or phases.
    pairs=[p for p in manifest['pairs'] if p['phase']==phase]
    cap=sum(p['members']+3*(p['members']+1)**2 for p in pairs)
    output_cap=sum(p['members']*4096+3*manifest['settings'][str(p['members'])]['coreta_workboard']['limits']['max_output_tokens_total'] for p in pairs)
    if output.exists(): raise ValueError('New output required; no overwrite or implicit resume')
    output.mkdir(parents=True)
    write_json(output/'manifest.json',manifest)
    progress=dict(phase=phase,status='running',manifest_sha256=sha,http_attempts=0,output_tokens=0,
        max_http_attempts=cap,max_output_tokens=output_cap,completed_pairs=[],units=[],
        unknown_usage=False,input_tokens=0,format_repairs=0)
    counter=counter or load_counter()

    def persist(): write_json(output/'progress.json',progress)

    def attach(runner):
        call=runner.gateway.call
        def bounded(stage,member,packet):
            if progress['unknown_usage']: raise ProtocolError('USAGE_UNKNOWN','Batch accounting incomplete')
            if progress['http_attempts']>=cap: raise ProtocolError('ATTEMPT_BUDGET','Phase request cap')
            if progress['output_tokens']+runner.gateway.outputs[stage.lower()]>output_cap:
                raise ProtocolError('OUTPUT_BUDGET','Phase output cap')
            before=runner.gateway.client.attempts;offset=len(runner.journal.usage)
            repairs_before=runner.journal.repairs
            try:
                return call(stage,member,packet)
            finally:
                count=runner.gateway.client.attempts-before
                usage=runner.journal.usage[offset:]
                progress['http_attempts']+=count
                progress['format_repairs']+=runner.journal.repairs-repairs_before
                known=(len(usage)==count and all(type(u.get(k)) is int and u[k]>=0
                       for u in usage for k in ('input_tokens','output_tokens')))
                if not known: progress['unknown_usage']=True
                else:
                    progress['output_tokens']+=sum(u['output_tokens'] for u in usage)
                    progress['input_tokens']+=sum(u['input_tokens'] for u in usage)
                persist()
        runner.gateway.call=bounded
        return runner

    def make(folder,packets,method,pair,cache=None):
        folder.mkdir(parents=True)
        transport=transport_factory(dict(pair=pair['id'],system=method)) if transport_factory else None
        return attach(engine(folder,packets,config,legacy,method,pair['ordinal'],counter,
                             cache=cache,transport=transport))

    try:
        for pair in pairs:
            packets=ChoicePackets(Path(pair['pack']),'distributed')
            n=len(packets.agents)
            if n!=pair['members'] or packets.task['task_id']!=pair['task_id']: raise ValueError('Roster mismatch')
            folder=output/pair['id']
            row=dict(pair=pair['id'],method='initial',status='running');progress['units'].append(row)
            initial=make(folder/'initial',packets,'initial',pair)
            cache=dict(origin=str(folder/'initial'),member_packet_hashes=packets.hashes,candidates={})
            for index,member in enumerate(packets.agents):
                packet=initial.packet(member,'INITIAL')
                packet['BUDGET']['remaining_network_attempts']=n-index
                if payload_for(initial,'INITIAL',packet)!=read(prepared/pair['id']/f'{member}.initial.request.json'):
                    raise ValueError('Initial request differs from frozen payload')
                cache['candidates'][member]=initial.gateway.call('INITIAL',member,packet)
            cache_sha=hashlib.sha256(json.dumps(cache,sort_keys=True).encode()).hexdigest()
            write_json(folder/'initial/cache.json',cache)
            row.update(status='completed',cache_sha256=cache_sha)
            for method in pair['methods']:
                row=dict(pair=pair['id'],method=method,status='running',cache_sha256=cache_sha)
                progress['units'].append(row);persist()
                runner=make(folder/method,packets,method,pair,copy.deepcopy(cache))
                result=runner.run()
                row.update(status=result['status'],http_attempts=result['http_attempts'],error=result['error'])
                if result['status']!='completed' or progress['unknown_usage']:
                    raise ProtocolError('DEVELOPMENT_STOP',f"Technical interruption: {pair['id']}/{method}")
                # The supplied initial cache is immutable; future methods receive no peer continuations.
                if hashlib.sha256(json.dumps(cache,sort_keys=True).encode()).hexdigest()!=cache_sha:
                    raise ValueError('Shared initial cache mutated')
            progress['completed_pairs'].append(pair['id']);persist()
        progress['status']='completed'
    except Exception as exc:
        if progress['units'] and progress['units'][-1]['status']=='running':
            progress['units'][-1]['status']='interrupted'
        progress.update(status='stopped_on_first_technical_error',error=dict(type=type(exc).__name__,detail=str(exc)))
        raise
    finally:
        persist()
    return progress


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--prepared',type=Path,required=True)
    parser.add_argument('--output',type=Path,required=True)
    parser.add_argument('--phase',choices=['pilot','remainder'],required=True)
    parser.add_argument('--prior',type=Path)
    parser.add_argument('--live',action='store_true')
    args=parser.parse_args()
    if not args.live or not os.environ.get('DEEPSEEK_API_KEY'): parser.error('Requires --live and configured API key')
    value=run(args.prepared,args.output,phase=args.phase,prior=args.prior)
    print(json.dumps(dict(status=value['status'],http_attempts=value['http_attempts'])))
