"""Check literal evidence for eight existing cases; interpretations are declared, not inferred by code."""
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parent.parent
SEED = PROJECT / 'research/expert-team-assets-20261029/CASE_SEED_8.json'


def leaves(value, path=()):
    if isinstance(value, dict):
        for key, item in value.items():
            yield from leaves(item, path + (str(key),))
    elif isinstance(value, list):
        for index, item in enumerate(value):
            yield from leaves(item, path + (str(index),))
    elif isinstance(value, str):
        yield path, value


def event(case, slot, field, fragment, observation):
    index, record = next((i, r) for i, r in enumerate(case['records']) if r['row']['slot'] == slot)
    value = record
    for key in field:
        value = value[key]
    matches = [(p, text) for p, text in leaves(value) if fragment.lower() in text.lower()]
    if not matches:
        raise ValueError(f"Missing evidence {case['id']} slot {slot}: {fragment}")
    path, text = matches[0]
    start = text.lower().index(fragment.lower())
    excerpt = text[max(0, start - 70):start + len(fragment) + 150]
    request_path = PROJECT / case['folder'] / 'requests.jsonl'
    request_line = next(i for i, s in enumerate(request_path.read_text(encoding='utf-8').splitlines(), 1)
                        if json.loads(s).get('slot', json.loads(s).get('attempt')) == slot)
    return {'slot': slot, 'seed_pointer': '/cases/' + str(int(case['id'][1:]) - 1) + '/records/' + str(index) + '/' + '/'.join(map(str, field + list(path))),
            'raw_path': record['raw_path'], 'request_file': request_path.relative_to(PROJECT).as_posix(),
            'request_line': request_line, 'matched_fragment': fragment, 'excerpt': excerpt,
            'observation': observation}


def author_event(case, round_number, message_index, field, fragment, observation):
    ri, rd = next((i, r) for i, r in enumerate(case['run']['rounds']) if r['round'] == round_number)
    message = rd['messages'][message_index]
    text = message[field]
    assert fragment.lower() in text.lower()
    start = text.lower().index(fragment.lower())
    return {'round': round_number, 'message_index': message_index, 'agent': message['agent'],
            'original_file': case['source_file'],
            'original_pointer': f"/conditions/{case['condition_index']}/runs/{case['source_run_index']}/rounds/{ri}/messages/{message_index}/{field}",
            'matched_fragment': fragment, 'excerpt': text[max(0, start - 70):start + len(fragment) + 150],
            'observation': observation}


def main():
    cases = json.loads(SEED.read_text(encoding='utf-8'))['cases']
    assert [c['id'] for c in cases] == [f'C{i:02}' for i in range(1, 9)]
    reviewed = []
    specs = {
        'C01': [(2, ['packet', 'information_available'], 'co-investor partnership', '原始私有资料支持共同投资条件已满足'),
                (10, ['packet', 'messages_from_other_participants'], 'PRIVATE.A2 resolves', '接收者确实收到了该条件已满足的报告'),
                (10, ['row', 'answer', 'reasoning'], 'cannot be credited', '接收者称原始私有资料不在本包，拒绝计入'),
                (13, ['row', 'answer', 'reasoning'], 'within 12 hours', '答对分支也把选择期限推成成交期限，需单独核忠实性')],
        'C02': [(17, ['packet', 'information_available'], 'main highway', '原始资料只指主公路'),
                (17, ['row', 'answer', 'reasoning'], 'only viable route', '发送者将主公路扩大为唯一可行道路'),
                (21, ['row', 'answer', 'reasoning'], 'unsupported', '接收者拒绝道路封闭报告，包含支持性与可信度争议'),
                (23, ['row', 'answer', 'reasoning'], 'Nova', '完整资料分支选中新参考候选，不等于所有理由均忠实')],
        'C03': [(55, ['packet', 'information_available'], 'Cape Industries: (h) N', '接收者自己的资料已明确Cape成本条件失败'),
                (55, ['packet', 'messages_from_other_participants'], "A2/A3's claims", 'A1消息反称已有失败信息不受资料支持'),
                (55, ['row', 'answer', 'reasoning'], "Cape fails (h) cost", '接收者仍承认成本失败'),
                (55, ['row', 'answer', 'reasoning'], "I follow A1", '输出明示追随，但仍不能从自述建立因果机制')],
        'C04': [(29, ['row', 'answer', 'choice'], 'option_1', 'A2中间答案命中参考'),
                (32, ['row', 'answer', 'choice'], 'option_3', '相同原始资料下A2改为非参考答案')],
        'C05': [(3, ['packet', 'own_sources'], 'less than 30', '局部持有者直接看到年龄限制'),
                (4, ['packet', 'local_reconstruction'], 'less than 30', '限制也确实进入终答接收者输入'),
                (4, ['packet', 'historical_work'], 'passenger', '乘客说法已出现在旧稿，不能说由本轮接收者首次创造'),
                (4, ['row', 'answer', 'reasoning'], 'cannot override', '终答承认年龄冲突却优先自身车辆/酒精推断')],
        'C06': [(27, ['packet', 'own_sources'], 'only access road', '原始地理范围限定为唯一通路'),
                (27, ['row', 'answer', 'text'], 'expectation', '局部稿保留预计持续关闭的时间不确定性'),
                (26, ['row', 'answer', 'reasoning'], 'categorical obstacle', '参考命中分支将预计关闭表述为确定障碍'),
                (28, ['row', 'answer', 'reasoning'], 'alternative route', '另一分支对唯一通路与替代通路作不同应用')],
    }
    interpretations = {
        'C01': ('资料不在直接来源栏，被当成不可用', '披露真实资料与汇总观点的协议同时改变；12小时语义也不稳。不能归因为专家身份或从众。'),
        'C02': ('信息组合产生原初答没有的正确候选', '发送者也存在范围扩大；原始资料路由不是单纯改善说服，不能将0对1解释为单因素效果。'),
        'C03': ('事实已承认但终答未依此处理，含明示意见依赖', '普通终票2:2、评分0.5；缺少固定消息的反事实和无消息对照，不能确定从众因果。'),
        'C04': ('没有他人推荐也能从对改错', '自身previous_answer变化、再次生成及推理波动仍未分离；不是所有错误都能由社会影响解释。'),
        'C05': ('收到且承认限制，并未保证正确应用', '乘客字段在上游共享稿/旧稿已存在；不能简单归责为接收者新编造，也不构成稳定专家证据。'),
        'C06': ('地理范围与时间不确定性被不同处理', '局部稿内容和历史可见性同时变化，且答对分支有强于原文的时间表述；无单因素因果结论。'),
        'C07': ('受阻说法实际进入下一成员收件后被开放说法覆盖', '初始没有正确选票，隐藏信息随机分配原映射未发布，不能称正确专家少数被压倒。'),
        'C08': ('同伴声称取得外部核验，后续按其统一行动且答对', '当前发布文件无独立工具回执字段；不确认真实核验，也不证明现实运行绝无外部工具。'),
    }
    for case in cases:
        cid = case['id']
        observations = [event(case, *spec) for spec in specs.get(cid, [])]
        checks = {}
        if cid == 'C04':
            a, b = [next(r['packet'] for r in case['records'] if r['row']['slot'] == s) for s in (29, 32)]
            checks['different_packet_keys'] = sorted(k for k in a.keys() | b.keys() if a.get(k) != b.get(k))
            checks['peer_messages_are_source_records'] = all(set(m) == {'ref', 'content'} for m in b['messages_from_other_participants'])
            assert checks['different_packet_keys'] == ['previous_answer']
        if cid == 'C05':
            p = next(r['packet'] for r in case['records'] if r['row']['slot'] == 4)
            checks['passenger_explicit_in_original_public_sources'] = any('passenger' in s['content'].lower() for s in p['public_sources'])
            checks['passenger_already_in_shared_structured_facts'] = any('passenger' in text.lower() for _, text in leaves(p['shared_contributions']))
        if cid == 'C07':
            observations = [author_event(case, 2, 0, 'response', 'blocked South Street', '成员明确报告阻断'),
                            author_event(case, 2, 1, 'prompt', 'blocked South Street', '下一成员输入含该消息，不是只有说出而无法证明收到'),
                            author_event(case, 2, 1, 'response', 'South Street remains open', '下一成员仍称开放'),
                            author_event(case, 3, 0, 'response', 'South Street confirmed open', '原报告者随后也采纳开放说法')]
        if cid == 'C08':
            observations = [author_event(case, 3, 3, 'response', 'I am contacting', '先提出并声称发起核验'),
                            author_event(case, 5, 3, 'response', 'unified report', '后声称已经收到EOC报告'),
                            author_event(case, 6, 0, 'response', 'Oakridge Library', '后续成员采用该结论')]
            checks['released_run_keys'] = sorted(case['run'])
        finding, limitation = interpretations[cid]
        reviewed.append({'id': cid, 'task': case['task'], 'observations': observations, 'checks': checks,
                         'finding': finding, 'interpretation_boundary': limitation,
                         'expertise': case['expertise_status'], 'annotation_status': 'Assistant evidence review, not independent human/blind annotation'})
    result = {'date': '2026-10-30', 'source': str(SEED), 'case_units': 8, 'unique_tasks': 7,
              'literal_evidence_events': sum(len(c['observations']) for c in reviewed), 'new_model_calls': 0,
              'scope': 'Literal/source-layer checks plus explicitly authored interpretations; not mechanism prevalence or causal estimation', 'cases': reviewed}
    (HERE / 'CASE_EVIDENCE_REVIEW.json').write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps({'cases': 8, 'evidence_events': result['literal_evidence_events'], 'checks': {c['id']:c['checks'] for c in reviewed if c['checks']}, 'new_model_calls': 0}, ensure_ascii=True))


if __name__ == '__main__':
    main()
