"""Prepare source-only ten-task screening; no model calls or gold-derived fields."""
import argparse
import json
import random
import re
from pathlib import Path
from order_calibration import ROOT,read,write,sha

IDS=[10,11,15,18,20,21,22,23,26,27]
MEANINGS={
 'safe_for_task':'Safe for the particular people, objects, activities and time window stated in the task; a possible risk is not automatically a confirmed prohibition.',
 'accessible_for_task':'At least one usable access or transport method exists for the stated group or cargo within the task time window; one blocked route does not prove all routes blocked.',
 'ready_for_task':'Currently ready, or explicitly ready by the required start, for the stated use; reputation, equipment ownership or beginning preparation alone does not confirm readiness.',
 'full_duration_supported':'Can support the stated use for its required duration; do not invent a duration or equate temporary backup with adequate full-duration support.',
 'distribution_possible':'Supplies can be moved from this candidate to the intended communities in the task time window; landing at the site alone does not establish onward distribution.',
 'catering_permitted':'The kind of catering required by the task is permitted; limited snacks or unrelated food permission are not automatically sufficient.',
 'group_capacity_sufficient':'Can accommodate the full group size specified by the task for its intended use; historical attendance alone is not current capacity confirmation.',
 'heavy_infrastructure_supported':'The site can support the heavy laboratory infrastructure stated in the task under the stated conditions; potential reinforcement is not completed reinforcement.'}
FIELDS={
 10:['safe_for_task','accessible_for_task','distribution_possible'],
 11:['safe_for_task','ready_for_task','full_duration_supported'],
 15:['safe_for_task','accessible_for_task','ready_for_task','full_duration_supported'],
 18:['safe_for_task','accessible_for_task','full_duration_supported'],
 20:['safe_for_task','accessible_for_task','full_duration_supported'],
 21:['safe_for_task','accessible_for_task','ready_for_task'],
 22:['safe_for_task','accessible_for_task','full_duration_supported'],
 23:['accessible_for_task','ready_for_task','catering_permitted','group_capacity_sufficient'],
 26:['safe_for_task','accessible_for_task','ready_for_task'],
 27:['safe_for_task','accessible_for_task','full_duration_supported','heavy_infrastructure_supported']}
EXCLUDED={12:'already used in live development',13:'culprit deduction needs a different inference representation',
 14:'mixed preferences and group dietary suitability; deferred from this feasibility scope',
 16:'main distinctions are uncertain comparative risks, not explicit failed prerequisites',
 17:'four choices; preserve current three-choice screening scope',
 19:'requires composing closures across multiple access routes; deferred rather than host-precomputed',
 24:'security of offline delivery versus network connectivity needs a separate subsystem representation',
 25:'four choices; preserve current three-choice screening scope'}


def exposure_audit(records):
    normalize=lambda x:re.sub('[^a-z0-9]','',x.lower())
    needles={i:normalize(records[i]['description'][:110]) for i in IDS}
    hits={str(i):[] for i in IDS};paths=list((ROOT/'runs').rglob('requests.jsonl'))
    for path in paths:
        hay=normalize(path.read_text(encoding='utf-8',errors='replace'))
        for number,needle in needles.items():
            if needle in hay:hits[str(number)].append(str(path.relative_to(ROOT)))
    return dict(files_scanned=len(paths),method='normalized first 110 description characters in saved request logs; not proof against undocumented exposure',hits=hits)


def prepare(output):
    if output.exists():raise ValueError('new directory required')
    source=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
    split=read(ROOT/'data/dataset-selection-20261022/SELECTION_MANIFEST.json')
    if sha(source)!=split['source_sha256']:raise ValueError('source changed')
    records={int(r['id']):r for r in read(source)}
    audit=exposure_audit(records)
    if any(audit['hits'].values()):raise ValueError('selected task appears in previous request logs; inspect rather than silently replace')
    output.mkdir(parents=True);write(output/'EXPOSURE_AUDIT.json',audit);roster=[]
    for number in IDS:
        r=records[number]
        if len(r['hidden_information'])!=4 or len(r['possible_answers'])!=3:raise ValueError('native team/choice mismatch')
        folder=output/f'candidate-{number:03d}';folder.mkdir()
        choices=list(r['possible_answers']);random.Random(f'candidate-screening-v1-{number}').shuffle(choices)
        options=[dict(id=f'option_{i+1}',text=value) for i,value in enumerate(choices)]
        task=dict(task_id=f'candidate-screening-{number:03d}',scenario=r['description'],
                  shared_information=r['shared_information'],choices=options,
                  instruction='Choose one option from the available evidence. Explain limits and unresolved interpretations.')
        public=[dict(ref='TASK',content=r['description'])]+[dict(ref=f'PUBLIC.{i+1}',content=x) for i,x in enumerate(r['shared_information'])]
        write(folder/'task.json',task);write(folder/'public_sources.json',public)
        for i,text in enumerate(r['hidden_information']):
            owner=f'A{i+1}'
            write(folder/(owner+'.json'),dict(member=owner,task=task,public_sources=public,
                  own_sources=[dict(ref=f'S{i+1:02d}',content=text)]))
        write(folder/'proposed_encoding.json',dict(fields=FIELDS[number],
              field_meanings={f:MEANINGS[f] for f in FIELDS[number]},value_types=['boolean','null'],
              field_values_provided_by_host=False,field_requirements_provided_by_host=False,
              note='Manual task vocabulary supplied equally to both arms; representation-assisted screening, not automatic schema discovery.'))
        (folder/'offline').mkdir()
        write(folder/'offline/label.json',dict(official_correct_text=r['correct_answer'],
              correct_option_id=next(o['id'] for o in options if o['text']==r['correct_answer']),
              source_name=r['name'],metric='official_choice_match_not_semantic_validation'))
        roster.append(dict(source_id=number,directory=folder.name,members=4,choices=3,
              former_split='evaluation_pool',current_role='screening_development_not_final_holdout'))
    files={p.relative_to(output).as_posix():sha(p) for p in output.rglob('*.json')}
    write(output/'SOURCE_MANIFEST.json',dict(status='source_packets_only_not_ready_for_live',roster=roster,
          source_sha256=sha(source),source_revision=split['hf_revision'],files=files,
          preparation_code_sha256=sha(Path(__file__)),exclusions=EXCLUDED,
          selection='Ascending source IDs 10..27; native four-member three-choice current-use candidate selection, representable by local boolean requirements; exclusions explicit, no outcome-based replacement.',
          proposed_calls=120,proposed_output_cap=368640,
          limitations=['manually reviewed convenience subset, not random benchmark sample',
                       'mostly urgent candidate-selection tasks; not broad task-family generalization',
                       'host vocabulary assists both arms; source information not guaranteed to make all members indispensable',
                       'source text may contain ambiguity; official option correctness and semantic faithfulness scored separately']))


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('output',type=Path)
    prepare(parser.parse_args().output)
