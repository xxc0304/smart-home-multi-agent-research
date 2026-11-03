"""Engineering fixtures only: no pretrained weights or task outcomes."""
import json
from pathlib import Path
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tools'))
from b0_answers import (answer_score, answer_text, write_json, score_run, compare_runs,
                        select_candidate, paired_interval)
from b0_training import AnswerCollator, encode_row, require_config, train, generate
from prepare_answer_only_expert import SYSTEM


def row(answer='1900'):
    return dict(id='FIXTURE', messages=[dict(role='system', content=SYSTEM),
        dict(role='user', content='X established 1900'),
        dict(role='assistant', content=answer)])


def tiny_model(folder):
    import torch
    from tokenizers import Tokenizer, models, pre_tokenizers
    from transformers import PreTrainedTokenizerFast, LlamaConfig, LlamaForCausalLM
    torch.manual_seed(13)
    tokens = ['<unk>', '<pad>', '</turn>', '<system>', '<user>', '<assistant>',
              'X', 'established', '1900', '1950']
    raw = Tokenizer(models.WordLevel(dict(zip(tokens, range(len(tokens)))), unk_token='<unk>'))
    raw.pre_tokenizer = pre_tokenizers.WhitespaceSplit()
    tok = PreTrainedTokenizerFast(tokenizer_object=raw, unk_token='<unk>',
                                 pad_token='<pad>', eos_token='</turn>')
    tok.chat_template = ("{% for m in messages %}{{ '<' + m['role'] + '> ' + m['content'] + ' </turn> ' }}"
                         "{% endfor %}{% if add_generation_prompt %}{{ '<assistant> ' }}{% endif %}")
    model = LlamaForCausalLM(LlamaConfig(vocab_size=len(tokens), hidden_size=32,
        intermediate_size=64, num_hidden_layers=1, num_attention_heads=4,
        num_key_value_heads=2, max_position_embeddings=256, eos_token_id=2, pad_token_id=1))
    model.save_pretrained(folder)
    tok.save_pretrained(folder)
    return model, tok


def fixture_config(base):
    return dict(fixture=True, reviewed_for_run=False, model_path=str(base), revision='local-fixture',
        dtype='float32',quantization='none',device='cpu',max_length=128,template_kwargs={},
        wall_seconds=120,target_modules=['q_proj','v_proj'],gradient_accumulation_steps=1,
        gradient_checkpointing=False,r=2,alpha=4,learning_rate=1e-3,epochs=1,seed=20261102,
        generation=dict(do_sample=False,max_new_tokens=4),purpose='engineering_fixture')


class AnswerChecks(unittest.TestCase):
    def test_real_technical_prefix_cannot_enable_primary_scoring(self):
        with tempfile.TemporaryDirectory() as d:
            directory=Path(d)
            write_json(directory/'manifest.json',dict(expected_ids=['v1'],fixture=False,
                role='V',condition='B',technical_preflight=True))
            (directory/'responses.jsonl').write_text(json.dumps(dict(id='v1',status='OK',raw_output='NYC'))+'\n')
            result=score_run(directory,{'v1':dict(answer='NYC')})
            self.assertEqual(result['status'],'COMPLETE')
            self.assertFalse(result['primary_enabled'])
            with self.assertRaisesRegex(ValueError,'technical_prefix_requires'):
                generate(fixture_config(directory),'C','B',None,directory/'bad',technical_prefix=3)

    def test_alias_and_normalization_without_schema(self):
        target = dict(answer='New York City', answer_aliases=['NYC'])
        self.assertEqual(answer_score(' Answer: NYC ',target)['em'],1)
        self.assertEqual(answer_score('new york city!',target)['em'],1)
        self.assertEqual(answer_score('New York',target)['em'],0)
        self.assertGreater(answer_score('New York',target)['f1'],0)

    def test_no_gold_search_in_explanation(self):
        self.assertEqual(answer_text('Answer: X\nbecause Y'), 'X\nbecause Y')
        self.assertEqual(answer_score('X or Y',dict(answer='X'))['em'],0)

    def test_pending_config_cannot_run(self):
        c=json.loads((ROOT/'config/b0_answer_only_pending.json').read_text(encoding='utf-8'))
        with self.assertRaisesRegex(ValueError,'unresolved_configuration'):
            require_config(c,training=True)


class TrainingChecks(unittest.TestCase):
    def test_mask_padding_and_overlength(self):
        import torch
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as d:
            _,tok=tiny_model(d)
            a=encode_row(tok,row(),128,{})
            b=encode_row(tok,row('1900 1950'),128,{})
            first=next(i for i,v in enumerate(a['labels']) if v!=-100)
            self.assertEqual(tok.decode(a['labels'][first:]),'1900 </turn>')
            self.assertTrue(all(x==-100 for x in a['labels'][:first]))
            batch=AnswerCollator(tok.pad_token_id)([a,b])
            self.assertEqual(batch['labels'][0,-1].item(),-100)
            self.assertEqual(batch['attention_mask'][0,-1].item(),0)
            with self.assertRaisesRegex(ValueError,'overlength_no_truncation'):
                encode_row(tok,row(),3,{})
            bad=row();bad['messages'][0]['content']='train all fields'
            with self.assertRaises(ValueError):encode_row(tok,bad,128,{})

    def test_real_cpu_adapter_update_and_reload(self):
        import torch
        from peft import PeftModel
        from transformers import AutoModelForCausalLM
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'base';out=Path(d)/'FIXTURE_training'
            original,tok=tiny_model(base)
            frozen=original.get_input_embeddings().weight.detach().clone()
            config=fixture_config(base)
            model,tok=train(config,[row(),row('1950')],out,max_steps=2)
            self.assertTrue(torch.equal(frozen,model.get_input_embeddings().weight))
            self.assertTrue(any(torch.any(v!=0) for k,v in model.named_parameters() if 'lora_B' in k))
            model.eval();feature=encode_row(tok,row(),128,{})
            ids=torch.tensor([feature['input_ids']])
            with torch.no_grad(): expected=model(ids).logits
            reloaded=PeftModel.from_pretrained(AutoModelForCausalLM.from_pretrained(base,
                local_files_only=True),out/'adapter')
            reloaded.eval()
            with torch.no_grad(): actual=reloaded(ids).logits
            self.assertTrue(torch.allclose(expected,actual,atol=1e-6))
            self.assertEqual(json.loads((out/'training_status.json').read_text())['status'],'COMPLETE')
            tasks=[dict(id='FIXTURE',question='When was X established?',paragraphs=[
                dict(idx=0,title='X',paragraph_text='X established 1900')])]
            config['generation']['max_new_tokens']=4
            manifest=generate(config,'V','E',out/'adapter',Path(d)/'FIXTURE_generation',fixture_tasks=tasks)
            self.assertTrue(manifest['fixture'])
            records=[json.loads(x) for x in (Path(d)/'FIXTURE_generation/responses.jsonl').read_text().splitlines()]
            self.assertEqual(len(records),1)
            self.assertIsInstance(records[0]['raw_output'],str)
            wrong=dict(config,revision='different')
            with self.assertRaisesRegex(ValueError,'adapter_base_or_fixture_mismatch'):
                generate(wrong,'V','E',out/'adapter',Path(d)/'wrong',fixture_tasks=tasks)

    def test_timeout_retains_partial_status(self):
        import torch
        torch.set_num_threads(1)
        with tempfile.TemporaryDirectory() as d:
            base=Path(d)/'base';tiny_model(base)
            config=fixture_config(base);config['wall_seconds']=.000001
            with self.assertRaises(TimeoutError):train(config,[row()],Path(d)/'out',max_steps=1)
            status=json.loads((Path(d)/'out/training_status.json').read_text())
            self.assertEqual(status['status'],'INTERRUPTED_NOT_CANDIDATE')


class EvaluationChecks(unittest.TestCase):
    def report(self,folder,condition,answers,role='C',missing=False):
        folder.mkdir()
        ids=[str(i) for i in range(len(answers))]
        write_json(folder/'manifest.json',dict(role=role,condition=condition,fixture=True,
            expected_ids=ids,inference={'shared':'FIXTURE'},adapter='fixture_adapter' if condition=='E' else None))
        records=[dict(id=k,status='OK',raw_output=a) for k,a in zip(ids,answers)]
        if missing:records.pop()
        (folder/'responses.jsonl').write_text(''.join(json.dumps(r)+'\n' for r in records))
        return score_run(folder,{k:dict(answer='X') for k in ids})

    def test_paired_stats_fixture_and_missing_denominator(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            b=self.report(root/'b','B',['Y']*12)
            e=self.report(root/'e','E',['X']*12)
            groups={str(i):i for i in range(12)}
            compared=compare_runs(b,e,groups,repeats=100)
            self.assertEqual(compared['difference'],1)
            self.assertEqual(compared['cluster_ci95'],[1,1])
            self.assertFalse(compared['primary_enabled'])
            self.assertEqual(compared['qualification'],'NOT_ESTABLISHED')
            partial=self.report(root/'partial','E',['X']*12,missing=True)
            self.assertIsNone(partial['metrics'])
            self.assertEqual(partial['n_expected'],12)
            self.assertEqual(compare_runs(b,partial,groups)['status'],'INCOMPLETE')
            e['manifest']['inference']={'different':'policy'}
            with self.assertRaisesRegex(ValueError,'unpaired'):compare_runs(b,e,groups)

    def test_group_weights_and_mapping(self):
        values={'a':1,'b':1,'c':-1}
        self.assertEqual(paired_interval(values,dict(a=0,b=0,c=0),100),None)
        with self.assertRaises(ValueError):paired_interval(values,{'a':0},100)
        a=paired_interval(values,dict(a=0,b=0,c=1),1000)
        self.assertEqual(a,paired_interval(values,dict(a=0,b=0,c=1),1000))

    def test_V_selection_ties_and_no_C_selection(self):
        with tempfile.TemporaryDirectory() as d:
            root=Path(d)
            a=self.report(root/'a','E',['X','Y'],role='V')
            b=self.report(root/'b','E',['X','Y'],role='V')
            c=self.report(root/'c','E',['X','X'],role='V')
            self.assertEqual(select_candidate([a,b])['selected_index'],0)
            self.assertEqual(select_candidate([a,c])['selected_index'],1)
            c['manifest']['role']='C'
            with self.assertRaises(ValueError):select_candidate([a,c])


if __name__=='__main__':unittest.main()
