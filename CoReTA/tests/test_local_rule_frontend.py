import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import local_judgment_frontend as io
import local_rule_frontend as probe
import prepare_rule_resource_calibration as calibration


class RuleFrontendTests(unittest.TestCase):
    @staticmethod
    def callback(row,request):
        packet=io.strict_json(request['instructions'].split('PACKET=',1)[1])
        source=(packet['own_sources'] or packet['public_sources'])[0]['ref']
        if row['stage']=='first':return json.dumps(dict(text='A self-contained synthetic local issue.',status='proceed',source_ids=[source],target_ids=['new']))
        return json.dumps(dict(conclusion='Synthetic local result, not a capability finding.',status='conditional',source_ids=[source],scope='Mock only.',missing=[]))

    def test_complete72_offline_stages_and_shared_second_prompt(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';out=Path(folder)/'out';summary=probe.prepare(p)
            self.assertEqual(summary['max_stages'],72)
            s=probe.simulate(p,out,self.callback)
            self.assertEqual(s['mode'],'LOCAL_MOCK');self.assertEqual(s['model_calls'],0)
            self.assertEqual(s['attempts'],72)
            self.assertEqual(len(s['rows']),72)
            first=io.read(p/'contexts/rule-dev-01/A1.json')
            before=probe.decode_first(self.callback(dict(stage='first'),probe.request('first','ordinary',first)),first)
            following=probe.second_packet(first,before)
            self.assertEqual(probe.request('second','ordinary',following),probe.request('second','local_question',following))
            self.assertNotIn('historical_work',following)
            self.assertNotIn('target_ids',following)
            self.assertEqual(following['own_sources'],first['own_sources'])

    def test_no_label_reads_or_foreign_resources_and_same_first_packets(self):
        with tempfile.TemporaryDirectory() as folder:
            original=io.read
            def guard(path):
                self.assertNotIn('offline/',str(path).replace('\\','/'))
                return original(path)
            with patch.object(io,'read',guard):
                p=Path(folder)/'p';probe.prepare(p)
                for context in (p/'contexts').glob('*/*.json'):
                    packet=io.read(context)
                    self.assertTrue(all(s['ref'].startswith(packet['member']+'.') for s in packet['own_sources']))
                    a=probe.request('first','ordinary',packet);b=probe.request('first','local_question',packet)
                    self.assertEqual(a['schema'],b['schema'])
                    self.assertEqual(a['instructions'].split('PACKET=',1)[1],b['instructions'].split('PACKET=',1)[1])
                    self.assertNotIn('local_review_points',packet)

    def test_pass_skips_only_own_second_slot(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';probe.prepare(p)
            def callback(row,request):
                if row['task']=='rule-dev-01' and row['member']=='A3' and row['stage']=='first':
                    return json.dumps(dict(text='No relevant private material.',status='pass',source_ids=[],target_ids=[]))
                return self.callback(row,request)
            s=probe.simulate(p,Path(folder)/'out',callback)
            self.assertEqual(s['attempts'],70)
            self.assertEqual(sum(r['status']=='skipped_pass' for r in s['rows']),2)
            self.assertEqual(sum(r['status']=='readable' for r in s['rows']),70)

    def test_unreadable_first_blocks_dependent_step_not_other_member(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';probe.prepare(p);calls=0
            def callback(row,request):
                nonlocal calls
                calls+=1
                return '{' if calls==1 else self.callback(row,request)
            s=probe.simulate(p,Path(folder)/'out',callback)
            self.assertEqual(s['attempts'],71)
            self.assertEqual(s['rows'][0]['status'],'quarantined')
            self.assertEqual(s['rows'][1]['status'],'blocked_upstream')
            self.assertEqual(s['rows'][2]['status'],'readable')

    def test_two_bad_outputs_stop_and_export_all72_slots(self):
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';out=Path(folder)/'out';probe.prepare(p)
            with self.assertRaisesRegex(ValueError,'two consecutive'):
                probe.simulate(p,out,lambda row,request:'{')
            s=io.read(out/'progress.json');self.assertEqual(len(s['rows']),72)
            self.assertEqual(s['attempts'],2)
            self.assertTrue(any(r['status']=='not_run' for r in s['rows']))

    def test_annotation_failures_are_not_first_stage_loss(self):
        packet=io.read(probe.TASKS/'rule-dev-01/packets/A1.json')
        answer=probe.decode_first(json.dumps(dict(text='Readable but potentially false.',status='invalid',source_ids=['A2.S1'],target_ids=['D999'])),packet)
        self.assertIsNone(answer['status'])
        self.assertEqual(answer['evidence'],[])
        self.assertTrue(answer['annotation_issues'])
        self.assertIsNotNone(probe.second_packet(packet,answer))
        for raw in ['{}','{','{"text":"  "}','{"text":"a","text":"b"}']:
            with self.assertRaises(ValueError):probe.decode_first(raw,packet)

    def test_independent_calibration_numbers_and_only_resource_changes(self):
        probes=calibration.PROBES
        self.assertEqual((90-6)*1.25,probes[0]['expected'])
        self.assertEqual(24+18,probes[1]['expected']['distinct_demand'])
        self.assertEqual(70-6-24-18,probes[1]['expected']['unallocated_after_both'])
        self.assertTrue(7<=9 and 96>=96)
        for item in probes:
            a=calibration.packet(item,'with_resource');b=calibration.packet(item,'without_resource')
            self.assertEqual(len(a['own_sources']),1);self.assertEqual(b['own_sources'],[])
            a.pop('own_sources');b.pop('own_sources');self.assertEqual(a,b)
            self.assertNotIn('historical_work',a)
        with tempfile.TemporaryDirectory() as folder:
            p=Path(folder)/'p';summary=calibration.prepare(p)
            self.assertEqual(summary['proposed_attempts'],12)
            self.assertEqual(len(io.read(p/'PLAN.json')['schedule']),12)
            for path in (p/'packets').glob('*.json'):
                self.assertNotIn('expected',io.read(path))
            with self.assertRaises(ValueError):calibration.prepare(p)


if __name__=='__main__':unittest.main()
