"""Prepare new-instance source packets and plan offline. No API execution."""
import hashlib
import json
import re
from pathlib import Path
from tokenizers import Tokenizer
import receiver_target_view as presentation
import prepare_receiver_baseline_20261026 as previous
import local_judgment_frontend as io

ROOT=io.ROOT
OUT=ROOT/'research/receiver-confirmation-20261026-v1'


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def build_task(identifier,scenario,shared,private,options):
    task=dict(task_id=identifier,scenario=scenario,shared_information=shared,
              choices=[dict(id=f'option_{i+1}',text=x) for i,x in enumerate(options)],
              instruction='Follow the decision requirement in the task and explain genuine unresolved conditions.')
    public=[dict(ref='TASK',content=scenario)]+[dict(ref=f'PUBLIC.{i+1}',content=x) for i,x in enumerate(shared)]
    members={f'A{i+1}':dict(task=task,member=f'A{i+1}',public_sources=public,
        own_sources=[dict(ref=f'PRIVATE.A{i+1}',content=text)]) for i,text in enumerate(private)}
    return task,members


def main():
    if OUT.exists(): raise ValueError('new preparation directory required')
    source=ROOT/'data/task-source-audit-20261021/hiddenbench.json'
    split=io.read(ROOT/'data/dataset-selection-20261022/SELECTION_MANIFEST.json')
    assert digest(source)==split['source_sha256']
    records={r['id']:r for r in io.read(source)}
    ids=[30,33]
    assert all(n in split['development_ids'] for n in ids)
    # No outcome files are consulted to select tasks. This only searches submitted input logs.
    norm=lambda x:re.sub('[^a-z0-9]','',x.lower())
    needles={n:norm(records[n]['description'][:120]) for n in ids}
    paths=list((ROOT/'runs').rglob('requests.jsonl'))
    hits={str(n):[] for n in ids}
    for path in paths:
        hay=norm(path.read_text(encoding='utf-8',errors='replace'))
        for n,needle in needles.items():
            if needle in hay:hits[str(n)].append(path.relative_to(ROOT).as_posix())
    if any(hits.values()): raise ValueError('candidate exposure found; inspect instead of silently replacing')
    OUT.mkdir(parents=True)
    roster=[]
    for n in ids:
        raw=records[n]
        task,members=build_task(f'hb-receiver-confirm-{n:03d}',raw['description'],raw['shared_information'],
                               raw['hidden_information'],raw['possible_answers'])
        assert len(members)==3
        folder=OUT/'benchmark'/f'{n:03d}'
        for member,packet in members.items():io.write(folder/'members'/f'{member}.json',packet)
        io.write(folder/'public_draft_input.json',dict(task=task,public_sources=next(iter(members.values()))['public_sources']))
        io.write(folder/'offline/reference.json',dict(correct_option_id=next(c['id'] for c in task['choices'] if c['text']==raw['correct_answer']),
            metric='reference_choice_match_secondary_to_semantic_application'))
        roster.append(dict(id=task['task_id'],kind='public_benchmark_new_to_recorded_requests',members=3,
            setup_calls=4,paired_calls=12,initial_draft='one new public-only model draft, same for both arms and all receivers',
            contributions='three new independent local contributions, one per native member; originals disclosed by host equally'))

    controls=[dict(id='control-correct-with-wrong-report',
        scenario='At 16:00 today assign exactly one chamber for eight sealed display pieces. The chamber must hold all eight pieces, be open for this event at 16:00, and have a documented current temperature between 15 and 20 C. Select the best supported eligible chamber; do not invent future repairs.',
        shared=['Cedar can hold six pieces. Birch and Elm can each hold eight pieces.','Readiness and current temperature must be checked against the supplied updates.'],
        private=['Cedar is open at 16:00 with a current temperature of 18 C, but its capacity remains six pieces.',
                 'Birch will not reopen until 16:30 today; its current temperature is 18 C.',
                 'Elm passed its inspection at 15:40 today. It is open for the 16:00 event, holds eight pieces, and its current logged temperature is 18 C.'],
        options=['Cedar','Birch','Elm'],draft=dict(choice='option_3',reasoning='Elm is open for 16:00, has capacity eight and a current 18 C reading. Cedar lacks capacity and Birch opens too late.'),
        report=dict(origin='fallible_prior_check',claim='Elm is unavailable at 16:00 because its inspection occurred at 15:40.',ready=False),
        evaluation=dict(expected_choice='option_3',purpose='preserve correct draft and reject mistaken earlier-than-start exclusion',synthetic=True)),
        dict(id='control-genuinely-underdetermined',
        scenario='Assign a sealed batch to a certified machine for processing today. A valid choice requires capacity at least 120 units and a calibration certificate valid today. Do not authorize a machine without evidence that its certificate is valid; if the available records do not establish an eligible choice, report that the choice cannot be determined.',
        shared=['Machines Quartz, Topaz and Opal are candidates. Records are complete only for the facts explicitly supplied.'],
        private=['Quartz has capacity 110 and a certificate valid today.',
                 'Topaz has capacity 150. Its certificate exists, but the supplied record does not show its expiry date or whether it is valid today.',
                 'Opal has capacity 140. Its certificate status for today is absent from all supplied records.'],
        options=['Quartz','Topaz','Opal'],draft=dict(choice=None,reasoning='Quartz lacks capacity. Topaz and Opal have sufficient capacity but their current certificate validity is not established, so no eligible choice can be authorized from these records.'),
        report=None,evaluation=dict(expected_choice=None,purpose='retain genuine insufficiency rather than force a choice',synthetic=True))]
    for control in controls:
        task,members=build_task(control['id'],control['scenario'],control['shared'],control['private'],control['options'])
        contributions={m:dict(text=x['own_sources'][0]['content'],disclosed_originals=x['own_sources']) for m,x in members.items()}
        for member,packet in members.items():
            context=dict(**packet,shared_contributions=contributions,execution_report=control['report'],
                historical_work=control['draft'],historical_author='CONTROL_AUTHOR')
            io.write(OUT/'controls'/control['id']/f'{member}.json',context)
        io.write(OUT/'offline_controls'/f"{control['id']}.json",control['evaluation'])
        roster.append(dict(id=control['id'],kind='authored_control_not_benchmark_score',members=3,setup_calls=0,
            paired_calls=12,initial_draft='fixed authored control',contributions='fixed authored source carriers'))

    tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    audits=[]
    original_prepared=ROOT/'runs/receiver-baseline-prepared-20261026-r3'
    for path in sorted((original_prepared/'contexts').rglob('*.json')):
        context=io.read(path)
        view=presentation.present(context)
        assert presentation.restore(view)==context
        requests=[presentation.first_request(context,m) for m in ['ordinary','diagnose']]
        assert io.strict_json(requests[0]['instructions'].split('PACKET=',1)[1])==io.strict_json(requests[1]['instructions'].split('PACKET=',1)[1])
        # Replay the actual first output belonging to this task and receiver, no gold diagnostic.
        live=ROOT/'runs/receiver-baseline-live-20261026-r1'
        rows=io.read(live/'review.json')['rows']
        actual=next(r for r in rows if r['task']==path.parent.name and r['receiver']==path.stem and r['method']=='diagnose' and r['stage']=='first')
        raw=(live/f"{actual['slot']:03d}.raw.txt").read_text(encoding='utf-8')
        decoded=previous.decode_first(raw)
        final=presentation.final_request(context,decoded)
        assert presentation.restore(io.strict_json(final['instructions'].split('PACKET=',1)[1]))==context
        audits.append(dict(task=path.parent.name,receiver=path.stem,roundtrip_lossless=True,
            paired_packets_equal=True,old_first_semantics_not_certified=True,
            final_input_estimate=len(tok.encode(final['instructions']+json.dumps(final['schema'])).ids)+256))
    assert len(audits)==16
    for path in (OUT/'controls').rglob('*.json'):
        context=io.read(path)
        assert presentation.restore(presentation.present(context))==context
    io.write(OUT/'EXPOSURE_AUDIT.json',dict(recorded_request_logs_scanned=len(paths),hits=hits,
        method='normalized first 120 description characters in saved request logs',
        limitation='No hit is not proof against undocumented use or pretrained-model exposure.'))
    io.write(OUT/'PLAN.json',dict(status='source_packets_and_design_only_not_live_ready',tasks=roster,
        proposed_max_requests=sum(r['setup_calls']+r['paired_calls'] for r in roster),
        formation_calls=sum(r['setup_calls'] for r in roster),paired_calls=sum(r['paired_calls'] for r in roster),
        output_cap_per_request=1536,proposed_total_output_cap=56*1536,proposed_total_input_cap=786432,
        repeats_per_condition=1,receiver_policy='all native members; three in each chosen task, no fictitious fourth expert',
        scientific_scope='new benchmark-instance application confirmation plus separately scored synthetic controls',
        no_auto_expand=True))
    io.write(OUT/'LOCAL_CHECKS.json',dict(new_api_calls=0,old_real_context_checks=audits,
        maximum_replay_input_estimate=max(r['final_input_estimate'] for r in audits),
        control_contexts_checked=6,
        limitations=['Lossless representation and full real-text carrier replay do not prove reduction of semantic object confusion.',
                    'No new draft or member response has been generated; no fake result or automatic success score.']))
    io.write(OUT/'SOURCE_MANIFEST.json',dict(source_sha256=digest(source),ids=ids,
        split='existing development pool; no final evaluation pool consumed',
        code_sha256={str(Path(x).relative_to(ROOT)).replace('\\','/'):digest(Path(x)) for x in [__file__,presentation.__file__]},
        files={x.relative_to(OUT).as_posix():digest(x) for x in OUT.rglob('*.json')}))
    print(json.dumps(dict(status='offline_prepared',benchmark_tasks=2,native_members_each=3,controls=2,
        maximum_proposed_requests=56,formation_calls=8,paired_calls=48,lossless_real_contexts=16,new_api_calls=0)))


if __name__=='__main__':main()
