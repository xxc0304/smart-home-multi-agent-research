"""Scripted length/schema stress checks with real tokenizer; not service compatibility."""
import argparse
import json
import tempfile
from pathlib import Path
from unittest.mock import patch

from prepare_issue_loop_comparison import DATA, ARCHIVE, METHODS, read, engine
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.handoff.gateway import write_json
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.issue_loop import CHECK_STAGES, CHOICE_STAGES


def response(packet, method, issues_per_check=0):
    stage = packet['STAGE']
    if stage == 'OBSERVE':
        return dict(action='offer', offer=dict(target=packet['CURRENT_WORK']['id'],
            knowledge='SCRIPTED: compare the evidence with the relevant task criterion.',
            support=[dict(ref='T', excerpt='SCRIPTED evidence placeholder, not a true quotation.')],
            proposed_use='SCRIPTED: revise the affected reasoning and preserve other evidence.',
            claims=[dict(statement='SCRIPTED claim to check', premises='SCRIPTED visible premises', source_refs=['T'])]))
    if stage == 'GROUND':
        return dict(assessments={c['id']: dict(status='unresolved', reason='SCRIPTED limits; no truth certification.',
            evidence_refs=['T']) for c in packet['CLAIMS']}, limits='SCRIPTED check only')
    if stage in {'TRY', 'FINALIZE'}:
        return dict(action='new', candidate_id=None, reason=None, declared_sources=['T'],
            work=dict(artifact='option_2', work_text='SCRIPTED revision: evidence is acknowledged but weighting remains disputed.',
                      open_points=['SCRIPTED unresolved comparison']),
            use_record='SCRIPTED: revised the affected comparison; inspect actual output for remaining defects.')
    if stage in CHECK_STAGES:
        value = dict(finding='no_issue_found', observation='SCRIPTED inspection of evidence and downstream choice.',
                     scope='SCRIPTED current revision only')
        if method == METHODS[1]:
            issues = [dict(concern=f'SCRIPTED issue {packet["AFTER"]["id"]}/{i}: the evidence does not justify the stated comparison.',
                location=packet['AFTER']['id'], kind='reasoning', evidence_refs=['T'],
                consequence='SCRIPTED: this assumption may change the selected option; compare against the explicit task requirement.')
                for i in range(issues_per_check)]
            value.update(issues=issues, rechecks={row['issue_id']: dict(status='persists',
                reason='SCRIPTED: the revision names the objection but does not supply evidence for the disputed comparison.',
                evidence_refs=['T']) for row in packet['ISSUES_TO_RECHECK']})
            if issues or value['rechecks']:
                value['finding'] = 'issue'
        return value
    if stage in CHOICE_STAGES:
        value = dict(candidate_id=packet['CHOICES'][-1], reason='SCRIPTED best-effort choice with recorded limits.')
        if method == METHODS[1]:
            value['issue_dispositions'] = {ref: dict(disposition='unresolved',
                reason='SCRIPTED: this evidence-weighting objection remains open; the available versions do not resolve it.')
                for ref in packet['REQUIRED_ISSUE_IDS']}
        return value
    raise ValueError(stage)


def audit(output):
    config, legacy = configure(PROJECT/'config/deepseek_flash_inspection.json', DESIGN/'runtime.defaults.json')
    counter = load_counter()
    profiles = []
    for task, ordinal in (('hb-dev-005', 1), ('hb-dev-006', 2)):
        packets = ChoicePackets(DATA/task, 'distributed')
        cache = read(ARCHIVE/(task+'-r1')/'initial/cache.json')
        archived_state = read(ARCHIVE/(task+'-r1')/'ground_full_public_v1/state.json')
        archived_works = {w['id']: w for w in archived_state['works']}
        for method in METHODS:
            for count in ((0,) if method == METHODS[0] else (0, 1, 3, 5)):
                measurements = []
                with tempfile.TemporaryDirectory() as folder, patch('urllib.request.urlopen', side_effect=AssertionError('No network')):
                    def transport(payload, timeout):
                        packet = json.loads(payload['instructions'].split('\nPACKET=', 1)[1].split('\nOUTPUT_SCHEMA=', 1)[0])
                        text = json.dumps(response(packet, method, count), ensure_ascii=False)
                        if packet['STAGE'] in {'TRY', 'FINALIZE'}:
                            value = json.loads(text)
                            if task == 'hb-dev-005':
                                ref = 'W7' if packet['STAGE'] == 'FINALIZE' else 'W'+str(4+packet['BUDGET']['cycle'])
                            else:
                                ref = 'W4'
                            work = archived_works[ref]
                            value['work'] = {key: work[key] for key in ('artifact', 'work_text', 'open_points')}
                            text = json.dumps(value, ensure_ascii=False)
                        tokens = counter(text)
                        measurements.append(dict(stage=packet['STAGE'], input_tokens=runner.gateway.client.size(payload),
                            output_tokens=tokens, output_cap=payload['max_output_tokens']))
                        return dict(status='completed', usage=dict(input_tokens=measurements[-1]['input_tokens'], output_tokens=tokens),
                            output=[dict(type='message', content=[dict(type='output_text', text=text)])])
                    runner = engine(Path(folder), packets, config, legacy, method, ordinal, cache, counter, transport)
                    result = runner.run()
                exceeded = [r for r in measurements if r['output_tokens'] > r['output_cap']]
                profiles.append(dict(task_id=task, method=method, new_issues_per_check=count,
                    status=result['status'], calls=len(measurements),
                    max_input_tokens=max(r['input_tokens'] for r in measurements),
                    max_output_ratio=max(r['output_tokens']/r['output_cap'] for r in measurements),
                    exceeded_stages=exceeded, error=result['error'],
                    pass_within_caps=result['status']=='completed' and not exceeded))
    report = dict(kind='scripted_load_audit_not_model_quality', network_requests=0, profiles=profiles,
        all_profiles_pass=all(p['pass_within_caps'] for p in profiles),
        limits='Synthetic concise issue/recheck replies with real historical revision text; not a universal length bound or proof of live JSON compatibility. Historical revisions used only offline, never supplied to the live comparison.')
    output.parent.mkdir(parents=True, exist_ok=True)
    write_json(output, report)
    print(json.dumps(dict(profiles=len(profiles), all_profiles_pass=report['all_profiles_pass'], network_requests=0)))
    return report


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--output', type=Path, required=True)
    audit(parser.parse_args().output)
