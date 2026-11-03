"""Bounded transport for standalone review packets; no full-task orchestration."""
import json
import time
from jsonschema import Draft202012Validator
from .schemas import ProtocolError


def provider_payload(client,request,output_limit):
    instructions=request['instructions']+'\n'+json.dumps({'packet':request['packet'],'feedback':request['feedback']},ensure_ascii=False,separators=(',',':'))
    return client.payload(instructions,request['schema'],output_limit)


def execute_review(adapter,client,packet,timeout_seconds=1800):
    request=adapter.request(packet);deadline=time.monotonic()+timeout_seconds
    output_limit=client.config['generation']['max_output_tokens']['inspect']
    projections=[];terminal=None
    while True:
        payload=provider_payload(client,request,output_limit)
        size=client.size(payload)
        adapter.log('provider_preflight',{'request_id':request['request_id'],'input_estimate':size,
            'input_limit':client.config['generation']['max_input_tokens'],'output_limit':output_limit})
        if size>client.config['generation']['max_input_tokens']:
            terminal={'code':'CONTEXT_OVERFLOW','detail':'Actual provider payload exceeds input limit; not sent'};break
        raw='';status='completed'
        try:
            raw=client.complete(payload,deadline=deadline,logical_seed='minimal-review|'+packet['packet_id'])
        except ProtocolError as exc:
            if exc.code not in {'SCHEMA_ERROR','INVALID_JSON'}:
                terminal={'code':exc.code,'detail':exc.detail};break
            raw=getattr(client,'last_output','')
            incomplete=getattr(client,'last_incomplete',None)
            status='incomplete' if incomplete else 'completed'
            adapter.log('provider_output_error',{'code':exc.code,'detail':exc.detail,'raw':raw,'incomplete':incomplete})
        projection=adapter.consume(request['request_id'],raw,packet['candidate_identity'],status)
        projections.append(projection)
        structural=[]
        if status!='completed':structural.append('Incomplete output; regenerate complete object preserving observations')
        try:
            value=json.loads(raw)
            structural += [f'{list(e.path)}: {e.message}' for e in Draft202012Validator(request['schema']).iter_errors(value)]
        except json.JSONDecodeError as exc:structural.append(str(exc))
        if not structural:break  # Business/semantic conflicts remain evidence; never retry them away.
        if adapter.repairs>=adapter.budget.limit:
            terminal={'code':'REPAIR_LIMIT','detail':'Structural recovery exhausted; all attempts retained'};break
        try:request=adapter.repair(request['request_id'],raw,structural)
        except ProtocolError as exc:
            terminal={'code':exc.code,'detail':exc.detail};break
    result={'scope':'Standalone component only; not end-to-end task success','terminal_error':terminal,
        'http_attempts':client.attempts,'repairs_used':adapter.repairs,'response_attempts':len(projections),
        'final_projection':projections[-1] if projections else None,'task_correctness_proven':False}
    adapter.log('execution_result',result)
    return result
