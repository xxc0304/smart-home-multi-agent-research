from pathlib import Path
import tempfile
import unittest

import local_judgment_frontend as io
import build_local_rule_development as builder


class LocalRuleDevelopmentTests(unittest.TestCase):
    def test_oracles_match_independent_hand_checks(self):
        expected={'rule-dev-01':'Birch','rule-dev-02':'B','rule-dev-03':'B',
                  'rule-dev-04':'Alpha_only','rule-dev-05':'75','rule-dev-06':'Cloud_B'}
        for name,answer in expected.items():self.assertEqual(builder.oracle(name)[0],answer)
        self.assertEqual(builder.oracle('rule-dev-01')[1],{'Alder':88.0,'Birch':112.0})
        self.assertAlmostEqual(builder.oracle('rule-dev-02')[1]['A'],1.52)
        self.assertAlmostEqual(builder.oracle('rule-dev-03')[1]['B'],0.675)
        self.assertEqual(builder.oracle('rule-dev-04')[1]['both_remaining'],10)
        self.assertEqual(builder.oracle('rule-dev-05')[1]['fixture_active_minutes'],35)

    def test_packets_have_no_gold_and_private_sources_do_not_cross_members(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'pack';builder.build(out)
            for entry in builder.tasks():
                packets=[io.read(out/entry['id']/'packets'/f'A{i}.json') for i in range(1,4)]
                for i,p in enumerate(packets,1):
                    self.assertEqual(set(p),{'task','member','public_sources','own_sources','historical_work'})
                    self.assertEqual(p['member'],f'A{i}')
                    self.assertTrue(all(s['ref'].startswith(f'A{i}.') for s in p['own_sources']))
                    self.assertEqual(p['historical_work'],packets[0]['historical_work'])
                    self.assertEqual(p['public_sources'],packets[0]['public_sources'])
                    self.assertEqual(set(p['task']),{'task_id','scenario','shared_information','choices','instruction'})
                    self.assertEqual([s['content'] for s in p['own_sources']],entry['private'][i-1])
                    self.assertNotIn('local_question',p)

    def test_three_wrong_and_correct_partial_controls_are_retained(self):
        entries=builder.tasks()
        self.assertEqual(sum(t['draft_type']=='wrong' for t in entries),3)
        self.assertEqual(sum(t['draft_type']=='correct_supported_control' for t in entries),1)
        self.assertEqual(sum(t['draft_type']=='incomplete' for t in entries),1)
        for t in entries:
            self.assertEqual(len(t['private']),3)
            if t['draft_type']=='wrong':self.assertNotEqual(t['draft'],t['expected'])
            if t['draft_type'].startswith('correct'):self.assertEqual(t['draft'],t['expected'])
            if t['draft_type']=='incomplete':self.assertIsNone(t['draft'])

    def test_manifest_integrity_and_no_overwrite(self):
        with tempfile.TemporaryDirectory() as temp:
            out=Path(temp)/'pack';result=builder.build(out)
            self.assertEqual(result,dict(tasks=6,packets=18,oracle_checks=6,model_calls=0))
            manifest=io.read(out/'manifest.json')
            self.assertFalse(manifest['resource_advantage_measured'])
            self.assertFalse(manifest['official_benchmark'])
            self.assertFalse(manifest['outcome_based_selection'])
            for name,sha in manifest['files'].items():self.assertEqual(io.digest(out/name),sha)
            self.assertEqual(len(list(out.glob('*/packets/*.json'))),18)
            with self.assertRaises(ValueError):builder.build(out)


if __name__=='__main__':unittest.main()
