"""Meaningful safety/consistency checks; no model calls or claimed task gains."""
import copy
import json
import unittest
from coreta.constraint_commit import ConstraintSession, CommitError
import constraint_commit_probe as probe


class ConstraintCommitTests(unittest.TestCase):
    def make(self):
        task=dict(choices=[dict(id='a',text='Ada'),dict(id='b',text='Bo'),dict(id='c',text='Cy')])
        public=[dict(ref='TASK',content='Select a participant.'),dict(ref='PUB',content='Ada is 53; Bo is 17. Cy age unknown.')]
        sources={'A1':{'S1':dict(chunks=['The selected participant is under 30.'],access='own_original')}}
        pool={'A1':dict(text='local',facts=[dict(candidate='a',field='age',value=53,source='PUB',quote='Ada is 53'),
              dict(candidate='b',field='age',value=17,source='PUB',quote='Bo is 17')],
              conditions=[dict(field='age',op='lt',value=30,source='S1',quote='under 30')],caveats=[])}
        return ConstraintSession(task,public,sources,pool,dict(age='number'))

    def update(self,s,key,action='retire'):
        return dict(entry_id=key,action=action,reason='Offline action fixture, not source entailment proof.',evidence_ids=[next(iter(s.evidence))])

    def test_report_reference_and_commit_differ_only_in_delivery(self):
        s=self.make();p=dict(choice='a',reasoning='Historical proposal.')
        r=s.deliver(p,'report_reference',1);c=s.deliver(p,'constraint_commit',1)
        self.assertEqual(r['choice'],'a');self.assertIsNone(c['choice'])
        self.assertEqual(c['selector'],'no_admissible_proposal')
        self.assertEqual(c['not_excluded'],['b','c'])
        self.assertEqual(s.version,1)

    def test_unique_choice_is_logged_as_host_not_model_acceptance(self):
        s=self.make()
        s.contributions['A1']['facts'].append(dict(candidate='c',field='age',value=60,source='PUB',quote='Ada is 53'))
        # Explicitly wrong semantic encoding is still structurally well-formed.
        s=ConstraintSession(s.task,s.public,s.sources,s.contributions,s.field_types)
        r=s.deliver(dict(choice='a',reasoning='Keep Ada.'),'constraint_commit',1)
        self.assertEqual(r['choice'],'b');self.assertEqual(r['model_choice'],'a')
        self.assertTrue(r['host_changed_choice']);self.assertEqual(r['feasibility'],'not_certified')
        self.assertEqual(len(r['exclusion_trace']),2)

    def test_unknown_does_not_exclude_or_certify(self):
        s=self.make();r=s.deliver(dict(choice='c',reasoning='Best effort.'),'constraint_commit',1)
        self.assertEqual(r['choice'],'c');self.assertEqual(r['feasibility'],'not_certified')
        self.assertEqual(s.report()['candidate_checks'][2]['checks'][0]['status'],'unknown')

    def test_retirement_and_restoration_recompute_and_keep_stable_ids(self):
        s=self.make();old=s.report()
        s.revise([self.update(s,'A1.C1')],1)
        self.assertEqual(s.report()['not_excluded'],['a','b','c'])
        with self.assertRaises(CommitError):s.deliver(dict(choice='a',reasoning='x'),'constraint_commit',1)
        s.revise([self.update(s,'A1.C1','restore')],2)
        self.assertEqual(s.report()['candidate_checks'],old['candidate_checks'])
        self.assertEqual(s.report()['member_conditions'][0]['id'],'A1.C1')
        self.assertEqual(s.events[-1]['reason_entailment'],'not_verified_by_host')

    def test_wrong_fact_withdrawal_restores_unknown_not_opposite(self):
        s=self.make();s.revise([self.update(s,'A1.F1')],1)
        self.assertIn('a',s.report()['not_excluded'])
        self.assertIsNone(s.report()['model_fact_table'].get('a',{}).get('age'))

    def test_transaction_rejects_every_change_if_one_is_invalid(self):
        s=self.make();before=copy.deepcopy(s.entries)
        bad=self.update(s,'A1.F2');bad['evidence_ids']=['unseen-private']
        with self.assertRaises(CommitError):s.revise([self.update(s,'A1.F1'),bad],1)
        self.assertEqual(s.entries,before);self.assertEqual(s.version,1)
        with self.assertRaises(CommitError):s.revise([self.update(s,'A1.F1')]*2,1)

    def test_readable_bad_optional_action_does_not_destroy_final_core(self):
        s=self.make();context=dict(task=s.task)
        raw=json.dumps(dict(choice='b',reasoning='Use supported candidate.',updates=[dict(entry_id='fake')]))
        r=probe.process(raw,context,s,'constraint_commit',1)
        self.assertEqual(r['model_answer']['choice'],'b')
        self.assertEqual(r['action']['status'],'rejected_optional_action')
        self.assertEqual(r['delivery']['choice'],'b')

    def test_no_action_metadata_is_not_fabricated(self):
        s=self.make();r=probe.process('{"choice":"b","reasoning":"Full historical body."}',dict(task=s.task),s,'constraint_commit',1)
        self.assertEqual(r['action']['status'],'not_proposed')
        with self.assertRaises(CommitError):probe.process('{"choice":"b","reasoning":"x"}',dict(task=s.task),s,'constraint_commit',True)

    def test_conflicting_facts_are_unknown(self):
        s=self.make();pool=copy.deepcopy(s.contributions)
        pool['A1']['facts'].append(dict(candidate='a',field='age',value=20,source='PUB',quote='Ada is 53'))
        s=ConstraintSession(s.task,s.public,s.sources,pool,s.field_types)
        self.assertTrue(s.report()['fact_conflicts']);self.assertIn('a',s.report()['not_excluded'])

    def test_type_citation_and_expression_losses_are_reported_per_item(self):
        s=self.make();pool=copy.deepcopy(s.contributions)
        pool['A1']['facts'].extend([dict(candidate='c',field='age',value=True,source='PUB',quote='Cy age unknown'),
            dict(candidate='c',field='age',value=7,source='unseen',quote='private'),
            dict(candidate='c',field='age',value=7,source='PUB',quote='Ada is 53\nThe selected participant')])
        s=ConstraintSession(s.task,s.public,s.sources,pool,s.field_types)
        rejected=[r for r in s.admission if r['status']=='not_executable']
        self.assertEqual(len(rejected),3);self.assertEqual(len(s.entries),3)
        self.assertIn('c',s.report()['not_excluded'])

    def test_all_excluded_is_semantic_unresolved_not_arbitrary_choice(self):
        s=self.make();pool=copy.deepcopy(s.contributions)
        pool['A1']['facts'].append(dict(candidate='c',field='age',value=70,source='PUB',quote='Cy age unknown'))
        pool['A1']['conditions'][0]['value']=0
        s=ConstraintSession(s.task,s.public,s.sources,pool,s.field_types)
        r=s.deliver(dict(choice='b',reasoning='Try Bo.'),'constraint_commit',1)
        self.assertIsNone(r['choice']);self.assertEqual(r['selector'],'encoded_conflict')

    def test_core_json_boundaries_stay_strict(self):
        s=self.make()
        for raw in ['{"choice":"a","choice":"b","reasoning":"x"}', '{"choice":"a","reasoning":null}', '{"choice":null,"reasoning":"x","n":NaN}']:
            with self.assertRaises(ValueError):probe.process(raw,dict(task=s.task),s,'report_reference',1)


if __name__=='__main__':unittest.main()
