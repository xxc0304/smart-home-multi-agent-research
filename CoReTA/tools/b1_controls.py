"""Two-round, four-arm protocol. No models or gold in request construction."""
from copy import deepcopy
import json
import random

from b0_answers import answer_text, answer_score, paired_interval, write_json
from metrics.answer import normalize_answer
from expert_mechanism_protocol import ACTORS, task_data, validate_task
from prepare_answer_only_expert import SYSTEM

ARMS = ('A', 'B', 'C', 'D')
PUBLIC = ('B', 'D')
REVEALED = ('C', 'D')
WORK = ('Continue solving this question using the supplied material and visible history. '
        'You may explain reasons, raise questions, challenge claims, add information '
        'from the supplied material, or revise your judgment. Write in natural language.')
FINAL = 'Give only your final short answer to the question.'


class Trial:
    def __init__(self, task, *, expert_actor, seed=20261102, task_index=0, fixture=False):
        self.task = validate_task(task)
        if (expert_actor not in ACTORS or type(seed) is not int or type(fixture) is not bool
                or type(task_index) is not int or task_index < 0):
            raise ValueError('explicit_expert_seed_fixture_required')
        self.config = dict(expert_actor=expert_actor, seed=seed, task_index=task_index, fixture=fixture)
        self.base_seed = seed + task_index * 10000
        rng = random.Random(self.base_seed)
        self.initial_order = rng.sample(list(ACTORS), 4)
        self.orders = [rng.sample(list(ACTORS), 4) for _ in range(2)]
        self.schedule = [('initial', None, 0, actor) for actor in ACTORS]
        for arm in ARMS:
            self.schedule += [('work', arm, r + 1, actor) for r, order in enumerate(self.orders) for actor in order]
            self.schedule += [('final', arm, 3, actor) for actor in ACTORS]
        self.cursor = 0
        self.initials = {}
        self.work = {arm: [] for arm in ARMS}
        self.finals = {arm: {} for arm in ARMS}
        self.failed = set()
        self.initial_failed = False
        self.records = []
        self.pending = None

    def next_request(self):
        if self.initial_failed:
            return None
        if self.pending is not None:
            return deepcopy(self.pending)
        while self.cursor < len(self.schedule):
            stage, arm, round_no, actor = self.schedule[self.cursor]
            if arm not in self.failed:
                break
            self.cursor += 1
        if self.cursor == len(self.schedule):
            return None
        data = dict(task_data(self.task))
        if stage != 'initial':
            initial_actors = self.initial_order if arm in PUBLIC else [actor]
            history = [dict(sender=a, phase='initial', text=self.initials[a]) for a in initial_actors]
            history += [deepcopy(m) for m in self.work[arm] if arm in PUBLIC or m['sender'] == actor]
            data.update(own_actor=actor, history=history,
                work_visibility='team_message' if arm in PUBLIC else 'private_work')
            if arm in REVEALED:
                data['team_information'] = (f'Participant {self.config["expert_actor"]} performed better '
                    'on separate calibration questions from this task. This does not establish '
                    'that their answer to the current question is correct.')
        stage_seed = (0 if stage == 'initial' else 1000 + round_no * 100 if stage == 'work' else 2000)
        self.pending = dict(request_id=f'{self.task["id"]}|{self.cursor:02d}', arm=arm,
            stage=stage, round=round_no, actor=actor,
            seed=self.base_seed + stage_seed + ACTORS.index(actor),
            max_new_tokens=512 if stage == 'work' else 64,
            payload=dict(system=SYSTEM if stage == 'initial' else WORK if stage == 'work' else FINAL,
                user='TASK_DATA\n' + json.dumps(data, ensure_ascii=False, indent=2)))
        return deepcopy(self.pending)

    def submit(self, request_id, raw_output, *, status='OK', usage=None, source_kind=None):
        if self.pending is None or request_id != self.pending['request_id']:
            raise ValueError('response_request_mismatch')
        req = deepcopy(self.pending)
        if not self.config['fixture'] and source_kind != 'ACTUAL_LOCAL_MODEL_RESPONSE':
            raise ValueError('real_response_origin_required')
        if status == 'OK' and not isinstance(raw_output, str):
            status = 'NON_TEXT_OUTPUT'
        record = dict(**req, raw_output=raw_output, status=status, usage=deepcopy(usage),
                      source_kind=source_kind, fixture=self.config['fixture'])
        self.records.append(record)
        if status != 'OK':
            if req['stage'] == 'initial':
                self.initial_failed = True
            else:
                self.failed.add(req['arm'])
        elif req['stage'] == 'initial':
            self.initials[req['actor']] = raw_output
        elif req['stage'] == 'work':
            self.work[req['arm']].append(dict(sender=req['actor'], phase='work',
                round=req['round'], text=raw_output))
        else:
            self.finals[req['arm']][req['actor']] = raw_output
        self.cursor += 1
        self.pending = None
        return record

    @property
    def complete(self):
        return (not self.initial_failed and not self.failed and len(self.initials) == 4
                and all(len(self.finals[a]) == 4 for a in ARMS))

    def export(self):
        return deepcopy(dict(protocol='B1_TWO_ROUND_FOUR_ARM_V1', task=self.task,
            config=self.config, initial_order=self.initial_order, orders=self.orders,
            initials=self.initials, work=self.work, finals=self.finals,
            records=self.records, complete=self.complete, expected_generations=52,
            failed=sorted(self.failed), initial_failed=self.initial_failed))


def replay(trace):
    trial = Trial(trace['task'], **trace['config'])
    for record in trace['records']:
        request = trial.next_request()
        if request is None or any(record.get(k) != v for k, v in request.items()):
            raise ValueError('trace_does_not_match_protocol')
        trial.submit(record['request_id'],record['raw_output'],status=record['status'],
            usage=record['usage'],source_kind=record['source_kind'])
    return trial


def vote(answers, seed):
    if set(answers) != set(ACTORS):
        raise ValueError('vote_needs_four_answers')
    groups = {}
    abstained = []
    for actor in ACTORS:
        key = normalize_answer(answer_text(answers[actor]))
        if key:
            groups.setdefault(key, []).append(actor)
        else:
            abstained.append(actor)
    if not groups:
        return dict(answer='',winners=[],counts={},abstained=abstained,tie=False,seed=seed)
    top = max(len(v) for v in groups.values())
    winners = sorted(k for k, v in groups.items() if len(v) == top)
    selected = random.Random(seed).choice(winners)
    return dict(answer=answers[groups[selected][0]], winners=[answers[groups[k][0]] for k in winners],
        counts={k:len(v) for k,v in groups.items()},abstained=abstained,tie=len(winners)>1,seed=seed)


def vote_scores(voted, target):
    choices = voted['winners'] or ['']
    scores = [answer_score(answer,target) for answer in choices]
    actual = answer_score(voted['answer'],target)
    return dict(expected_em=sum(s['em'] for s in scores)/len(scores),
        expected_f1=sum(s['f1'] for s in scores)/len(scores),actual_em=actual['em'],
        actual_f1=actual['f1'])


def score_trial(trace, target):
    t = replay(trace)
    if t.task['id'] != target['id']:
        raise ValueError('target_task_mismatch')
    report = dict(id=t.task['id'],config=t.config,complete=t.complete,
        primary_enabled=t.complete and not t.config['fixture'],n_expected=52,n_recorded=len(t.records),
        arms={},initial=None,evidence_type='FIXTURE_NOT_RESEARCH_RESULT' if t.config['fixture'] else 'ACTUAL_LOCAL_MODEL_RESPONSE')
    if len(t.initials) != 4:
        return report
    expert = t.config['expert_actor']
    initial = {a:answer_score(s,target) for a,s in t.initials.items()}
    iv = vote(t.initials,t.base_seed+1000)
    report['initial'] = dict(members=initial,vote=iv,scores=vote_scores(iv,target),
                             oracle_hit=any(s['em'] for s in initial.values()))
    for arm in ARMS:
        if arm in t.failed or len(t.finals[arm]) != 4:
            report['arms'][arm] = dict(complete=False)
            continue
        members = {a:answer_score(s,target) for a,s in t.finals[arm].items()}
        voted = vote(t.finals[arm],t.base_seed+1001)
        metrics = vote_scores(voted,target)
        before,after = initial[expert]['em'],members[expert]['em']
        report['arms'][arm] = dict(complete=True,members=members,vote=voted,**metrics,
            expert_em=after,expert_f1=members[expert]['f1'],expert_initial_em=before,
            expert_harm=int(before==1 and after==0),expert_correction=int(before==0 and after==1),
            expert_correct_but_not_selected_expected=after*(1-metrics['expected_em']),
            expert_correct_but_not_selected_actual=after*(1-metrics['actual_em']),
            oracle_hit=any(s['em'] for s in members.values()),
            member_transitions={a:dict(initial_em=initial[a]['em'],final_em=members[a]['em'],
                harmful=int(initial[a]['em']==1 and members[a]['em']==0),
                corrected=int(initial[a]['em']==0 and members[a]['em']==1)) for a in ACTORS})
    return report


def summarize(traces, targets, expected_ids, groups, repeats=10000):
    by_id = {trace['task']['id']:trace for trace in traces}
    if (len(by_id)!=len(traces) or set(by_id)-set(expected_ids) or not expected_ids
            or len(set(expected_ids))!=len(expected_ids) or set(groups)!=set(expected_ids)):
        raise ValueError('duplicate_or_extra_trials')
    reports=[score_trial(by_id[k],targets[k]) for k in expected_ids if k in by_id]
    signatures={(r['config']['expert_actor'],r['config']['seed'],r['config']['fixture']) for r in reports}
    if len(signatures)>1:
        raise ValueError('mixed_batch_conditions')
    completed=[r for r in reports if r['complete']]
    result=dict(n_expected=len(expected_ids),n_recorded=len(reports),n_complete=len(completed),
        status='COMPLETE' if len(completed)==len(expected_ids) else 'INCOMPLETE',
        primary_enabled=len(completed)==len(expected_ids) and all(r['primary_enabled'] for r in completed),
        scope='DEVELOPMENT_DESCRIPTION_NOT_CONFIRMATORY_TEST',arms={},contrasts={},reports=reports)
    if not completed:
        return result
    n=len(completed)
    init_correct=sum(r['initial']['members'][r['config']['expert_actor']]['em'] for r in completed)
    result['initial_baseline']=dict(expert_em=init_correct/n,
        expert_f1=sum(r['initial']['members'][r['config']['expert_actor']]['f1'] for r in completed)/n,
        team_expected_em=sum(r['initial']['scores']['expected_em'] for r in completed)/n,
        team_actual_em=sum(r['initial']['scores']['actual_em'] for r in completed)/n,
        team_expected_f1=sum(r['initial']['scores']['expected_f1'] for r in completed)/n,
        team_actual_f1=sum(r['initial']['scores']['actual_f1'] for r in completed)/n,
        oracle_hit=sum(r['initial']['oracle_hit'] for r in completed)/n)
    for arm in ARMS:
        values=[r['arms'][arm] for r in completed]
        harms=sum(v['expert_harm'] for v in values)
        corrections=sum(v['expert_correction'] for v in values)
        result['arms'][arm]=dict(n=n,
            **{key:sum(v[key] for v in values)/n for key in
               ('expected_em','actual_em','expected_f1','actual_f1','expert_em','expert_f1',
                'expert_correct_but_not_selected_expected','expert_correct_but_not_selected_actual','oracle_hit')},
            tie_rate=sum(v['vote']['tie'] for v in values)/n,
            expert_harm_n=harms,expert_harm_denominator=init_correct,
            expert_harm_rate=harms/init_correct if init_correct else None,
            expert_retention_rate=1-harms/init_correct if init_correct else None,
            expert_correction_n=corrections,expert_correction_denominator=n-init_correct,
            expert_correction_rate=corrections/(n-init_correct) if n-init_correct else None,
            members={})
        for actor in ACTORS:
            denom=sum(r['initial']['members'][actor]['em'] for r in completed)
            harm=sum(r['arms'][arm]['member_transitions'][actor]['harmful'] for r in completed)
            correction=sum(r['arms'][arm]['member_transitions'][actor]['corrected'] for r in completed)
            result['arms'][arm]['members'][actor]=dict(n=n,
                initial_em=denom/n,
                initial_f1=sum(r['initial']['members'][actor]['f1'] for r in completed)/n,
                final_em=sum(r['arms'][arm]['members'][actor]['em'] for r in completed)/n,
                final_f1=sum(r['arms'][arm]['members'][actor]['f1'] for r in completed)/n,
                harm_n=harm,correct_initial_n=denom,harm_rate=harm/denom if denom else None,
                retention_rate=1-harm/denom if denom else None,
                correction_n=correction,wrong_initial_n=n-denom,
                correction_rate=correction/(n-denom) if n-denom else None)
    for label,left,right in (('B-A','B','A'),('D-C','D','C'),('D-B','D','B'),('C-A','C','A')):
        result['contrasts'][label]={}
        for key in ('expected_em','expert_em'):
            differences={r['id']:r['arms'][left][key]-r['arms'][right][key] for r in completed}
            result['contrasts'][label][key]=dict(difference=sum(differences.values())/n,
                cluster_ci95=paired_interval(differences,{k:groups[k] for k in differences},repeats,20261102),
                item_ci95_sensitivity=paired_interval(differences,{k:k for k in differences},repeats,20261102))
    return result


def smoke(path):
    task = dict(id='HOST_FIXTURE',question='Which value is given for X?',paragraphs=[
        dict(idx=0,title='X',paragraph_text='The value for X is 1900.')])
    trial = Trial(task,expert_actor='M1',fixture=True)
    while (req := trial.next_request()) is not None:
        trial.submit(req['request_id'], 'Fixture work.' if req['stage']=='work' else '1900')
    report = dict(evidence_type='FIXTURE_NOT_RESEARCH_RESULT',primary_enabled=False,
                  trial=trial.export(),model_calls=0)
    write_json(path,report)
    return dict(evidence_type=report['evidence_type'],complete=trial.complete,
                recorded_generations=len(trial.records),primary_enabled=False,model_calls=0)
