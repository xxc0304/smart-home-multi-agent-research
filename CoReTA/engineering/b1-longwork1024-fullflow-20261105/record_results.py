"""Record the verified stage; never rewrite original run artifacts."""
import json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-longwork1024-fullflow-20261105-v1'
load=lambda p:json.loads(p.read_text())
a=load(HERE/'POST_RUN_AUDIT.json');r=load(OUT/'RESULTS.json')
assert a['verdict']=='PASS_RECORDS_AND_D8_COMPLETENESS'
fmt=lambda s:f'{int(s//60)}分{int(round(s%60)):02d}秒'
serial,batch=(r['seconds'][e] for e in ('serial','batch2'))
text=f'''# V6统一1024工作上限：完整D8对照结果

研究意义PASS、执行记录与D8完整性PASS；助手自审none/provisional。结论限已反复使用的开发前8题、固定单种子与当前3090/NF4设置，不构成质量等价、稳定优越性或独立确认。

总耗时{fmt(r['elapsed_seconds'])}，832尝试=832返回，serial与batch2各8/8题、416/416 EOS；0截断、0Unknown、无异常/预算停止。所有四cell审核PASS。新合同V6保留旧v2长提示和256初/终答，四组、所有成员工作上限统一1024，无新短化/Unknown指导；完整新工作进入各自后续历史，没有拼接旧结果。

## 完整同8题成本

serial {fmt(serial)}，batch2 {fmt(batch)}，省{fmt(serial-batch)}，时间减少{100*r['time_saved_fraction']:.2f}%（吞吐提升{100*(serial/batch-1):.2f}%）。两者均416调用，因此本次可直接比较整批耗时；仍是单次当前负载测量，不是所有未来规模的保证。两组四题顺序交替，batch2仅352/416条响应实际双条合批，其余64单条；保持题内依赖、即时广播及adapter路由。

| 成本 | serial | batch2 |
|---|---:|---:|
| 输入token | {r['counts']['serial']['input_tokens']} | {r['counts']['batch2']['input_tokens']} |
| 输出token | {r['counts']['serial']['output_tokens']} | {r['counts']['batch2']['output_tokens']} |
| 最大峰值allocated显存GiB | {max(t['peak_allocated_bytes'] for t in r['timings'] if t['engine']=='serial')/2**30:.2f} | {max(t['peak_allocated_bytes'] for t in r['timings'] if t['engine']=='batch2')/2**30:.2f} |

batch2的实际文本/输出长度不同；时间差是完整实际执行器的观测，不是严格同token或所有中间文本相同的内核速度实验。reserved是共享加载对象的缓存高水位，不能直接当两模式独立显存需求。

## 正确率与研究边界

预注册团队读出使用最高票答案类平局均匀随机，期望EM优先，固定种子实际EM另列；本批primary_enabled=false。

| 条件 | serial期望EM | batch2期望EM | serial实际答对 | batch2实际答对 |
|---|---:|---:|---:|---:|
'''
names={'A':'私人/隐藏专家','B':'讨论/隐藏专家','C':'私人/公开专家','D':'讨论/公开专家'}
for arm in 'ABCD':
    s,b=(r['scores'][e]['arms'][arm] for e in ('serial','batch2'))
    text+=f"| {arm} {names[arm]} | {s['expected_em']*100:.3f}% | {b['expected_em']*100:.3f}% | {round(s['actual_em']*8)}/8 | {round(b['actual_em']*8)}/8 |\n"
text+='''
A改善、B/D不变、C下降，不能把加速表述为所有条件质量不降。C串行期望78.125%与实际7/8的区别来自平局，不是7道完整或评分出错；四组共享题目，不是32个独立样本。不能从8题断言batch2普遍更差或等价。批量形状改变可影响采样输出，固定seed并不保证原文相同。

两方式专家独立初答均6/8正确；四组均有1次专家EM从对变错（分母6个初答正确），这不是4个独立受害题，更不能把私人组的变化都归因于他人说服。隐藏讨论B专家另有1次错→对，两方式均最终6/8；其余条件与成员完整转移见各自scores.json。正确答案也不自动证明中间论据和使用机制正确。

## 旧截断与核验

'''
for q in a['rescued_requests']:
    text+=f"- 原{q['request_id']}（{q['arm']}/{q['actor']}）512截断，本次同payload/seed在{q['new_tokens']} token自然EOS。\n"
text+='\n与旧512串行/批量2的可比请求逐项比对：\n\n```json\n'+json.dumps(a['comparison_with_previous_512_run'],ensure_ascii=False,indent=2)+'\n```\n'
text+='''
冻结与审批绑定、16完整轨迹重放、journal/attempt一一对应、832条EOS/输出上限/252层LoRA实际开关、官方评分精确复算和4cell审核均通过；原run文件hash前后不变。详细POST_RUN_AUDIT.json。EOS和0Unknown只说明本轮技术完成，不证明事实正确，0Unknown仅指逐字Unknown，不排除其他不确定表述。

下一步建议：结束这轮工程筛选，保留batch2+统一1024作为后续开发候选，明确约一成提速与形状敏感性；优先分析现有对/错变化及中间讨论，选择下一轮有明确研究问题和有限预算的开发比较。暂不自动扩32、搜索cap/种子、训练、新C/H或付费API。是否继续更大完整实验需另冻结审核，不能把本批当独立验证。
'''
(HERE/'RESULTS.md').write_text(text)
entry=f'''## 2026-11-05 V6统一1024完整D8完成：双方8/8，省时10.70%

见engineering/b1-longwork1024-fullflow-20261105/RESULTS.md、POST_RUN_AUDIT.json及runs/b1-longwork1024-fullflow-20261105-v1。总{fmt(r['elapsed_seconds'])}，832尝试=832 EOS，串行/批量2各8/8，0截断/Unknown/异常，四cell PASS。串行{fmt(serial)}、batch2 {fmt(batch)}，省{fmt(serial-batch)}（10.70%），同完整416调用可比；旧两失败同输入/seed现528/586 EOS。团队期望EM A62.5→75、B75→75、C78.125→62.5、D62.5→62.5；实际答对A5→6、B6→6、C7→5、D5→5，不能称质量不降或等价。专家初答均6/8、各臂1次EM对→错，私人组变化不等于他人诱导。16轨迹/原文/attempt、官方评分复算、冻结审批/252层实际路由和EOS通过，旧原件不改。助手自审none/provisional，PASS限技术完整性/记录；重复开发8题、单种子。工程筛选结束，可保留batch2+1024为候选，下一优先既有过程/质量差异分析；未自动扩32/训练/新C-H。

'''
(HERE/'RESULT_STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    p=ROOT/name;old=p.read_text()
    if entry.splitlines()[0] not in old:p.write_text(entry+old)
print('Verified result report and stage records saved; no new generations.')
