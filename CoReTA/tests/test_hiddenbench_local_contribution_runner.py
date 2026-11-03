import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from jsonschema import Draft202012Validator
from coreta.schemas import ProtocolError
from coreta.model_client import DeepSeekClient
import local_judgment_frontend as io
import run_hiddenbench_local_contribution_v2 as runner

class PipelineTests(unittest.TestCase):
    @staticmethod
    def response(payload,call):
        p=io.strict_json(payload['instructions'].split('PACKET=',1)[1])
        if 'contributions' in p:
            a=dict(choice='O1',reasoning='Technical integration fixture.',used_contributions=['C4'])
        elif 'historical_work' in p:
            a=dict(text=f'Unique technical contribution {call}.',status='proceed',source_ids=[p['member']+'.S1'],target_ids=['D1'])
        elif 'earlier_work' in p:
            a=dict(conclusion='Technical local result.',status='conditional',source_ids=[p['member']+'.S1'],scope='Technical fixture.',missing=[])
        else:a=dict(choice='O1',reasoning=f'Common technical draft {call}.',used_contributions=[])
        return dict(status='completed',usage=dict(input_tokens=10,output_tokens=10),output=[dict(type='message',content=[dict(type='output_text',text=json.dumps(a))])])

    def test_full_pipeline_has_same_drafts_isolated_methods_and_no_offline_reads(self):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);original=io.read;calls=0
            def guard(path):
                self.assertNotIn('OFFLINE_',str(path));return original(path)
            def mock(payload,timeout):
                nonlocal calls
                calls+=1
                Draft202012Validator.check_schema(payload['text']['format']['schema'])
                return self.response(payload,calls)
            with patch.object(io,'read',guard):s=runner.run(p,o,transport=mock,local_validation=True)
            self.assertEqual(s['attempts'],152);self.assertEqual(s['status'],'completed');self.assertEqual(s['reserved_output'],233472)
            self.assertEqual(len(list(o.glob('*.raw.txt'))),152)
            plan=original(p/'PLAN.json')['schedule']
            for task in runner.TASKS:
                for rep in (1,2):
                    for member in runner.MEMBERS:
                        matched=[r for r in plan if r['task']==task and r['repeat']==rep and r['member']==member and r['stage']=='first']
                        packets=[json.loads(original(o/'actual_requests'/f"{r['slot']:03d}.json")['instructions'].split('PACKET=',1)[1]) for r in matched]
                        self.assertEqual(packets[0],packets[1])
                        self.assertEqual([x['ref'] for x in packets[0]['own_sources']],[member+'.S1'])
            for row in plan:
                req=original(o/'actual_requests'/f"{row['slot']:03d}.json");packet=json.loads(req['instructions'].split('PACKET=',1)[1])
                if row['stage'] in ('initial','integrate'):
                    self.assertEqual(set(req['schema']['required']),{'choice','reasoning','used_contributions'})
                if row['stage']=='second':
                    first=next(r for r in s['rows'] if r['slot']==row['slot']-1)
                    self.assertEqual(packet['earlier_work'],first['answer']['text']);self.assertNotIn('historical_work',packet)
                if row['stage']=='integrate':
                    self.assertEqual(len(packet['contributions']),4)
                    self.assertEqual(req['schema']['properties']['used_contributions']['items']['enum'],['C1','C2','C3','C4'])
            with self.assertRaisesRegex(ValueError,'no resume'):runner.run(p,o,transport=mock,local_validation=True)

    def test_pass_and_corrupt_dependencies_keep_full_roster(self):
        for mode in ('pass','bad_initial','missing_team_field','bad_first','bad_second','incomplete_first'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1;r=self.response(payload,calls)
                    if mode=='pass' and calls==2:
                        a=json.loads(r['output'][0]['content'][0]['text']);a['status']='pass';r['output'][0]['content'][0]['text']=json.dumps(a)
                    if mode=='missing_team_field' and calls==1:
                        a=json.loads(r['output'][0]['content'][0]['text']);a.pop('used_contributions');r['output'][0]['content'][0]['text']=json.dumps(a)
                    if (mode=='bad_initial' and calls==1) or (mode=='bad_first' and calls==2) or (mode=='bad_second' and calls==3):r['output'][0]['content'][0]['text']='{'
                    if mode=='incomplete_first' and calls==2:r['status']='incomplete'
                    return r
                s=runner.run(p,o,transport=mock,local_validation=True);rows=io.read(o/'review.json')['rows']
                self.assertEqual(len(rows),152)
                if mode=='pass':
                    self.assertEqual(calls,151);self.assertEqual(rows[2]['status'],'skipped_pass')
                    self.assertEqual(rows[9]['status'],'readable')
                    packet=json.loads(io.read(o/'actual_requests/010.json')['instructions'].split('PACKET=',1)[1])
                    self.assertEqual(packet['contributions'][0]['status'],'abstain')
                elif mode=='bad_initial':
                    self.assertEqual(calls,134);self.assertTrue(all(r['status']=='blocked_upstream' for r in rows[1:19]));self.assertEqual(rows[19]['status'],'readable')
                elif mode=='missing_team_field':
                    self.assertEqual(calls,134);self.assertEqual(rows[0]['status'],'quarantined')
                    self.assertTrue(all(r['status']=='blocked_upstream' for r in rows[1:19]))
                    self.assertEqual(rows[19]['status'],'readable')
                elif mode in ('bad_first','incomplete_first'):
                    self.assertEqual(calls,150);self.assertEqual(rows[2]['status'],'blocked_upstream');self.assertEqual(rows[9]['status'],'blocked_upstream');self.assertEqual(rows[18]['status'],'readable')
                else:self.assertEqual(calls,151);self.assertEqual(rows[9]['status'],'blocked_upstream');self.assertEqual(rows[18]['status'],'readable')

    def test_systemic_faults_budget_and_missing_usage_stop_without_retry(self):
        for mode in ('two_bad','transport','usage','overcap','actual_input'):
            with self.subTest(mode=mode),tempfile.TemporaryDirectory() as tmp:
                p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p);calls=0
                def mock(payload,timeout):
                    nonlocal calls
                    calls+=1
                    if mode=='transport' and calls==2:raise TimeoutError('Technical fixture')
                    r=self.response(payload,calls)
                    if mode=='two_bad':r['output'][0]['content'][0]['text']='{'
                    if mode=='usage' and calls==2:r.pop('usage')
                    if mode=='overcap' and calls==2:r['usage']['output_tokens']=1537
                    if mode=='actual_input' and calls==2:r['usage']['input_tokens']=runner.INPUT_CAP+1
                    return r
                with self.assertRaises((RuntimeError,ProtocolError)):runner.run(p,o,transport=mock,local_validation=True)
                self.assertEqual(calls,2);self.assertEqual(io.read(o/'progress.json')['status'],'stopped')
                self.assertEqual(len(io.read(o/'review.json')['rows']),152)
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';o=Path(tmp)/'o';runner.freeze(p)
            with patch.object(DeepSeekClient,'size',return_value=runner.INPUT_CAP+1):
                with self.assertRaisesRegex(RuntimeError,'pre-request'):runner.run(p,o,transport=self.response,local_validation=True)
            self.assertEqual(io.read(o/'progress.json')['attempts'],0)

    def test_long_capped_outputs_fit_and_gates_reject_wrong_batch(self):
        from tokenizers import Tokenizer
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'p';runner.freeze(p);_,_,config=runner.verify(p)
            tok=Tokenizer.from_file(str(runner.TOKENIZER));count=lambda x:len(tok.encode(x,add_special_tokens=False).ids)
            draft=runner.draft_from(dict(choice=None,reasoning='Draft basis. '*400,annotation_issues=[]))
            self.assertLessEqual(count(json.dumps(dict(choice=None,reasoning=draft['reason'],used_contributions=[]))),1536)
            task=runner.TASKS[0];packets=[io.read(p/'contexts'/task/f'{m}.json') for m in runner.MEMBERS]
            local=dict(conclusion='Local basis. '*350,status='conditional',scope='Fixture scope. '*10,missing=['Fixture uncertainty. '*10])
            self.assertLessEqual(count(json.dumps(dict(local,source_ids=['A1.S1']))),1536)
            deliveries={m:dict(local,evidence=[dict(source=x['own_sources'][0]['ref'],quote=x['own_sources'][0]['content'])]) for m,x in zip(runner.MEMBERS,packets)}
            packet=runner.team.assemble(packets[0]['task'],packets[0]['public_sources'],draft,packets,deliveries)
            req=runner.team.request(packet);client=DeepSeekClient(config,lambda *args:None,transport=lambda *a:None,token_counter=count)
            size=client.size(client.payload(req['instructions'],req['schema'],1536))
            self.assertLess(size,32768)
            with self.assertRaises(FileNotFoundError):runner.gates(p)
            sha=io.digest(p/'manifest.json')
            io.write(p/'PREFLIGHT.json',dict(status='passed',manifest_sha256=sha))
            io.write(p/'EXPERIMENT_REVIEW.json',dict(science='PASS',readiness='PASS',technical_launch='RUN_ALLOWED',manifest_sha256=sha))
            auth=dict(authorized=True,max_requests=152,max_output_tokens=233472,max_input_tokens=786432,manifest_sha256=sha,destination='https://api.deepseek.com/responses',user_authorization_text='TEST ONLY')
            io.write(p/'AUTHORIZATION.json',auth);runner.gates(p)
            io.write(p/'AUTHORIZATION.json',dict(auth,max_requests=24))
            with self.assertRaisesRegex(ValueError,'authorization'):runner.gates(p)
            (p/'contexts'/task/'A4.json').write_text('{}',encoding='utf-8')
            with self.assertRaisesRegex(ValueError,'changed'):runner.verify(p)

if __name__=='__main__':unittest.main()
