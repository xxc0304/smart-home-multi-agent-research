"""Gold-free vote selection plus descriptive official-score comparisons.

Vote selection never receives a target or gold aliases. The selected member's
support is only a representative's support, not a merged team evidence set.
"""
from copy import deepcopy
import random

from expert_mechanism_protocol import ACTORS, ProtocolError
from score_expert_mechanism import score_one, transitions
from metrics.answer import normalize_answer


def aggregate_votes(outputs, *, seed):
    if set(outputs) != set(ACTORS) or type(seed) is not int:
        raise ProtocolError('vote_requires_all_four_and_explicit_seed')
    groups, abstained = {}, []
    for actor in ACTORS:
        answer = outputs[actor]['answer']
        key = normalize_answer(answer) if answer is not None else ''
        if not key:
            abstained.append(actor)
        else:
            groups.setdefault(key, []).append(actor)
    if not groups:
        return dict(answer=None, selected_actor=None,
            output=dict(answer=None, support_idxs=[], reasoning='All members abstained.'),
            winning_groups=[], winning_actors=[], abstained=abstained, tie=False,
            vote_counts={}, selection_kind='HOST_VOTE_NOT_MODEL_OUTPUT')
    count = max(map(len, groups.values()))
    winners = sorted(k for k, v in groups.items() if len(v) == count)
    rng = random.Random(seed)
    selected_group = rng.choice(winners)
    actor = rng.choice(groups[selected_group])
    return dict(answer=outputs[actor]['answer'], selected_actor=actor,
        output=deepcopy(outputs[actor]), winning_groups=winners,
        winning_actors=[a for k in winners for a in groups[k]], abstained=abstained,
        tie=len(winners) > 1, vote_counts={k: len(v) for k, v in groups.items()},
        selection_kind='HOST_VOTE_NOT_MODEL_OUTPUT')


def vote_expected_metrics(vote, outputs, target):
    actors = vote['winning_actors']
    metrics = [score_one(outputs[a], target) for a in actors] if actors else [score_one(vote['output'], target)]
    return {key: sum(m[key] for m in metrics) / len(metrics)
            for key in ('answer_em', 'answer_f1', 'support_em', 'support_f1')}


def compare_session(team, target, solo=None):
    if target['id'] != team.task['id']:
        raise ProtocolError('scoring_target_task_mismatch')
    report = dict(task_id=team.task['id'], evidence_type=team.kind,
        status='INCOMPLETE_NO_PRIMARY_SUMMARY', primary_comparison_enabled=False,
        n_expected_team=24, n_recorded_team=len(team.records), comparisons=None,
        scientific_limit='Descriptive trajectories do not identify causal conformity or actual contribution use.')
    if not team.complete:
        return report
    expert = team.config['expert_actor']
    seed = team.config['seed']
    initial_vote = aggregate_votes(team.initials, seed=seed + 101)
    final_vote = aggregate_votes(team.finals, seed=seed + 102)
    report.update(status='COMPLETE_TEAM_DESCRIPTIVE', primary_comparison_enabled=False,
        comparisons=dict(
            expert_initial=score_one(team.initials[expert], target),
            initial_vote=score_one(initial_vote['output'], target),
            expert_team_final=score_one(team.finals[expert], target),
            team_final_vote=score_one(final_vote['output'], target)),
        member_transitions={a: transitions(team.initials[a], team.finals[a], target) for a in ACTORS},
        expert_to_team_selection=transitions(team.initials[expert], final_vote['output'], target),
        initial_vote=initial_vote, final_vote=final_vote,
        initial_vote_expected=vote_expected_metrics(initial_vote, team.initials, target),
        final_vote_expected=vote_expected_metrics(final_vote, team.finals, target),
        support_scope='Selected representative support, not independently constructed team evidence.')
    if solo is not None:
        if (solo.task != team.task or solo.config['expert_actor'] != expert or
                solo.fixture != team.fixture or solo.initials.get(expert) != team.initials[expert]):
            raise ProtocolError('solo_team_pair_mismatch')
        report.update(n_expected_solo=5, n_recorded_solo=len(solo.records))
        if not solo.complete:
            report.update(status='INCOMPLETE_SOLO_NO_PRIMARY_SUMMARY',
                          primary_comparison_enabled=False, comparisons=None)
        else:
            report['status'] = 'COMPLETE_PAIRED'
            report['primary_comparison_enabled'] = not team.fixture
            report['comparisons']['expert_solo_final'] = score_one(solo.finals[expert], target)
            report['expert_solo_transition'] = transitions(team.initials[expert], solo.finals[expert], target)
    return report
