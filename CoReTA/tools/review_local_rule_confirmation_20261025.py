"""Offline audit and explicit nonblind manual annotations; no model calls."""
import collections
import json
from pathlib import Path
import local_judgment_frontend as io
import local_rule_frontend as frontend
import run_local_rule_confirmation as runner

ROOT=io.ROOT
P=ROOT/'runs/local-rule-confirmation-prepared-20261025-r1'
OUT=ROOT/'runs/local-rule-confirmation-live-20261025-r1'
# task, member, repeat, ordinary category, question category, paired semantic review.
# E effective increment; M material error/mixed; C appropriate confirmation;
# R conditional rechecking without new needed contribution. Controls are not failures.
ANNOTATIONS=[
 (7,'A1',1,'E','E','两组都正确反算100/90，拒绝Maple；新组首轮已解题，并非纯提问。'),
 (7,'A1',2,'E','E','两组都保留正确逆运算；新组局部屏蔽与普通组完整选择均成立。'),
 (7,'A2',1,'M','E','普通组仍以任意合理换算都过95认证Maple；新组虽开头称eligible，完整conclusion/status/scope明确单位条件未决。'),
 (7,'A2',2,'E','E','普通首轮偏向Maple，最终撤回无条件资格；两组最终均正确保留单位换算缺口。'),
 (7,'A3',1,'E','E','两组均保留校准范围有效但不能据此证明单位阈值；新增适用范围信息与换算缺口有用。'),
 (7,'A3',2,'E','E','普通首轮误把校准范围当公式验证，最终撤回；新组始终保持转换未知。'),
 (8,'A1',1,'E','E','均纠正记录/作业和处理/完整会话口径，保留明确条件；新组末句误称draft move away from A不影响主要局部结论。'),
 (8,'A1',2,'E','M','普通组条件率正确；新组每服务空闲阈值36/24可用，但结论A或neither把两服务空闲时间设成相同，遗漏可能仅B合格；首轮同错未修。'),
 (8,'A2',1,'M','E','普通组声称任何重复都使A失败，实际至多15重复仍满足225门槛；新组保留去重未决条件，90/60分母正确，但条件表达有歧义。'),
 (8,'A2',2,'E','E','普通组完整时间和去重条件正确；新组给A需225独立作业的有用门槛。关于空闲期可能有未记录完成属额外待核实假设，未断言实际发生。'),
 (8,'A3',1,'M','M','普通组用处理60分钟直接认证完整会话；新组除同类分母问题外，漏读原件已确认其余记录独立，又虚构独立数150至180范围。'),
 (8,'A3',2,'M','E','普通仅以接受自身去重原件为条件，未处理会话分母；新组scope和missing明确限定为会话等于处理60分钟，正确去重180/210。'),
 (9,'A1',1,'R','R','两组均正确推得权重临界0.8，但把正确稿已报25/75视作待核验；无新增当前任务纠正，也未断言实际应选L。'),
 (9,'A1',2,'R','R','均为权重条件重推；新组一句at least80后明确等号打平，按完整交付不将此口误当关键反转。'),
 (9,'A2',1,'C','C','两组都确认正确0.375/0.65和M；不计新增纠正，不计失败。'),
 (9,'A2',2,'C','C','均保留正确权重计算；新组首轮质疑自己的同权重原件，最终仍确认其条件结论，另记无谓核验。'),
 (9,'A3',1,'C','R','普通最终确认数据完整并给25/75下正确计算；新组只重推未给权重的条件边界、没有必要新纠正。'),
 (9,'A3',2,'R','R','两组均反复要求确认共享摘要中的权重；数学正确，但不算把正确稿修好。'),
 (10,'A1',1,'E','E','均正确并集110。普通把150物理说成可用有瑕疵，但也显式检验原稿140时仍余30；有效纠正不受影响。新组明确全150可用是假设。'),
 (10,'A1',2,'M','E','普通无条件把物理150作可用来认证both、抹去原稿140；新组status/scope/missing保留可用量不确定，局部并集110有效。该配对属范围边界项。'),
 (10,'A2',1,'E','E','普通给短缺15及有重叠可能改变结果的条件；新组首轮将门槛写25，最终改为正确15并保留实际重叠未知。'),
 (10,'A2',2,'E','E','两组均正确推出重叠至少15，明确未掌握实际重叠20。'),
 (10,'A3',1,'E','M','普通最终在无重叠时以150上界尚余20不足25作条件否定，并要求权威可用数；新组明确把正确140/10改为150/20，误修可用库存。普通边界说明：20是物理上界，不能当实际可用量。'),
 (10,'A3',2,'E','M','普通显式以150可用为假设给至少5重叠的条件测试；新组把150可用直接当前提，给重叠至少5就反转的条件，漏掉可用量限制。两份都不得被读作真实只需5；普通条件范围也列边界。'),
 (11,'A1',1,'M','E','普通仍说可并行时20+25=45下界；新组正确35并行/45串行且保留资源未知。'),
 (11,'A1',2,'M','E','普通首轮还把停机后的build误算25，最终声称任意不可用下仍20，并未解决并行；新组连续两遍正确20+max(15,10)=35条件结果。'),
 (11,'A2',1,'E','E','普通首轮20+25写50，最终改45并明确前置/无后续停机条件；新组正确排程45，额外test-before-pack假设非必要但条件下成立。'),
 (11,'A2',2,'E','M','普通最终明确以build前置及20后可用为条件；新组由start>=0推出夹具最早20，虽列前置未知仍认证最早45，缺少关键前提。'),
 (11,'A3',1,'M','E','普通以总active45作所有安排的下界，忽略可并行且错误停机位置；新组在build先20结束且后续串行条件下正确得到45、停机增量0。'),
 (11,'A3',2,'M','M','普通称所有工序用夹具却让build0-20无视停机；新组无依据假设build用夹具并推30/55。新组若显式以build占夹具为条件可成立，但最终只限定build-first，未充分表达该假设。'),
 (12,'A1',1,'C','C','两组都正确确认V2 secure6/V3 secure4并保留部署独立核验；不会因确认或合理条件化而计失败。'),
 (12,'A1',2,'C','C','两组规则比较正确，条件Red、Blue或neither没有被断言为实际换答案；共享部署摘要仍未获充分采用。'),
 (12,'A2',1,'R','R','两组均要求部署和规则佐证，未新增本地请求纠正；假设式neither/Blue不等于实际错改。'),
 (12,'A2',2,'R','R','均悬置正确稿；普通Blue never supported是当前证据不足，不是所有可能部署都不合格。'),
 (12,'A3',1,'M','C','普通最终说不论规则表Blue都排除，部署版本本身不能推出这一点，且把稿件V2上限6误述5；新组确认部署、正确保留规则未知。'),
 (12,'A3',2,'C','C','均正确确认实际RedV2/BlueV3，不能独立确认规则表；不算新增知识收益。'),
]

def main():
    runner.verify(P);runner.gates(P)
    state=io.read(OUT/'progress.json');rows=io.read(OUT/'review.json')['rows']
    requests=[json.loads(x) for x in (OUT/'requests.jsonl').read_text(encoding='utf-8').splitlines()]
    responses=[json.loads(x) for x in (OUT/'responses.jsonl').read_text(encoding='utf-8').splitlines()]
    assert state['status']=='completed' and len(rows)==len(requests)==len(responses)==state['attempts']==144
    assert len(list(OUT.glob('*.raw.txt')))==144 and len(list((OUT/'actual_requests').glob('*.json')))==144
    assert all(r['status']=='readable' for r in rows) and all(x['retry']==0 for x in requests)
    assert all(x['response']['status']=='completed' for x in responses)
    for field in ('input_tokens','output_tokens'):assert sum(x['response']['usage'][field] for x in responses)==state[field]
    costs=collections.defaultdict(lambda:dict(requests=0,input_tokens=0,output_tokens=0))
    for idx,(r,q,a) in enumerate(zip(rows,requests,responses)):
        assert r['slot']==idx+1
        packet=io.read(P/r['context'])
        if r['stage']=='second':
            assert rows[idx-1]['group']==r['group']
            packet=frontend.second_packet(packet,rows[idx-1]['answer'])
        expected=frontend.request(r['stage'],r['method'],packet)
        assert expected==io.read(OUT/'actual_requests'/f"{r['slot']:02d}.json")
        assert q['payload']['instructions']==expected['instructions'] and q['payload']['max_output_tokens']==1536
        visible={s['ref'] for s in packet['public_sources']+packet['own_sources']}
        assert all(e['source'] in visible for e in r['answer']['evidence'])
        assert not r['answer']['annotation_issues']
        c=costs[r['method']];c['requests']+=1
        for field in ('input_tokens','output_tokens'):c[field]+=a['response']['usage'][field]
    audit=dict(status='PASS',requests=144,readable=144,raw_files=144,actual_requests=144,retries=0,annotation_issues=0,
        complete_pairs=36,independent_tasks=6,repeats=2,input_tokens=state['input_tokens'],output_tokens=state['output_tokens'],
        reserved_output=state['reserved_output'],unknown_usage=state['unknown_usage'],costs=dict(costs),
        frozen_hashes='verified',exact_dynamic_request_reconstruction='144/144',evidence_handles='all member-visible',
        transport_status='all completed',limitations='Exact reconstruction proves packet isolation and lack of offline-field injection, not semantic correctness.')
    io.write(OUT/'TECHNICAL_AUDIT.json',audit)
    annotated=[];pairs=[]
    for task,member,repeat,o,q,note in ANNOTATIONS:
        pair=dict(task=f'rule-confirm-{task:02d}',member=member,repeat=repeat,ordinary=o,local_question=q,semantic_review=note)
        final={r['method']:r for r in rows if r['task']==pair['task'] and r['member']==member and r['repeat']==repeat and r['stage']=='second'}
        pair['slots']={m:r['slot'] for m,r in final.items()}
        pair['outcome']='question_only' if q=='E' and o!='E' else 'ordinary_only' if o=='E' and q!='E' else 'tie_on_increment'
        pairs.append(pair)
        for method,category in [('ordinary',o),('local_question',q)]:
            slot=final[method]['slot']
            annotated.append(dict(task=pair['task'],member=member,repeat=repeat,method=method,first_slot=slot-1,final_slot=slot,
                category=category,effective_increment=category=='E',correct_control=task in (9,12),
                first_and_final_review=note,review_coverage='Both complete substantive outputs inspected; raw source provenance checked by packet audit.'))
    assert len(annotated)==72 and len(pairs)==36
    totals={m:sum(x['effective_increment'] for x in annotated if x['method']==m) for m in frontend.METHODS}
    task_counts={f'rule-confirm-{t:02d}':{m:sum(x['effective_increment'] for x in annotated if x['task']==f'rule-confirm-{t:02d}' and x['method']==m) for m in frontend.METHODS} for t in range(7,13)}
    repeats={str(rep):{m:sum(x['effective_increment'] for x in annotated if x['repeat']==rep and x['method']==m) for m in frontend.METHODS} for rep in (1,2)}
    # Boundary cases are identified explicitly rather than hidden in a single binary score.
    boundary_slots=[12,32,34,48,76,78,80,90,92,94,96,108,110,118]
    summary=dict(scope='Same-family new-instance contribution confirmation, not team accuracy',annotation='Same assistant, posthoc nonblind, not independent gold.',
        denominator_per_method=36,wrong_draft_opportunities_per_method=24,correct_control_attempts_per_method=12,
        effective_increment=totals,task_counts=task_counts,repeat_counts=repeats,
        paired_outcomes=dict(collections.Counter(p['outcome'] for p in pairs)),
        category_counts={m:dict(collections.Counter(x['category'] for x in annotated if x['method']==m)) for m in frontend.METHODS},
        correct_control_counts={m:dict(collections.Counter(x['category'] for x in annotated if x['method']==m and x['correct_control'])) for m in frontend.METHODS},
        boundary_slots=boundary_slots,boundary_policy='All flagged delivery scopes and materiality judgments remain auditable; no claimed high-precision effect size or significance.',
        technical=audit,
        decision='Keep candidate: positive aggregate and repeated within-member scheduling signal, mixed cross-task effects. Do not auto-expand; next stage can test team adoption on a small matched-budget design.',
        limitations=['Only six authored tasks, two generations each; neither36 pairs nor72 contributions are independent tasks.',
          'Correct-control confirmation/rechecking are not counted as failed answers. Neither group executed final team revisions.',
          'Some question outputs solve their question in stage1; intervention is the actual prompt policy, not a perfectly enforced pure-question decomposition.',
          'Scoring reflects explicit judgments of whole-delivery scope, not automatic oracle matching. Boundary cases may move counts.',
          'No proof of natural expertise, full CoReTA superiority, benchmark generalization, statistical significance or guaranteed safety.'])
    io.write(OUT/'SEMANTIC_REVIEW.json',dict(categories={'E':'有效局部增补','M':'关键错误或混合交付','C':'合理确认，不是失败','R':'条件性复核/无必要新增纠正，不是失败'},procedure=summary['annotation'],attempts=annotated,pairs=pairs))
    io.write(OUT/'SUMMARY.json',summary)
    table='\n'.join(f"| {t[-2:]} | {v['ordinary']}/6 | {v['local_question']}/6 |" for t,v in task_counts.items())
    report=f'''# 新实例确认结果（2026-10-25）

本批144次全部完成，零不可读、零重试、零注释异常。输入125327 tokens，输出38178 tokens；没有超出144次授权，也没有发送离线评分或历史回放文本。精确实际组包重建144/144通过，冻结文件和源码未变。

## 结果

按冻结的完整交付、局部支持及范围标准，由同一助手事后非盲复核，普通组有效增补{totals['ordinary']}/36，自主提问组{totals['local_question']}/36。不是团队答题正确率；每组含12次正确稿控制，合理确认不应也没有计为错答。两组各24次错误稿上的机会另作分母展示：{totals['ordinary']}/24和{totals['local_question']}/24，不能把这个子集比率混称全部成功率。

| 新实例 | 普通两次评议 | 自主提问后求解 |
|---|---:|---:|
{table}

两遍分布：{json.dumps(repeats,ensure_ascii=False)}。成员配对分布：{json.dumps(summary['paired_outcomes'],ensure_ascii=False)}。这些配对嵌套于6题，不作36独立任务的显著性推断。

## 有推进的地方

- 07/A2第一遍，普通组把原始ticks当作任意合理换算都达标；新组保留换算未决。第二遍普通组也纠正了，因此是一遍独有收益，不夸成两遍稳定优势。
- 11/A1两遍：普通组把并行后续也加成20+25=45；新组都给出20+max(15,10)=35的正确条件结果，区分35并行与45串行。这是重复出现的局部收益，不需要把条件35当整题最终答案45。
- 11/A3第一遍新组正确指出[5,15)停机不延迟20后开始的夹具工作；普通组错误把总active45当无并行限制时的下界。但第二遍新组又无依据假设build也用夹具，得到30/55，不能只挑第一遍。
- 正确稿控制09与12不要求制造修改。两组多数确认或保留独立核验疑问；12/A3第一遍普通组声称不用规则表就排除Blue，新组没有这种错误。没有实际团队最终改判，不能称实际最终答案损害率。

## 反向结果也保留

- 08/A1第二遍，新组虽正确计算单服务空闲阈值36/24，却把不同服务空闲量合成一个I，最终只留A或neither，遗漏仅B合格可能。普通组范围更完整。
- 08/A3第一遍，新组漏读原件已确认其余记录独立，还虚构150至180范围；两组都有处理分钟和完整会话混淆。
- 10库存题增益混合；一部分输出正确使用并集110，一部分把物理150直接当可用，或在缺少可用量前提时给至少5重叠的门槛。不同说法是无条件断言还是明确假设，影响评分，逐项标明。
- 11/A2第二遍普通组在conclusion明确限定build前置；新组未充分表达此前提却推出夹具最早20，属于反向损失。

## 评分边界

主标注不是无争议金标。槽位12/34/48的完整字段条件表达，以及76/78/80/90/92/94/96的物理/可用范围、32的共同I假设、108/110/118的条件前提均保留复核标记。特别是92将150用作无重叠时的物理上界仍能推出不能同时受理；94的至少5只在显式假设150全可用时成立，不能当实际门槛15。原始输出、标注理由及双方配对都保存在SEMANTIC_REVIEW.json，不能隐藏这些边界后把差值包装为精确能力增长。

数值比较仅是此批局部交付计数；新任务在旧结果之后构造，非独立官方留出集。提示机制没有额外组件，但有些自主问题首轮已解题，不能归因于严格先问后解。每组实际成本见TECHNICAL_AUDIT.json。

## 去留

保留候选，有理由进入下一阶段设计，而非因为剩余失败就继续添组件。聚合为正，且排程同一成员两遍出现明确收益；同时跨题有反向损失，尚不声称稳定总体优势。

下一阶段应检验更好的局部贡献是否被团队采用、是否改变最终解答，以同预算普通协作为基线；先设计小范围闭环，不立刻搭庞大架构。本批不自动追加付费请求。
'''
    (OUT/'RESULTS.md').write_text(report,encoding='utf-8')
    io.write(P/'EXECUTION_STATUS.json',dict(status='COMPLETED_REVIEWED',live_model_requests=144,automatic_expansion=False,run=str(OUT.relative_to(ROOT))))
    print(json.dumps(dict(technical='PASS',effective_increment=totals,tasks=task_counts,repeats=repeats,paired=summary['paired_outcomes'],costs=dict(costs)),ensure_ascii=False))

if __name__=='__main__':main()
