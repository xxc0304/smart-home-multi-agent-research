"""Source-preserving TAT-QA development adapter. Never builds oracle work items."""
import copy
import hashlib
import json
from pathlib import Path


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def write(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2, allow_nan=False) + '\n', encoding='utf-8')


def adapt(context, question, index):
    """Keep the complete native table and every paragraph; no gold-derived split."""
    table = context['table']
    sources = [{'id': 'T1', 'owner': 'A1', 'kind': 'table', 'upstream_uid': table['uid'],
                'content': json.dumps(table['table'], ensure_ascii=False)}]
    for number, paragraph in enumerate(context['paragraphs'], 1):
        sources.append({'id': f'P{number}', 'owner': 'A2', 'kind': 'paragraph',
                        'upstream_uid': paragraph['uid'], 'content': paragraph['text']})
    task = {'task_id': question['uid'], 'question': question['question'],
            'members': ['A1', 'A2'], 'sources': sources,
            'origin': {'dataset': 'TAT-QA', 'split': 'train', 'context_index': index,
                       'table_uid': table['uid'], 'question_uid': question['uid']}}
    reference = {key: copy.deepcopy(question.get(key)) for key in
                 ('answer', 'derivation', 'answer_type', 'answer_from', 'scale', 'rel_paragraphs')}
    return task, reference


def prepare(source, output, count=6):
    contexts = read(source)
    selected = []
    for index, context in enumerate(contexts):
        for question in context['questions']:
            if question.get('answer_type') == 'arithmetic' and question.get('answer_from') == 'table-text':
                task, reference = adapt(context, question, index)
                selected.append((task, reference))
                break
        if len(selected) == count:
            break
    if len(selected) != count:
        raise ValueError('insufficient eligible contexts')
    output = Path(output)
    for number, (task, reference) in enumerate(selected, 1):
        directory = output / f'task-{number:02d}'
        write(directory / 'runtime.json', task)
        write(directory / 'offline' / 'reference.json', reference)
        for member in task['members']:
            write(directory / 'packets' / f'{member}.json', member_packet(task, member))
    metadata = {'upstream_url': 'https://github.com/NExTplusplus/TAT-QA',
                'source_file': str(Path(source).resolve()),
                'source_sha256': hashlib.sha256(Path(source).read_bytes()).hexdigest(),
                'license': 'Dataset CC BY 4.0 per upstream README',
                'citation': 'Zhu et al., TAT-QA, ACL 2021, https://aclanthology.org/2021.acl-long.254/',
                'selection': 'first six arithmetic/table-text questions, one per context, original order',
                'selection_uses': ['answer_type', 'answer_from'],
                'partition': 'A1 complete native table; A2 all original paragraphs',
                'status': 'development adapter, not model evaluation or native multi-agent benchmark',
                'tasks': [{'task_id': t['task_id'], 'question': t['question'],
                           'context_index': t['origin']['context_index'], 'sources': len(t['sources'])}
                          for t, _ in selected]}
    write(output / 'DATA_AUDIT.json', metadata)
    return [task for task, _ in selected]


def member_packet(task, member, disclosed=()):
    if member not in task['members']:
        raise ValueError('unknown member')
    disclosed = set(disclosed)
    return {'task': {'task_id': task['task_id'], 'question': task['question']}, 'member': member,
            'sources': [copy.deepcopy(s) for s in task['sources']
                        if s['owner'] == member or s['id'] in disclosed]}


def centralized_packet(task):
    return {'task': {'task_id': task['task_id'], 'question': task['question']},
            'sources': copy.deepcopy(task['sources'])}


def swapped(task):
    value = copy.deepcopy(task)
    for source in value['sources']:
        source['owner'] = 'A2' if source['owner'] == 'A1' else 'A1'
    return value
