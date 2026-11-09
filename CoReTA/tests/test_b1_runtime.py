"""Offline runtime fixtures: no pretrained model, real training, or C/H labels."""
from copy import deepcopy
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from b0_answers import write_json
from b1_runtime import (POLICY,development_data,validate_runtime,LocalBackend,
                        run_batch,load_json,prefix_rows)
from b1_controls import replay,summarize
from test_b0_expert import tiny_model,fixture_config
from test_b1_controls import task


def runtime_config(base,adapter):
    c=fixture_config(base)
    c.update(generation=deepcopy(POLICY),expert_actor='M1',adapter_path=str(adapter),
             answer_tokens=64,work_tokens=512,max_length=2048)
    return c


def origin(base,adapter,fixture=True):
    adapter.mkdir()
    write_json(adapter/'b0_origin.json',dict(model_path=str(base),revision='local-fixture',
        fixture=fixture,technical_steps=None,purpose='expert_training'))


class ScriptedFixture:
    def __init__(self,fail_at=None):
        self.n=0
        self.fail_at=fail_at
    def respond(self,request,remaining):
        self.n+=1
        if self.n==self.fail_at:
            raise MemoryError('fixture OOM')
        return dict(raw_output='work' if request['stage']=='work' else '1900',
                    status='OK',usage=dict(fixture=True))


class RuntimeChecks(unittest.TestCase):
    def test_pending_configuration_refuses_before_load(self):
        c=load_json(ROOT/'config/b1_team_pending.json')
        with self.assertRaisesRegex(ValueError,'unresolved_configuration'):
            validate_runtime(c)

    def test_fixed_D_inputs_and_groups_without_targets(self):
        tasks,groups,targets=development_data(32)
        self.assertEqual(len(tasks),32)
        self.assertEqual(set(groups),{t['id'] for t in tasks})
        self.assertIsNone(targets)
        self.assertTrue(all(set(t)=={'id','question','paragraphs'} for t in tasks))
        with self.assertRaises(ValueError):
            development_data(3)

    def test_prefix_parser_does_not_parse_unselected_labels(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'fixture.jsonl'
            p.write_text('{"id":"ONE","answer":"1900"}\ninvalid unselected label\n',encoding='utf-8')
            self.assertEqual(prefix_rows(p,['ONE']),[dict(id='ONE',answer='1900')])

    def test_real_large_batch_cannot_skip_early_stages(self):
        c=dict(fixture=False)
        with patch('b1_runtime.validate_runtime',return_value={}):
            with self.assertRaisesRegex(ValueError,'required_staging'):
                run_batch(c,[dict(task(),id=str(i)) for i in range(8)],
                          {str(i):str(i) for i in range(8)},'NOT_CREATED')

    def test_origin_and_missing_independent_C_gate(self):
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'base';base.mkdir()
            adapter=Path(d)/'adapter';origin(base,adapter,False)
            c=runtime_config(base,adapter);c.update(fixture=False,reviewed_for_run=True)
            with self.assertRaisesRegex(ValueError,'existing_C_scores'):
                validate_runtime(c)
            c['model_path']=str(Path(d))
            with self.assertRaisesRegex(ValueError,'adapter_base'):
                validate_runtime(c)

    def test_C_scores_bound_to_adapter_and_inference(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir()
            adapter=folder/'adapter';origin(base,adapter,False)
            c=runtime_config(base,adapter);c.update(fixture=False,reviewed_for_run=True)
            meta=load_json(ROOT/'implement-stage/expert-answer-only-20261101/C_GROUPS.json')
            frozen=load_json(ROOT/'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json')
            expected=frozen['roles']['C_calibration']['ids']
            self.assertNotEqual(expected,meta['expected_ids'])  # Real export order vs metadata sort.
            inference={k:c[k] for k in ('model_path','revision','dtype','quantization',
                                       'max_length','template_kwargs','device','seed')}
            inference['generation']=dict(do_sample=False,max_new_tokens=64)
            # Hand-authored score shapes only, isolated temporary paths. Never used as research evidence.
            for condition in ('B','E'):
                score=dict(status='COMPLETE',primary_enabled=True,
                    manifest=dict(role='C',fixture=False,condition=condition,
                        adapter=str(adapter) if condition=='E' else None,
                        expected_ids=expected,inference=inference),
                    records=[dict(id=k,metrics=dict(em=int(condition=='E')))
                             for k in expected])
                path=folder/f'{condition}.json';write_json(path,score)
                c['baseline_C_score' if condition=='B' else 'expert_C_score']=str(path)
            q=validate_runtime(c)
            self.assertEqual(q['qualification'],'SUPPORTED_TASK_ADVANTAGE')
            # Bind a completed 256-token C protocol without rerunning or relabeling it.
            for field in ('baseline_C_score','expert_C_score'):
                score=load_json(c[field])
                score['manifest']['inference']['generation']['max_new_tokens']=256
                score['manifest']['inference']['evaluation_answer_suffix']='fixed short-answer suffix'
                write_json(c[field],score)
            with self.assertRaisesRegex(ValueError,'C_not_answer_only_frozen_policy'):
                validate_runtime(c)
            c['qualification_answer_tokens']=256
            with self.assertRaisesRegex(ValueError,'C_qualification_answer_suffix_mismatch'):
                validate_runtime(c)
            c['qualification_answer_suffix']='fixed short-answer suffix'
            self.assertEqual(validate_runtime(c)['qualification'],'SUPPORTED_TASK_ADVANTAGE')
            c['seed']+=1
            with self.assertRaisesRegex(ValueError,'registered_B1_seed'):
                validate_runtime(c)
            c['seed']-=1
            e=load_json(c['expert_C_score']);e['manifest']['adapter']=str(folder/'other')
            write_json(c['expert_C_score'],e)
            with self.assertRaisesRegex(ValueError,'C_runtime_adapter_mismatch'):
                validate_runtime(c)

    def test_complete_52_fixture_resume_and_budget(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir()
            adapter=folder/'adapter';origin(base,adapter)
            c=runtime_config(base,adapter)
            first=task();second=dict(task(),id='FIXTURE_SECOND')
            a=folder/'one';b=folder/'two'
            fake=ScriptedFixture()
            run_batch(c,[first],{first['id']:'g1'},a,fixture_backend=fake)
            self.assertEqual(fake.n,52)
            self.assertTrue(replay(load_json(a/'trials/000.json')).complete)
            next_fake=ScriptedFixture()
            run_batch(c,[first,second],{first['id']:'g1',second['id']:'g2'},b,
                      resume_from=a,fixture_backend=next_fake)
            self.assertEqual(next_fake.n,52)  # Only new item, no rerunning old responses.
            self.assertEqual(load_json(b/'execution.json')['n_complete'],2)
            traces=[load_json(p) for p in sorted((b/'trials').glob('*.json'))]
            result=summarize(traces,{t['id']:dict(id=t['id'],answer='1900') for t in (first,second)},
                [first['id'],second['id']],{first['id']:'g1',second['id']:'g2'},repeats=20)
            self.assertFalse(result['primary_enabled'])
            self.assertEqual(result['n_complete'],2)
            c['seed']+=1
            with self.assertRaisesRegex(ValueError,'resume_configuration_changed'):
                run_batch(c,[first,second],{first['id']:'g1',second['id']:'g2'},folder/'bad',
                          resume_from=a,fixture_backend=next_fake)

    def test_revised_answer_contract_replay_resume_and_scoring(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir()
            adapter=folder/'adapter';origin(base,adapter)
            c=runtime_config(base,adapter)
            c.update(answer_tokens=256,answer_suffix='\nOnly the short answer.',
                     answer_policy_version='B1_SHORT256_SUFFIX_V2')
            first=task();second=dict(task(),id='REVISED_SECOND')
            a=folder/'one';b=folder/'two'
            run_batch(c,[first],{first['id']:'g1'},a,fixture_backend=ScriptedFixture())
            trace=load_json(a/'trials/000.json')
            self.assertEqual(trace['protocol'],'B1_TWO_ROUND_FOUR_ARM_V2')
            self.assertTrue(replay(trace).complete)
            short=[r for r in trace['records'] if r['stage']!='work']
            work=[r for r in trace['records'] if r['stage']=='work']
            self.assertEqual((len(short),len(work)),(20,32))
            self.assertTrue(all(r['max_new_tokens']==256 and r['payload']['user'].endswith(c['answer_suffix']) for r in short))
            self.assertTrue(all(r['max_new_tokens']==512 and not r['payload']['user'].endswith(c['answer_suffix']) for r in work))
            backend=ScriptedFixture()
            run_batch(c,[first,second],{first['id']:'g1',second['id']:'g2'},b,
                      resume_from=a,fixture_backend=backend)
            self.assertEqual(backend.n,52)
            traces=[load_json(p) for p in sorted((b/'trials').glob('*.json'))]
            scored=summarize(traces,{t['id']:dict(id=t['id'],answer='1900') for t in (first,second)},
                [first['id'],second['id']],{first['id']:'g1',second['id']:'g2'},repeats=10)
            self.assertEqual(scored['n_complete'],2)
            c['answer_suffix']='changed'
            with self.assertRaisesRegex(ValueError,'resume_configuration_changed'):
                run_batch(c,[first,second],{first['id']:'g1',second['id']:'g2'},folder/'bad',
                    resume_from=a,fixture_backend=ScriptedFixture())

    def test_OOM_stops_and_records_missing_denominator(self):
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir()
            adapter=folder/'adapter';origin(base,adapter)
            c=runtime_config(base,adapter);first=task();second=dict(task(),id='SECOND')
            out=folder/'run'
            run_batch(c,[first,second],{first['id']:'g1',second['id']:'g2'},out,
                      fixture_backend=ScriptedFixture(fail_at=5))
            execution=load_json(out/'execution.json')
            self.assertEqual((execution['n_expected'],execution['n_recorded'],execution['n_complete']),
                             (2,1,0))
            trace=load_json(out/'trials/000.json')
            self.assertEqual(trace['records'][-1]['status'],'OOM')
            self.assertEqual(len(trace['records']),5)

    def test_tiny_local_Peft_route_and_generation_entry(self):
        import torch
        from peft import LoraConfig,get_peft_model
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as d:
            folder=Path(d);base=folder/'base';base.mkdir()
            model,_=tiny_model(base)
            model.generation_config.min_p=.4
            model.generation_config.do_sample=True
            model.generation_config.suppress_tokens=[8]
            model.generation_config.save_pretrained(base)
            model=get_peft_model(model,LoraConfig(task_type='CAUSAL_LM',r=2,lora_alpha=4,
                                                  target_modules=['q_proj','v_proj']))
            adapter=folder/'adapter';model.save_pretrained(adapter)
            write_json(adapter/'b0_origin.json',dict(model_path=str(base),revision='local-fixture',
                       fixture=True,technical_steps=0,purpose='engineering_fixture'))
            c=runtime_config(base,adapter)
            validate_runtime(c)
            backend=LocalBackend(c)
            self.assertEqual(backend.generation_config.top_k,0)
            self.assertEqual(backend.generation_config.num_beams,1)
            self.assertIsNone(backend.model.generation_config.min_p)
            self.assertIsNone(backend.model.base_model.model.generation_config.suppress_tokens)
            from b1_controls import Trial
            req=Trial(task(),expert_actor='M1',fixture=True).next_request()
            layer=backend.model.base_model.model.model.layers[0].self_attn.q_proj
            seen=[]
            def fake_generate(**kwargs):
                seen.append(layer.disable_adapters)
                return torch.cat([kwargs['input_ids'],torch.tensor([[2]])],dim=1)
            with patch.object(backend.model,'generate',side_effect=fake_generate):
                result=backend.respond(req,10)
                self.assertEqual(result['status'],'OK')
                backend.respond(dict(req,actor='M2'),10)
            self.assertEqual(seen,[False,True])
            self.assertFalse(layer.disable_adapters)
            # Exercise actual CPU generate (random weights, not task ability).
            backend.generation_config.forced_eos_token_id=2
            result=backend.respond(req,10)
            self.assertEqual(result['status'],'OK')
            self.assertLessEqual(result['usage']['output_tokens'],64)
            c['max_length']=1
            with self.assertRaisesRegex(ValueError,'overlength_no_truncation'):
                backend.respond(req,10)
            c['max_length']=2048
            backend.tokenizer.chat_template="{{ raise_exception('fixture bad template') }}"
            with self.assertRaisesRegex(ValueError,'chat_template_failure:TemplateError'):
                backend.respond(req,10)
            out=folder/'bad-template-batch'
            run_batch(c,[task(),dict(task(),id='SECOND')],{task()['id']:'g1','SECOND':'g2'},out,
                      fixture_backend=backend)
            execution=load_json(out/'execution.json')
            self.assertEqual(execution['new_backend_requests'],1)
            self.assertEqual((execution['n_expected'],execution['n_recorded']),(2,1))
            self.assertIsNone(execution['peak_memory'])


if __name__=='__main__':
    unittest.main()
