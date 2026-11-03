"""Local collaboration state machine; callbacks may be simulated or model-backed.

No reference-rule or solution loading. Conditions remain member interpretations.
"""
import copy
from .order_constraints import violations


def clone(value):
    return copy.deepcopy(value)


class OrderBoard:
    def __init__(self, task, sources):
        self.task = clone(task)
        self.sources = clone(sources)  # owner -> [{id, text}]
        self.conditions = {}
        self.contributions = []
        self.history = []
        self.snapshot = 0
        self.works = {}

    def _ground(self, owner, source, quote):
        texts = {s['id']: s['text'] for s in self.sources[owner]}
        if not isinstance(quote, str) or not quote or quote not in texts.get(source, ''):
            raise ValueError('source must belong to author and contain exact quote')

    def diagnose_expression(self, expression):
        """Compiler diagnostics only; no source interpretation or automatic repair."""
        if not isinstance(expression, dict):
            return dict(code='invalid_expression', reason='expected_object')
        op = expression.get('op')
        fields = {'before': {'op','a','b'}, 'not_adjacent': {'op','a','b'},
                  'deadline': {'op','a','value'}, 'not_position': {'op','a','value'}}
        if not isinstance(op, str) or op not in fields:
            return dict(code='invalid_expression', reason='unsupported_operator',
                        allowed_operators=sorted(fields))
        if set(expression) != fields[op]:
            return dict(code='invalid_expression', reason='field_mismatch',
                expected_fields=sorted(fields[op]), missing_fields=sorted(fields[op]-set(expression)),
                unexpected_fields=sorted(set(expression)-fields[op]))
        if not isinstance(expression['a'], str) or expression['a'] not in self.task['jobs']:
            return dict(code='invalid_expression', reason='unknown_job', field='a')
        if 'b' in expression:
            if not isinstance(expression['b'], str) or expression['b'] not in self.task['jobs']:
                return dict(code='invalid_expression', reason='unknown_job', field='b')
            if expression['a'] == expression['b']:
                return dict(code='invalid_expression', reason='identical_job_arguments')
        elif type(expression['value']) is not int or expression['value'] < 0:
            return dict(code='invalid_expression', reason='expected_nonnegative_integer', field='value')
        return None

    def _executable(self, expression):
        return self.diagnose_expression(expression) is None

    def contribute(self, owner, text, conditions):
        prepared = []
        for index, item in enumerate(conditions):
            self._ground(owner, item['source'], item['quote'])
            prepared.append(dict(id=f'{owner}.C{index+1}', owner=owner, version=1,
                kind='member_interpretation', source=item['source'], quote=item['quote'],
                expression=clone(item['expression']), active=True))
        if any(c['id'] in self.conditions for c in prepared):
            raise ValueError('duplicate contribution')
        for condition in prepared:
            self.conditions[condition['id']] = condition
        self.contributions.append(dict(owner=owner, text=text, conditions=clone(prepared)))
        self.snapshot += 1

    def revise_round(self, reviews):
        """Validate whole round before committing. Responses alone clear nothing."""
        changes, seen = [], set()
        for owner, response in reviews.items():
            for update in response.get('updates', []):
                cid = update['condition']
                old = self.conditions[cid]
                if old['owner'] != owner or cid in seen:
                    raise ValueError('only owner may revise once per round')
                self._ground(owner, update['source'], update['quote'])
                if not update['reason'].strip():
                    raise ValueError('revision reason required')
                new = {**old, 'version': old['version']+1, 'source': update['source'],
                       'quote': update['quote'], 'active': not update.get('withdraw', False)}
                if new['active']:
                    new['expression'] = clone(update['expression'])
                changes.append((clone(old), new, update['reason']))
                seen.add(cid)
        for old, new, reason in changes:
            self.conditions[new['id']] = new
            self.history.append(dict(old=old, new=clone(new), reason=reason))
        if changes:
            self.snapshot += 1

    def put_work(self, version, author, answer):
        if version in self.works:
            raise ValueError('work versions immutable')
        self.works[version] = dict(version=version, author=author, order=clone(answer['order']),
                                   reason=answer.get('reason', ''))

    def check(self, version):
        order = self.works[version]['order']
        jobs = self.task['jobs']
        legal = (isinstance(order, list) and all(isinstance(j, str) for j in order)
                 and len(order) == len(jobs) and set(order) == set(jobs))
        positions, finish, elapsed = {}, {}, 0
        if legal:
            positions = {job:i+1 for i,job in enumerate(order)}
            for job in order:
                elapsed += jobs[job]['duration']
                finish[job] = elapsed
        checks = []
        for c in self.conditions.values():
            if not c['active']:
                continue
            status = 'unknown'
            diagnostic = self.diagnose_expression(c['expression'])
            if not legal and diagnostic is None:
                diagnostic = dict(code='invalid_plan', reason='expected_each_job_exactly_once')
            if diagnostic is None:
                rule = {**c['expression'], 'id': c['id']}
                status = 'violates' if violations(order, jobs, [rule]) else 'consistent'
            checks.append(dict(condition=c['id'], condition_version=c['version'], status=status,
                               expression=clone(c['expression']), diagnostic=diagnostic))
        return dict(work_version=version, condition_snapshot=self.snapshot, legal_order=legal,
                    positions=positions, completion_times=finish, checks=checks)

    def packet(self, owner, arm, stage, report=None, reviews=None):
        if owner not in self.sources or arm not in {'A','B','C'}:
            raise ValueError('unknown member/arm')
        if report is not None and (report['condition_snapshot'] != self.snapshot or
                                   report['work_version'] not in self.works):
            raise ValueError('stale execution report')
        value = dict(member=owner, stage=stage, task=clone(self.task),
            own_sources=clone(self.sources[owner]), shared_contributions=clone(self.contributions),
            current_conditions=clone(list(self.conditions.values())), works=clone(self.works))
        if reviews is not None:
            value['shared_reviews'] = clone(reviews)
        if arm in {'B','C'} and report is not None:
            value['execution_report'] = clone(report)
        if arm == 'C':
            value['application_links'] = [dict(condition=c['condition'], owner=self.conditions[c['condition']]['owner'],
                condition_version=c['condition_version'], work_version=report['work_version'], status=c['status'])
                for c in report['checks']] if report else []
        return value

    def select(self, arm, final):
        """Always preserve raw works; checks never certify source interpretation."""
        before, after = self.check('W0'), self.check('W1')
        selection, reason = 'W1', 'editor_submission'
        if final.get('retain_work') == 'W0':
            selection, reason = 'W0', 'editor_retained_old'
        elif arm == 'C':
            old_v = {r['condition'] for r in before['checks'] if r['status']=='violates'}
            new_v = {r['condition'] for r in after['checks'] if r['status']=='violates'}
            old_u = {r['condition'] for r in before['checks'] if r['status']=='unknown'}
            new_u = {r['condition'] for r in after['checks'] if r['status']=='unknown'}
            blocked = not after['legal_order'] or (before['legal_order'] and
                         (not new_v <= old_v or not new_u <= old_u))
            required = (new_v-old_v) | (new_u-old_u)
            exceptions = final.get('exceptions', {})
            override = (after['legal_order'] and bool(required) and required <= set(exceptions)
                        and all(isinstance(exceptions[k], str) and exceptions[k].strip() for k in required))
            if blocked and not override and before['legal_order']:
                selection, reason = 'W0', 'new_conflicts_retained_old'
            elif blocked and override:
                reason = 'explicit_disputed_submission'
            elif blocked:
                reason = 'both_orders_invalid'
        chosen = before if selection=='W0' else after
        status = ('invalid_plan' if not chosen['legal_order'] else
                  'unresolved' if any(r['status']!='consistent' for r in chosen['checks']) else
                  'consistent_with_member_conditions')
        return dict(selected=selection, reason=reason, status=status,
                    before=before, after=after, raw_works=clone(self.works))


def simulate_episode(task, sources, editor, call, *, on_state=None, arm_order=('A','B','C'),
                     initial_answers=None, shared_work=None):
    """18 callbacks normally, or 12 for a frozen same-work replay diagnostic."""
    if len(arm_order) != 3 or set(arm_order) != {'A','B','C'}:
        raise ValueError('all three arms required once')
    if (initial_answers is None) != (shared_work is None):
        raise ValueError('replay requires both original contributions and shared work')
    if initial_answers is not None and set(initial_answers) != set(sources):
        raise ValueError('replay must include all members')
    initial = OrderBoard(task, sources)
    semantic_errors = []

    def emit(arm, stage, board, selection=None):
        if on_state:
            on_state(dict(arm=arm, stage=stage, works=clone(board.works),
                conditions=clone(board.conditions), history=clone(board.history),
                semantic_errors=clone(semantic_errors), selection=clone(selection)))

    for owner in sources:
        packet = initial.packet(owner, 'A', 'INIT')
        # INIT is independent: no previous member contributions or conditions.
        packet['shared_contributions'] = []
        packet['current_conditions'] = []
        answer = clone(initial_answers[owner]) if initial_answers is not None else call('INIT', owner, None, packet)
        valid = []
        for item in answer.get('conditions', []):
            try:
                initial._ground(owner, item['source'], item['quote'])
                valid.append(item)
            except (ValueError, KeyError, TypeError):
                semantic_errors.append(dict(stage='INIT', owner=owner, error='invalid_source_reference'))
        initial.contribute(owner, answer.get('text', ''), valid)
        emit(None, 'INIT', initial)
    result = {}
    for arm in arm_order:
        board = clone(initial)
        answer = clone(shared_work) if shared_work is not None else call('BUILD', editor, arm, board.packet(editor, arm, 'BUILD'))
        board.put_work('W0', editor, answer)
        emit(arm, 'BUILD', board)
        first = board.check('W0') if arm != 'A' else None
        packets = {owner:board.packet(owner, arm, 'REVIEW', first) for owner in sources}
        reviews = {owner:clone(call('REVIEW', owner, arm, packet)) for owner,packet in packets.items()}
        # Reject individual unauthorized revisions, preserving other valid updates.
        seen = set()
        for owner, review in reviews.items():
            valid = []
            for update in review.get('updates', []):
                try:
                    cid = update['condition']
                    if cid in seen or board.conditions[cid]['owner'] != owner or not update['reason'].strip():
                        raise ValueError('invalid revision')
                    board._ground(owner, update['source'], update['quote'])
                    valid.append(update)
                    seen.add(cid)
                except (ValueError, KeyError, TypeError):
                    semantic_errors.append(dict(stage='REVIEW', arm=arm, owner=owner,
                                                error='invalid_revision_reference'))
            review['updates'] = valid
        board.revise_round(reviews)
        emit(arm, 'REVIEW', board)
        updated = board.check('W0') if arm != 'A' else None
        final = call('FINAL', editor, arm, board.packet(editor, arm, 'FINAL', updated, reviews))
        board.put_work('W1', editor, final)
        if arm == 'A':
            # A gets no runtime semantic program checks, even internally during selection.
            selected = 'W0' if final.get('retain_work')=='W0' else 'W1'
            selection = dict(selected=selected, reason='editor_choice', status='not_program_checked',
                             raw_works=clone(board.works))
        else:
            selection = board.select(arm, final)
        result[arm] = dict(selection=selection, history=clone(board.history),
                           conditions=clone(board.conditions), first_check=first, updated_check=updated)
        emit(arm, 'FINAL', board, selection)
    return result
