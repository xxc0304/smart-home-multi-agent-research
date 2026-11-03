"""Literal finite-candidate checks over model-generated facts and conditions.

Citation existence is not entailment. Conflicting/missing facts remain unknown.
"""
FIELDS = {'age','sex','vehicle_context','driver_vehicle','license_years',
          'drank_spirits','measured_alcohol','speed_kmh','role','inattentive'}
OPS = {'eq','ne','lt','le','gt','ge'}


def execute(candidates, public_sources, private_sources, outputs, *, candidate_aliases=None,
            allowed_fields=None, private_candidate_facts=False, public_conditions=False,
            boolean_fields=()):
    public = {r['ref']:r['content'] for r in public_sources}
    facts, conditions, notices = {}, [], []
    candidate_aliases = candidate_aliases or {}
    allowed_fields = FIELDS if allowed_fields is None else set(allowed_fields)
    boolean_fields = set(boolean_fields)
    for owner, output in outputs.items():
        private = {r['ref']:r['content'] for r in private_sources[owner]}
        fact_sources = {**public,**private} if private_candidate_facts else public
        condition_sources = {**public,**private} if public_conditions else private
        for i, fact in enumerate(output['facts']):
            candidate = candidate_aliases.get(fact['candidate'],fact['candidate'])
            if candidate != fact['candidate']:
                notices.append(dict(owner=owner,kind='exact_candidate_alias',index=i,
                                    original=fact['candidate'],normalized=candidate))
            valid = (candidate in candidates and fact['field'] in allowed_fields
                     and bool(fact['quote']) and fact['quote'] in fact_sources.get(fact['source'], ''))
            if not valid:
                notices.append(dict(owner=owner,kind='rejected_fact',index=i))
                continue
            if fact['field'] in boolean_fields and fact['value'] is not None and type(fact['value']) is not bool:
                notices.append(dict(owner=owner,kind='invalid_fact_type',index=i))
                continue
            facts.setdefault((candidate,fact['field']),[]).append(fact['value'])
        for i, c in enumerate(output['conditions']):
            diagnostic = None
            if not c['quote'] or c['quote'] not in condition_sources.get(c['source'],''):
                diagnostic='invalid_source_reference'
            elif c['field'] not in allowed_fields or c['op'] not in OPS:
                diagnostic='unsupported_expression'
            elif c['field'] in boolean_fields and (c['op'] not in {'eq','ne'} or
                    (c['value'] is not None and type(c['value']) is not bool)):
                diagnostic='invalid_boolean_condition'
            conditions.append(dict(id=f'{owner}.C{i+1}',owner=owner,**c,diagnostic=diagnostic))
    table = {}
    conflicts = []
    for (candidate,field),values in facts.items():
        distinct = {('number',float(v)) if type(v) in {int,float} else (type(v).__name__,str(v))
                    for v in values if v is not None}
        value = next((v for v in values if v is not None),None) if len(distinct)==1 else None
        table.setdefault(candidate,{})[field]=value
        if len(distinct)>1:conflicts.append(dict(candidate=candidate,field=field,values=values))
    reports=[]
    for candidate in candidates:
        checks=[]
        for c in conditions:
            actual=table.get(candidate,{}).get(c['field'])
            status='unknown';diagnostic=c['diagnostic']
            if diagnostic is None and actual is None:
                diagnostic='missing_or_conflicting_candidate_fact'
            if diagnostic is None and actual is not None and c['value'] is not None:
                if c['op'] in {'eq','ne'}:
                    same_type=(type(actual) is type(c['value']) or
                               (type(actual) in {int,float} and type(c['value']) in {int,float}))
                    equal=same_type and actual==c['value']
                    passed=equal if c['op']=='eq' else not equal
                    status='consistent' if passed else 'violates'
                elif type(actual) in {int,float} and type(c['value']) in {int,float}:
                    passed={'lt':lambda:actual<c['value'],'le':lambda:actual<=c['value'],
                            'gt':lambda:actual>c['value'],'ge':lambda:actual>=c['value']}[c['op']]()
                    status='consistent' if passed else 'violates'
                else:diagnostic='incompatible_types'
            checks.append(dict(condition=c['id'],status=status,actual=actual,diagnostic=diagnostic))
        reports.append(dict(candidate=candidate,checks=checks))
    remaining=[r['candidate'] for r in reports if not any(c['status']=='violates' for c in r['checks'])]
    coverage={c['id']:sum(table.get(candidate,{}).get(c['field']) is not None for candidate in candidates)
              for c in conditions}
    return dict(member_conditions=conditions,model_fact_table=table,fact_conflicts=conflicts,
                candidate_fact_coverage=coverage,
                notices=notices,candidate_checks=reports,not_excluded=remaining,
                meaning='Literal checks of model interpretations, not source-semantic verification. Unknown is not true; not-excluded is not proven correct.')
