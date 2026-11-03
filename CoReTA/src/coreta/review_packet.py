"""Deterministic real-state to minimal-packet mapping. No model observations."""
import copy
from .closure import digest
from .minimal_review import preflight,fingerprint
from .review_preflight import prepare_review
from .schemas import ProtocolError


def build_packet(data):
    data,legacy_receipt=prepare_review(data)
    m=data['MATERIAL'];current=m['current']
    snapshots=[m['before'],current]+m.get('review_candidate_snapshots',[])
    # Only complete candidate snapshots may define historical objects.
    snapshots=[s for s in snapshots if 'artifact' in s.get('candidate',{})]
    packet={'packet_id':'review-'+fingerprint({'current':current,'pending':m['pending_closures']})[:20],
        'candidate_identity':{'version':current['version'],'hash':digest(current['candidate'])},
        'roles':{'integrator':'A0','builder':m['subject']['sent_from'],'checker':data['ACTOR']},
        'task':{'text':m['task']['prompt'],'sources':{'T1':m['task']['prompt']}},
        'current_targets':{'C1':{'definition':current['candidate']['artifact'],'candidate_version':current['version']}},
        'historical_objects':{},'issues':{},'supporting_history':copy.deepcopy(m.get('review_source_events',[]))+copy.deepcopy(m.get('review_candidate_snapshots',[])),
        'contribution':copy.deepcopy(m['subject'])}
    mapping={'candidate_hash':digest(current['candidate']),'issue_handles':{},'case_handles':{},'task_handles':{},'legacy_preflight':legacy_receipt}
    task_map={}
    for fact in m['task_facts']['payload']['facts']:
        for item in fact['check_items']:
            handle='T'+str(len(packet['task']['sources'])+1)
            packet['task']['sources'][handle]={'quoted_text':fact['quoted_text'],'check_item':item['description'],'interpretation_status':'model_asserted','source_binding':copy.deepcopy(fact['source_binding'])}
            task_map[(fact['fact_id'],item['item_id'])]=handle
            mapping['task_handles'][handle]={'fact_id':fact['fact_id'],'item_id':item['item_id']}
    issues={x['issue_id']:x for x in m['issues']};objects={}
    for number,(key,proposal) in enumerate(sorted(m['pending_closures'].items()),1):
        source=issues[key];handle='I'+str(number);mapping['issue_handles'][handle]=key
        issue={'closure_path':proposal['closure_path'],'acceptance_condition':source['acceptance_condition'],
            'description':source['description'],'active_objections':copy.deepcopy(source['objections']),
            'proposed_resolution_reason':proposal['reason'],'required_case_handles':[],
            'historical_cases':{},'current_target_handles':['C1'],'required_task_refs':[]}
        for record in source.get('evidence_records',[]):
            identity=(record['candidate_version'],record['candidate_hash'])
            if identity not in objects:
                snap=next((s for s in snapshots if s['version']==identity[0] and digest(s['candidate'])==identity[1]),None)
                if snap is None:raise ProtocolError('PACKET_ERROR','Complete original candidate missing for audit source')
                obj_handle='O'+str(len(objects)+1);objects[identity]=obj_handle
                packet['historical_objects'][obj_handle]={'candidate_version':identity[0],'candidate_hash':identity[1],'definition':snap['candidate']['artifact']}
            for index,case in enumerate(record['payload']['cases']):
                task_handle=task_map.get((case['fact_id'],case['check_item_id']))
                if task_handle is None:raise ProtocolError('PACKET_ERROR','Original case constraint missing')
                case_handle='H'+str(len(mapping['case_handles'])+1)
                issue['required_case_handles'].append(case_handle)
                issue['historical_cases'][case_handle]={'source_record_id':record['record_id'],'source_case_id':case['case_id'],
                    'audited_version':record['candidate_version'],'definition':{'object_handle':objects[identity]},
                    'input':case['input'],'quantity':case['quantity_key'],'expected_value':case['expected_value'],
                    'old_observed_value':case['observed_value'],'task_refs':[task_handle],
                    'original_claim':record['payload']['claim_text']}
                mapping['case_handles'][case_handle]={'issue_id':key,'record_id':record['record_id'],'case_index':index,'original_case':copy.deepcopy(case)}
                if task_handle not in issue['required_task_refs']:issue['required_task_refs'].append(task_handle)
        if not issue['required_task_refs']:issue['required_task_refs']=['T1']
        packet['issues'][handle]=issue
    preflight(packet)
    return packet,mapping
