"""Small deterministic scheduling interpreter. No generated code or model truth claims."""
from itertools import permutations


def violations(order, jobs, rules):
    if len(order) != len(jobs) or set(order) != set(jobs):
        raise ValueError('order must contain every job exactly once')
    positions = {job: i for i, job in enumerate(order)}
    end_times, total = {}, 0
    for job in order:
        total += jobs[job]['duration']
        end_times[job] = total
    failed = []
    for rule in rules:
        op, a = rule['op'], rule['a']
        if op == 'before':
            ok = positions[a] < positions[rule['b']]
        elif op == 'not_adjacent':
            ok = abs(positions[a] - positions[rule['b']]) > 1
        elif op == 'deadline':
            ok = end_times[a] <= rule['value']
        elif op == 'not_position':
            ok = positions[a] + 1 != rule['value']
        else:
            raise ValueError('unsupported rule')
        if not ok:
            failed.append(rule['id'])
    return failed


def solutions(jobs, rules):
    return [list(order) for order in permutations(jobs)
            if not violations(order, jobs, rules)]
