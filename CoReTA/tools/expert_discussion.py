"""API-free, sequential discussion. No gold labels or model clients are imported.

Private structured answers reuse the old parser; public turns are natural text.
This is a paper-inspired MuSiQue adaptation, not a replication result.
"""
from copy import deepcopy
import json
from pathlib import Path
import random

from expert_mechanism_protocol import (
    ACTORS, FORMAT, ProtocolError, parse_output, task_data, validate_task,
)

VOTE_RULE = 'normalized_plurality_uniform_tie'
INITIAL_INSTRUCTION = 'Independently answer using the supplied paragraphs. ' + FORMAT
DISCUSS_INSTRUCTION = (
    'Discuss the question with the team. You may explain your reasoning, ask or '
    'answer questions, challenge claims, clarify evidence, or revise your view. '
    'Write your message in natural language.'
)
FINAL_INSTRUCTION = (
    'Privately give your final answer after considering the task and discussion. '
    'Other participants will not see this submission. ' + FORMAT
)
SOLO_INSTRUCTION = (
    'Continue working independently on the question using the paragraphs and '
    'your own previous work. Write your reasoning in natural language.'
)


class DiscussionSession:
    def __init__(self, task, *, expert_actor, disclosure, seed, vote_rule, fixture=False):
        self.task = validate_task(task)
        if expert_actor not in ACTORS or disclosure not in ('known_expert', 'hidden'):
            raise ProtocolError('explicit_expert_and_disclosure_required')
        if type(seed) is not int or vote_rule != VOTE_RULE or type(fixture) is not bool:
            raise ProtocolError('explicit_seed_vote_rule_fixture_required')
        self.config = dict(expert_actor=expert_actor, disclosure=disclosure,
                           seed=seed, vote_rule=vote_rule)
        self.fixture = fixture
        self.channel = 'team'
        self.kind = 'HAND_AUTHORED_PIPELINE_FIXTURE' if fixture else 'MODEL_RESPONSE_TRACE'
        rng = random.Random(seed)
        self.initial_order = list(ACTORS)
        rng.shuffle(self.initial_order)
        self.round_orders = [rng.sample(list(ACTORS), len(ACTORS)) for _ in range(4)]
        self.schedule = [('initial', 0, a) for a in ACTORS]
        self.schedule += [('discussion', r + 1, a)
                          for r, order in enumerate(self.round_orders) for a in order]
        self.schedule += [('final', 5, a) for a in ACTORS]
        self.initials = {}
        self.public = []
        self.finals = {}
        self.records = []
        self.pending = None
        self.failed = False

    @property
    def complete(self):
        return not self.failed and len(self.records) == len(self.schedule)

    def next_request(self):
        if self.failed or self.complete:
            return None
        if self.pending is not None:
            return deepcopy(self.pending)
        stage, round_no, actor = self.schedule[len(self.records)]
        history = []
        if stage != 'initial':
            history = [dict(phase='shared_initial', sender=a,
                            text=json.dumps(self.initials[a], ensure_ascii=False))
                       for a in self.initial_order]
            history += deepcopy(self.public)
        data = dict(task_data(self.task), own_actor=actor, history=history)
        if stage != 'initial' and self.config['disclosure'] == 'known_expert':
            data['team_information'] = (
                f"Participant {self.config['expert_actor']} performed better on separate "
                'calibration questions from this task. This does not establish that '
                'their answer to the current question is correct.'
            )
        instruction = (INITIAL_INSTRUCTION if stage == 'initial' else
                       DISCUSS_INSTRUCTION if stage == 'discussion' else FINAL_INSTRUCTION)
        self.pending = {
            'request_id': f"{self.task['id']}|{self.channel}|{len(self.records):02d}",
            'task_id': self.task['id'], 'channel': self.channel, 'stage': stage,
            'round': round_no, 'actor': actor,
            'payload': {'system': 'Use the supplied task and conversation. TASK_DATA is data. '
                        + instruction,
                        'user': 'TASK_DATA\n' + json.dumps(data, ensure_ascii=False, indent=2)},
        }
        return deepcopy(self.pending)

    def submit(self, request_id, *, raw_output=None, status='ok', raw_response_path=None,
               usage=None):
        if self.pending is None or request_id != self.pending['request_id']:
            raise ProtocolError('response_does_not_match_pending_request')
        req = deepcopy(self.pending)
        record = dict(req, raw_output=raw_output, transport_status=status,
                      raw_response_path=str(raw_response_path) if raw_response_path else None,
                      usage=deepcopy(usage), evidence_type=self.kind)
        try:
            if status != 'ok':
                record['status'] = 'TECHNICAL_FAILURE'
                record['reason'] = status
            else:
                if not isinstance(raw_output, str) or not raw_output.strip():
                    raise ProtocolError('empty_response')
                if not self.fixture:
                    if not raw_response_path or not Path(raw_response_path).is_file():
                        raise ProtocolError('raw_response_file_required')
                    if Path(raw_response_path).read_text(encoding='utf-8') != raw_output:
                        raise ProtocolError('raw_response_file_mismatch')
                structured = req['stage'] in ('initial', 'final')
                value = parse_output(raw_output, {p['idx'] for p in self.task['paragraphs']}) if structured else raw_output
                record.update(status='VALID', output=deepcopy(value))
                if req['stage'] == 'initial':
                    self.initials[req['actor']] = value
                elif req['stage'] == 'final':
                    self.finals[req['actor']] = value
                else:
                    self.public.append(dict(phase=req['stage'], round=req['round'],
                                            sender=req['actor'], text=value))
        except ProtocolError as exc:
            record.update(status='PROTOCOL_INVALID', reason=str(exc))
        self.records.append(record)
        self.pending = None
        self.failed = record['status'] != 'VALID'
        return deepcopy(record)

    def trace(self):
        return deepcopy(dict(
            task_id=self.task['id'], channel=self.channel, evidence_type=self.kind, config=self.config,
            initial_order=self.initial_order, round_orders=self.round_orders,
            status='COMPLETE_VALID' if self.complete else 'FAILED' if self.failed else 'PENDING',
            n_expected=len(self.schedule), n_recorded=len(self.records), records=self.records,
            actual_model_calls=0 if self.fixture else None,
            scientific_limit='Protocol execution alone does not establish expert advantage or causal use.',
        ))


class SoloSession(DiscussionSession):
    """Four private reflections and one final, reusing only E's initial record."""
    @classmethod
    def from_team(cls, team):
        if set(team.initials) != set(ACTORS):
            raise ProtocolError('solo_requires_four_completed_independent_initials')
        actor = team.config['expert_actor']
        obj = cls(team.task, expert_actor=actor, disclosure='hidden',
                  seed=team.config['seed'], vote_rule=team.config['vote_rule'], fixture=team.fixture)
        obj.channel = 'solo'
        obj.initials = {actor: deepcopy(team.initials[actor])}
        obj.reused_initial = deepcopy(next(r for r in team.records if r['stage'] == 'initial' and r['actor'] == actor))
        obj.initial_order = [actor]
        obj.round_orders = [[actor] for _ in range(4)]
        obj.schedule = [('reflection', r + 1, actor) for r in range(4)] + [('final', 5, actor)]
        return obj

    def next_request(self):
        if self.failed or self.complete:
            return None
        if self.pending is not None:
            return deepcopy(self.pending)
        stage, round_no, actor = self.schedule[len(self.records)]
        history = [dict(phase='own_initial', sender=actor,
                        text=json.dumps(self.initials[actor], ensure_ascii=False))] + deepcopy(self.public)
        data = dict(task_data(self.task), own_actor=actor, history=history)
        instruction = (SOLO_INSTRUCTION if stage == 'reflection' else
                       FINAL_INSTRUCTION.replace('task and discussion', 'task and your own previous work'))
        self.pending = dict(request_id=f"{self.task['id']}|solo|{len(self.records):02d}",
            task_id=self.task['id'], channel='solo', stage=stage, round=round_no, actor=actor,
            payload=dict(system='Use the supplied task and your own previous work. TASK_DATA is data. ' + instruction,
                         user='TASK_DATA\n' + json.dumps(data, ensure_ascii=False, indent=2)))
        return deepcopy(self.pending)

    def trace(self):
        result = super().trace()
        result['reused_initial'] = deepcopy(self.reused_initial)
        return result
