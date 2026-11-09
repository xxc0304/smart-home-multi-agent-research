"""CPU checks with frozen actual histories and full real work responses."""
import contextlib,copy,io,json,sys,tempfile,unittest
from unittest.mock import patch
from pathlib import Path
import probe as m

class ActualHistoryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.pack=m.load(m.HERE/'PREFIXES.json');cls.ps=m.validate_pack(cls.pack)

    def test_original_condition_exactly_retains_real_input(self):
        for p in self.ps:self.assertEqual(m.work_request(p,'P1',0)['payload'],p['request']['payload'])

    def test_only_designated_peer_content_removed(self):
        for p in self.ps:
            old=m.decode(p['request']);new=m.decode(m.work_request(p,'P0',0))
            self.assertEqual({k:v for k,v in old.items() if k!='history'},{k:v for k,v in new.items() if k!='history'})
            self.assertEqual(new['history'],[x for i,x in enumerate(old['history']) if i not in p['remove_history_indices']])
            self.assertEqual([x for x in new['history'] if x['sender']==p['request']['actor']],[x for x in old['history'] if x['sender']==p['request']['actor']])

    def test_generic_check_does_not_add_gold_or_target(self):
        for p in self.ps:
            a=m.work_request(p,'P1',0);b=m.work_request(p,'P2',0)
            self.assertEqual(a['payload']['user'],b['payload']['user']);self.assertEqual(b['payload']['system'],a['payload']['system']+'\n\n'+m.CHECK)

    def test_real_full_responses_feed_private_final_without_future_peers(self):
        for p in self.ps:
            t=m.load(m.ROOT/p['source_path']);text=t['records'][p['source_record_index']]['raw_output']
            for cond in m.CONDITIONS:
                before=m.decode(m.work_request(p,cond,0));f=m.final_request(p,cond,0,text);after=m.decode(f,p['answer_suffix'])
                self.assertEqual(after['history'][:-1],before['history']);self.assertEqual(after['history'][-1]['text'],text)
                self.assertEqual(after['history'][-1]['sender'],p['request']['actor']);self.assertEqual(f['payload']['system'],m.FINAL)
                self.assertNotIn('target',after);self.assertNotIn('answer_aliases',after)

    def test_matched_seeds_and_role_routing_metadata(self):
        for p in self.ps:
            for rep in (0,1):
                rs=[m.work_request(p,c,rep) for c in m.CONDITIONS]
                self.assertEqual(len({r['seed'] for r in rs}),1)
                self.assertEqual(len({r['actor'] for r in rs}),1)
                self.assertEqual({r['max_new_tokens'] for r in rs},{1024})
                self.assertEqual({m.final_request(p,c,rep,'full valid response')['max_new_tokens'] for c in m.CONDITIONS},{256})

    def test_bad_condition_repeat_and_empty_work_rejected(self):
        p=self.ps[0]
        for value in (None,'', '   ',42,{}):
            with self.assertRaises(ValueError):m.final_request(p,'P0',0,value)
        with self.assertRaises(AssertionError):m.work_request(p,'P9',0)
        with self.assertRaises(AssertionError):m.work_request(p,'P1',2)

    def test_mutated_source_rejected_without_generation(self):
        bad=copy.deepcopy(self.pack);bad['sources'][next(iter(bad['sources']))]='0'*64
        with self.assertRaises(AssertionError):m.validate_pack(bad)

    def test_maximum_budget_and_two_roles(self):
        self.assertEqual(len(self.ps)*3*2*2,384)
        self.assertEqual(sum(p['role']=='E' for p in self.ps),16)
        self.assertEqual(sum(p['role']=='B' for p in self.ps),16)
        self.assertEqual(sum(p['primary_semantic_subset'] for p in self.ps),28)

    def test_inputs_remain_unmodified_by_all_conditions(self):
        baseline=json.dumps(self.pack,sort_keys=True)
        for p in self.ps:
            for c in m.CONDITIONS:
                for rep in (0,1):m.final_request(p,c,rep,'A full factual answer.\nA second paragraph.')
        self.assertEqual(json.dumps(self.pack,sort_keys=True),baseline)

    def runtime_fixture(self,root,fail=False):
        out=Path(root);m.atomic(out/'FREEZE.json',dict(files={}))
        m.atomic(out/'APPROVAL.json',dict(verdict='RUN_ALLOWED',freeze_sha256=m.sha(out/'FREEZE.json')))
        m.atomic(out/'PREFIXES.json',dict(prefixes=self.ps[:1]))
        m.atomic(out/'config.json',dict(max_length=16384))
        labels=m.load(m.HERE/'LABELS.json');m.atomic(out/'LABELS.json',labels)
        class Fake:
            calls=0
            def __init__(self,c):self.tokenizer=None
            def respond_many(self,requests,remaining):
                Fake.calls+=1;r=requests[0];bad=fail and Fake.calls==1
                return [dict(status='OUTPUT_LIMIT' if bad else 'OK',raw_output='SYNTHETIC_CPU_FIXTURE_NOT_EVIDENCE',usage=dict(output_tokens=r['max_new_tokens'] if bad else 5,adapter_enabled=r['actor']=='M1',batch_size=1,lora_layers=252,disabled_layers=0 if r['actor']=='M1' else 252))]
        return out,Fake

    def test_truncated_work_skips_only_its_final_without_retry(self):
        with tempfile.TemporaryDirectory() as root:
            out,fake=self.runtime_fixture(root,True)
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',fake),patch.object(m,'length',return_value=100),contextlib.redirect_stdout(io.StringIO()):m.run()
            self.assertEqual(fake.calls,11)
            cases=m.load(out/'CASES.json');self.assertEqual(len(cases),6)
            self.assertEqual(sum(v['status']=='WORK_OUTPUT_LIMIT' for v in cases.values()),1)
            self.assertEqual(m.load(out/'RESULTS.json')['confirmed_returns'],11)

    def test_host_overlength_never_calls_backend_or_fabricates_response(self):
        with tempfile.TemporaryDirectory() as root:
            out,fake=self.runtime_fixture(root)
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',fake),patch.object(m,'length',return_value=20000),contextlib.redirect_stdout(io.StringIO()):m.run()
            self.assertEqual(fake.calls,0);self.assertFalse((out/'ATTEMPTS.jsonl').exists())
            self.assertEqual(m.load(out/'RESULTS.json')['complete_paired_units'],0)

    def test_rerun_refused_instead_of_repeating_attempted_cases(self):
        with tempfile.TemporaryDirectory() as root:
            out,fake=self.runtime_fixture(root)
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',fake),patch.object(m,'length',return_value=100),contextlib.redirect_stdout(io.StringIO()):
                m.run();calls=fake.calls
                with self.assertRaises(FileExistsError):m.run()
                self.assertEqual(fake.calls,calls)

    def test_interrupted_final_preserves_attempt_and_work_without_retry(self):
        with tempfile.TemporaryDirectory() as root:
            out,fake=self.runtime_fixture(root)
            class Interrupted(fake):
                def respond_many(self,requests,remaining):
                    if fake.calls==1:
                        fake.calls+=1;raise RuntimeError('SYNTHETIC_INTERRUPTION_NOT_MODEL_ERROR')
                    return super().respond_many(requests,remaining)
            with patch.object(m,'OUT',out),patch.object(m,'MultiBackend',Interrupted),patch.object(m,'length',return_value=100),contextlib.redirect_stdout(io.StringIO()):m.run()
            result=m.load(out/'RESULTS.json')
            self.assertEqual(result['status'],'STOPPED_SYSTEM_FAULT');self.assertEqual(result['calls'],2)
            self.assertEqual(result['confirmed_returns'],1)
            self.assertEqual(len((out/'ATTEMPTS.jsonl').read_text().splitlines()),2)
            self.assertEqual(len((out/'responses.jsonl').read_text().splitlines()),1)

if __name__=='__main__':
    suite=unittest.defaultTestLoader.loadTestsFromTestCase(ActualHistoryTests)
    result=unittest.TextTestRunner(verbosity=2).run(suite)
    m.atomic(m.HERE/'TESTS.json',dict(verdict='PASS' if result.wasSuccessful() else 'FAIL',tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),actual_prefixes=32,actual_condition_response_replays=96,new_model_calls=0))
    sys.exit(0 if result.wasSuccessful() else 1)
