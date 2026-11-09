"""Local B1 execution. No network, training, or automatic expert qualification run."""
from contextlib import nullcontext
from copy import deepcopy
import json
from importlib.metadata import version
from pathlib import Path
import time

from b0_answers import ROOT, read_jsonl, write_json, compare_runs
from b0_training import require_config, load_tokenizer, load_base
from b1_controls import Trial, replay, summarize
from expert_mechanism_protocol import ACTORS, validate_task
from prepare_expert_training import dependency_groups

SOURCE = ROOT / 'data/external/musique-v1.0-20261030'
SPLIT = ROOT / 'research/musique-data-preparation-20261030/SPLIT_MANIFEST.json'
C_GROUPS = ROOT / 'implement-stage/expert-answer-only-20261101/C_GROUPS.json'
POLICY = dict(do_sample=True, temperature=.7, top_p=.95, top_k=0)


def load_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def selected_rows(path, expected):
    wanted = set(expected)
    rows = {}
    with Path(path).open(encoding='utf-8') as stream:
        for line in stream:
            row = json.loads(line)
            if row['id'] in wanted:
                if row['id'] in rows:
                    raise ValueError('duplicate_selected_id')
                rows[row['id']] = row
    if set(rows) != wanted:
        raise ValueError('missing_selected_id')
    return [rows[k] for k in expected]


def development_data(n, *, targets=False):
    if type(n) is not int or n not in (1, 2, 8, 32):
        raise ValueError('only_predeclared_D_prefix_1_2_8_32')
    all_ids = load_json(SPLIT)['roles']['D_development']['ids']
    expected = all_ids[:n]
    tasks = prefix_rows(SOURCE/'inputs/D_development.jsonl', expected)
    tasks = [validate_task(t) for t in tasks]
    index = selected_rows(SOURCE/'corpus_index.jsonl', all_ids)
    buckets = dependency_groups(index)
    groups = {k: bucket[0] for bucket in buckets for k in bucket if k in expected}
    labels = ({r['id']:r for r in prefix_rows(SOURCE/'scoring/D_development.jsonl', expected)}
              if targets else None)
    return tasks, groups, labels


def prefix_rows(path, expected):
    rows=[]
    with Path(path).open(encoding='utf-8') as stream:
        for task_id in expected:
            row=json.loads(next(stream))
            if row['id']!=task_id:
                raise ValueError('frozen_prefix_file_order_mismatch')
            rows.append(row)
    return rows


def validate_runtime(config):
    require_config(config)
    if config.get('expert_actor') not in ACTORS or type(config.get('seed')) is not int:
        raise ValueError('expert_actor_and_integer_seed_required')
    if (config.get('generation') != POLICY or config.get('answer_tokens') != 64
            or config.get('work_tokens') != 512):
        raise ValueError('B1_decoding_policy_not_matched')
    if not config.get('adapter_path'):
        raise ValueError('adapter_path_required')
    origin = load_json(Path(config['adapter_path'])/'b0_origin.json')
    if (Path(origin['model_path']).resolve() != Path(config['model_path']).resolve()
            or origin['revision'] != config['revision'] or origin['fixture'] != config['fixture']):
        raise ValueError('adapter_base_or_fixture_mismatch')
    if config['fixture']:
        return dict(qualification='FIXTURE_ONLY', primary_enabled=False)
    if config['seed'] != 20261102 or config['expert_actor'] != 'M1':
        raise ValueError('registered_B1_seed_and_expert_slot_required')
    if origin['technical_steps'] is not None or origin['purpose'] != 'expert_training':
        raise ValueError('technical_adapter_not_expert_candidate')
    if not config.get('baseline_C_score') or not config.get('expert_C_score'):
        raise ValueError('existing_C_scores_required_no_automatic_C_run')
    baseline, expert = (load_json(config[k]) for k in ('baseline_C_score','expert_C_score'))
    metadata = load_json(C_GROUPS)
    for score in (baseline, expert):
        m = score['manifest']
        if (m['role'] != 'C' or m['fixture'] or len(m['expected_ids']) != 160
                or set(m['expected_ids']) != set(metadata['expected_ids'])
                or len(score['records']) != 160
                or {r['id'] for r in score['records']} != set(metadata['expected_ids'])):
            raise ValueError('not_fixed_real_C160_scores')
        inference = m['inference']
        if Path(inference['model_path']).resolve() != Path(config['model_path']).resolve():
            raise ValueError('C_runtime_base_mismatch')
        if any(inference[k] != config[k] for k in
               ('revision','dtype','quantization','template_kwargs')):
            raise ValueError('C_runtime_inference_mismatch')
        qualification_cap = config.get('qualification_answer_tokens', 64)
        if type(qualification_cap) is not int or qualification_cap not in (64, 256):
            raise ValueError('C_qualification_cap_not_registered')
        if inference['generation'] != dict(do_sample=False, max_new_tokens=qualification_cap):
            raise ValueError('C_not_answer_only_frozen_policy')
        if inference.get('evaluation_answer_suffix', '') != config.get('qualification_answer_suffix', ''):
            raise ValueError('C_qualification_answer_suffix_mismatch')
    if baseline['manifest']['adapter'] is not None or (
            Path(expert['manifest']['adapter']).resolve() != Path(config['adapter_path']).resolve()):
        raise ValueError('C_runtime_adapter_mismatch')
    qualification = compare_runs(baseline, expert, metadata['groups'])
    if qualification['qualification'] != 'SUPPORTED_TASK_ADVANTAGE':
        raise ValueError('independent_expert_advantage_not_established')
    return qualification


class LocalBackend:
    def __init__(self, config):
        from peft import PeftModel
        from transformers import GenerationConfig
        import torch
        self.config = config
        if config['device'].startswith('cuda') and torch.cuda.is_available():
            torch.cuda.reset_peak_memory_stats()
        self.tokenizer = load_tokenizer(config)
        self.model = PeftModel.from_pretrained(load_base(config), config['adapter_path'],
                                              is_trainable=False)
        self.model.eval()
        self.generation_config=GenerationConfig(**config['generation'],
            num_beams=1,repetition_penalty=1.0,no_repeat_ngram_size=0,
            bos_token_id=self.model.generation_config.bos_token_id,
            eos_token_id=self.model.generation_config.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id)
        # Transformers fills unset call-level fields from the model configuration;
        # PEFT in turn propagates its wrapper configuration to the underlying model.
        self.model.generation_config=self.generation_config
        self.model.base_model.model.generation_config=self.generation_config

    def respond(self, request, remaining):
        import torch
        from transformers import set_seed
        tok, model, config = self.tokenizer, self.model, self.config
        payload = request['payload']
        messages = [dict(role=role, content=payload[role]) for role in ('system','user')]
        try:
            ids = tok.apply_chat_template(messages, tokenize=True, add_generation_prompt=True,
                                         return_dict=False, **config['template_kwargs'])
        except Exception as exc:
            raise ValueError('chat_template_failure:'+type(exc).__name__+':'+str(exc)) from exc
        cap = request['max_new_tokens']
        if len(ids) + cap > config['max_length']:
            raise ValueError('overlength_no_truncation')
        set_seed(request['seed'])
        x = torch.tensor([ids], device=config['device'])
        expert = request['actor'] == config['expert_actor']
        started = time.monotonic()
        with (nullcontext() if expert else model.disable_adapter()), torch.inference_mode():
            y = model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                generation_config=self.generation_config, max_new_tokens=cap, max_time=remaining)
        tail = y[0,len(ids):].tolist()
        eos = self.generation_config.eos_token_id
        eos = eos if isinstance(eos,list) else [eos if eos is not None else tok.eos_token_id]
        usage=dict(input_tokens=len(ids),output_tokens=len(tail),
            elapsed_seconds=time.monotonic()-started, adapter_enabled=expert)
        if config['device'].startswith('cuda'):
            usage['peak_allocated_bytes']=torch.cuda.max_memory_allocated()
            usage['peak_reserved_bytes']=torch.cuda.max_memory_reserved()
        return dict(raw_output=tok.decode(tail, skip_special_tokens=True),
            status='OK' if tail and tail[-1] in eos else 'OUTPUT_LIMIT',
            usage=usage)


def append_jsonl(path, value):
    with Path(path).open('a', encoding='utf-8') as stream:
        stream.write(json.dumps(value,ensure_ascii=False)+'\n')


def run_batch(config, tasks, groups, output, *, resume_from=None, fixture_backend=None):
    qualification = validate_runtime(config)  # Before loading weights or creating a run.
    if fixture_backend is not None and not config['fixture']:
        raise ValueError('injected_backend_fixture_only')
    ids = [t['id'] for t in tasks]
    if not ids or len(set(ids)) != len(ids) or set(groups) != set(ids):
        raise ValueError('unique_tasks_and_exact_groups_required')
    if not config['fixture']:
        previous_n=len(load_json(Path(resume_from)/'manifest.json')['expected_ids']) if resume_from else 0
        if ((len(tasks) in (1,2) and previous_n!=0)
                or (len(tasks)==8 and previous_n not in (1,2))
                or (len(tasks)==32 and previous_n!=8)):
            raise ValueError('required_staging_1_or_2_then_8_then_32')
        canonical, canonical_groups, _ = development_data(len(tasks))
        if tasks != canonical or groups != canonical_groups:
            raise ValueError('real_batch_must_use_fixed_D_prefix')
    inherited = []
    if resume_from:
        prior = Path(resume_from)
        m = load_json(prior/'manifest.json')
        old_config = m['config']
        keys = set(config) | set(old_config)
        if any(config.get(k) != old_config.get(k) for k in keys-{'wall_seconds'}):
            raise ValueError('resume_configuration_changed')
        old_ids = m['expected_ids']
        if ids[:len(old_ids)] != old_ids or len(old_ids) >= len(ids):
            raise ValueError('resume_requires_longer_fixed_prefix')
        for i, task_id in enumerate(old_ids):
            trace = load_json(prior/'trials'/f'{i:03d}.json')
            trial = replay(trace)
            if (not trial.complete or trial.task != tasks[i] or trial.config != dict(
                    expert_actor=config['expert_actor'],seed=config['seed'],task_index=i,
                    fixture=config['fixture'])):
                raise ValueError('resume_requires_complete_matching_prefix')
            inherited.append(trial.export())
    output = Path(output)
    output.mkdir(parents=True, exist_ok=False)
    (output/'trials').mkdir()
    journal = output/'responses.jsonl'
    journal.touch()
    manifest = dict(protocol='B1_TWO_ROUND_FOUR_ARM_V1',config=deepcopy(config),
        expected_ids=ids,groups=groups,qualification=qualification,
        fixture=config['fixture'],expected_generations=52*len(ids),
        inherited_items=len(inherited),resume_from=str(resume_from) if resume_from else None,
        scope='DEVELOPMENT_DESCRIPTION_NOT_CONFIRMATORY_TEST')
    write_json(output/'manifest.json',manifest)
    traces = list(inherited)
    for i, trace in enumerate(inherited):
        write_json(output/'trials'/f'{i:03d}.json',trace)
        for record in trace['records']:
            append_jsonl(journal,dict(item_index=i,inherited=True,**record))
    started = time.monotonic()
    fatal = None
    calls = 0
    try:
        backend = fixture_backend if fixture_backend is not None else LocalBackend(config)
        write_json(output/'backend.json',dict(fixture=config['fixture'],
            effective_generation_config=backend.generation_config.to_dict()
                if isinstance(backend,LocalBackend) else None,
            generation_config_note='Unset neutral fields use recorded library defaults; checkpoint policy reset.',
            libraries={k:version(k) for k in ('torch','transformers','peft')}
                if isinstance(backend,LocalBackend) else None,
            load_seconds=time.monotonic()-started))
        stop_batch = False
        for i in range(len(inherited),len(tasks)):
            if time.monotonic()-started >= config['wall_seconds']:
                break
            trial = Trial(tasks[i],expert_actor=config['expert_actor'],seed=config['seed'],
                          task_index=i,fixture=config['fixture'])
            try:
                while (request:=trial.next_request()) is not None:
                    remaining = config['wall_seconds']-(time.monotonic()-started)
                    if remaining <= 0:
                        response=dict(raw_output=None,status='WALL_BUDGET',usage=None)
                        stop_batch=True
                    else:
                        try:
                            calls += 1
                            response=backend.respond(request,remaining)
                        except Exception as exc:
                            oom = 'OutOfMemory' in type(exc).__name__ or isinstance(exc,MemoryError)
                            response=dict(raw_output=None,status='OOM' if oom else 'TECHNICAL_FAILURE',
                                usage=dict(reason=type(exc).__name__+':'+str(exc)))
                            stop_batch = oom or isinstance(exc,ValueError)
                    record=trial.submit(request['request_id'],**response,
                        source_kind='FIXTURE_BACKEND' if config['fixture'] else 'ACTUAL_LOCAL_MODEL_RESPONSE')
                    append_jsonl(journal,dict(item_index=i,inherited=False,**record))
                    write_json(output/'trials'/f'{i:03d}.json',trial.export())
                    if stop_batch:
                        break
            finally:
                traces.append(trial.export())
                write_json(output/'trials'/f'{i:03d}.json',trial.export())
            if stop_batch:
                break
    except Exception as exc:
        fatal=type(exc).__name__+':'+str(exc)
        raise
    finally:
        peak_memory=None
        if config.get('device','').startswith('cuda'):
            import torch
            if torch.cuda.is_initialized():
                peak_memory=dict(peak_allocated_bytes=torch.cuda.max_memory_allocated(),
                                 peak_reserved_bytes=torch.cuda.max_memory_reserved())
        write_json(output/'execution.json',dict(fixture=config['fixture'],fatal_error=fatal,
            n_expected=len(tasks),n_recorded=len(traces),n_complete=sum(t['complete'] for t in traces),
            new_backend_requests=calls,wall_seconds=config['wall_seconds'],
            elapsed_seconds=time.monotonic()-started,peak_memory=peak_memory,
            peak_scope='load_and_all_requests_including_failures; unavailable_on_CPU'))
    return manifest


def score_batch(directory):
    directory=Path(directory)
    manifest=load_json(directory/'manifest.json')
    if manifest['fixture']:
        raise ValueError('fixture_targets_must_be_supplied_in_tests')
    tasks, groups, targets=development_data(len(manifest['expected_ids']),targets=True)
    if [t['id'] for t in tasks]!=manifest['expected_ids'] or groups!=manifest['groups']:
        raise ValueError('manifest_D_prefix_mismatch')
    traces=[load_json(path) for path in sorted((directory/'trials').glob('*.json'))]
    for trace in traces:
        i=manifest['expected_ids'].index(trace['task']['id'])
        if trace['task'] != tasks[i] or trace['config'] != dict(
                expert_actor=manifest['config']['expert_actor'],seed=manifest['config']['seed'],
                task_index=i,fixture=False):
            raise ValueError('trace_manifest_or_task_mismatch')
    result=summarize(traces,targets,manifest['expected_ids'],groups)
    write_json(directory/'scores.json',result)
    return result
