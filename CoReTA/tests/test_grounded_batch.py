"""Batch safety and natural-shape execution tests; fixtures are not model results."""
import copy
import json
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

from freeze_grounded_v3 import freeze
from run_grounded_batch import run, verify, digest
from score_grounded_batch import export
from prepare_grounded_batch import engine, DATA
from coreta.handoff.__main__ import PROJECT, DESIGN, configure, load_counter
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import payload_for
from coreta.schemas import ProtocolError


def response(p):
    stage=p['STAGE']
    work=dict(artifact=p['TASK']['choices'][0]['id'],work_text='SCRIPTED local fixture, no solving evidence.',open_points=[])
    if stage in ('INITIAL','DISCUSS'): return work
    if stage=='OBSERVE':
        offer=dict(target=p['CURRENT_WORK']['id'],knowledge='SCRIPTED observation',
            support=[dict(ref='T',excerpt='SCRIPTED evidence')],proposed_use='SCRIPTED apply')
        if p.get('METHOD_VARIANT')=='ground_full_public_v1':
            offer['claims']=[dict(statement='SCRIPTED claim',premises='SCRIPTED premise',source_refs=['T'])]
        return dict(action='offer',offer=offer)
    if stage=='GROUND':
        return dict(assessments={c['id']:dict(status='unresolved',reason='SCRIPTED limits',evidence_refs=['T'])
                                for c in p['CLAIMS']},limits='SCRIPTED limited access')
    if stage in ('TRY','FINALIZE'):
        return dict(action='new' if stage=='TRY' else 'reuse',work=work if stage=='TRY' else None,
            candidate_id=None if stage=='TRY' else p['CURRENT_WORK']['id'],use_record='SCRIPTED application',
            reason=None,declared_sources=['T'])
    if 'CHECK' in stage: return dict(finding='unable',observation='SCRIPTED limited observation',scope='fixture')
    if stage in ('CHOOSE','FINAL_CHOOSE'): return dict(candidate_id=p['CHOICES'][0],reason='SCRIPTED selection')
    raise AssertionError(stage)


class GroundedBatchTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp=tempfile.TemporaryDirectory(prefix='grounded-batch-')
        cls.root=Path(cls.tmp.name);cls.prepared=cls.root/'prepared'
        freeze(cls.prepared)

    @classmethod
    def tearDownClass(cls): cls.tmp.cleanup()

    def setUp(self):
        self.guard=patch('urllib.request.urlopen',side_effect=AssertionError('Offline tests prohibit network'))
        self.guard.start();self.addCleanup(self.guard.stop)
        self.folder=self.root/self._testMethodName;self.folder.mkdir()
        self.calls=[]

    def factory(self,handler=None,unknown=False):
        def factory(unit):
            def transport(payload,timeout):
                p=json.JSONDecoder().raw_decode(payload['instructions'].split('PACKET=',1)[1])[0]
                self.calls.append((copy.deepcopy(unit),copy.deepcopy(p)))
                value=(handler or response)(p)
                if isinstance(value,dict):
                    work=value.get('work') if p['STAGE'] in ('TRY','FINALIZE') else value
                    if isinstance(work,dict) and 'work_text' in work:
                        work['work_text']+=f" TRACE_METHOD:{unit['system']} TRACE_PAIR:{unit['pair']}"
                text=value if isinstance(value,str) else json.dumps(value)
                return dict(status='completed',usage={} if unknown else dict(input_tokens=1,output_tokens=1),
                    output=[dict(type='message',content=[dict(type='output_text',text=text)])])
            return transport
        return factory

    def test_complete_520_calls_shared_initials_and_scoring(self):
        pilot=self.folder/'pilot';rest=self.folder/'rest'
        a=run(self.prepared,pilot,phase='pilot',transport_factory=self.factory())
        self.assertEqual(a['http_attempts'],130)
        b=run(self.prepared,rest,phase='remainder',prior=pilot,transport_factory=self.factory())
        self.assertEqual(b['http_attempts'],390)
        self.assertEqual(a['status'],b['status']);self.assertEqual(a['status'],'completed')
        self.assertEqual(len(self.calls),520)
        for progress in (a,b):
            for pair in progress['completed_pairs']:
                rows=[r for r in progress['units'] if r['pair']==pair]
                self.assertEqual(len(rows),4)
                self.assertEqual(len({r['cache_sha256'] for r in rows}),1)
        for unit,p in self.calls:
            own=ChoicePackets(DATA/p['TASK']['task_id'],'distributed').member(p['SELF']['agent_id'])
            self.assertEqual(p['SELF_MATERIALS'],own['SELF_MATERIALS'])
            self.assertNotIn('correct_option_id',json.dumps(p))
            for method in ('ordinary_discussion','coreta_workboard','ground_full_public_v1'):
                if method!=unit['system']: self.assertNotIn('TRACE_METHOD:'+method,json.dumps(p))
            for pair in (f'hb-dev-{number:03d}-r{repeat}' for number in (5,6,7,8) for repeat in (1,2)):
                if pair!=unit['pair']: self.assertNotIn('TRACE_PAIR:'+pair,json.dumps(p))
        rows=export(self.prepared,[pilot,rest],self.folder/'score')
        self.assertEqual(len(rows),24)
        self.assertTrue(all(r['status']=='completed' for r in rows))
        initial_rows=json.loads((self.folder/'score/INITIAL_EXACT_MATCH.json').read_text())
        self.assertEqual(len(initial_rows),28)
        evidence=json.loads((self.folder/'score/PROCESS_EVIDENCE.json').read_text())
        self.assertEqual(sum(e['kind']=='ground_review' for row in evidence for e in row['events']),20)
        self.assertEqual(sum(u['system']=='initial' for u,p in self.calls),28)

    def test_first_bad_format_stops_batch(self):
        def handler(p): return 'NOT JSON' if p['STAGE']=='GROUND' else response(p)
        with self.assertRaises(ProtocolError):
            run(self.prepared,self.folder/'bad',phase='pilot',transport_factory=self.factory(handler))
        progress=json.loads((self.folder/'bad/progress.json').read_text())
        self.assertEqual(progress['status'],'stopped_on_first_technical_error')
        self.assertEqual(self.calls[-1][1]['STAGE'],'GROUND')
        self.assertEqual(sum(p['STAGE']=='GROUND' for u,p in self.calls),1)
        self.assertLess(progress['http_attempts'],130)

    def test_unknown_usage_stops_after_one(self):
        with self.assertRaises(ProtocolError):
            run(self.prepared,self.folder/'unknown',phase='pilot',transport_factory=self.factory(unknown=True))
        progress=json.loads((self.folder/'unknown/progress.json').read_text())
        self.assertTrue(progress['unknown_usage']);self.assertEqual(progress['http_attempts'],1)

    def test_transport_failure_has_no_retry(self):
        def fail(p): raise urllib.error.URLError('SCRIPTED transport failure')
        with self.assertRaises(ProtocolError):
            run(self.prepared,self.folder/'transport',phase='pilot',transport_factory=self.factory(fail))
        self.assertEqual(len(self.calls),1)

    def test_remainder_requires_completed_pilot(self):
        with self.assertRaises(ValueError): run(self.prepared,self.folder/'rest',phase='remainder',transport_factory=self.factory())
        self.assertFalse(self.calls)

    def test_completed_label_without_units_cannot_unlock_remainder(self):
        prior=self.folder/'prior';prior.mkdir()
        (prior/'progress.json').write_text(json.dumps(dict(status='completed',phase='pilot',
            manifest_sha256=digest(self.prepared/'manifest.json'),completed_pairs=['hb-dev-005-r1','hb-dev-006-r1'])))
        with self.assertRaises(ValueError):
            run(self.prepared,self.folder/'rest',phase='remainder',prior=prior,transport_factory=self.factory())
        self.assertFalse(self.calls)

    def test_tampered_prepared_input_refused(self):
        import shutil
        target=self.folder/'tampered';shutil.copytree(self.prepared,target)
        path=next(target.glob('*/*.request.json'));path.write_text('{}')
        with self.assertRaises(ValueError): run(target,self.folder/'live',phase='pilot',transport_factory=self.factory())
        self.assertFalse(self.calls)

    def test_output_directory_not_overwritten(self):
        output=self.folder/'existing';output.mkdir()
        with self.assertRaises(ValueError): run(self.prepared,output,phase='pilot',transport_factory=self.factory())

    def test_real_tokenizer_ground_long_history(self):
        config,legacy=configure(PROJECT/'config/deepseek_flash_inspection.json',DESIGN/'runtime.defaults.json')
        counter=load_counter();packets=ChoicePackets(DATA/'hb-dev-005','distributed')
        r=engine(self.folder,packets,config,legacy,'ground_full_public_v1',1,counter,
                 transport=self.factory()({}))
        text=('This is a scripted hypothetical claim about evidence and consequences, with no factual significance.\n')*80
        for member in packets.agents:
            r.board.add(dict(artifact='option_1',work_text=text,open_points=[]),member,initial=True)
        r.board.initialize(r.editor,r.agents)
        provider=next(a for a in r.agents if a!=r.editor)
        offer=dict(ref='O1',author=provider,base_version=r.board.current,
            knowledge='fixture',support=[dict(ref='T',excerpt='fixture')],proposed_use='fixture',
            claims=[dict(statement='fixture',premises='fixture',source_refs=['T'])])
        r.published=[offer]
        p=r.ground_packet(offer);payload=payload_for(r,'GROUND',p)
        small=r.gateway.client.size(payload)
        while len(r.board.ids())<40:
            r.board.add(dict(artifact='option_1',work_text=text,open_points=[]),provider)
        p=r.ground_packet(offer)
        schema=r.gateway.contracts.schema('GROUND',p)
        bigpayload=r.gateway.client.payload(r.gateway.prompts.render('GROUND',p,schema),schema,3072)
        big=r.gateway.client.size(bigpayload)
        self.assertLess(small,32768);self.assertGreater(big,32768)
        with self.assertRaises(ProtocolError): r.gateway.call('GROUND',p['SELF']['agent_id'],p)
        self.assertFalse(self.calls)
        (self.folder/'CONTEXT_STRESS.json').write_text(json.dumps(dict(four_works_input=small,forty_works_input=big)))


if __name__=='__main__': unittest.main()
