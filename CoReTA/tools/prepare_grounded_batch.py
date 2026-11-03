"""Offline-only three-arm preparation; no live execution entry point."""
import copy
import hashlib
import json
from pathlib import Path

from build_hiddenbench_dev import build, read
from coreta.workboard.choice_experiment import engine as baseline_engine, payload_for, input_sources
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.artifacts import ChoiceAdapter
from coreta.workboard.experiment_settings import settings
from coreta.workboard.gateway import Gateway
from coreta.workboard.grounded import GroundRunner, GroundContracts, GroundPrompts
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import Journal, write_json

IDS=(5,6,7,8)
METHODS=('ordinary_discussion','coreta_workboard','ground_full_public_v1')
OUT=PROJECT/'runs/grounded-three-arm-prepared-20261024-r1'
DATA=PROJECT/'data/task-packs/hiddenbench-grounded-dev-20261024-v1'
DOC=PROJECT/'refine-logs/evidence-before-application-20261024/BATCH_PLAN.md'


def variant_settings(n, legacy, method):
    value=settings(n,legacy,'coreta_workboard' if method=='ground_full_public_v1' else method)
    if method=='ground_full_public_v1':
        value['max_output_tokens']['ground']=value['max_output_tokens']['check_effect']
    return value


def engine(folder, packets, config, legacy, method, ordinal, counter, *, cache=None, transport=None):
    if method not in METHODS+('initial',): raise ValueError('Unknown method')
    if method!='ground_full_public_v1':
        return baseline_engine(folder,packets,config,legacy,method,ordinal,counter,cache=cache,transport=transport)
    adapter=ChoiceAdapter(packets.task)
    gateway=Gateway(config,variant_settings(len(packets.agents),legacy,method),GroundContracts(adapter),
                    GroundPrompts(),Journal(folder),token_counter=counter,transport=transport)
    return GroundRunner(packets,gateway,gateway.journal,adapter,task_ordinal=ordinal,initial_cache=cache)


def prepare():
    if OUT.exists() or DATA.exists(): raise ValueError('Use new output paths; never overwrite frozen inputs')
    # Search local request logs by both IDs and characteristic names, not by results.
    keys=['hb-dev-005','hb-dev-006','hb-dev-007','hb-dev-008',
          'Stevens','Prentice','Starlight Incorporated','schulz_hardt_mojzisch_2012']
    logs=sorted((PROJECT/'runs').rglob('requests.jsonl'))
    matches={}
    for path in logs:
        text=path.read_text(encoding='utf-8').lower()
        hits=[key for key in keys if key.lower() in text]
        if hits: matches[str(path.relative_to(PROJECT))]=hits
    if matches: raise ValueError('Selected tasks matched prior requests: '+json.dumps(matches))
    meta=build(DATA,dev_ids=IDS)
    config,legacy=configure(PROJECT/'config/deepseek_flash_inspection.json',DESIGN/'runtime.defaults.json')
    counter=load_counter()
    OUT.mkdir(parents=True)
    manifest=dict(kind='grounded_three_arm_development_v1',dataset=str(DATA),
        task_ids=list(IDS),methods=list(METHODS),pairs=[],max_http_attempts=0,max_output_tokens=0,
        model=config['model'],generation=config['generation'],network_requests=0,
        history_audit=dict(request_logs_scanned=len(logs),keys=keys,matches=matches,
            limitation='local retained requests only; qualitative task 006 has no unique name anchor'),
        scope='development_not_holdout_or_causal_component_estimate',settings={})
    for index, task in enumerate(meta['tasks']):
        packets=ChoicePackets(DATA/task['pack'],'distributed');n=len(packets.agents)
        manifest['settings'][str(n)]={m:variant_settings(n,legacy,m) for m in METHODS+('initial',)}
        for repeat in (1,2):
            ordinal=index+repeat;pair_id=f"{task['task_id']}-r{repeat}"
            shift=(2*index+repeat-1)%3
            order=list(METHODS[shift:]+METHODS[:shift])
            folder=OUT/pair_id;folder.mkdir()
            manifest['pairs'].append(dict(id=pair_id,task_id=task['task_id'],pack=str(DATA/task['pack']),
                members=n,repeat=repeat,ordinal=ordinal,editor=packets.agents[ordinal%n],methods=order))
            manifest['max_http_attempts']+=n+3*(n+1)**2
            manifest['max_output_tokens']+=n*4096+3*settings(n,legacy,'coreta_workboard')['limits']['max_output_tokens_total']
            initial=engine(folder,packets,config,legacy,'initial',ordinal,counter)
            for offset,member in enumerate(packets.agents):
                packet=initial.packet(member,'INITIAL')
                packet['BUDGET']['remaining_network_attempts']=n-offset
                write_json(folder/f'{member}.initial.request.json',payload_for(initial,'INITIAL',packet))
    manifest['source_hashes']=input_sources(DATA)
    for p in (Path(__file__),DOC):
        manifest['source_hashes'][str(p.resolve())]=hashlib.sha256(p.read_bytes()).hexdigest()
    manifest['prepared_hashes']={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest()
                                 for p in OUT.glob('*/*.request.json')}
    manifest['status']='inputs_and_schedule_frozen_no_live_executor'
    write_json(OUT/'manifest.json',manifest)
    print(json.dumps({k:manifest[k] for k in ('task_ids','max_http_attempts','max_output_tokens','status')}))


if __name__=='__main__': prepare()
