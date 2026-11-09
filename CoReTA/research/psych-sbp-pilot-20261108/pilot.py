"""Bounded SBP information-expertise adaptation; never executes upstream code."""
import argparse, ast, collections, hashlib, itertools, json, os, random, re, sys, time
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
ACTORS = ['M1', 'M2', 'M3', 'M4']
ARMS = ['A_private', 'B_hidden', 'D_revealed', 'F_full', 'N_none']
SYSTEM = 'You are a committee member solving the supplied ranking task. Treat supplied task facts as evidence. Do not invent facts.'
CONTRACT = '\nGive at most two sentences of reasoning, then exactly four numbered lines under MY RANKING:, each containing one exact candidate name. Rank best to worst.'

def load(p):
    return json.loads(Path(p).read_text(encoding='utf-8'))

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, value):
    p = Path(p); p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(p.suffix + '.tmp')
    with tmp.open('w', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n')
        f.flush(); os.fsync(f.fileno())
    os.replace(tmp, p)

def append(p, value):
    with Path(p).open('a', encoding='utf-8') as f:
        f.write(json.dumps(value, ensure_ascii=False, allow_nan=False) + '\n')
        f.flush(); os.fsync(f.fileno())

def extract():
    tree = ast.parse((HERE/'source/student_body_president_task.py').read_text(encoding='utf-8'))
    cls = next(x for x in tree.body if isinstance(x, ast.ClassDef) and x.name == 'StudentBodyPresidentTask')
    fields = {}
    for x in cls.body:
        if isinstance(x, ast.Assign) and isinstance(x.targets[0], ast.Name): fields[x.targets[0].id] = x.value
        elif isinstance(x, ast.AnnAssign) and isinstance(x.target, ast.Name): fields[x.target.id] = x.value
    items = ast.literal_eval(fields['ITEMS']); shared = ast.literal_eval(fields['SHARED_INFORMATION'])
    private = []
    for group in fields['PER_AGENT_UNIQUE_INFORMATION'].values:
        for call in group.elts:
            assert isinstance(call, ast.Call) and call.func.id == 'UniqueInformationPiece'
            private.append({k.arg: ast.literal_eval(k.value) for k in call.keywords})
    weights = {'positive': 1, 'neutral': 0, 'negative': -1}
    scores = {}
    for candidate, block in re.findall(r'CANDIDATE ([A-D]):(.*?)(?=CANDIDATE [A-D]:|$)', shared, re.S):
        scores[candidate] = sum(weights[v.lower()] for v in re.findall(r': (Positive|Neutral|Negative)', block))
    totals = {k: v + sum(weights[f['valence']] for f in private if f['candidate'] == k) for k, v in scores.items()}
    ranking = sorted(items, key=lambda name: -totals[name[-1]])
    ranks = [ranking.index(name)+1 for name in items]
    assert len(private) == 16 and len(set(totals.values())) == 4
    assert ranks == ast.literal_eval(fields['GROUND_TRUTH_RANKING'])
    write(HERE/'task.json', {'items': items, 'shared': shared, 'private': private})
    write(HERE/'labels.json', {'ranking': ranking, 'totals': totals, 'shared_totals': scores})

def parse(text):
    matches = re.findall(r'^\s*([1-4])[.)]\s*(Candidate [A-D])\s*$', text, re.M)
    if len(matches) != 4 or [int(n) for n, _ in matches] != [1, 2, 3, 4]: return None
    names = [name for _, name in matches]
    return names if len(set(names)) == 4 else None

def error(ranking, gold):
    return None if ranking is None else sum(abs(ranking.index(k)-gold.index(k)) for k in gold)

def aggregate(rankings, gold):
    if len(rankings) != 4 or any(r is None for r in rankings): return None
    counts = collections.Counter(tuple(r) for r in rankings)
    winners = [list(r) for r, count in counts.items() if count == max(counts.values())]
    sums = {k: sum(r.index(k) for r in rankings) for k in gold}
    # All Borda ties averaged exactly over candidate permutations, never broken using gold.
    borda = [list(p) for p in itertools.permutations(sorted(gold)) if
             all(sums[p[i]] <= sums[p[i+1]] for i in range(3))]
    return {'vote_expected_l1': sum(error(r, gold) for r in winners)/len(winners),
            'vote_winners': winners, 'random_submitter_expected_l1': sum(error(r, gold) for r in rankings)/4,
            'borda_expected_l1': sum(error(r, gold) for r in borda)/len(borda)}

def context(task, actor, arm, seed):
    items = task['items'].copy(); random.Random(seed).shuffle(items)
    full = arm == 'F_full' or (arm != 'N_none' and actor == 'M1')
    facts = task['private'] if full else []
    extra = '\n'.join(f"Candidate {f['candidate']}: {f['trait']} (valence: {f['valence']})" for f in facts)
    return (f'You are {actor}, one of four committee members M1, M2, M3, M4.\n'
            'Select a student body president by ranking these four candidates:\n' + '\n'.join(items) + '\n\n' + task['shared'] +
            '\n\nAdditional evidence available to you:\n' + (extra or '(No additional evidence supplied.)') +
            '\n\nSome committee members may hold evidence unavailable to others. Rank by the sum of fact valences: positive=+1, neutral=0, negative=-1. Count each fact once. Do not invent missing evidence.' )

def payload(task, actor, arm, seed, stage, own, public):
    text = context(task, actor, arm, seed)
    if arm == 'D_revealed' and stage != 'initial':
        text += '\n\nInformation allocation: M1 received all additional candidate evidence; other members received only the shared evidence. This identifies information access, not guaranteed answer correctness.'
    if arm == 'A_private':
        text += '\n\nYour own prior responses only:\n' + '\n\n'.join(own)
        text += '\nWork independently; no responses from other members are available.'
    elif public:
        text += '\n\nCommittee transcript (responses are opinions to evaluate, not new independent facts):\n' + '\n\n'.join(f'{a}: {s}' for a, s in public)
    if stage == 'initial': text += '\n\nProvide your individual ranking before discussion.'
    elif stage == 'final': text += '\n\nAll four work rounds are complete. Provide your final ranking privately; other members will not see this response.'
    elif arm == 'A_private': text += '\n\nReconsider the task using your own evidence and prior work.'
    else: text += '\n\nIt is your turn in the discussion. Evaluate the available evidence and respond to the other members as useful.'
    return {'system': SYSTEM, 'user': text + CONTRACT}

def schedule(seed):
    rng = random.Random(seed); initial = ACTORS.copy(); rng.shuffle(initial)
    rounds = []
    for _ in range(4):
        order = ACTORS.copy(); rng.shuffle(order); rounds.append(order)
    return initial, rounds

def check_length(n, cap, limit):
    if n + cap > limit: raise ValueError('overlength_no_truncation')

def freeze():
    paths = [HERE/'pilot.py', HERE/'task.json', HERE/'labels.json', HERE/'config.json', HERE/'EXPERIMENT_REVIEW.md']
    paths += sorted((HERE/'source').glob('*.py'))
    paths += [ROOT/'tools/b0_training.py', ROOT/'tools/b0_answers.py', ROOT/'tools/prepare_answer_only_expert.py']
    return {str(p.relative_to(ROOT)): sha(p) for p in paths}

class Backend:
    def __init__(self, config):
        sys.path.insert(0, str(ROOT/'tools'))
        from b0_training import load_base, load_tokenizer
        from transformers import GenerationConfig
        self.config = config; self.tokenizer = load_tokenizer(config); self.model = load_base(config)
        self.model.eval()
        self.generation = GenerationConfig(**config['generation'], num_beams=1, repetition_penalty=1.,
            no_repeat_ngram_size=0, eos_token_id=self.model.generation_config.eos_token_id,
            pad_token_id=self.tokenizer.pad_token_id, bos_token_id=self.model.generation_config.bos_token_id)
    def encode(self, p):
        return self.tokenizer.apply_chat_template([{'role': k, 'content': p[k]} for k in ('system', 'user')],
            tokenize=True, add_generation_prompt=True, return_dict=False, **self.config['template_kwargs'])
    def respond(self, p, cap, seed):
        import torch
        from transformers import set_seed
        ids = self.encode(p)
        check_length(len(ids), cap, self.config['max_length'])
        set_seed(seed); started = time.monotonic(); x = torch.tensor([ids], device=self.config['device'])
        with torch.inference_mode():
            y = self.model.generate(input_ids=x, attention_mask=torch.ones_like(x),
                                   generation_config=self.generation, max_new_tokens=cap)
        tail = y[0, len(ids):].tolist(); eos = self.generation.eos_token_id
        if not isinstance(eos, list): eos = [eos]
        ended = bool(tail) and tail[-1] in eos
        return {'text': self.tokenizer.decode(tail, skip_special_tokens=True), 'output_ids': tail,
                'input_tokens': len(ids), 'output_tokens': len(tail), 'elapsed_seconds': time.monotonic()-started,
                'status': 'OK' if ended else 'OUTPUT_LIMIT', 'ended_with_eos': ended, 'adapter_enabled': False}

def preflight():
    extract(); task = load(HERE/'task.json'); gold = load(HERE/'labels.json')['ranking']; cfg = load(HERE/'config.json')
    assert parse('MY RANKING:\n1. Candidate D\n2. Candidate C\n3. Candidate A\n4. Candidate B') == gold
    for bad in ['', 'null', '{"ranking":null}', '1. Candidate A\n2. Candidate A\n3. Candidate C\n4. Candidate D',
                '1. Candidate A\n2. Candidate B', '1. Candidate A\n2. Candidate B\n3. Candidate C\n4. Candidate D\n1. Candidate A']:
        assert parse(bad) is None
    assert error(list(reversed(gold)), gold) == 8
    assert aggregate([gold]*4, gold)['vote_expected_l1'] == 0
    assert aggregate([gold]*3+[None], gold) is None
    check_length(16000,384,16384)
    try: check_length(16001,384,16384)
    except ValueError: pass
    else: raise AssertionError('overlength_not_rejected')
    for actor in ACTORS:
        assert context(task, actor, 'A_private', 1) == context(task, actor, 'B_hidden', 1)
        assert ('Vision for campus' in context(task, actor, 'B_hidden', 1)) == (actor == 'M1')
        assert 'Vision for campus' in context(task, actor, 'F_full', 1)
        assert 'Vision for campus' not in context(task, actor, 'N_none', 1)
        assert 'PEER_MARKER' not in payload(task, actor, 'A_private', 1, 'work', ['OWN_MARKER'], [('M2','PEER_MARKER')])['user']
        assert 'OWN_MARKER' in payload(task, actor, 'A_private', 1, 'work', ['OWN_MARKER'], [])['user']
    # Real prior MuSiQue responses exercise common text envelope; not ranking validity evidence.
    reference = ROOT/'runs/b1-stage-advantage-seed1-20261107-v1/responses.jsonl'
    with reference.open(encoding='utf-8') as f: real = json.loads(next(f))
    real_text = real.get('raw_output') or real.get('response', {}).get('raw_output')
    if real_text is None:
        def find_text(v):
            if isinstance(v, dict):
                if isinstance(v.get('raw_output'), str): return v['raw_output']
                for z in v.values():
                    found = find_text(z)
                    if found is not None: return found
            return None
        real_text = find_text(real)
    assert isinstance(real_text, str) and real_text
    replay = payload(task, 'M2', 'B_hidden', 1, 'work', [], [('M1', real_text)])
    assert real_text in replay['user']
    sys.path.insert(0, str(ROOT/'tools')); from b0_training import load_tokenizer
    tok = load_tokenizer(cfg)
    long_text = ('Candidate A positive Candidate B negative Candidate C neutral Candidate D positive. ' * 145)
    maximum = 0
    for arm in ARMS:
        for actor in ACTORS:
            own = [long_text]*5; public = [(a, long_text) for a in ACTORS]*5
            p = payload(task, actor, arm, 1, 'final', own, public)
            n = len(tok.apply_chat_template([{'role': k, 'content': p[k]} for k in ('system','user')], tokenize=True,
                       add_generation_prompt=True, return_dict=False, **cfg['template_kwargs']))
            maximum = max(maximum, n+cfg['final_tokens'])
    # This deliberately large synthetic stress case may exceed context. Runtime must reject it.
    normal = payload(task, 'M1','B_hidden',1,'final',[],[(a,'MY RANKING:\n1. Candidate D\n2. Candidate C\n3. Candidate A\n4. Candidate B') for a in ACTORS]*5)
    normal_n = len(tok.apply_chat_template([{'role': k, 'content': normal[k]} for k in ('system','user')], tokenize=True,add_generation_prompt=True,return_dict=False,**cfg['template_kwargs']))
    assert normal_n + cfg['final_tokens'] < cfg['max_length']
    hashes = freeze(); write(HERE/'FREEZE.json', hashes)
    write(HERE/'PREFLIGHT.json', {'result':'PASS', 'hashes':hashes, 'arithmetic': load(HERE/'labels.json'),
          'old_real_envelope_replayed':str(reference), 'old_real_envelope_sha256':sha(reference),
          'new_ranking_parser_tests':'synthetic_only; no historical ranking output in this checkout',
          'normal_full_history_tokens_plus_cap':normal_n+cfg['final_tokens'],
          'synthetic_stress_tokens_plus_cap':maximum, 'long_input_policy':'reject before generation, no truncation',
          'scope':'two-seed technical/development adaptation, not confirmatory reproduction',
          'maximum_calls':112*len(cfg['seeds']), 'maximum_output_tokens':49152*len(cfg['seeds'])})
    print(json.dumps(load(HERE/'PREFLIGHT.json'), ensure_ascii=False))

def run():
    import fcntl
    cfg = load(HERE/'config.json'); assert load(HERE/'FREEZE.json') == freeze()
    assert load(HERE/'PREFLIGHT.json')['result'] == 'PASS'
    assert 'RUN_ALLOWED' in (HERE/'EXPERIMENT_REVIEW.md').read_text(encoding='utf-8')
    out = ROOT/cfg['run_dir']; out.mkdir(parents=True, exist_ok=False)
    lock = (out/'run.lock').open('w'); fcntl.flock(lock, fcntl.LOCK_EX|fcntl.LOCK_NB)
    write(out/'manifest.json', {'config':cfg, 'freeze':freeze(), 'independent_scenarios':1, 'status':'STARTING'})
    write(out/'PID.json', {'pid':os.getpid()}); started = time.monotonic()
    task = load(HERE/'task.json'); backend = Backend(cfg); gold = load(HERE/'labels.json')['ranking']
    calls = 0; scores = []; failure = None
    def call(seed, arm, actor, stage, own, public, round_no=0):
        nonlocal calls
        cap = cfg['work_tokens'] if stage == 'work' else cfg['final_tokens']
        generation_seed = (seed*10000 + {'initial':0,'work':1000,'final':9000}[stage] + round_no*10 + ACTORS.index(actor)) % (2**32)
        p = payload(task, actor, arm, seed, stage, own, public)
        req = {'call':calls, 'seed':seed, 'arm':arm, 'actor':actor, 'stage':stage, 'round':round_no,
               'generation_seed':generation_seed, 'cap':cap, 'payload':p}
        append(out/'attempts.jsonl',req)
        r = backend.respond(p,cap,generation_seed); calls += 1
        ranking = parse(r['text']); row = {**req, **r, 'ranking':ranking, 'l1':error(ranking,gold)}
        append(out/'responses.jsonl',row)
        write(out/'STATUS.json',{'status':'RUNNING','calls':calls,'maximum_calls':112*len(cfg['seeds']),
              'seed':seed,'arm':arm,'stage':stage,'elapsed_seconds':time.monotonic()-started})
        if r['status'] != 'OK' or not r['text'].strip(): raise ValueError('incomplete_generation_branch_dependency')
        return row
    try:
        for seed in cfg['seeds']:
            initial_order, orders = schedule(seed); initials = {}; seed_rows = []; failed_arms = []
            # Same concentrated independent initials shared by private/hidden/revealed.
            for actor in initial_order:
                initials[actor] = call(seed,'B_hidden',actor,'initial',[],[])
            for arm in ARMS:
                try:
                    branch_initial = initials
                    if arm in ['F_full','N_none']:
                        branch_initial = {actor:call(seed,arm,actor,'initial',[],[]) for actor in initial_order}
                    own = {a:[branch_initial[a]['text']] for a in ACTORS}
                    public = [] if arm == 'A_private' else [(a,branch_initial[a]['text']) for a in initial_order]
                    for round_no, order in enumerate(orders,1):
                        for actor in order:
                            row = call(seed,arm,actor,'work',own[actor],public,round_no)
                            own[actor].append(row['text'])
                            if arm != 'A_private': public.append((actor,row['text']))
                    finals = [call(seed,arm,a,'final',own[a],public) for a in ACTORS]
                    result = {'seed':seed,'arm':arm,'initials':{a:branch_initial[a]['l1'] for a in ACTORS},
                              'finals':{a:r['l1'] for a,r in zip(ACTORS,finals)},
                              'initial_aggregate':aggregate([branch_initial[a]['ranking'] for a in ACTORS],gold),
                              'final_aggregate':aggregate([r['ranking'] for r in finals],gold),
                              'order':orders, 'complete':True}
                    seed_rows.append(result); scores.append(result); write(out/'scores.json',scores)
                except ValueError as exc:
                    if str(exc) != 'incomplete_generation_branch_dependency': raise
                    failed_arms.append(arm)
                    result = {'seed':seed,'arm':arm,'complete':False,'reason':str(exc)}
                    seed_rows.append(result); scores.append(result); write(out/'scores.json',scores)
            if len(failed_arms) >= 2: raise RuntimeError('two_failed_arms_stop_before_next_seed')
            write(out/f'seed-{seed}.json',seed_rows)
    except BaseException as exc:
        import traceback
        failure = {'type':type(exc).__name__, 'message':str(exc),'traceback':traceback.format_exc()}
    write(out/'STATUS.json',{'status':'FAILED' if failure else 'COMPLETED','calls':calls,
          'maximum_calls':112*len(cfg['seeds']), 'elapsed_seconds':time.monotonic()-started,'failure':failure,
          'scores':scores, 'freeze_unchanged':load(HERE/'FREEZE.json') == freeze()})
    print(json.dumps(load(out/'STATUS.json'),ensure_ascii=False))
    if failure: raise SystemExit(1)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(); parser.add_argument('mode',choices=['preflight','run'])
    args = parser.parse_args()
    preflight() if args.mode == 'preflight' else run()
