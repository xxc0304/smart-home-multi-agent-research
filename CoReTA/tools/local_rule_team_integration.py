"""Native-member adapter only. Keeps the existing ordinary integration prompt."""
import copy
import json
import local_judgment_frontend as io
from prepare_local_rule_adoption import INSTRUCTIONS

def assemble(task,public_sources,historical_work,member_packets,deliveries):
    """Publish only evidence actually disclosed by each member's final delivery."""
    if len(member_packets)<2 or set(deliveries)!={p['member'] for p in member_packets}:raise ValueError('member set differs')
    shared={s['ref']:s['content'] for s in public_sources};contributions=[]
    for index,packet in enumerate(member_packets,1):
        if packet['task']!=task or packet['public_sources']!=public_sources:raise ValueError('task/public context differs')
        answer=deliveries[packet['member']]
        visible={s['ref']:s['content'] for s in public_sources+packet['own_sources']}
        for e in answer['evidence']:
            if e['source'] not in visible or visible[e['source']]!=e['quote']:raise ValueError('not a disclosed visible original')
            if e['source'] in shared and shared[e['source']]!=e['quote']:raise ValueError('source content differs')
            shared[e['source']]=e['quote']
        contributions.append(dict(id=f'C{index}',member=packet['member'],conclusion=answer['conclusion'],status=answer.get('status'),
            scope=answer.get('scope'),missing=answer.get('missing'),source_ids=[e['source'] for e in answer['evidence']]))
    return dict(task=copy.deepcopy(task),public_sources=copy.deepcopy(public_sources),historical_work=copy.deepcopy(historical_work),
        contributions=contributions,disclosed_evidence=[dict(ref=k,content=v) for k,v in sorted(shared.items())])

def schema(packet):
    ids=[c['id'] for c in packet['contributions']]
    if len(ids)!=len(set(ids)):raise ValueError('duplicate contribution id')
    return dict(type='object',additionalProperties=False,required=['reasoning'],properties=dict(
        choice=dict(anyOf=[dict(type='string',enum=[c['id'] for c in packet['task']['choices']]),dict(type='null')]),
        reasoning=dict(type='string',minLength=1),used_contributions=dict(type='array',items=dict(type='string',enum=ids))))

def request(packet):
    return dict(instructions=INSTRUCTIONS+'\nPACKET='+json.dumps(packet,ensure_ascii=False),schema=schema(packet),max_output_tokens=1536)

def decode(raw,packet):
    a=io.strict_json(raw)
    if not isinstance(a,dict) or not isinstance(a.get('reasoning'),str) or not a['reasoning'].strip():raise io.InterfaceError('unreadable final reasoning')
    issues=[];choice=a.get('choice');choices={c['id'] for c in packet['task']['choices']};ids={c['id'] for c in packet['contributions']}
    if 'choice' not in a:issues.append(dict(field='choice',issue='missing'))
    elif choice is not None and (not isinstance(choice,str) or choice not in choices):issues.append(dict(field='choice',issue='invalid',raw=copy.deepcopy(choice)));choice=None
    refs=a.get('used_contributions',[]);valid=[]
    if not isinstance(refs,list):issues.append(dict(field='used_contributions',issue='wrong_type',raw=copy.deepcopy(refs)));refs=[]
    for ref in refs:
        if isinstance(ref,str) and ref in ids:
            if ref not in valid:valid.append(ref)
        else:issues.append(dict(field='used_contributions',issue='unknown',raw=copy.deepcopy(ref)))
    if 'used_contributions' not in a:issues.append(dict(field='used_contributions',issue='missing'))
    extra=set(a)-set(schema(packet)['properties'])
    if extra:issues.append(dict(field='extra_fields',issue='retained_in_raw',names=sorted(extra)))
    return dict(choice=choice,reasoning=a['reasoning'],used_contributions=valid,annotation_issues=issues)
