"""Offline engineering demonstrations only; never calls a model."""
import argparse
import json
from pathlib import Path

from expert_discussion import DiscussionSession, SoloSession, VOTE_RULE
from expert_discussion_scoring import compare_session

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'implement-stage/expert-preparation-20261030'


def smoke():
    # HAND-AUTHORED FIXTURE: this is not an observed MuSiQue/model result.
    task = dict(id='SMOKE_ONLY', question='When was School X established?', paragraphs=[
        dict(idx=0, title='School X', paragraph_text='School X was established in 1900.')])
    session = DiscussionSession(task, expert_actor='M1', disclosure='known_expert',
                                seed=20261030, vote_rule=VOTE_RULE, fixture=True)
    answer = json.dumps(dict(answer='1900', support_idxs=[0], reasoning='Hand-authored fixture.'))
    while (request := session.next_request()) is not None:
        text = ('HAND-AUTHORED turn: the paragraph states 1900.'
                if request['stage'] == 'discussion' else answer)
        session.submit(request['request_id'], raw_output=text)
    assert session.complete and len(session.records) == 24
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / 'discussion_smoke.json').write_text(
        json.dumps(session.trace(), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return session, task


def verify():
    from prepare_expert_mechanism import controlled_scoring
    from tokenizers import Tokenizer

    session, task = smoke()
    solo = SoloSession.from_team(session)
    while (req := solo.next_request()) is not None:
        text = ('HAND-AUTHORED independent reflection.' if req['stage'] == 'reflection' else
                json.dumps(dict(answer='1900', support_idxs=[0], reasoning='Hand-authored final.')))
        solo.submit(req['request_id'], raw_output=text)
    gold = dict(id=task['id'], answer='1900', answer_aliases=[], answerable=True,
                paragraphs=[dict(idx=0, is_supporting=True)])
    comparison = compare_session(session, gold, solo)
    assert comparison['status'] == 'COMPLETE_PAIRED' and not comparison['primary_comparison_enabled']
    (OUT / 'paired_smoke.json').write_text(json.dumps(dict(team=session.trace(), solo=solo.trace(),
        scoring=comparison), ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    legacy_folder = ROOT / 'data/expert-mechanism-inputs-20261030-v0.2/demos'
    legacy_task = json.loads((legacy_folder / 'LEGACY_interface_task.json').read_text(encoding='utf-8'))
    bundle = json.loads((legacy_folder / 'LEGACY_initial_bundle.json').read_text(encoding='utf-8'))
    originals = {r['actor']: r for r in bundle['records']}
    for row in originals.values():
        assert (ROOT / row['original_raw_path']).read_text(encoding='utf-8') == row['original_raw_output']
    legacy = DiscussionSession(legacy_task, expert_actor='M1', disclosure='hidden', seed=20261030,
                               vote_rule=VOTE_RULE, fixture=True)
    legacy.kind = 'LEGACY_SCHEMA_ADAPTER_COMPATIBILITY_FIXTURE'
    while (req := legacy.next_request()) is not None:
        row = originals[req['actor']]
        # Old responses are replayed, not new replies to the generated discussion.
        raw = row['original_raw_output'] if req['stage'] == 'discussion' else row['raw_output']
        legacy.submit(req['request_id'], raw_output=raw)
    assert legacy.complete
    (OUT / 'legacy_compatibility_smoke.json').write_text(json.dumps(dict(
        trace=legacy.trace(), source_records=bundle['records'],
        limit='Old initial responses reused as messages/finals solely for interface checks; no interactive new-task evidence.'),
        ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

    source = ROOT / 'data/external/musique-v1.0-20261030'
    with (source / 'scoring/D_development.jsonl').open(encoding='utf-8') as handle:
        score_target = json.loads(next(handle))
    _, _, parity = controlled_scoring(score_target)
    assert len(parity['official_parity']) == 6

    tokenizer = Tokenizer.from_file(str(ROOT / 'data/external/qwen3-4b-tokenizer-20261030/tokenizer.json'))
    with (source / 'inputs/D_development.jsonl').open(encoding='utf-8') as handle:
        development = [json.loads(line) for line in handle]
    def tokens(payload):
        return len(tokenizer.encode(payload['system'] + '\n' + payload['user'], add_special_tokens=False).ids)
    # Longest base D payload, with complete old responses standing in for each public message.
    longest = max(development, key=lambda t: tokens(DiscussionSession(t, expert_actor='M1',
        disclosure='hidden', seed=20261030, vote_rule=VOTE_RULE, fixture=True).next_request()['payload']))
    pressure = DiscussionSession(longest, expert_actor='M1', disclosure='hidden', seed=20261030,
                                 vote_rule=VOTE_RULE, fixture=True)
    pressure.kind = 'LONG_INPUT_LEGACY_LENGTH_FIXTURE'
    measurements = []
    while (req := pressure.next_request()) is not None:
        measurements.append(dict(stage=req['stage'], round=req['round'], actor=req['actor'],
                                 input_tokens_without_chat_template=tokens(req['payload'])))
        pressure.submit(req['request_id'], raw_output=originals[req['actor']][
            'original_raw_output' if req['stage'] == 'discussion' else 'raw_output'])
    result = dict(verdict='PASS_OFFLINE_ENGINEERING_ONLY', actual_model_calls=0, training_runs=0,
        H_question_or_target_files_read=0, team_generations=24, extra_solo_generations=5,
        old_original_responses_verified=4, legacy_replay_messages=24,
        official_score_cases=parity['official_parity'], primary_comparison_enabled=False,
        pressure=dict(task_id=longest['id'], measurements=measurements,
            max_input_tokens_without_chat_template=max(m['input_tokens_without_chat_template'] for m in measurements),
            scope='Reference tokenizer only; old messages reused; no chat/reasoning/output reserve; neither real fit measurement nor worst-case bound.'),
        execution_verdict='DO_NOT_RUN_UNTIL_BACKEND_AND_CONTRACT_PREFLIGHT',
        limits=['No real new-task discussion or expert advantage demonstrated.',
                'No trained adapter, model client, deployment, or paid run.',
                'Identity and vote configurations are explicit candidates, not a frozen campaign contract.',
                'Training-side V distribution differs; independent C calibration still required.'])
    (OUT / 'PREFLIGHT_OFFLINE.json').write_text(json.dumps(result, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--smoke', action='store_true')
    parser.add_argument('--verify', action='store_true')
    args = parser.parse_args()
    if args.verify:
        result = verify()
        print(json.dumps(dict(verdict=result['verdict'], actual_model_calls=0,
                              pressure_input_tokens=result['pressure']['max_input_tokens_without_chat_template'])))
    elif args.smoke:
        session, _ = smoke()
        print(json.dumps(dict(status=session.trace()['status'], n_recorded=len(session.records),
                              evidence_type=session.kind, actual_model_calls=0)))
    else:
        parser.error('choose --smoke or --verify')


if __name__ == '__main__':
    main()
