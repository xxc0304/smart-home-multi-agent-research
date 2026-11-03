"""Prepare model-free scheduling tasks. Gold never enters member packets."""
import argparse
import hashlib
from itertools import permutations
import json
from pathlib import Path
import random

from coreta.workboard.order_constraints import solutions, violations


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')


def sentence(rule):
    a = rule['a']
    if rule['op'] == 'before':
        return f"{a} must finish no later than the start of {rule['b']}; equality is allowed."
    if rule['op'] == 'not_adjacent':
        return f"{a} and {rule['b']} must not occupy consecutive positions in either order."
    if rule['op'] == 'deadline':
        return f"{a} must finish no later than minute {rule['value']} after time zero."
    return f"{a} must not occupy position {rule['value']} (positions start at one)."


def build(seed, n):
    rng = random.Random(seed)
    names = [f'J{i+1}' for i in range(n)]
    jobs = {name: {'duration': rng.randint(2, 7)} for name in names}
    # Requirements are sampled before solving, not reverse-written from a correct plan.
    pairs = rng.sample([(a, b) for a in names for b in names if a != b], n-1)
    rules = [dict(op='before', a=a, b=b) for a, b in pairs]
    a, b = rng.sample(names, 2)
    rules.append(dict(op='not_adjacent', a=a, b=b))
    rules.append(dict(op='deadline', a=rng.choice(names), value=rng.randint(8, sum(j['duration'] for j in jobs.values()))))
    rules.append(dict(op='not_position', a=rng.choice(names), value=rng.randint(1, n)))
    rng.shuffle(rules)
    for i, rule in enumerate(rules):
        rule.update(id=f'R{i+1}', owner=f'A{i%3+1}')
    return jobs, rules


def prepare(output):
    if output.exists():
        raise ValueError('new directory required')
    output.mkdir(parents=True)
    roster, offline = [], {}
    # These are same-family held-out instances, not new task families or external benchmarks.
    for split, base, count in [('calibration', 24000, 6), ('heldout', 97000, 12)]:
        seed, accepted = base, 0
        while accepted < count:
            n = [6, 7, 8][accepted % 3]
            jobs, rules = build(seed, n)
            valid = solutions(jobs, rules)
            trial_seed = seed
            seed += 1
            # Structural screen only: satisfiable, <=5% of permutations valid,
            # and every member owns at least one nonredundant requirement.
            if not valid:
                continue
            total = 1
            for k in range(2, n+1):
                total *= k
            if len(valid)/total > .05:
                continue
            essential = []
            for rule in rules:
                rest = [r for r in rules if r['id'] != rule['id']]
                if len(solutions(jobs, rest)) > len(valid):
                    essential.append(rule['id'])
            if any(not any(r['id'] in essential and r['owner'] == owner for r in rules)
                   for owner in ['A1','A2','A3']):
                continue
            cid = f'{split}-{accepted+1:02d}'
            task = dict(id=cid, jobs=jobs, goal='Return any order satisfying all mandatory requirements.',
                semantics='One machine; start at minute zero, no idle time or overlap. Each job runs once, without interruption. Durations are minutes. Precedence allows finish time equal to the next job start time. Positions start at one. All three source sheets contain mandatory requirements.')
            write(output/split/cid/'task.json', task)
            for owner in ['A1','A2','A3']:
                write(output/split/cid/f'{owner}.json', dict(member=owner, task=task,
                    sources=[dict(id=r['id'], text=sentence(r)) for r in rules if r['owner']==owner]))
            # Oracle conditions for isolated application diagnostic; never pretend automatic extraction.
            write(output/split/cid/'oracle_conditions.json', rules)
            near_miss = next(list(o) for o in permutations(jobs) if len(violations(o,jobs,rules)) == 1)
            offline[cid] = dict(seed=trial_seed, valid_orders=valid,
                essential_rule_ids=essential, near_miss=near_miss,
                near_miss_violations=violations(near_miss,jobs,rules))
            roster.append(dict(id=cid, split=split, jobs=n, rules=len(rules), valid_orders=len(valid),
                               candidate_orders=total, seed=trial_seed))
            accepted += 1
    write(output/'offline'/'reference.json', offline)
    files = {p.relative_to(output).as_posix():hashlib.sha256(p.read_bytes()).hexdigest()
             for p in output.rglob('*.json')}
    write(output/'manifest.json', dict(roster=roster, files=files, calls_made=0,
        selection='structural only; no model outcomes consulted',
        status='local_task_pack_not_frozen_model_experiment'))
    return roster


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('output', type=Path)
    print(json.dumps(prepare(parser.parse_args().output)))
