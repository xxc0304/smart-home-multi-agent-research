"""Offline isolation/access/stop checks for evidence diagnostic, not model efficacy."""
import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from coreta.handoff.__main__ import PROJECT

sys.path.insert(0,str(PROJECT/'tools'))
import workboard_evidence_probe as probe


class EvidenceProbeTests(unittest.TestCase):
    def setUp(self):
        temp=tempfile.TemporaryDirectory(prefix='evidence-diagnostic-offline-')
        self.addCleanup(temp.cleanup);self.root=Path(temp.name);self.prepared=self.root/'prepared'
        self.manifest=probe.prepare(self.prepared)
        guard=patch('urllib.request.urlopen',side_effect=AssertionError('Offline network forbidden'))
        guard.start();self.addCleanup(guard.stop)

    def test_frozen_evidence_isolation_and_own_source_privacy(self):
        for item in self.manifest['inputs']:
            values={c:probe.read(self.prepared/f"{item['id']}--{c}.json") for c in ['F','H','L']}
            self.assertEqual(values['F'],probe.read(probe.PREVIOUS/(item['id']+'--B.json')))
            p={c:probe.packet_of(v) for c,v in values.items()}
            h=p['H'].copy();h.pop('PUBLIC_VERSION_EXCERPTS')
            self.assertEqual(h,p['F'])
            for c in ['H','L']:
                self.assertEqual(p[c]['SELF_MATERIALS'],p['F']['SELF_MATERIALS'])
                self.assertEqual(p[c]['SELF'],p['F']['SELF'])
                self.assertNotIn('S01',p[c]['SOURCE_ACCESS']['direct_original_refs'])
                for passage in p[c]['PUBLIC_VERSION_EXCERPTS']:
                    work=next(w for w in p['F']['CANDIDATES'] if w['id']==passage['version'])
                    self.assertIn(passage['text'],work['work_text'])
                    self.assertEqual(passage['author'],work['author'])
            self.assertNotIn('TARGET_OFFER',p['L'])
            self.assertNotIn('CANDIDATES',p['L'])
            self.assertEqual(p['L']['VERSION_PAIR'],{'before':p['F']['BEFORE']['id'],'after':p['F']['AFTER']['id']})
            self.assertEqual(p['L']['TASK'],p['F']['TASK'])
            self.assertIn(probe.LOCAL_SCOPE,values['L']['instructions'])
            for c in ['H','L']:
                self.assertEqual(values[c]['text'],values['F']['text'])
                self.assertEqual(values[c]['max_output_tokens'],3072)

    def test_24_calls_are_fixed_independent_and_complete(self):
        seen=[]
        def script(payload,timeout):
            seen.append(payload)
            return {'status':'completed','usage':{'input_tokens':2,'output_tokens':3},'output':[
                {'type':'message','content':[{'type':'output_text','text':json.dumps(
                    {'finding':'unable','observation':'SCRIPTED_MARKER','scope':'offline fixture'})}]}]}
        result=probe.run(self.prepared,self.root/'fixture',script)
        self.assertEqual((result['status'],result['completed'],result['actual_http_attempts']),('completed',24,0))
        for c in ['F','H','L']:self.assertEqual(sum(r['condition']==c for r in result['rows']),8)
        for row,payload in zip(result['rows'],seen):
            self.assertEqual(payload,probe.read(self.prepared/row['payload_file']))
            self.assertNotIn('SCRIPTED_MARKER',payload['instructions'])

    def test_first_incomplete_stops_and_preserves_usage(self):
        def script(payload,timeout):
            return {'status':'incomplete','usage':{'input_tokens':4,'output_tokens':3072},'output':[]}
        result=probe.run(self.prepared,self.root/'failed',script)
        self.assertEqual(result['status'],'stopped_on_first_error')
        self.assertEqual(result['transport_attempts'],1)
        self.assertEqual(result['output_tokens'],3072)
        self.assertEqual(sum(r['status']=='not_started' for r in result['rows']),23)


if __name__=='__main__':unittest.main()
