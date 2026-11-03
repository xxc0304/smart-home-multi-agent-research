"""Mixed main-population sampling; supplements never enter the main estimate."""
import random
from collections import Counter
from .data import read, write, adapt, member_packet

EXCLUDED_CONTEXTS = {5, 6, 9, 11, 12, 15}
SUPPLEMENTS = ('281ec4c8-1632-40e9-bdf2-8ceac4303d61', '0d3a1b7b-890b-455a-b55a-082bb5fe6ceb')


def select(source, count=12, seed=20261027):
    contexts = read(source)
    pool = [(i, q) for i, c in enumerate(contexts) if i not in EXCLUDED_CONTEXTS
            for q in c['questions'] if q.get('answer_type') == 'arithmetic']
    selected = random.Random(seed).sample(pool, count)
    index = {q['uid']: (i, q) for i, c in enumerate(contexts) for q in c['questions']}
    if len(index) != sum(len(c['questions']) for c in contexts):
        raise ValueError('duplicate upstream question IDs')
    supplements = [index[uid] for uid in SUPPLEMENTS]
    main_contexts = {i for i, _ in selected}
    if any(i in main_contexts | EXCLUDED_CONTEXTS for i, _ in supplements):
        raise ValueError('supplement context overlaps main or old engineering pool')
    rows = []
    for group, values in [('main', selected), ('diagnostic', supplements)]:
        for number, (i, q) in enumerate(values, 1):
            rows.append(dict(case_id=f'{group}-{number:02d}', group=group, context_index=i,
                             question_uid=q['uid'], question=q['question'],
                             source_annotation=q.get('answer_from'),
                             final_member='A1' if number % 2 else 'A2'))
    return dict(selection_kind='development_preparation_not_model_results', seed=seed,
                population='train arithmetic questions excluding six prior engineering contexts',
                eligible_questions=len(pool), excluded_contexts=sorted(EXCLUDED_CONTEXTS),
                main_count=len(selected), main_distinct_contexts=len(main_contexts),
                main_annotations=dict(Counter(q.get('answer_from') for _, q in selected)),
                diagnostic_count=len(supplements),
                pooling_policy='main and diagnostic reported separately; never report pooled 14 as natural accuracy',
                rows=rows)


def prepare(source, output):
    from pathlib import Path
    plan = select(source)
    contexts = read(source)
    output = Path(output)
    cases = []
    for row in plan['rows']:
        context = contexts[row['context_index']]
        question = next(q for q in context['questions'] if q['uid'] == row['question_uid'])
        task, reference = adapt(context, question, row['context_index'])
        case = dict(case_id=row['case_id'], group=row['group'], final_member=row['final_member'], task=task)
        write(output / row['case_id'] / 'runtime.json', case)
        write(output / row['case_id'] / 'offline' / 'reference.json', reference)
        for actor in task['members']:
            write(output / row['case_id'] / 'packets' / f'{actor}.json', member_packet(task, actor))
        cases.append(case)
    write(output / 'SELECTION.json', plan)
    return cases, plan
