"""Versioned commitment of literal model constraints; never semantic certification.

Reuses the historical executor without changing frozen batches. Supplied source
chunks and contribution interpretations remain distinct from verified truth.
"""
from __future__ import annotations

import copy
import hashlib
import json
import math
from .workboard.candidate_probe import execute, OPS


class CommitError(ValueError):
    pass


def fingerprint(value):
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


class ConstraintSession:
    def __init__(self, task, public_sources, source_chunks, contributions, field_types):
        self.task=copy.deepcopy(task)
        self.public=copy.deepcopy(public_sources)
        self.sources=copy.deepcopy(source_chunks)
        self.contributions=copy.deepcopy(contributions)
        self.field_types=dict(field_types)
        self.ids=[r['id'] for r in task['choices']]
        aliases={r['text']:r['id'] for r in task['choices']}
        if not self.ids or len(set(self.ids))!=len(self.ids) or len(aliases)!=len(self.ids):
            raise CommitError('ambiguous task choices')
        if any(k in self.ids and k!=v for k,v in aliases.items()):raise CommitError('ambiguous alias')
        if not field_types or any(t not in {'number','boolean','string'} for t in field_types.values()):
            raise CommitError('explicit typed field vocabulary required')
        self.aliases=aliases
        self.version=1
        self.entries={}
        self.admission=[]
        self.events=[]
        self.evidence={}
        self.evidence_origin={}
        for row in self.public:
            self._evidence('public',row['ref'],row['content'],'visible_public_original')
        for owner,refs in self.sources.items():
            for ref,record in refs.items():
                for chunk in record['chunks']:
                    self._evidence(owner,ref,chunk,record['access'])
        for owner,output in self.contributions.items():
            if not isinstance(output,dict) or not isinstance(output.get('facts'),list) or not isinstance(output.get('conditions'),list):
                raise CommitError('contribution core requires fact and condition arrays')
            for section,tag in [('facts','F'),('conditions','C')]:
                for i,original in enumerate(output[section],1):
                    key=f'{owner}.{tag}{i}'
                    try:
                        normalized,events=self._admit(owner,section,original)
                    except CommitError as exc:
                        self.admission.append(dict(id=key,status='not_executable',reason=str(exc),raw=copy.deepcopy(original)))
                        continue
                    self.entries[key]=dict(id=key,owner=owner,section=section,value=normalized,status='active',
                        truth_status='model_declared_not_semantically_verified')
                    self.admission.append(dict(id=key,status='mechanically_admitted',normalizations=events))
        self._cached=None

    def _evidence(self,owner,ref,text,access):
        if not isinstance(text,str) or not text.strip():raise CommitError('blank source chunk')
        key=f'E{len(self.evidence)+1}'
        self.evidence[key]=dict(id=key,owner=owner,source=ref,text=text,access=access)
        self.evidence_origin[key]=(owner,ref)

    def _visible(self,owner):
        result={r['ref']:[r['content']] for r in self.public}
        for ref,record in self.sources.get(owner,{}).items():
            if ref in result:raise CommitError('duplicate public/private source ref')
            result[ref]=record['chunks']
        return result

    def _admit(self,owner,section,original):
        if not isinstance(original,dict):raise CommitError('entry must be an object')
        value=copy.deepcopy(original)
        fields={'field','value','source','quote'}|({'candidate'} if section=='facts' else {'op'})
        if not fields<=value.keys():raise CommitError('missing essential entry field')
        value={k:value[k] for k in fields}
        if not isinstance(value['field'],str) or value['field'] not in self.field_types:raise CommitError('unsupported field')
        expected=self.field_types[value['field']]
        actual=value['value']
        if actual is not None:
            valid=(type(actual) in {int,float} and math.isfinite(actual) if expected=='number' else
                   type(actual) is bool if expected=='boolean' else type(actual) is str and bool(actual.strip()))
            if not valid:raise CommitError('field value type mismatch')
        if section=='conditions':
            if not isinstance(value['op'],str) or value['op'] not in OPS:raise CommitError('unsupported operator')
            if value['op'] not in {'eq','ne'} and expected!='number':raise CommitError('ordered comparison needs numeric field')
        else:
            candidate=value['candidate']
            value['candidate']=self.aliases.get(candidate,candidate) if isinstance(candidate,str) else None
            if value['candidate'] not in self.ids:raise CommitError('unknown candidate')
        sources=self._visible(owner)
        ref,quote=value['source'],value['quote']
        if not isinstance(ref,str) or ref not in sources:raise CommitError('source outside contributor visibility')
        if not isinstance(quote,str) or not quote.strip():raise CommitError('blank quote')
        events=[]
        if not any(quote in chunk for chunk in sources[ref]):
            matches=[r for r,chunks in sources.items() if any(quote in chunk for chunk in chunks)]
            if len(matches)!=1:raise CommitError('quote absent or ambiguous')
            value['source']=matches[0]
            events.append(dict(kind='unique_exact_quote_source',before=ref,after=matches[0]))
        if section=='facts' and value['candidate']!=original['candidate']:
            events.append(dict(kind='exact_candidate_alias',before=original['candidate'],after=value['candidate']))
        return value,events

    def report(self):
        outputs={owner:dict(facts=[],conditions=[]) for owner in self.contributions}
        mapping={}
        for key,entry in self.entries.items():
            if entry['status']!='active':continue
            rows=outputs[entry['owner']][entry['section']]
            rows.append(copy.deepcopy(entry['value']))
            if entry['section']=='conditions':mapping[f"{entry['owner']}.C{len(rows)}"]=key
        # Every quote is individually checked against its original chunk before this
        # legacy API joins chunks. No new concatenated span is admitted by joining.
        private={owner:[dict(ref=ref,content='\n'.join(r['chunks'])) for ref,r in self.sources.get(owner,{}).items()]
                 for owner in self.contributions}
        r=execute(self.ids,self.public,private,outputs,candidate_aliases=self.aliases,
            allowed_fields=self.field_types,private_candidate_facts=True,public_conditions=True,
            boolean_fields=[f for f,t in self.field_types.items() if t=='boolean'])
        bad=[n for n in r['notices'] if n['kind'] in {'rejected_fact','invalid_fact_type'}]
        if bad or any(c['diagnostic'] for c in r['member_conditions']):raise CommitError('admitted item lost in executor')
        for c in r['member_conditions']:c['id']=mapping[c['id']]
        for candidate in r['candidate_checks']:
            for check in candidate['checks']:check['condition']=mapping[check['condition']]
        return dict(version=self.version,**r,admission=copy.deepcopy(self.admission),
            entries=copy.deepcopy(list(self.entries.values())),evidence=copy.deepcopy(list(self.evidence.values())),
            semantics='Active means current model-declared interpretation, not independently verified truth.')

    def revise(self,updates,expected_version):
        if type(expected_version) is not int or expected_version!=self.version:raise CommitError('stale state version')
        if not isinstance(updates,list) or len(updates)>4:raise CommitError('at most four explicit updates')
        if not updates:return dict(status='no_change',version=self.version)
        seen=set()
        for u in updates:
            if not isinstance(u,dict) or not {'entry_id','action','reason','evidence_ids'}<=u.keys():raise CommitError('update core missing')
            key=u['entry_id']
            if not isinstance(key,str) or key not in self.entries or key in seen:raise CommitError('unknown or duplicate entry')
            seen.add(key)
            action=u['action']
            if not isinstance(action,str) or action not in {'retire','restore'}:raise CommitError('unknown update action')
            if not isinstance(u['reason'],str) or not u['reason'].strip():raise CommitError('update reason missing')
            refs=u['evidence_ids']
            if not isinstance(refs,list) or not refs or any(not isinstance(x,str) or x not in self.evidence for x in refs):
                raise CommitError('update evidence must use visible handles')
            expected='active' if action=='retire' else 'retired'
            if self.entries[key]['status']!=expected:raise CommitError('update does not target current entry status')
        before=self.report()
        # Validate all changes first; no partially applied transaction on error.
        for u in updates:self.entries[u['entry_id']]['status']='retired' if u['action']=='retire' else 'active'
        self.version+=1
        after=self.report()
        event=dict(before_version=before['version'],after_version=self.version,updates=copy.deepcopy(updates),
            before_remaining=before['not_excluded'],after_remaining=after['not_excluded'],
            reason_entailment='not_verified_by_host')
        self.events.append(event)
        return event

    def deliver(self,proposal,mode,expected_version):
        if type(expected_version) is not int or expected_version!=self.version:raise CommitError('stale submission version')
        if mode not in {'report_reference','constraint_commit'}:raise CommitError('unknown policy')
        choice=proposal.get('choice')
        if choice is not None and choice not in self.ids:raise CommitError('invalid proposed choice')
        if not isinstance(proposal.get('reasoning'),str) or not proposal['reasoning'].strip():raise CommitError('proposal reasoning required')
        report=self.report();remaining=report['not_excluded']
        if mode=='report_reference':delivered=choice;selector='model_proposal'
        elif len(remaining)==1:delivered=remaining[0];selector='unique_not_excluded'
        elif choice is not None and choice in remaining:delivered=choice;selector='model_among_not_excluded'
        else:delivered=None;selector='encoded_conflict' if not remaining else 'no_admissible_proposal'
        trace=[]
        condition_by_id={c['id']:c for c in report['member_conditions']}
        for row in report['candidate_checks']:
            violations=[dict(**check,premise=condition_by_id[check['condition']]) for check in row['checks'] if check['status']=='violates']
            if violations:trace.append(dict(candidate=row['candidate'],violations=violations))
        return dict(mode=mode,version=self.version,choice=delivered,model_choice=choice,
            model_reasoning=proposal['reasoning'],selector=selector,host_changed_choice=(delivered!=choice),
            not_excluded=remaining,exclusion_trace=trace,unresolved=delivered is None,
            feasibility='not_certified',interpretation='Conditional on the current model encodings; not a guarantee of task correctness.',
            reasoning_source='model' if mode=='report_reference' else 'host_selection_and_encoded_trace; model reasoning retained separately')


def session_from_receiver(context,field_types):
    """Use only originals or quoted spans already visible in this receiver packet."""
    chunks={owner:{} for owner in context['shared_contributions']}
    owner=context['member']
    if owner not in chunks:raise CommitError('receiver not in contribution roster')
    for r in context['own_sources']:
        chunks[owner][r['ref']]=dict(chunks=[r['content']],access='receiver_visible_original')
    public={r['ref'] for r in context['public_sources']}
    for author,output in context['shared_contributions'].items():
        for row in output['facts']+output['conditions']:
            ref=row.get('source');quote=row.get('quote')
            if author==owner or ref in public or not isinstance(ref,str) or not isinstance(quote,str) or not quote.strip():continue
            record=chunks[author].setdefault(ref,dict(chunks=[],access='already_shared_quotes_not_full_original'))
            if quote not in record['chunks']:record['chunks'].append(quote)
    return ConstraintSession(context['task'],context['public_sources'],chunks,context['shared_contributions'],field_types)
