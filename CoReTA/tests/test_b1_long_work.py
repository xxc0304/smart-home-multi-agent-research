"""V6 work budget registration and old-contract compatibility, no model calls."""
import json,sys,tempfile,unittest
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
from b1_controls import Trial,replay,summarize
from b1_output_contract import LONG_WORK_VERSION
from b1_runtime import run_batch,validate_runtime,trial_parameters,load_json
from test_b1_controls import task,finish
from test_b1_runtime import runtime_config,origin,ScriptedFixture
SUFFIX='\n\nOutput ONLY the short answer. Do not explain.'

def make(t=None,**extra):
    options=dict(expert_actor='M1',fixture=True,answer_tokens=256,answer_suffix=SUFFIX,output_contract=LONG_WORK_VERSION)
    options.update(extra);return Trial(t or task(),**options)

class LongWorkChecks(unittest.TestCase):
    def test_only_work_cap_changes_prompts_visibility_and_seeds_identical(self):
        old=Trial(task(),expert_actor='M1',fixture=True,answer_tokens=256,answer_suffix=SUFFIX);new=make()
        for _ in range(52):
            a,b=old.next_request(),new.next_request()
            self.assertEqual({k:v for k,v in a.items() if k!='max_new_tokens'},{k:v for k,v in b.items() if k!='max_new_tokens'})
            self.assertEqual(b['max_new_tokens'],1024 if b['stage']=='work' else 256)
            old.submit(a['request_id'],'1900');new.submit(b['request_id'],'1900')
        self.assertTrue(new.complete);self.assertEqual(new.export()['protocol'],'B1_TWO_ROUND_FOUR_ARM_V6')
        self.assertEqual(old.export()['protocol'],'B1_TWO_ROUND_FOUR_ARM_V2')
        self.assertEqual(replay(new.export()).export(),new.export())

    def test_no_word_limit_or_new_unknown_instruction(self):
        t=make();r=t.next_request();rec=t.submit(r['request_id'],'word '*300+'\nmore words')
        self.assertEqual(rec['status'],'OK');self.assertFalse((rec['usage'] or {}).get('format_warning'))
        finish(t);self.assertTrue(t.complete)

    def test_long_contract_requires_registered_short_answer_shape(self):
        for extra in (dict(answer_tokens=128),dict(answer_tokens=64),dict(answer_suffix='')):
            with self.assertRaisesRegex(ValueError,'registered_answer_contract'):make(**extra)

    def test_real_failure_still_isolates_dependents(self):
        t=make()
        for _ in range(4):r=t.next_request();t.submit(r['request_id'],'1900')
        r=t.next_request();t.submit(r['request_id'],'unfinished',status='OUTPUT_LIMIT')
        finish(t);self.assertEqual(t.failed,{'A'});self.assertEqual(len(t.finals['B']),4)
        self.assertEqual(replay(t.export()).export(),t.export())

    def test_cannot_pool_old_and_new_contract(self):
        a=finish(Trial(task(),expert_actor='M1',fixture=True,answer_tokens=256,answer_suffix=SUFFIX)).export()
        b=finish(make(dict(task(),id='SECOND'))).export()
        targets={i:dict(id=i,answer='1900') for i in ('HOST_FIXTURE','SECOND')}
        with self.assertRaisesRegex(ValueError,'mixed_batch_conditions'):summarize([a,b],targets,list(targets),{i:i for i in targets})

    def test_runtime_manifest_registration_and_resume_gate(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir();adapter=folder/'adapter';origin(base,adapter)
            old=runtime_config(base,adapter);old.update(answer_tokens=256,answer_suffix=SUFFIX,answer_policy_version='B1_SHORT256_SUFFIX_V2')
            new=dict(old,work_tokens=1024,output_contract=LONG_WORK_VERSION,answer_policy_version=LONG_WORK_VERSION)
            self.assertEqual(validate_runtime(new)['qualification'],'FIXTURE_ONLY')
            for broken in (dict(new,work_tokens=512),dict(old,work_tokens=1024),dict(new,answer_policy_version='B1_SHORT256_SUFFIX_V2')):
                with self.assertRaisesRegex(ValueError,'B1_decoding_policy'):validate_runtime(broken)
            self.assertEqual(trial_parameters(new,0)['output_contract'],LONG_WORK_VERSION)
            m=run_batch(new,[task()],{task()['id']:'G'},folder/'new',fixture_backend=ScriptedFixture())
            self.assertEqual(m['protocol'],'B1_TWO_ROUND_FOUR_ARM_V6')
            trace=load_json(folder/'new/trials/000.json');self.assertTrue(trace['complete'])
            self.assertTrue(all(r['max_new_tokens']==1024 for r in trace['records'] if r['stage']=='work'))
            run_batch(old,[task()],{task()['id']:'G'},folder/'old',fixture_backend=ScriptedFixture())
            tasks=[task(),dict(task(),id='SECOND')]
            with self.assertRaisesRegex(ValueError,'resume_configuration_changed'):
                run_batch(new,tasks,{t['id']:'G' for t in tasks},folder/'mixed',resume_from=folder/'old',fixture_backend=ScriptedFixture())

if __name__=='__main__':unittest.main()
