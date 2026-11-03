"""Offline audit and explicit same-assistant semantic annotations; never calls models."""
import collections
import json
import sys
from pathlib import Path

import local_rule_frontend as frontend
import run_local_rule_frontend as runner

ROOT = Path(__file__).resolve().parents[1]
PREPARED = ROOT / 'runs/local-rule-frontend-prepared-20261025-r2'
OUT = ROOT / 'runs/local-rule-frontend-live-20261025-r1'

def read(path):
    return json.loads(path.read_text(encoding='utf-8'))

def write(name, value):
    (OUT / name).write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')

# Each tuple: task, member, O-final, Q-final, O-note, Q-note, first-to-final note.
# E=effective increment; M=mixed with material error; U=unclear increment;
# R=redundant conditional review; C=appropriate local confirmation, not increment.
PAIRS = [
 (1,'A1','E','E','正确换算88/112并纠正选择。','正确证明Alder为88不合格；只处理Alder，列为缺失的Birch换算其实可由同一原件完成。','普通保持；提问保持相关问题并产出有效局部结论。'),
 (1,'A2','M','M','正确应用82>80，但仍将150 ticks直接当成100标准单位以上。','同样混淆ticks/标准单位，并把同日更新的适用性重新悬置。','两组均保持混合错误；自主问题本身带入120>100的单位混淆。'),
 (1,'A3','E','E','最终明确缺少换算规则，给出有边界条件的选择。','明确原始ticks不能直接对标准单位阈值；条件比较可成立。','普通首轮说没有规则会让120不达标而150达标，这是无依据推测，最终已删除；提问组保持局部缺口识别。'),
 (2,'A1','E','E','纠正按事件总数比较，明确完整会话和去重条件。','纠正率的分子分母，明确启动和去重未知。','普通首轮把2.5称为恰好达标，最终删除；提问首轮已给部分条件计算，不能称纯粹提问。'),
 (2,'A2','M','E','写出B=2.5仍声称只有A达到2的门槛；存在直接比较错误。','正确得到含启动时A至多80/50=1.6，不足2；B仍需去重信息。','普通的门槛错误在二轮保留；提问组没有该错误，但把已给启动时间再要求确认。'),
 (2,'A3','M','E','结论直接选A，只有missing中说明完整会话待确认，交付边界不一致；敏感性口径可视为隐含条件结论。','明确选择A仅在处理区间代表完整会话等条件下成立，正确去重76。','普通首轮有显式条件，最终主结论丢失条件；提问组保留条件。'),
 (3,'A1','M','E','正确采用逐组支配，但把72/180写成0.72；定性选择仍对，敏感性口径可保留其贡献。','正确0.40，并证明差值0.05p_small+0.30p_large>0，不需要知道权重。','普通算错从首轮带到二轮；提问首轮声称需权重才能唯一选择，二轮正确撤回。'),
 (3,'A2','E','E','正确50/50加权得到0.50和0.675。','同样正确加权；要求重新确认A2.S1是否权威是额外疑问，不产生新数值错误。','两组保持有效；提问并未产生普通组缺少的知识。'),
 (3,'A3','M','M','已列B两组更优，却说全小任务时A更好。','列正确函数后解错不等式：0.25w>0.30应为w>1.2，写成w>0.30。','两组均未解决基础推理错误；问题表达完整不保证求解正确。'),
 (4,'A1','M','M','把120物理库存当120可用并认证both；只知预约子集不能排除损坏。','同样跨越可用库存边界，还错误指控120-55-40双扣R20。','两组都未保留仅预约关系的局部范围；提问组首轮已虚构草稿存在额外扣除。'),
 (4,'A2','E','E','正确105可用、两项只余10，给出Alpha_only且保留预约未知。','相同关键纠正；已明确损坏在120内却再次列为待确认。','两组均保留有效局部纠正；提问不增加独有收益。'),
 (4,'A3','U','U','正确非重叠加法和预约条件分支，但未区分物理与可用库存；按严格范围暂不计，宽口径可接受条件诊断。','同样预约分支，未显式利用自身非重叠证据且物理/可用范围未充分限定。','两组均未形成干净的新增纠正；不把两组的同类疑难点只扣一组。'),
 (5,'A1','E','E','依赖规则下50/65为有条件情形；明确设备和停机未知。','同样保持依赖与资源限制区别、条件性结果。','两组均有有效局部贡献；提问首轮也已算出50/65。'),
 (5,'A2','M','M','本地无build前置规则仍认证65；同时说build可与test重叠又给65，内部矛盾。','同样未经确认build前置就认证65，并把无停机下界当最早可行结果。','两组均未纠正关键范围问题；不能因官方全题75就简单将65判错，错误在适用前提未成立。'),
 (5,'A3','M','R','给出条件75时间线，却声称并行需要禁止的额外夹具，缺少设备原件支持。','合理指出夹具使用关系未知并abstain；但W0已指出共享未知，未加工自身40-50停机为新的条件结果。','提问组减少无依据断言，但主要表现为停止求解；不计为独有有效增补。'),
 (6,'A1','R','R','正确解释含等号阈值，但与原正确稿重复，继续把部署摘要当未获确认。','同样重复规则并悬置部署版本，没有新的纠正。','两组都未体现正确稿上的新增收益；独立不能核验原件与摘要为假必须区分。'),
 (6,'A2','R','R','正确确认请求和价格，又要求重查稿件已有的部署与规则摘要。','同样反复追问B部署；未把本地请求证据与已有解答直接连接。','两组均保持验证顾虑；没有实际团队整合，不能声称已把正确最终答案改错。'),
 (6,'A3','C','R','正确确认部署版本；谨慎区分自身不能核验其余规则，不计新纠正。','也确认版本，却新增没有资料依据的head node/exclusive门槛疑问。','提问组增加无据疑问，普通组有更直接的局部确认；不能将假设性问句直接计为实际错误修改。'),
]

def main():
    manifest, plan, _ = runner.verify(PREPARED)
    runner.gates(PREPARED)
    state = read(OUT/'progress.json')
    rows = read(OUT/'review.json')['rows']
    reqs = [json.loads(x) for x in (OUT/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses = [json.loads(x) for x in (OUT/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['status'] == 'completed'
    assert len(rows) == len(reqs) == len(responses) == state['attempts'] == 72
    assert len(list(OUT.glob('*.raw.txt'))) == 72
    assert [r['slot'] for r in rows] == list(range(1,73))
    assert all(r['status'] == 'readable' for r in rows)
    assert all(r['retry'] == 0 for r in reqs)
    assert all(r['response']['status'] == 'completed' for r in responses)
    for field in ('input_tokens','output_tokens'):
        assert sum(r['response']['usage'][field] for r in responses) == state[field]
    lookup = {r['slot']:r for r in rows}
    costs = collections.defaultdict(lambda:dict(requests=0,input_tokens=0,output_tokens=0))
    for row, request_log, response in zip(rows,reqs,responses):
        slot = row['slot']
        packet = read(PREPARED/row['context'])
        actual = read(OUT/'actual_requests'/f'{slot:02d}.json')
        expected_packet = packet if row['stage']=='first' else frontend.second_packet(packet,lookup[slot-1]['answer'])
        assert actual == frontend.request(row['stage'],row['method'],expected_packet)
        assert request_log['payload']['instructions'] == actual['instructions']
        assert request_log['payload']['max_output_tokens'] == 1536
        # Exact packet reconstruction verifies no foreign originals/offline rubric fields.
        assert set(expected_packet) == (set(packet) if row['stage']=='first' else {'task','member','public_sources','own_sources','earlier_work'})
        allowed = {s['ref'] for s in packet['public_sources']+packet['own_sources']}
        assert all(e['source'] in allowed for e in row['answer']['evidence'])
        c = costs[row['method']]; c['requests'] += 1
        for field in ('input_tokens','output_tokens'): c[field] += response['response']['usage'][field]
    annotation_issues = [{'slot':r['slot'],'issues':r['answer']['annotation_issues']} for r in rows if r['answer']['annotation_issues']]
    audit = dict(status='PASS',requests=72,readable=72,raw_responses=72,retries=0,
                 complete_member_pairs=18,unknown_usage=state['unknown_usage'],annotation_issues=annotation_issues,
                 input_tokens=state['input_tokens'],output_tokens=state['output_tokens'],costs=dict(costs),
                 source_packet_reconstruction='72/72 exact',frozen_files_and_code='verified',
                 first_packet_pair_match='both methods reconstructed from same context',
                 evidence_handle_scope='all evidence handles visible to originating member',
                 rubric_transmission='exact request reconstruction excludes offline fields; no inference from keyword scan',
                 checks_not_proved='Semantics and paid-provider future reliability are not certified by this audit.')
    write('TECHNICAL_AUDIT.json',audit)
    annotations=[]; paired=[]
    for task, member, o, q, onote, qnote, transition in PAIRS:
        selected=[r for r in rows if r['task']==f'rule-dev-{task:02d}' and r['member']==member]
        finalslots={r['method']:r['slot'] for r in selected if r['stage']=='second'}
        paired.append(dict(task=f'rule-dev-{task:02d}',member=member,ordinary=o,local_question=q,
                           strict_discordance='question_only' if q=='E' and o!='E' else 'ordinary_only' if o=='E' and q!='E' else 'tie',
                           first_to_final_review=transition))
        for method,code,note in [('ordinary',o,onote),('local_question',q,qnote)]:
            slot=finalslots[method]
            annotations.append(dict(task=f'rule-dev-{task:02d}',member=member,method=method,first_slot=slot-1,final_slot=slot,
                category=code,effective_increment=(code=='E'),semantic_review=note,
                support='supported_or_conditional' if code in ('E','R','C') else 'mixed_material_error' if code=='M' else 'unclear',
                applicability='preserved' if code in ('E','C') else 'see_semantic_review',
                task_value='new_or_corrective' if code=='E' else 'confirmation' if code=='C' else 'see_semantic_review'))
    strict={method:sum(a['effective_increment'] for a in annotations if a['method']==method) for method in frontend.METHODS}
    # Deliberately explicit sensitivity, not a replacement of the frozen criterion:
    # credit O 02/A3 implicit caveat, O 03/A1 valid dominance despite wrong numeral.
    # U 04/A3 accepted symmetrically adds one to both and does not change difference.
    summary=dict(scope='Local contribution development diagnostic, not team accuracy',tasks=6,members=3,repeats=1,
        annotation='Same assistant, posthoc and nonblind; qualitative error severity judgments are not independently validated.',
        per_method_denominator=18,strict_effective_increment=strict,
        strict_delta_count=strict['local_question']-strict['ordinary'],
        strict_relative_count_change=(strict['local_question']-strict['ordinary'])/strict['ordinary'],
        category_counts={m:dict(collections.Counter(a['category'] for a in annotations if a['method']==m)) for m in frontend.METHODS},
        task_effective_counts={f'rule-dev-{t:02d}':{m:sum(a['effective_increment'] for a in annotations if a['task']==f'rule-dev-{t:02d}' and a['method']==m) for m in frontend.METHODS} for t in range(1,7)},
        paired_discordance=dict(collections.Counter(p['strict_discordance'] for p in paired)),
        sensitivity=dict(credit_ordinary_conditional_scope_and_qualitative_dominance={'ordinary':8,'local_question':9},
                         also_accept_inventory_unclear_symmetrically={'ordinary':9,'local_question':10},
                         interpretation='Difference shrinks from 3 to 1, concentrated in task02/A2; no robust two-task benefit claim.'),
        technical=audit,
        decision='Do not build C or expand paid runs. Candidate has a limited local signal; stop architecture escalation pending audit of genuine new knowledge, evidence scope and lost correct draft information.',
        limitations=['18 member pairs nested in only six constructed tasks; one generation per condition.',
          'Some first-stage question outputs already solve parts of the task, so no pure question-then-solve causal claim.',
          'Second-stage removal of W0 is shared by both methods, so anchoring reduction is not isolated.',
          'No no-resource control in H1, no measured natural expertise, no final team integration or adoption outcome.',
          'Correct draft06 is not backed by teammate original files in local packets; reasonable requests for independent evidence must not be mislabeled as false factual edits.'])
    write('SEMANTIC_REVIEW.json',dict(category_legend={'E':'有效增补/纠正','M':'正确部分与关键错误混合','U':'增补/范围不清楚','R':'重复或保留验证疑问，没有新纠正','C':'合理局部确认'},annotation_procedure=summary['annotation'],attempts=annotations,pairs=paired))
    write('SUMMARY.json',summary)
    table='\n'.join(f"| {t[-2:]} | {v['ordinary']}/3 | {v['local_question']}/3 |" for t,v in summary['task_effective_counts'].items())
    report=f'''# 72次局部贡献对照结果（2026-10-25）

结论：有局部正信号，但不足以证明这个前端稳定有效，更不支持完整CoReTA架构改善。按原定去留规则，本批不进入整合C，不自动扩跑。

## 技术执行

72/72请求完成，72份原文与实际请求齐全，0重试、0不可读、0注释异常。输入59,855 tokens，输出17,550 tokens。冻结文件和源码hash复验通过；72份实际组包与冻结前端逐一重建一致；第二轮只含当前任务、公共/自身原件及实际首轮text，没有额外W0或其他成员原件。输入输出逐响应usage合计与progress一致。详见TECHNICAL_AUDIT.json。

## 比较的是什么

普通组允许直接给证据、计算、问题或条件结论，再改进一次。新组要求先自主提出局部问题，再求解。两组各36次调用、18次成员贡献尝试。6题是人工规则任务和人工旧稿，没有成员互相交换本轮贡献，没有整合者。因此这不是普通集中讨论与完整CoReTA的最终正确率比较。

## 逐题原始计数

以下为同一助手事后非盲标注，评分是局部有效增补/纠正，不是整题答对率。最后一轮为交付；不能挑两轮中最好的一份。混合关键错误、范围不清楚以及合理确认/不改分开保存，未把无增补都当作错误。

| 任务 | 普通两次评议 | 自主提问再求解 |
|---|---:|---:|
{table}
| 合计 | 6/18 | 9/18 |

严格口径差3次（+16.7个百分点；计数相对+50%）。不能用这个相对百分比称稳定能力提高。三个差异中：02/A2是普通组写出2.5却判定不达2的直接错误；02/A3主要是条件写在missing还是主结论的评分边界；03/A1是0.72误抄但定性支配论证仍有效。对后两项采用宽口径，变为8/18对9/18，只剩同一道任务的一个配对差异。04/A3范围疑难若两组都接受，则9/18对10/18，差值仍为1。逐项理由、槽位和首轮到最终变化均在SEMANTIC_REVIEW.json；这些是敏感性分析，不替换冻结标准。

## 真正有价值的观察

1. 提问不能保证解出问题。03/A3列出正确函数A=0.10+0.80w、B=0.40+0.55w，却把0.25w>0.30解为w>0.30，虚构选择反转；应为w>1.2，在合法权重内不成立。普通组同处也犯错。
2. 局部范围没有解决。01/A2两组都用ticks直接比较标准单位；05/A2两组都在自己没有前置依赖原件时认证65，而且未处理未知停机。新组并未稳定让成员停留在已知知识能支持的范围。
3. 更保守不一定更有用。05/A3新组不再强行给75，减少假设扩张，但只回到W0已指出的夹具关系未知，没有把自身停机窗口加工成新的条件结果。这是减少无据断言，不能计作新增知识利用成功。
4. 正确稿控制没有显示清晰优势。06两组都再次要求确认稿件已有的部署/规则摘要；新组A3还引入head node与排他阈值疑问。可以合理声明无法独立核验，不能据此断言共享事实为假；本批没有最终整合，不声称实际把正确团队答案改错。
5. 个别有效条件被保留，但流程也会丢信息。01/A1新组正确算出88，却把同包可算的Birch换算列为缺失；03/A1新组二轮纠正了首轮不必要的权重依赖。应分别记录实际修复、计算遗漏和无谓重新确认。

## 不能据此声称什么

不声称专长已建立、互补知识已在团队中正确组合、最终团队准确率提高、旧答案锚定被隔离解决或有统计显著改善。仅6题且一遍生成；18配对不是18道独立任务。一些自主问题首轮已经给出数值/条件解，不能把差异完全归因于纯粹先提问。二轮去掉W0是两组共有处理，不能归为新组独有机制。

## 后续决策

先冻结本批负面与正面案例，不新增流程组件，不启动更大付费实验。优先在现有材料上区分三类问题：本地规则会用但错误扩张到全解、已有共享摘要缺乏可追溯依据、基础计算/逻辑自身错误。前两类才直接对应我们可设计的协作机制；第三类不能由多一轮协调自动解决。

在现有日志上先形成可审查的最小机制条件：局部产物明确哪些结论由本地原件支持、哪些仍依赖别人；共享稿件中的跨成员事实能追溯到提供者的实际贡献；合理保留/确认不被要求制造问题。只有在确认现有流程具体缺少哪条连接后，才决定保留、重做或放弃这个前端。不要直接把这些条件堆成新协议后付费验证。
'''
    (OUT/'RESULTS.md').write_text(report,encoding='utf-8')
    runner.io.write(PREPARED/'EXECUTION_STATUS.json',dict(status='COMPLETED_REVIEWED',run=str(OUT.relative_to(ROOT)),requests=72,automatic_expansion=False,report=str((OUT/'RESULTS.md').relative_to(ROOT))))
    print(json.dumps(dict(technical=audit['status'],counts=strict,sensitivity=summary['sensitivity'],costs=dict(costs)),ensure_ascii=False))

if __name__ == '__main__':
    sys.stdout.reconfigure(encoding='utf-8')
    main()
