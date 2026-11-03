"""Source packets for two new candidate tasks; not an API experiment manifest."""
import argparse
import hashlib
import random
from pathlib import Path
from order_calibration import ROOT,read,write,sha


FIELDS={9:['ambulance_accessible','critical_care_available'],
        12:['accessible','safe_for_evacuation','prepared_for_immediate_evacuation',
            'open_for_emergency_evacuation','power_available']}


def prepare(output):
    if output.exists():raise ValueError('new directory required')
    output.mkdir(parents=True)
    source=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
    split=read(ROOT/'data/dataset-selection-20261022/SELECTION_MANIFEST.json')
    if sha(source)!=split['source_sha256']:raise ValueError('source snapshot changed')
    records={int(r['id']):r for r in read(source)}
    roster=[]
    for number in [9,12]:
        r=records[number];folder=output/f'candidate-{number:03d}';folder.mkdir()
        choices=list(r['possible_answers']);random.Random(f'candidate-transfer-pilot-v1-{number}').shuffle(choices)
        options=[dict(id=f'option_{i+1}',text=value) for i,value in enumerate(choices)]
        task=dict(task_id=f'candidate-transfer-{number:03d}',scenario=r['description'],
            shared_information=r['shared_information'],choices=options,
            instruction='Choose one option from the available evidence. Explain limits and unresolved interpretations.')
        public=[dict(ref='TASK',content=r['description'])]+[
            dict(ref=f'PUBLIC.{i+1}',content=value) for i,value in enumerate(r['shared_information'])]
        write(folder/'task.json',task);write(folder/'public_sources.json',public)
        team=[f'A{i+1}' for i in range(len(r['hidden_information']))]
        for i,owner in enumerate(team):
            write(folder/(owner+'.json'),dict(member=owner,task=task,public_sources=public,
                own_sources=[dict(ref=f'S{i+1:02d}',content=r['hidden_information'][i])]))
        write(folder/'proposed_encoding.json',dict(fields=FIELDS[number],value_types=['boolean','null'],
            field_values_provided_by_host=False,field_requirements_provided_by_host=False,
            conflicts='unknown; no automatic private-source priority or majority vote',
            facts='public or own private source with exact quote; no access to other originals',
            conditions='mandatory goals from TASK or own source; preferences remain caveats'))
        offline=folder/'offline';offline.mkdir()
        write(offline/'label.json',dict(official_correct_text=r['correct_answer'],
            correct_option_id=next(o['id'] for o in options if o['text']==r['correct_answer']),
            source_name=r['name'],metric='official_choice_match_not_proof_of_all_encoded_conditions'))
        roster.append(dict(source_id=number,directory=folder.name,members=len(team),choices=len(options),
            former_split='evaluation_pool',current_role='new_development_pilot_not_final_holdout'))
    files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*.json')}
    write(output/'SOURCE_MANIFEST.json',dict(status='source_packets_only_not_ready_for_live',roster=roster,
        source_sha256=sha(source),source_revision=split['hf_revision'],files=files,
        selection='explicit named candidate states/goals; no model outcome consulted',
        runtime_requests=0,proposed_calls=24,proposed_output_cap=73728,
        limitations=['two emergency-decision instances, not broad domain generalization',
                     'content reviewed by experiment designer, not secret or model-pretraining-unseen',
                     'automatic conditions and inferred risk judgments may still be wrong']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    prepare(parser.parse_args().output)
