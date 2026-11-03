"""Minimal local HF/PEFT answer-only training and generation support.

Heavy libraries are imported only by runtime operations. No implicit downloads.
"""
import importlib.util
import json
from pathlib import Path
import time

from b0_answers import ROOT, read_jsonl, write_json
from prepare_answer_only_expert import SYSTEM


def encode_row(tokenizer, row, max_length, template_kwargs):
    messages = row['messages']
    if [m['role'] for m in messages] != ['system', 'user', 'assistant']:
        raise ValueError('expected_one_answer_completion:' + row['id'])
    if messages[0]['content'] != SYSTEM or not messages[-1]['content'].strip():
        raise ValueError('wrong_supervision_contract:' + row['id'])
    prefix = tokenizer.apply_chat_template(messages[:-1], tokenize=True,
        add_generation_prompt=True, return_dict=False, **template_kwargs)
    full = tokenizer.apply_chat_template(messages, tokenize=True,
        add_generation_prompt=False, return_dict=False, **template_kwargs)
    if full[:len(prefix)] != prefix or len(full) <= len(prefix):
        raise ValueError('template_prefix_not_aligned:' + row['id'])
    if len(full) > max_length:
        raise ValueError(f'overlength_no_truncation:{row["id"]}:{len(full)}>{max_length}')
    return dict(input_ids=full, attention_mask=[1] * len(full),
                labels=[-100] * len(prefix) + full[len(prefix):])


class AnswerCollator:
    def __init__(self, pad_id):
        self.pad_id = pad_id

    def __call__(self, rows):
        import torch
        width = max(len(row['input_ids']) for row in rows)
        batch = {k: [] for k in ('input_ids', 'attention_mask', 'labels')}
        for row in rows:
            n = width - len(row['input_ids'])
            for key, pad in (('input_ids', self.pad_id), ('attention_mask', 0), ('labels', -100)):
                batch[key].append(row[key] + [pad] * n)
        return {k: torch.tensor(v, dtype=torch.long) for k, v in batch.items()}


def require_config(config, *, training=False):
    required = ['model_path', 'revision', 'dtype', 'quantization', 'device',
                'max_length', 'template_kwargs', 'wall_seconds']
    if training:
        required += ['target_modules', 'gradient_accumulation_steps', 'gradient_checkpointing']
    missing = [key for key in required if config.get(key) is None]
    if missing:
        raise ValueError('unresolved_configuration:' + ','.join(missing))
    if not config.get('fixture') and not config.get('reviewed_for_run'):
        raise ValueError('batch_preflight_not_reviewed')
    if not Path(config['model_path']).is_dir():
        raise ValueError('local_model_directory_required')
    if config['dtype'] not in ('float32', 'float16', 'bfloat16'):
        raise ValueError('unsupported_dtype')
    if config['quantization'] not in ('none', '4bit'):
        raise ValueError('unsupported_quantization')
    if config['device'] not in ('cpu', 'cuda:0'):
        raise ValueError('single_device_only')
    if config['max_length'] <= 0 or config['wall_seconds'] <= 0:
        raise ValueError('positive_length_and_walltime_required')
    if training and (not config['target_modules'] or config['gradient_accumulation_steps'] < 1):
        raise ValueError('training_targets_and_batch_required')


def dependencies():
    return {name: bool(importlib.util.find_spec(name)) for name in
            ('torch', 'transformers', 'peft', 'accelerate', 'bitsandbytes')}


def load_tokenizer(config):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(config['model_path'], revision=config['revision'],
                                       local_files_only=True, trust_remote_code=False)
    if tok.pad_token_id is None:
        if tok.eos_token_id is None:
            raise ValueError('tokenizer_needs_pad_or_eos')
        tok.pad_token = tok.eos_token
    return tok


def load_base(config):
    import torch
    from transformers import AutoModelForCausalLM, BitsAndBytesConfig
    if config['device'].startswith('cuda') and not torch.cuda.is_available():
        raise ValueError('cuda_unavailable')
    if config['dtype'] == 'bfloat16' and config['device'].startswith('cuda') and not torch.cuda.is_bf16_supported():
        raise ValueError('bf16_unsupported')
    kwargs = dict(revision=config['revision'], local_files_only=True,
                  trust_remote_code=False, dtype=getattr(torch, config['dtype']))
    if config['quantization'] == '4bit':
        if not config['device'].startswith('cuda'):
            raise ValueError('4bit_requires_cuda_in_this_path')
        kwargs.update(quantization_config=BitsAndBytesConfig(load_in_4bit=True,
            bnb_4bit_quant_type='nf4', bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=getattr(torch, config['dtype'])),
            device_map={'': config['device']})
    model = AutoModelForCausalLM.from_pretrained(config['model_path'], **kwargs)
    if config['quantization'] == 'none':
        model.to(config['device'])
    return model


def train(config, rows, output, *, max_steps=None):
    require_config(config, training=True)
    import torch
    from transformers import Trainer, TrainerCallback, TrainingArguments, set_seed
    from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'config.json', config)
    set_seed(config['seed'])
    started = time.monotonic()
    model = None
    try:
        tok = load_tokenizer(config)
        features = [encode_row(tok, row, config['max_length'], config['template_kwargs']) for row in rows]
        write_json(output / 'lengths.json', dict(n=len(rows),
            max_tokens=max(len(f['input_ids']) for f in features),
            total_tokens=sum(len(f['input_ids']) for f in features), truncation=False))
        model = load_base(config)
        if config['quantization'] == '4bit':
            model = prepare_model_for_kbit_training(model,
                use_gradient_checkpointing=config['gradient_checkpointing'])
        model = get_peft_model(model, LoraConfig(task_type='CAUSAL_LM',
            r=config['r'], lora_alpha=config['alpha'], lora_dropout=0,
            bias='none', target_modules=config['target_modules']))
        model.config.use_cache = False

        class Budget(TrainerCallback):
            def on_step_begin(self, args, state, control, **kwargs):
                if time.monotonic() - started >= config['wall_seconds']:
                    raise TimeoutError('training_wall_budget_exhausted')

            def on_pre_optimizer_step(self, args, state, control, **kwargs):
                if any(p.grad is not None and not torch.isfinite(p.grad).all()
                       for p in model.parameters() if p.requires_grad):
                    raise ValueError('nonfinite_gradient')

            def on_log(self, args, state, control, logs=None, **kwargs):
                if logs and 'loss' in logs and not torch.isfinite(torch.tensor(logs['loss'])):
                    raise ValueError('nonfinite_loss')

        args = TrainingArguments(output_dir=str(output / 'trainer'),
            per_device_train_batch_size=1,
            gradient_accumulation_steps=config['gradient_accumulation_steps'],
            num_train_epochs=config['epochs'], max_steps=max_steps if max_steps is not None else -1,
            learning_rate=config['learning_rate'], weight_decay=0, warmup_steps=0,
            lr_scheduler_type='constant', seed=config['seed'], data_seed=config['seed'],
            bf16=config['dtype'] == 'bfloat16', fp16=config['dtype'] == 'float16',
            use_cpu=config['device'] == 'cpu', gradient_checkpointing=config['gradient_checkpointing'],
            gradient_checkpointing_kwargs={'use_reentrant': False},
            logging_steps=1, save_strategy='no', report_to='none',
            dataloader_num_workers=0, dataloader_pin_memory=config['device'] != 'cpu',
            max_grad_norm=1.0, logging_nan_inf_filter=False)
        trainer = Trainer(model=model, args=args, train_dataset=features,
                          data_collator=AnswerCollator(tok.pad_token_id), callbacks=[Budget()])
        trainer.train()
        if time.monotonic() - started >= config['wall_seconds']:
            raise TimeoutError('training_wall_budget_exhausted_at_final_step')
        model.save_pretrained(output / 'adapter')
        tok.save_pretrained(output / 'tokenizer')
        write_json(output / 'adapter' / 'b0_origin.json', dict(
            model_path=config['model_path'], revision=config['revision'], fixture=config['fixture'],
            purpose=config['purpose'], technical_steps=max_steps))
        write_json(output / 'training_status.json', dict(status='COMPLETE',
            fixture=config['fixture'], steps=trainer.state.global_step,
            elapsed_seconds=time.monotonic() - started,
            peak_allocated_bytes=torch.cuda.max_memory_allocated() if config['device'] != 'cpu' else None,
            history=trainer.state.log_history))
        return model, tok
    except Exception as exc:
        save_error = None
        if model is not None and hasattr(model, 'peft_config'):
            try:
                model.save_pretrained(output / 'partial_adapter_NOT_CANDIDATE')
            except Exception as save_exc:
                save_error = str(save_exc)
        write_json(output / 'training_status.json', dict(status='INTERRUPTED_NOT_CANDIDATE',
            fixture=config['fixture'], reason=type(exc).__name__ + ':' + str(exc),
            elapsed_seconds=time.monotonic() - started, partial_save_error=save_error))
        raise


def generate(config, role, condition, adapter, output, *, fixture_tasks=None):
    require_config(config)
    if role not in ('V', 'C') or condition not in ('B', 'E'):
        raise ValueError('only_V_or_C_and_B_or_E')
    if bool(adapter) != (condition == 'E'):
        raise ValueError('expert_requires_adapter_baseline_must_not_have_one')
    if fixture_tasks is not None and not config['fixture']:
        raise ValueError('custom_tasks_fixture_only')
    if config['generation'] != dict(do_sample=False, max_new_tokens=64) and not config['fixture']:
        raise ValueError('generation_policy_not_frozen_default')
    if adapter:
        origin = json.loads((Path(adapter) / 'b0_origin.json').read_text(encoding='utf-8'))
        if (Path(origin['model_path']).resolve() != Path(config['model_path']).resolve()
                or origin['revision'] != config['revision'] or origin['fixture'] != config['fixture']):
            raise ValueError('adapter_base_or_fixture_mismatch')
        if not config['fixture'] and (origin['technical_steps'] is not None or origin['purpose'] != 'expert_training'):
            raise ValueError('technical_adapter_not_expert_candidate')
    from expert_mechanism_protocol import task_data
    import torch
    from transformers import set_seed
    from peft import PeftModel
    tasks = fixture_tasks if fixture_tasks is not None else read_jsonl(ROOT / (
        'data/expert-training-20261030-v1/validation.inputs.jsonl' if role == 'V' else
        'data/external/musique-v1.0-20261030/inputs/C_calibration.jsonl'))
    if len({t['id'] for t in tasks}) != len(tasks) or not tasks:
        raise ValueError('invalid_task_ids')
    if not config['fixture'] and len(tasks) != (200 if role == 'V' else 160):
        raise ValueError('unexpected_role_size')
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    inference = {key:config[key] for key in ('model_path','revision','dtype','quantization',
        'device','max_length','template_kwargs','seed','generation')}
    manifest = dict(role=role, condition=condition, adapter=str(adapter) if adapter else None,
        fixture=config['fixture'], expected_ids=[t['id'] for t in tasks], inference=inference)
    write_json(output / 'manifest.json', manifest)
    response_path = output / 'responses.jsonl'
    response_path.touch()
    started = time.monotonic()
    fatal_error = None
    try:
        tok = load_tokenizer(config)
        model = load_base(config)
        if adapter:
            model = PeftModel.from_pretrained(model, adapter, is_trainable=False, local_files_only=True)
        model.eval()
        model.config.use_cache = True
        for task in tasks:
            remaining = config['wall_seconds'] - (time.monotonic() - started)
            if remaining <= 0:
                break
            record = dict(id=task['id'], status='TECHNICAL_FAILURE', raw_output=None)
            try:
                messages = [dict(role='system',content=SYSTEM),dict(role='user',content='TASK_DATA\n' +
                    json.dumps(task_data(task), ensure_ascii=False, indent=2))]
                ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                    return_dict=False, **config['template_kwargs'])
                if len(ids) + config['generation']['max_new_tokens'] > config['max_length']:
                    raise ValueError('overlength_no_truncation')
                set_seed(config['seed'])
                x = torch.tensor([ids],device=config['device'])
                before = time.monotonic()
                with torch.inference_mode():
                    y = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                        **config['generation'], max_time=remaining, pad_token_id=tok.pad_token_id)
                tail = y[0,len(ids):].tolist()
                eos = model.generation_config.eos_token_id
                eos = eos if isinstance(eos,list) else [eos if eos is not None else tok.eos_token_id]
                record.update(status='OK' if tail and tail[-1] in eos else 'OUTPUT_LIMIT',
                    raw_output=tok.decode(tail,skip_special_tokens=True),input_tokens=len(ids),
                    output_tokens=len(tail),elapsed_seconds=time.monotonic()-before)
            except torch.cuda.OutOfMemoryError as exc:
                record['reason']='CUDA_OOM:' + str(exc)
                with response_path.open('a',encoding='utf-8') as handle:
                    handle.write(json.dumps(record,ensure_ascii=False)+'\n')
                break
            except Exception as exc:
                record['reason']=type(exc).__name__+':'+str(exc)
            with response_path.open('a',encoding='utf-8') as handle:
                handle.write(json.dumps(record,ensure_ascii=False)+'\n')
    except Exception as exc:
        fatal_error = type(exc).__name__ + ':' + str(exc)
        raise
    finally:
        write_json(output/'execution.json',dict(elapsed_seconds=time.monotonic()-started,
            fixture=config['fixture'], n_recorded=len(read_jsonl(response_path)),
            n_expected=len(tasks), wall_seconds=config['wall_seconds'], fatal_error=fatal_error))
    return manifest
