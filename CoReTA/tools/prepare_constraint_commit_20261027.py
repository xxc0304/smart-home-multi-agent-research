"""Offline full historical replay and paired request preparation. No API client."""
import copy
import json
from pathlib import Path
from jsonschema import Draft202012Validator
from tokenizers import Tokenizer
import local_judgment_frontend as io
from coreta.constraint_commit import session_from_receiver, CommitError
import constraint_commit_probe as probe

ROOT=io.ROOT
SOURCE=ROOT/'runs/inference-link-prepared-20261027-r3'
OUT=ROOT/'research/constraint-commit-prototype-20261027-v1'
NUMERIC=dict(age='number',sex='string',vehicle_context='string',driver_vehicle='string',license_years='number',
    drank_spirits='boolean',measured_alcohol='number',speed_kmh='number',role='string',inattentive='boolean')
SPECS=[('004-identity',NUMERIC),('011-time-supported',dict(safe_for_task='boolean',ready_for_task='boolean',full_duration_supported='boolean')),
       ('023-notice',dict(accessible_for_task='boolean',ready_for_task='boolean',catering_permitted='boolean',group_capacity_sufficient='boolean'))]


def prepare():
    if (OUT/'LOCAL_REPLAY.json').exists():raise ValueError('preserve existing replay; use a new version')
    index={r['case_id']:r for r in io.read(SOURCE/'CASE_INDEX.json')}
    tok=Tokenizer.from_file(str(ROOT/'data/tokenizer-v4.1-flash-1017/tokenizer.json'))
    results=[];lineage=[];counts=[]
    for cid,types in SPECS:
        source=SOURCE/'cases'/(cid+'.json');case=io.read(source);context=case['receiver_context']
        original_raw=ROOT/index[cid]['answer_path'];raw=original_raw.read_text(encoding='utf-8')
        assert io.digest(original_raw)==index[cid]['answer_sha256']
        requests=[];paired=[]
        for mode in probe.METHODS:
            session=session_from_receiver(context,types)
            req=probe.request(context,session,mode)
            Draft202012Validator.check_schema(req['schema'])
            requests.append(req)
            io.write(OUT/'request_examples'/cid/(mode+'.json'),req)
            result=probe.process(raw,context,session,mode,1)
            assert result['action']['status']=='not_proposed'
            paired.append(result)
            io.write(OUT/'historical_replay'/cid/(mode+'.json'),result)
            body=json.dumps(req,ensure_ascii=False,separators=(',',':'))
            counts.append(dict(case=cid,method=mode,input_estimate=len(tok.encode(body,add_special_tokens=False).ids)+256))
        assert probe.packet(requests[0])==probe.packet(requests[1])
        assert requests[0]['schema']==requests[1]['schema']
        assert paired[0]['report']==paired[1]['report']
        assert paired[0]['model_answer']==paired[1]['model_answer']
        assert not [r for r in paired[0]['report']['admission'] if r['status']=='not_executable']
        results.append(dict(case_id=cid,model_choice=paired[0]['model_answer']['choice'],
            reference_delivery=paired[0]['delivery']['choice'],constraint_delivery=paired[1]['delivery']['choice'],
            remaining=paired[1]['delivery']['not_excluded'],mode='deterministic_replay_of_old_outputs_not_new_model_experiment'))
        lineage.append(dict(case_path=source.relative_to(ROOT).as_posix(),case_sha256=io.digest(source),
            raw_path=original_raw.relative_to(ROOT).as_posix(),raw_sha256=io.digest(original_raw)))
        # Wrong-encoding withdrawal is an explicit manual mechanical control only.
        if cid=='011-time-supported':
            session=session_from_receiver(context,types);before=session.report()
            assert before['not_excluded']==[]
            target=session.entries['A4.F1']
            assert target['value']['field']=='ready_for_task' and target['value']['value'] is False
            evidence=next(k for k,v in session.evidence.items() if target['value']['quote'] in v['text'])
            update=dict(entry_id='A4.F1',action='retire',reason='MANUAL MECHANICAL CONTROL: withdraw the current-readiness interpretation; no model repair claimed.',evidence_ids=[evidence])
            event=session.revise([update],1);after=session.report()
            assert after['not_excluded']==['option_1']
            assert after['model_fact_table']['option_1']['ready_for_task'] is None
            try:session.deliver(io.strict_json(raw),'constraint_commit',1)
            except CommitError:pass
            else:raise AssertionError('stale final accepted')
            session.revise([dict(update,action='restore',reason='MANUAL MECHANICAL CONTROL: restore original erroneous interpretation.')],2)
            assert session.report()['not_excluded']==[]
            io.write(OUT/'manual_controls/011-withdrawal-and-restoration.json',dict(
                kind='manual_control_not_model_success',before=before,withdrawal=event,after=after,restored=session.report()))
    evidence=dict(status='offline_replay_passed',new_api_calls=0,full_real_final_bodies=3,
        full_real_contribution_pools=3,paired_input_and_report_equality=True,request_counts=counts,
        results=results,source_lineage=lineage,
        mechanical_control='Manual A4.F1 withdrawal/restoration only; not generated correction or a paid result.',
        limitation='Historical finals were not generated under this new prompt and had no updates. This is not a comparative model-effect estimate or live preflight.')
    io.write(OUT/'LOCAL_REPLAY.json',evidence)
    code=['src/coreta/constraint_commit.py','src/coreta/workboard/candidate_probe.py',
          'tools/constraint_commit_probe.py','tools/prepare_constraint_commit_20261027.py',
          'tools/minimal_final_answer_contract.py','tools/local_judgment_frontend.py','tests/test_constraint_commit.py']
    for name in code:
        dest=OUT/'frozen_source'/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((ROOT/name).read_bytes())
    io.write(OUT/'SOURCE_SNAPSHOT.json',dict(kind='offline_snapshot_not_paid_manifest',
        code_sha256={name:io.digest(ROOT/name) for name in code},source_lineage=lineage,
        files={x.relative_to(OUT).as_posix():io.digest(x) for x in OUT.rglob('*') if x.is_file()}))
    print(json.dumps(dict(status=evidence['status'],new_api_calls=0,results=results,max_input=max(x['input_estimate'] for x in counts)),ensure_ascii=False))

if __name__=='__main__':prepare()
