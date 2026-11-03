"""Freeze executor, scoring references, schedule and initial requests offline."""
import hashlib
import json
from pathlib import Path

from prepare_grounded_batch import DATA, METHODS, engine, variant_settings
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import write_json
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import input_sources, payload_for

OUT=PROJECT/'runs/grounded-three-arm-prepared-20261024-r6'
DOC=PROJECT/'refine-logs/evidence-before-application-20261024'

GUARDS={
 'hb-dev-005': ['Fundraising involvement is not proof of personal fundraising success.',
   'Qualitative hiring criteria do not define a unique numerical weighting.',
   'Personal background facts do not by themselves establish job suitability.'],
 'hb-dev-006': ['No explicit equal-weight trait-count rule is supplied.',
   'Keep each positive/negative trait attached to the right candidate.',
   'Candidate C has positive private traits despite negative shared traits.'],
 'hb-dev-007': ['No proposal satisfies all a-j across the complete supplied materials.',
   'Repeated reports of one criterion are one fact, not independent votes.',
   'Starlight fails a/c; Franklin fails a/b/c/i/j; Cape fails b/f/g/h.',
   'Preferred by official key does not mean feasible under every criterion as a hard constraint.'],
 'hb-dev-008': ['Eddie hearing difficulty challenges reliability; it does not prove deliberate lying.',
   'Cafe footage covers 6:30-6:45; later golf sighting has imprecise time.',
   'Direct cafe-to-golf travel time does not supply an exact route via the house.',
   'Fingerprints have an alternative reported explanation; motive alone does not prove guilt.']}


def references():
    tasks=[]
    for task_id,guards in GUARDS.items():
        task=json.loads((DATA/task_id/'public/task.json').read_text(encoding='utf-8'))
        blocks=[dict(ref='T:scenario',text=task['scenario'])]
        blocks += [dict(ref=f'T:shared:{i}',text=text) for i,text in enumerate(task['shared_information'],1)]
        for path in sorted((DATA/task_id/'packets/distributed').glob('A*.json')):
            p=json.loads(path.read_text(encoding='utf-8'))
            blocks += [dict(ref=m['ref'],owner=p['SELF']['agent_id'],text=m['content']) for m in p['SELF_MATERIALS']]
        for block in blocks:
            block['lines']=[dict(line=i,text=line) for i,line in enumerate(block['text'].splitlines(),1)]
        tasks.append(dict(task_id=task_id,blocks=blocks,interpretation_limits=guards))
    return dict(kind='offline_only_source_reference_not_oracle',tasks=tasks,
        rules=dict(support=['explicit','supported_inference','unsupported','contradicted','uncertain'],
          unit='Atomic decision-relevant claim linked to its subject and conditions; retain combined-premise reasoning.',
          dedup='One subject/relation/condition claim per trajectory; repeated wording tracked as occurrences, not new facts.',
          applied='A later reasoning step or artifact actually relies on it; mere citation or approval is not application.',
          retained='Still used or explicitly preserved in the selected final work; repetition alone is insufficient.',
          error_opportunity='An unsupported/contradicted consequential proposal appears before application; absent => N/A.',
          correction='Trace whether recognized, applied correctly and retained; these are separate outcomes.',
          denominator='Per trajectory opportunities; do not compare conditional rates as equal-difficulty samples.',
          uncertainty='Disputed semantic classifications remain uncertain; do not silently count as errors.',
          control='Use the same claim units for ordinary discussion and both CoReTA variants.'))


def freeze(output=OUT):
    output=Path(output)
    if output.exists(): raise ValueError('New freeze directory required')
    meta=json.loads((DATA/'dataset_manifest.json').read_text(encoding='utf-8'))
    if meta['ids']!=[5,6,7,8]: raise ValueError('Unexpected roster')
    config,legacy=configure(PROJECT/'config/deepseek_flash_inspection.json',DESIGN/'runtime.defaults.json')
    counter=load_counter();output.mkdir(parents=True)
    write_json(output/'OFFLINE_PROCESS_REFERENCE.json',references())
    write_json(output/'ANNOTATION_TEMPLATE.json',dict(rows=[],required_row_fields=[
        'unit_id','claim_id','claim','occurrences','source_locations','support_status',
        'application_before','application_after','applied','retained','error_opportunity',
        'recognized','new_error','uncertainty_reason'],
        instructions='No automatic semantic scoring. Source references are offline only. Preserve quoted evidence and mark uncertain.'))
    manifest=dict(kind='grounded_three_arm_development_v3',config=config,dataset=str(DATA),pairs=[],settings={},
        max_http_attempts=0,max_output_tokens=0,phase_limits={},scoring_feedback=False,
        pilot_advance_rule='technical_completion_only; no automatic continuation',
        format_policy=dict(identical_duplicate_keys='collapse only when JSON values are exactly equal',
            conflicting_duplicate_keys='reject and stop',api_retry='none',audit_log='format_repairs.jsonl'),
        network_requests=0,status='frozen_not_run')
    for index,task in enumerate(meta['tasks']):
        pack=DATA/task['pack'];packets=ChoicePackets(pack,'distributed');n=len(packets.agents)
        manifest['settings'][str(n)]={m:variant_settings(n,legacy,m) for m in METHODS+('initial',)}
        for repeat in (1,2):
            pair_id=f"{task['task_id']}-r{repeat}";folder=output/pair_id;folder.mkdir()
            shift=(2*index+repeat-1)%3
            phase='pilot' if task['task_id'] in ('hb-dev-005','hb-dev-006') and repeat==1 else 'remainder'
            pair=dict(id=pair_id,task_id=task['task_id'],pack=str(pack),members=n,repeat=repeat,
                      ordinal=index+repeat,methods=list(METHODS[shift:]+METHODS[:shift]),phase=phase)
            manifest['pairs'].append(pair)
            limit=manifest['phase_limits'].setdefault(phase,dict(max_http_attempts=0,max_output_tokens=0))
            calls=n+3*(n+1)**2;tokens=n*4096+3*manifest['settings'][str(n)]['coreta_workboard']['limits']['max_output_tokens_total']
            limit['max_http_attempts']+=calls;limit['max_output_tokens']+=tokens
            manifest['max_http_attempts']+=calls;manifest['max_output_tokens']+=tokens
            initial=engine(folder,packets,config,legacy,'initial',pair['ordinal'],counter)
            for offset,member in enumerate(packets.agents):
                packet=initial.packet(member,'INITIAL');packet['BUDGET']['remaining_network_attempts']=n-offset
                write_json(folder/f'{member}.initial.request.json',payload_for(initial,'INITIAL',packet))
    manifest['source_hashes']=input_sources(DATA)
    for path in (Path(__file__),PROJECT/'tools/run_grounded_batch.py',PROJECT/'tools/prepare_grounded_batch.py',
                 PROJECT/'tools/score_grounded_batch.py',DOC/'BATCH_PLAN_V3.md',DOC/'FORMAT_FAILURE_REVIEW.md'):
        manifest['source_hashes'][str(path.resolve())]=hashlib.sha256(path.read_bytes()).hexdigest()
    files=list(output.glob('*/*.request.json'))+[output/'OFFLINE_PROCESS_REFERENCE.json',output/'ANNOTATION_TEMPLATE.json']
    manifest['prepared_hashes']={str(p.relative_to(output)):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
    write_json(output/'manifest.json',manifest)
    return manifest


if __name__=='__main__':
    m=freeze();print(json.dumps(dict(pairs=len(m['pairs']),phase_limits=m['phase_limits'],network_requests=0)))
