import copy
import json
import unittest
from pathlib import Path
from coreta.closure_diff import DiffClosureRunner, candidate_diff
from coreta.closure import ClosureRunner
from coreta.schemas import ProtocolError
from test_closure_feedback import FeedbackChecks

ROOT=Path(__file__).resolve().parents[1]

class DiffChecks(FeedbackChecks):
    def setup_runner(self):
        runner=super().setup_runner()
        runner.__class__=DiffClosureRunner
        return runner

    def fixtures(self):
        plan=json.loads((ROOT/'engineering/RETENTION_PLAN_20261019.json').read_text(encoding='utf-8'))
        selected={'number_theory/592','intermediate_algebra/156','intermediate_algebra/1262',
                  'counting_and_probability/525','number_theory/643'}
        for job in plan['jobs']:
            if job['task_id'].removeprefix('math_train/') not in selected: continue
            folder=ROOT/'runs/retention-feedback-20261019'/job['job_id']
            requests=[json.loads(x) for x in (folder/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
            prompt=requests[-1]['payload']['instructions']
            material=json.JSONDecoder().raw_decode(prompt[prompt.index('\n{"ACTOR"')+1:])[0]['MATERIAL']
            records=[json.loads(x) for x in (folder/'validation.jsonl').read_text(encoding='utf-8').splitlines()]
            value=json.loads(records[-1]['raw'])
            runner=self.setup_runner(); runner.current=copy.deepcopy(material['current'])
            runner.version=material['candidate_version']
            runner.issues={i['issue_id']:copy.deepcopy(i) for i in material['issues']}
            yield job['task_id'],runner,value

    def test_five_real_rejected_updates_reach_pending_without_erasing_declarations(self):
        count=0
        for task,runner,value in self.fixtures():
            count+=1
            with self.subTest(task=task):
                with self.assertRaises(ProtocolError): ClosureRunner.validate_proposals(runner,value)
                runner.validate_proposals(value)
                saved=copy.deepcopy(value)
                runner.commit_proposals(value)
                self.assertEqual(value,saved)
                self.assertTrue(runner.pending)
                self.assertTrue(all(runner.issues[k]['status']=='pending_check' for k in runner.pending))
                audit=json.loads((runner.directory/'candidate_diffs.jsonl').read_text(encoding='utf-8'))
                self.assertEqual(audit['model_declarations'],[
                    {'issue_id':p['issue_id'],'changed_step_ids':p['changed_step_ids']} for p in value['closure_proposals']])
        self.assertEqual(count,5)

    def test_evidence_and_objection_coverage_still_required(self):
        _,runner,value=next(self.fixtures())
        bad=copy.deepcopy(value); bad['closure_proposals'][0]['evidence_refs']=[]
        with self.assertRaises(ProtocolError): runner.validate_proposals(bad)
        bad=copy.deepcopy(value); bad['closure_proposals'][0]['response_to_objection_ids']=[]
        with self.assertRaises(ProtocolError): runner.validate_proposals(bad)

    def test_exact_diff_and_artifact_only_change(self):
        before={'steps':[{'id':'s1','text':'a'},{'id':'s2','text':'b'}],'artifact':'a'}
        after={'steps':[{'id':'s1','text':'c'},{'id':'s3','text':'d'}],'artifact':'b'}
        self.assertEqual(candidate_diff(before,after),{'added_step_ids':['s3'],
            'modified_step_ids':['s1'],'removed_step_ids':['s2'],'artifact_changed':True})
        other=copy.deepcopy(before); other['artifact']='b'
        self.assertEqual(candidate_diff(before,other)['modified_step_ids'],[])
        self.assertTrue(candidate_diff(before,other)['artifact_changed'])

if __name__=='__main__': unittest.main()
