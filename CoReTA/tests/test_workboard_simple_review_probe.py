"""Offline intervention-isolation and actual shared-runner execution checks."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from coreta.handoff.__main__ import PROJECT
from coreta.handoff.contracts import HandoffContracts
from coreta.schemas import ProtocolError

sys.path.insert(0,str(PROJECT/'tools'))
import workboard_simple_review_probe as probe


class SimpleReviewProbeTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='plain-review-offline-')
        self.addCleanup(temp.cleanup);self.root=Path(temp.name);self.prepared=self.root/'prepared'
        self.manifest=probe.prepare(self.prepared)
        guard=patch('urllib.request.urlopen',side_effect=AssertionError('Offline network forbidden'))
        guard.start();self.addCleanup(guard.stop)

    def test_current_exact_and_plain_only_changes_instruction_prefix(self):
        for item in self.manifest['inputs']:
            c=probe.read(self.prepared/(item['id']+'--C.json'))
            s=probe.read(self.prepared/(item['id']+'--S.json'))
            historical=probe.read(probe.PREVIOUS/(item['id']+'--B.json'))
            self.assertEqual(c,probe.format_payload(historical))
            self.assertEqual(c['instructions'],historical['instructions'])
            self.assertEqual(c['text']['format'],{'type':'json_object'})
            self.assertEqual(c['input'],probe.FORMAT_INPUT)
            self.assertEqual(c['instructions'].split('\nPACKET=',1)[1],s['instructions'].split('\nPACKET=',1)[1])
            self.assertEqual({k:v for k,v in c.items() if k!='instructions'},
                             {k:v for k,v in s.items() if k!='instructions'})
            prefix=s['instructions'].split('\nPACKET=',1)[0]
            self.assertEqual(prefix,probe.COMMON+'\n'+probe.DUTIES[item['stage']])
            self.assertNotRegex(prefix,r'\b(?:Pine|son|110)\b')
            p=probe.packet_of(s)
            self.assertEqual(p['SELF']['agent_id'],item['member'])
            self.assertEqual(p['SOURCE_ACCESS']['direct_original_refs'],sorted(['T',*[m['ref'] for m in p['SELF_MATERIALS']]]))

    def test_shared_runner_executes_fixed32_without_feedback_injection(self):
        seen=[]
        def script(payload,timeout):
            seen.append(payload)
            return {'status':'completed','usage':{'input_tokens':2,'output_tokens':3},'output':[
                {'type':'message','content':[{'type':'output_text','text':json.dumps(
                    {'finding':'unable','observation':'SCRIPTED_ONLY_MARKER','scope':'offline fixture'})}]}]}
        result=probe.run(self.prepared,self.root/'fixture',transport=script)
        self.assertEqual((result['status'],result['completed'],result['actual_http_attempts']),('completed',32,0))
        for condition in ['C','S']:self.assertEqual(sum(x['condition']==condition for x in result['rows']),16)
        for row,payload in zip(self.manifest['calls'],seen):
            self.assertEqual(payload,probe.read(self.prepared/row['payload_file']))
            self.assertNotIn('SCRIPTED_ONLY_MARKER',payload['instructions'])
        self.assertEqual(result['unknown_usage_attempts'],0)

    def test_actual_fourth_response_is_rejected_without_selecting_a_draft(self):
        rows=[json.loads(x) for x in (PROJECT/'runs/simple-review-live-20261023-r1/responses.jsonl').read_text(encoding='utf-8').splitlines()]
        response=rows[3]['response']
        raw=''.join(part['text'] for item in response['output'] if item['type']=='message'
                    for part in item['content'] if part['type']=='output_text')
        first,end=json.JSONDecoder().raw_decode(raw)
        second=json.loads(raw[end:])
        self.assertNotEqual(first,second)
        schema=probe.read(self.prepared/self.manifest['calls'][3]['payload_file'])['instructions'].rsplit('\nOUTPUT_SCHEMA=',1)[1]
        with self.assertRaises(ProtocolError):HandoffContracts.decode(raw,json.loads(schema))
        seen=[]
        def replay(payload,timeout):
            seen.append(payload)
            return response
        result=probe.run(self.prepared,self.root/'replay',transport=replay)
        self.assertEqual(len(seen),1)
        self.assertEqual((result['status'],result['completed'],result['actual_http_attempts']),('stopped_on_first_error',0,0))
        self.assertEqual(result['output_tokens'],794)
        self.assertEqual(sum(r['status']=='not_started' for r in result['rows']),31)

    def test_json_mode_still_enforces_schema_and_rejects_malformed_outputs(self):
        schema=json.loads(probe.read(self.prepared/self.manifest['calls'][0]['payload_file'])['instructions'].rsplit('\nOUTPUT_SCHEMA=',1)[1])
        valid={'finding':'unable','observation':'fixture','scope':'offline'}
        self.assertEqual(HandoffContracts.decode(json.dumps(valid),schema),valid)
        for raw in [json.dumps(valid)+'\n'+json.dumps(valid),json.dumps(valid)+' explanation',
                    '```json\n'+json.dumps(valid)+'\n```',json.dumps(valid)[:-1],
                    '{"finding":"unable","finding":"issue","observation":"x","scope":"y"}',
                    '{"finding":"unknown","observation":"x","scope":"y"}',
                    '{"finding":"unable","observation":"x"}',
                    '{"finding":"unable","observation":"x","scope":"y","extra":true}']:
            with self.subTest(raw=raw),self.assertRaises(ProtocolError):
                HandoffContracts.decode(raw,schema)


if __name__=='__main__':unittest.main()
