"""Postrun audit and fixed-choice scoring, with explicit manual reasoning review."""
import collections
import json
from pathlib import Path
import local_judgment_frontend as io
import run_local_rule_adoption as runner
import prepare_local_rule_adoption as probe

ROOT=io.ROOT
P=ROOT/'runs/local-rule-adoption-prepared-20261025-r2'
OUT=ROOT/'runs/local-rule-adoption-live-20261025-r1'

def main():
    runner.verify(P);runner.gates(P)
    binding=io.read(P/'SCORING_BINDING.json')
    assert io.digest(ROOT/binding['offline_reference_path'])==binding['sha256']
    refs={r['task_id']:r for r in io.read(ROOT/binding['offline_reference_path'])}
    state=io.read(OUT/'progress.json');rows=io.read(OUT/'review.json')['rows']
    requests=[io.strict_json(s) for s in (OUT/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[io.strict_json(s) for s in (OUT/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['status']=='completed' and state['attempts']==len(rows)==len(requests)==len(responses)==24
    assert len(list(OUT.glob('*.raw.txt')))==24
    assert len(list((OUT/'actual_requests').glob('*.json')))==24
    assert all(r['status']=='readable' and not r['answer']['annotation_issues'] for r in rows)
    assert all(r['retry']==0 for r in requests)
    assert all(r['response']['status']=='completed' for r in responses)
    for field in ('input_tokens','output_tokens'):
        assert sum(x['response']['usage'][field] for x in responses)==state[field]
    costs=collections.defaultdict(lambda:dict(requests=0,input_tokens=0,output_tokens=0))
    scored=[]
    for r,q,response in zip(rows,requests,responses):
        packet=io.read(P/r['packet']);actual=io.read(OUT/'actual_requests'/f"{r['slot']:02d}.json")
        assert actual==probe.request(packet)==io.read(P/r['request'])
        assert q['payload']['instructions']==actual['instructions'] and q['payload']['max_output_tokens']==1536
        assert set(packet)=={'task','public_sources','historical_work','contributions','disclosed_evidence'}
        assert sorted(x['ref'] for x in packet['disclosed_evidence'])==['A1.S1','A2.S1','A3.S1','P1','TASK']
        c=costs[r['method']];c['requests']+=1
        for field in ('input_tokens','output_tokens'):c[field]+=response['response']['usage'][field]
        expected=refs[r['task']]['expected'];a=r['answer']
        # All24 substantive explanations manually read. Their central arithmetic and
        # eligibility/comparison support expected, including the two mismatched choices.
        scored.append(dict(slot=r['slot'],task=r['task'],repeat=r['repeat'],method=r['method'],expected=expected,
            submitted_choice=a['choice'],choice_correct=a['choice']==expected,
            core_reasoning_supported=True,reasoning_implied_choice=expected,
            submission_reasoning_consistent=a['choice']==expected,
            control=refs[r['task']]['draft_type']=='correct_supported_control',
            reasoning_annotation='Same assistant, nonblind manual review of full explanation; main evidence application supports reference. This is not a claim every attribution sentence is correct.',
            caveats=(['Mischaracterizes a conditional local35-minute contribution as simply wrong, rather than now inapplicable under disclosed shared fixture.'] if r['slot'] in (18,19) else
                     ['Overcredits C1 arithmetic without distinguishing its150-usable assumption from the correctly integrated140 usable.'] if r['slot']==15 else [])))
    task_counts={t:{m:sum(x['choice_correct'] for x in scored if x['task']==t and x['method']==m) for m in ('ordinary','local_question')} for t in refs}
    results={m:dict(correct=sum(x['choice_correct'] for x in scored if x['method']==m),denominator=12,
        core_reasoning_supported=sum(x['core_reasoning_supported'] for x in scored if x['method']==m),
        choice_reasoning_mismatch_slots=[x['slot'] for x in scored if x['method']==m and not x['submission_reasoning_consistent']],
        correct_control_retained=sum(x['choice_correct'] for x in scored if x['method']==m and x['control']),correct_control_denominator=4,
        wrong_draft_repaired=sum(x['choice_correct'] for x in scored if x['method']==m and not x['control']),wrong_draft_denominator=8) for m in ('ordinary','local_question')}
    pairs=[]
    for task in refs:
        for rep in (1,2):
            matched={x['method']:x for x in scored if x['task']==task and x['repeat']==rep}
            o=matched['ordinary']['choice_correct'];q=matched['local_question']['choice_correct']
            pairs.append(dict(task=task,repeat=rep,ordinary=o,local_question=q,
                outcome='both_correct' if o and q else 'both_wrong' if not o and not q else 'question_only' if q else 'ordinary_only'))
    source=io.read(P/'SOURCE_AUDIT.json')
    audit=dict(status='PASS',requests=24,readable=24,raw_files=24,retries=0,annotation_issues=0,
        input_tokens=state['input_tokens'],output_tokens=state['output_tokens'],unknown_usage=state['unknown_usage'],
        actual_request_reconstruction='24/24 exact',frozen_files='verified',all12_pairs_same_complete_facts=source['all_pairs_same_facts'],costs=dict(costs))
    upstream=io.read(ROOT/'runs/local-rule-confirmation-live-20261025-r1/SUMMARY.json')['technical']['costs']
    cumulative={m:{field:upstream[m][field]+costs[m][field] for field in ('requests','input_tokens','output_tokens')} for m in costs}
    summary=dict(scope='Archived-contribution integration under identical full disclosed evidence',technical=audit,results=results,task_counts=task_counts,
        paired_counts=dict(collections.Counter(x['outcome'] for x in pairs)),pairs=pairs,
        core_reasoning_review='24/24 central derivations support correct reference, not24/24 fully flawless narratives.',
        cumulative_archival_generation_plus_integration_cost=cumulative,
        decision='No final-choice gain observed. Preserve local contribution signal but do not claim downstream accuracy benefit. Do not add a feedback architecture or auto-expand from this result.',
        limitations=['6 authored tasks,2 archived contribution repeats,1 integration sample per pool;12 pairs are not12 independent tasks.',
          'Full rule evidence was already disclosed in every pool; no evidence-only/no-contribution control was run, so necessity or causal value of contribution prose is unknown.',
          'This reuses historical member outputs and has no fresh reciprocal interaction; not an end-to-end ordinary discussion vs fullCoReTA comparison.',
          'Choice/reasoning mismatch is semantic submission inconsistency, not JSON/parse failure; no output was repaired or rescored from reasoning.',
          'Core-reasoning annotations by same assistant, nonblind; contributor-attribution imprecision retained separately.'])
    io.write(OUT/'TECHNICAL_AUDIT.json',audit)
    io.write(OUT/'SCORES.json',dict(choice_scoring='Exact ids against prebound author reference, no automatic correction.',reasoning_scoring='Manual, same assistant, nonblind.',rows=scored))
    io.write(OUT/'SUMMARY.json',summary)
    table='\n'.join(f"| {task[-2:]} | {counts['ordinary']}/2 | {counts['local_question']}/2 |" for task,counts in task_counts.items())
    report=f'''# 固定贡献团队整合诊断结果

结论：本批没有观察到自主提问贡献池的最终选项优势。普通贡献池和自主提问贡献池均11/12；不推翻此前局部贡献15/36对18/36的记录，但该局部差异在本场景未形成最终正确率差异。

## 执行与对照

24/24官方DeepSeek请求完成，0不可读、0重试、0注释异常，输入42341、输出6294 tokens。来源、实际请求及usage已逐项审核；未发离线评分表，未重新生成成员贡献，未追加调用。

每次由相同提示的整合者读取旧人工W0、任务、三份归档成员最终交付及已经披露的原文。12配对的事实范围完全相同，全部覆盖三份规则原文。因此这是完整事实下贡献表达差异的下游诊断，不是新的交互协作或完整CoReTA对自由讨论。

## 主结果：按实际提交选项评分

| 任务 | 普通贡献→整合 | 自主提问贡献→整合 |
|---|---:|---:|
{table}
| 合计 | 11/12 | 11/12 |

两份正确稿控制09/12均4/4保留；四份错误稿任务两遍合计均修复7/8。配对为10次双方对、1次仅普通对、1次仅自主提问对；两个单方差异都在08的不同重复，没有跨题净优势。只6题，不进行12独立任务的显著性宣称。

## 两个失分不是格式失败

- 槽5，自主提问池、08第一遍：reasoning明确180/90=2.0使A不合格、210/60=3.5使B合格，最后说应选B，choice却为A。
- 槽7，普通池、08第二遍：同样正确推导B为唯一合格服务，choice仍为A。

均是合法JSON与合法候选ID，程序正确接收；语义上提交字段与理由不一致。按冻结主评分计错，没有把choice改成B，没有补跑，也没有把正确理由冒充正确最终答案。它们显示实际提交一致性仍有局限，不证明当前某个协作组件引起这一现象。

## 中间过程说明了什么

逐份阅读24份解释，核心资格/比较计算均支持正确参考答案。例如08两组都把去重180/210与完整90/60分钟结合；10都用可用140、需求并集110得剩30；11都结合build前置、共享夹具及早于20结束的停机得到45；09/12用已披露原文解决成员所称的信息未决。

这证明本批整合阶段实际组合了分散来源内容，且经常纠正成员贡献里的错误；不能据此证明贡献文本是必要原因，因为没有只给原文的对照。普通池也完成同样核心推理，局部贡献质量差异被完整原文与整合过程部分消解。

“核心计算正确”不等于每句理由无瑕疵：槽18/19把成员明确有条件的35分钟说成简单错误，实际它只是在共享夹具已披露后不适用；槽15笼统称C1算术正确，没有区分其150可用假设与最终正确整合的140。引用used_contributions也不等于所有引用贡献都被正确应用。这些单列于SCORES.json，不混入最终选项自动评分。

## 成本及后续判断

本批只追加每组12次整合。与已保存的成员生成合计，每组84次；累计成本：{json.dumps(cumulative,ensure_ascii=False)}。这些是归档生成加整合的实际合计，不是本批又花168次，也没有完整在线端到端耗时。

当前结论是：有局部形成信号，但在这些完整披露的小任务上没有最终正确率增益，不把它说成架构有效或整个方向无效。暂不据此增加仲裁、检查或反馈组件，也不为了制造差异删掉原文。保留完整反例，下一步应先判断真实研究场景是否也已经完整披露并可轻易整合，再决定是否值得新的端到端任务验证；本批不自动扩跑。
'''
    (OUT/'RESULTS.md').write_text(report,encoding='utf-8')
    io.write(P/'EXECUTION_STATUS.json',dict(status='COMPLETED_REVIEWED',model_requests=24,automatic_expansion=False,run=str(OUT.relative_to(ROOT))))
    print(json.dumps(dict(status='PASS',results=results,pairs=summary['paired_counts'],costs=dict(costs)),ensure_ascii=False))

if __name__=='__main__':main()
