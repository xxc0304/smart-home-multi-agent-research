"""Task-scoped interface checks. Provenance matching does not prove entailment."""
import copy
from jsonschema import validate

VERSION = 'candidate-contribution/v2'


class ContributionInterfaceError(ValueError):
    pass


def visible_sources(packet):
    sources = {}
    for entry in packet['public_sources'] + packet['own_sources']:
        if entry['ref'] in sources:
            raise ContributionInterfaceError('duplicate visible source ID')
        sources[entry['ref']] = entry['content']
    return sources


def extraction_schema(packet):
    def obj(**properties):
        return dict(type='object', additionalProperties=False,
                    required=list(properties), properties=properties)
    text = dict(type='string')
    quote = dict(type='string', minLength=1)
    choices = packet['task']['choices']
    candidate = dict(type='string', enum=[c[k] for c in choices for k in ('id', 'text')])
    field = dict(type='string', enum=list(packet['field_meanings']))
    source = dict(type='string', enum=list(visible_sources(packet)))
    value = dict(type=['boolean', 'null'])
    result = obj(text=text,
        facts=dict(type='array', items=obj(candidate=candidate, field=field, value=value,
                                          source=source, quote=quote)),
        conditions=dict(type='array', items=obj(field=field,
            op=dict(type='string', enum=['eq', 'ne']), value=value, source=source, quote=quote)),
        caveats=dict(type='array', items=text))
    result['properties']['solution'] = dict(type='null')
    return result


def normalize_contribution(answer, packet):
    """Only normalize exact labels and unique exact-quote provenance, never meanings."""
    normalized = copy.deepcopy(answer)
    aliases = {c['text']: c['id'] for c in packet['task']['choices']}
    ids = {c['id'] for c in packet['task']['choices']}
    if len(packet['task']['choices']) != len(aliases) or len(aliases) != len(ids) or any(k in ids and k != v for k, v in aliases.items()):
        raise ContributionInterfaceError('ambiguous candidate labels')
    sources = visible_sources(packet)
    events = []
    for i, fact in enumerate(normalized['facts']):
        candidate = fact['candidate']
        if candidate in aliases:
            fact['candidate'] = aliases[candidate]
            if candidate != fact['candidate']:
                events.append(dict(kind='exact_candidate_label', section='facts', index=i,
                                   original=candidate, normalized=fact['candidate']))
        if fact['candidate'] not in ids:
            raise ContributionInterfaceError(f'facts[{i}]: unknown/out-of-scope candidate {candidate!r}')
    for section in ('facts', 'conditions'):
        for i, entry in enumerate(normalized[section]):
            declared, quote = entry['source'], entry['quote']
            if declared not in sources:
                raise ContributionInterfaceError(f'{section}[{i}]: source not visible to member')
            if not quote:
                raise ContributionInterfaceError(f'{section}[{i}]: empty quote')
            if quote in sources[declared]:
                continue
            matches = [ref for ref, content in sources.items() if quote in content]
            if len(matches) != 1:
                raise ContributionInterfaceError(
                    f'{section}[{i}]: quote absent or ambiguous among visible sources')
            entry['source'] = matches[0]
            events.append(dict(kind='unique_exact_quote_source', section=section, index=i,
                               original=declared, normalized=matches[0]))
    validate(normalized, extraction_schema(packet))
    return normalized, events


def assert_execution_admission(report):
    bad = [n for n in report['notices'] if n['kind'] in
           {'rejected_fact', 'invalid_fact_type'}]
    bad_conditions = [c for c in report['member_conditions'] if c['diagnostic'] is not None]
    if bad or bad_conditions:
        raise ContributionInterfaceError('validated contribution was rejected by executor')
