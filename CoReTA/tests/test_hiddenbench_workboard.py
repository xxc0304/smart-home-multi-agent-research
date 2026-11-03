"""Offline choice-adapter and development preparation checks. No solving evidence."""
import copy
import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import test_workboard as fixtures
from coreta.handoff.__main__ import PROJECT,DESIGN,configure,load_counter
from coreta.schemas import ProtocolError
from coreta.workboard.artifacts import Board,ChoiceAdapter
from coreta.workboard.choice_inputs import ChoicePackets
from coreta.workboard.choice_experiment import engine,prepare,run
from coreta.workboard.contracts import Contracts
from coreta.workboard.experiment_settings import settings

DATA=PROJECT/"data/task-packs/hiddenbench-workboard-dev-v1"
spec=importlib.util.spec_from_file_location('choice_score',PROJECT/'tools/score_hiddenbench_dev.py')
scoring=importlib.util.module_from_spec(spec);spec.loader.exec_module(scoring)


def work(p):
    return {"artifact":p['TASK']['choices'][0]['id'],"work_text":"SCRIPTED offline choice; not reasoning evidence.","open_points":[]}


def respond(p):
    stage=p['STAGE']
    if stage in {'INITIAL','DISCUSS'}:return work(p)
    if stage=='OBSERVE':return {'action':'offer','offer':{'target':p['CURRENT_WORK']['id'],'knowledge':'SCRIPTED',
        'support':[{'ref':'T','excerpt':'SCRIPTED'}],'proposed_use':'SCRIPTED trial'}}
    if stage in {'TRY','FINALIZE'}:
        return {'action':'new' if stage=='TRY' else 'reuse',
                'work':work(p) if stage=='TRY' else None,
                'candidate_id':None if stage=='TRY' else p['CURRENT_WORK']['id'],
                'use_record':'SCRIPTED record','reason':'SCRIPTED optional explanation','declared_sources':['T']}
    if 'CHECK' in stage:return {'finding':'no_issue_found','observation':'SCRIPTED only','scope':'fixture'}
    if stage in {'CHOOSE','FINAL_CHOOSE'}:return {'candidate_id':p['CHOICES'][-1],'reason':'SCRIPTED choice'}
    raise AssertionError(stage)


class HiddenBenchTests(unittest.TestCase):
    def setUp(self):
        tmp=tempfile.TemporaryDirectory(prefix='coreta-hiddenbench-');self.addCleanup(tmp.cleanup);self.folder=Path(tmp.name)
        guard=patch('urllib.request.urlopen',side_effect=AssertionError('No real network in offline checks'))
        guard.start();self.addCleanup(guard.stop)
        self.config,self.legacy=configure(PROJECT/'config/deepseek_flash_inspection.json',DESIGN/'runtime.defaults.json')
        self.counter=load_counter()

    def test_choice_adapter_and_official_mapping(self):
        task=json.loads((DATA/'hb-dev-001/public/task.json').read_text(encoding='utf-8'))
        adapter=ChoiceAdapter(task)
        self.assertTrue(adapter.deliverable(task['choices'][0]['id']))
        for invalid in (None,[],True,'West City','option_999'):
            self.assertFalse(adapter.deliverable(invalid))
        e=json.loads((DATA/'hb-dev-001/offline/evaluation.json').read_text(encoding='utf-8'))
        self.assertEqual(scoring.score(e['correct_option_id'],e)['exact'],1)
        self.assertEqual(scoring.score(e['official_correct_text'],e)['exact'],0)

    def test_native_rosters_and_private_access_preserved(self):
        source=json.loads((PROJECT/'data/task-source-audit-20261021/hiddenbench.json').read_text(encoding='utf-8'))
        for number,n in ((1,4),(4,3),(34,3),(50,3)):
            packets=ChoicePackets(DATA/f'hb-dev-{number:03d}','distributed')
            original=next(r for r in source if int(r['id'])==number)
            self.assertEqual(len(packets.agents),n)
            for i,a in enumerate(packets.agents):
                p=packets.member(a);self.assertEqual(len(p['SELF_MATERIALS']),1)
                self.assertEqual(p['SELF_MATERIALS'][0]['content'],original['hidden_information'][i])
                self.assertEqual(len(p['REFERENCE_INDEX']),2)
                text=json.dumps(p)
                for key in ('correct_answer','correct_option_id','source_name','rationale'):
                    self.assertNotIn(key,text)
                self.assertNotIn(original['name'],text)
                self.assertEqual(p['TASK']['scenario'],original['description'])
                self.assertEqual(p['TASK']['shared_information'],original['shared_information'])

    def test_reference_modes_preserve_facts_without_team_history(self):
        pack=DATA/'hb-dev-004';all_info=ChoicePackets(pack,'all_information');shared=ChoicePackets(pack,'shared_only')
        self.assertEqual(len(all_info.member('A1')['SELF_MATERIALS']),3)
        self.assertEqual(shared.member('A1')['SELF_MATERIALS'],[])
        self.assertEqual(all_info.task,shared.task)
        self.assertNotIn('CANDIDATES',all_info.member('A1'))

    def test_uncollected_and_collected_empty_are_distinct(self):
        packet=ChoicePackets(DATA/'hb-dev-004','distributed').member('A1');board=Board(ChoiceAdapter(packet['TASK']))
        a=board.add(work(packet),'A1');b=board.add(work(packet),'A1',sources=[])
        self.assertEqual(board.get(a)['source_declaration_status'],'not_collected')
        self.assertEqual(board.get(b)['source_declaration_status'],'collected')
        self.assertEqual(board.get(a)['declared_sources'],board.get(b)['declared_sources'])

    def test_three_four_member_budgets_match(self):
        for n,total,calls,final in ((3,40448,16,5888),(4,61440,25,6144)):
            a=settings(n,self.legacy,'coreta_workboard');b=settings(n,self.legacy,'ordinary_discussion')
            self.assertEqual(a['limits'],b['limits']);self.assertEqual(a['limits']['max_network_attempts_total'],calls)
            self.assertEqual(a['limits']['max_output_tokens_total'],total)
            self.assertEqual(n*(n+2)*b['max_output_tokens']['discuss']+b['max_output_tokens']['finalize'],total)
            self.assertEqual(b['max_output_tokens']['finalize'],final)

    def test_both_protocols_complete_choice_full_paths(self):
        for number,n in ((1,4),(4,3)):
            p=ChoicePackets(DATA/f'hb-dev-{number:03d}','distributed')
            cache={'origin':'SCRIPTED_OFFLINE','member_packet_hashes':p.hashes,
                   'candidates':{a:work(p.member(a)) for a in p.agents}}
            for method in ('ordinary_discussion','coreta_workboard'):
                folder=self.folder/f'{number}-{method}';folder.mkdir()
                r=engine(folder,p,self.config,self.legacy,method,1,self.counter,cache=cache,
                         transport=fixtures.Script(None,respond))
                result=r.run();self.assertEqual(result['status'],'completed')
                self.assertEqual(result['http_attempts'],(n+1)**2)
                self.assertEqual(result['artifact'],p.task['choices'][0]['id'])
                if method=='ordinary_discussion':
                    packet=r.packet('A1','DISCUSS')
                    self.assertIn('uncollected_declaration_meaning',packet['SOURCE_ACCESS'])

    def test_invalid_or_unread_sources_rejected(self):
        packets=ChoicePackets(DATA/'hb-dev-004','distributed');p=packets.member('A1')
        p['REFERENCE_INDEX'].append({'ref':'S02','kind':'private_material'})
        with self.assertRaises(ProtocolError):ChoicePackets._validate(p)
        p=packets.member('A1');p['TASK']['correct_answer']='SECRET'
        with self.assertRaises(ProtocolError):ChoicePackets._validate(p)
        c=Contracts(ChoiceAdapter(packets.task));p=packets.member('A1')
        with self.assertRaises(ProtocolError):c.decode(json.dumps({**work(p),'artifact':'option_999'}),c.schema('INITIAL',p))

    def test_full_preparation_and_scripted_334_request_batch(self):
        prepared=self.folder/'prepared';out=self.folder/'SCRIPTED_NOT_MODEL';prepare(DATA,prepared)
        result=run(prepared,out,transport_factory=lambda _:fixtures.Script(None,respond))
        self.assertEqual(result['status'],'completed');self.assertEqual(result['http_attempts'],334)
        self.assertEqual(len(result['units']),16);self.assertEqual(len(result['references']),16)
        for pair in json.loads((prepared/'manifest.json').read_text())['pairs']:
            states=[json.loads((out/pair['id']/m/'state.json').read_text()) for m in pair['methods']]
            self.assertEqual([w for w in states[0]['works'] if w['initial']],
                             [w for w in states[1]['works'] if w['initial']])
        report=scoring.score_run(out,self.folder/'SCRIPTED_OFFLINE_SCORES_NOT_EVIDENCE.json')
        self.assertEqual(len(report['units']),16)

    def test_runtime_preparation_never_reads_offline_answers(self):
        original=Path.read_text
        def guard(path,*args,**kwargs):
            if 'offline' in path.parts:raise AssertionError('Runtime must not read evaluation files')
            return original(path,*args,**kwargs)
        prepared=self.folder/'prepared'
        with patch.object(Path,'read_text',guard):
            m=prepare(DATA,prepared)
            self.assertEqual(m['max_http_attempts'],334)
            # Full path also uses no answer files; stop at first schema error to keep this check short.
            out=self.folder/'stopped'
            with self.assertRaises(ProtocolError):run(prepared,out,transport_factory=lambda _:fixtures.Script(None,lambda _:'NOT JSON'))
        p=json.loads((out/'progress.json').read_text())
        self.assertEqual(p['status'],'stopped_on_first_technical_error');self.assertEqual(p['http_attempts'],1)
        self.assertTrue(all(u['status']=='not_started' for u in p['units']))

    def test_prepared_input_tampering_stops_before_network(self):
        prepared=self.folder/'prepared';m=prepare(DATA,prepared)
        path=prepared/next(iter(m['prepared_hashes']));path.write_text('{}',encoding='utf-8')
        with self.assertRaises(ValueError):run(prepared,self.folder/'never_created')
        self.assertFalse((self.folder/'never_created').exists())


if __name__=='__main__':unittest.main()
