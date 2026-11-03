"""Research integrity and scorer-integration checks, all offline."""
from pathlib import Path
from copy import deepcopy
import json
import sys
import tempfile
import unittest

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from expert_mechanism_protocol import (ProtocolError,ACTORS,ARMS,render_initial,
    render_replay,load_frozen_bundle,parse_output,APPLICATION_CUE,assess_context)
from score_expert_mechanism import score_one,score_batch,paired_effects,transitions


def task():
    return {'id':'HOST_ONLY_2hop_ID','question':'When was School X established?', 'paragraphs':[
        {'idx':0,'title':'Person','paragraph_text':'Person P worked for School X.'},
        {'idx':1,'title':'School','paragraph_text':'School X was established in 1900.'},
        {'idx':2,'title':'City','paragraph_text':'The city was renamed in 1950.'}]}


def outputs():
    return {a:{'answer':'1900' if a=='M1' else '1950','support_idxs':[0,1] if a in ('M1','M3') else [],
               'reasoning':'Full natural-language reasoning from a test fixture.'} for a in ACTORS}


def target():
    return {'id':'HOST_ONLY_2hop_ID','answer':'1900','answer_aliases':['the year 1900'],'answerable':True,
        'paragraphs':[{'idx':0,'is_supporting':True},{'idx':1,'is_supporting':True},{'idx':2,'is_supporting':False}]}


class ProtocolChecks(unittest.TestCase):
    def test_prompt_has_no_structural_id_or_gold_fields(self):
        p=render_initial(task());self.assertNotIn(task()['id'],p['user'])
        self.assertEqual(p['response_schema']['properties']['support_idxs']['items']['enum'],[0,1,2])
        bad=task();bad['answer']='1900'
        with self.assertRaises(ProtocolError):render_initial(bad)
        bad=task();bad['paragraphs'][0]['is_supporting']=True
        with self.assertRaises(ProtocolError):render_initial(bad)

    def test_all_conditions_keep_question_context_and_prior(self):
        original=task();initial=outputs()
        for arm in ARMS:
            data=render_replay(original,initial,arm)['task_data']
            self.assertEqual(data['question'],original['question'])
            self.assertEqual(data['paragraphs'],original['paragraphs'])
            self.assertEqual(data['previous_answer'],initial['M2'])
            self.assertEqual(len(data['messages']),0 if arm.startswith('N') else 3)
        self.assertEqual(original,task());self.assertEqual(initial,outputs())

    def test_citation_locator_uses_submitted_visible_ids_only(self):
        r=render_replay(task(),outputs(),'C10')
        loc=r['task_data']['citation_locators']
        self.assertEqual([p['idx'] for p in loc],[0,1])
        self.assertEqual(loc[0]['reported_by'],['M1','M3'])
        self.assertEqual(loc[0]['title'],task()['paragraphs'][0]['title'])
        self.assertNotIn('paragraph_text',loc[0])
        self.assertEqual(r['task_data']['paragraphs'],task()['paragraphs'])
        self.assertNotIn(2,[p['idx'] for p in loc])
        broken=outputs();broken['M1']['support_idxs']=[99]
        with self.assertRaises(ProtocolError):render_replay(task(),broken,'C10')

    def test_no_citations_no_fake_source_treatment(self):
        initial=outputs()
        for out in initial.values():out['support_idxs']=[]
        base=render_replay(task(),initial,'C00');enhanced=render_replay(task(),initial,'C10')
        self.assertFalse(enhanced['operation_checks']['source_locator_applied'])
        self.assertEqual(base['payload'],enhanced['payload'])

    def test_application_same_instruction_with_and_without_peer(self):
        a=render_replay(task(),outputs(),'C01')['payload']['user']
        n=render_replay(task(),outputs(),'N1')['payload']['user']
        self.assertTrue(a.endswith(APPLICATION_CUE));self.assertTrue(n.endswith(APPLICATION_CUE))

    def test_missing_actor_blocks_downstream(self):
        initial=outputs();initial.pop('M4')
        with self.assertRaises(ProtocolError):render_replay(task(),initial,'C00')

    def test_duplicate_keys_and_nonstandard_json_rejected(self):
        for raw in ['{"answer":"x","answer":"y","support_idxs":[],"reasoning":"r"}',
                    '{"answer":NaN,"support_idxs":[],"reasoning":"r"}',
                    '```json\n{"answer":"x","support_idxs":[],"reasoning":"r"}\n```',
                    '{"answer":']:
            with self.subTest(raw=raw):
                with self.assertRaises(ProtocolError):parse_output(raw,range(3))

    def test_invalid_support_types_not_coerced(self):
        for refs in [[True],[1.0],['1'],[0,0],[9]]:
            with self.subTest(refs=refs):
                out={'answer':'1900','support_idxs':refs,'reasoning':'r'}
                with self.assertRaises(ProtocolError):parse_output(json.dumps(out),range(3))

    def test_null_is_valid_abstention_not_transport_failure(self):
        out=parse_output('{"answer":null,"support_idxs":[],"reasoning":"Unresolved."}',range(3))
        self.assertEqual(score_one(out,target())['answer_em'],0)
        self.assertTrue(score_one(out,target())['abstained'])

    def test_fixture_cannot_enter_real_initial_path(self):
        b={'kind':'HAND_AUTHORED_PIPELINE_FIXTURE','task_id':task()['id'],
           'records':[{'actor':a,'raw_output':json.dumps(v)} for a,v in outputs().items()]}
        with self.assertRaises(ProtocolError):load_frozen_bundle(b,task())
        self.assertEqual(set(load_frozen_bundle(b,task(),allow_fixture=True)),set(ACTORS))

    def test_real_bundle_pointer_must_match_original_bytes(self):
        # Temporary hand-written files test pointer validation, not model provenance.
        with tempfile.TemporaryDirectory() as folder:
            rows=[]
            for a,v in outputs().items():
                raw=json.dumps(v);path=Path(folder)/(a+'.json');path.write_text(raw,encoding='utf-8')
                rows.append({'actor':a,'raw_response_path':str(path),'raw_output':raw})
            bundle={'kind':'FROZEN_MODEL_OUTPUTS','task_id':task()['id'],'records':rows}
            load_frozen_bundle(bundle,task())
            rows[0]['raw_output']=rows[0]['raw_output']+' '
            with self.assertRaises(ProtocolError):load_frozen_bundle(bundle,task())

    def test_context_checks_do_not_guess_provider_fit(self):
        self.assertEqual(assess_context(17918,512,16384)['status'],'EXCEEDS_CONTEXT')
        self.assertEqual(assess_context(2000)['status'],'CONTEXT_LIMIT_UNSELECTED')
        self.assertEqual(assess_context(2000,512,8192)['status'],'CHAT_SCHEMA_OVERHEAD_UNMEASURED')
        self.assertEqual(assess_context(2000,512,8192,100)['status'],'FITS_SUPPLIED_MEASUREMENT')


class ScoringChecks(unittest.TestCase):
    def examples(self):
        req=[{'request_id':a,'task_id':task()['id'],'condition':'independent_C','actor':a} for a in ('M1','M2')]
        res=[{'request_id':a,'status':'ok','raw_output':json.dumps(outputs()[a])} for a in ('M1','M2')]
        return req,res

    def test_independent_actors_not_merged_in_summary(self):
        req,res=self.examples();s=score_batch(req,res,{task()['id']:target()},fixture=True)
        self.assertEqual(len(s['condition_summaries']),2)
        self.assertFalse(s['primary_comparison_enabled'])

    def test_missing_and_transport_records_kept_without_primary(self):
        req,res=self.examples();s=score_batch(req,res[:1],{task()['id']:target()},fixture=True)
        self.assertEqual(s['n_expected'],2);self.assertEqual(len(s['records']),2)
        self.assertEqual(s['status_counts']['MISSING'],1)
        self.assertIsNone(s['condition_summaries'])
        res[1]={'request_id':'M2','status':'timeout','raw_output':None}
        s=score_batch(req,res,{task()['id']:target()},fixture=True)
        self.assertEqual(s['status_counts']['TECHNICAL_FAILURE'],1)

    def test_duplicate_or_extra_response_rejected(self):
        req,res=self.examples()
        with self.assertRaises(ProtocolError):score_batch(req,res+[res[0]],{task()['id']:target()},fixture=True)

    def test_fixture_is_not_accepted_as_declared_model_output(self):
        req,res=self.examples();s=score_batch(req,res,{task()['id']:target()},fixture=False)
        self.assertEqual(s['status_counts']['PROTOCOL_INVALID'],2)
        self.assertFalse(s['primary_comparison_enabled'])

    def test_alias_partial_support_and_update_direction(self):
        out={'answer':'the year 1900','support_idxs':[0],'reasoning':'fixture'}
        s=score_one(out,target());self.assertEqual(s['answer_em'],1)
        self.assertAlmostEqual(s['support_f1'],2/3)
        wrong={'answer':'1950','support_idxs':[2],'reasoning':'fixture'}
        self.assertEqual(transitions(out,wrong,target())['direction'],'correct_to_wrong')
        self.assertEqual(transitions(wrong,out,target())['direction'],'wrong_to_correct')


if __name__=='__main__':unittest.main()
