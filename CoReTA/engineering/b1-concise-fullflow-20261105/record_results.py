"""Summarize completed bounded diagnostics and append project history."""
import hashlib,json,tarfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=ROOT/'runs/b1-sampling-check-20261105-v2';V=ROOT/'runs/b1-concise-V8-20261105-v1';T=ROOT/'runs/b1-concise-tech6-20261105-v1'
s=load(S/'RESULTS.json');v=load(V/'RESULTS.json')
assert (T/'RESULTS.json').exists(),'Team phase is still running or has not launched; do not mark stage complete'
t=load(T/'RESULTS.json');vs=load(V/'scores.json');ts=load(T/'scores.json')
rows=[json.loads(line) for line in (T/'responses.jsonl').read_text().splitlines()]
vcounts={a:dict(n=sum(r['actor']==a for r in vs['records']),correct=sum(r['actor']==a and bool(r['metrics']) and r['metrics']['em']==1 for r in vs['records'])) for a in ('M1','M2')}
last=rows[-1] if rows else None
maxwords={stage:max((len(r['raw_output'].split()) for r in rows if r['stage']==stage),default=0) for stage in ('initial','work','final')}
stagepass=t['verdict']=='PASS_TECHNICAL_ONLY'
if stagepass:
    assert len(rows)==312 and ts['n_complete']==6 and all(r['status']=='OK' and r['usage']['finish_reason']=='EOS' for r in rows)
assert not ts['primary_enabled'] and all(not r['primary_enabled'] for r in ts['reports'])
frozen=load(T/'FREEZE.json');old=ROOT/'runs/b1-dev32-final-20261104-v2/scores.json'
assert sha(old)==frozen['files'][str(old)] and load(old)['n_complete']==28
summary=dict(date='2026-11-05',reviewer='assistant',independence='none/provisional',sampling=s,V_migration=v,V_counts=vcounts,team=t,team_status_counts={status:sum(r['status']==status for r in rows) for status in {r['status'] for r in rows}},team_max_word_counts=maxwords,last_request=dict(request_id=last['request_id'],actor=last['actor'],stage=last['stage'],arm=last['arm'],status=last['status'],usage=last['usage']) if last else None,original32_still_complete28=True,overall_stage='PASS_TECHNICAL_ONLY' if stagepass else 'REVISE_FULLFLOW',new_generations=s['n_generated']+v['n_generated']+t['n_generated'])
(HERE/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
details='六题全部完整、312/312自然结束且格式通过。' if stagepass else f'完整流程尚未通过；末条请求{summary["last_request"]}。已按冻结规则停止，未自动换提示/补跑。'
report=f'''# T2/T3 实际执行结果

2026-11-05，助手自审none/provisional。已按NEXT_TASKS顺序执行采样核验、V独答迁移、历史失败完整团队技术验证。

| 批次 | 实际/计划请求 | 正常响应 | 耗时（含加载） | 判定 |
|---|---:|---:|---:|---|
| T2随机后端 | {s['n_generated']}/24 | {s['n_ok']} | {s['elapsed_seconds']:.2f}s | {s['verdict']} |
| T3 V前8题双路 | {v['n_generated']}/16 | {v['n_ok']} | {v['elapsed_seconds']:.2f}s | {v['verdict']} |
| T3六题完整四组 | {t['n_generated']}/312 | {t['n_ok']} | {t['elapsed_seconds']:.2f}s | {t['verdict']} |

T2：真实multinomial与生成token逐项一致，252个LoRA层开关正确；不同seed随机状态不同，12对原样重复逐token相同。两题底座跨seed仍同答，专家一题有措辞变体，不能将同答判为实现故障。旧28题普通三人对错向量相同（3对25错，phi=1），是高度相关的同底座弱成员，不是独立证据，也不能外推一般异构团队。

新合同：所有成员/四臂，初/终答单行≤12词cap128，工作≤120词cap768，两轮不变；EOS和格式分开，超限保留全文并失败，不截取答案。Unknown合法但按未答对报告。V16中Unknown {v['unknown_outputs']}份；M1答对{vcounts['M1']['correct']}/{vcounts['M1']['n']}，M2答对{vcounts['M2']['correct']}/{vcounts['M2']['n']}，只是同合同下8题开发观察，不是新独立资格或与旧V20的配对效果。未以分数选提示。

32项B1回归通过，原32真实轨迹重放和评分复算完全一致。旧源码与已完成T2的冻结源码在更新前存档（T2/SOURCE_ARCHIVE.json），旧准备失败v1保留REJECTED（0生成）。

六题固定原索引9/13/16/22四个历史失败+0/1正常对照，按该顺序，原题/seed/说话顺序保留。{details}已完整{ts['n_complete']}/6题；本批Unknown {t['unknown_outputs']}份；实际最大词数{maxwords}。这是历史失败选择的技术样本，不能用于估计总体准确率或证明新提示更优；自动评分primary_enabled=false，所有单题报告也false。

原32仍28完整，旧分数SHA256未变；没有将新6题拼回旧28，也没有重跑/读取新C-H或训练、付费API。新生成总计{summary['new_generations']}。新合同提示与cap同时变化，耗时变化不能叫引擎加速或科学条件严格等价。

阶段判定：{summary['overall_stage']}。本轮意义是消除采样失效疑点并检验完整合同，不是机制确认。下一动作：{'在保持本合同/精度/轮次的条件下，准备一项有限单因素加速比较；另决定是否需要完整同合同开发批次，不自动扩跑旧32。终答稳定性机制仍需同时包含有效纠错对照。' if stagepass else '先分析具体失败约束，不直接扩大样本或把部分成功记作修复完成；任何修改另存版本、重新审核，不自动搜索提示。'}
'''
(HERE/'RESULTS.md').write_text(report)
entry=f'''## 2026-11-05 T2采样核验/T3完整合同验证实际执行

见engineering/b1-sampling-check-20261105/RESULTS.md与engineering/b1-concise-fullflow-20261105/RESULTS.md、SUMMARY.json。T2 24/24成功，实际采样/seed/252层adapter开关通过，12对重复逐token一致；旧普通三人对错向量完全相同，不能当独立三证据。32回归与旧32轨迹/评分完全一致；T3 V16 {v['n_ok']}/{v['n_generated']}正常（Unknown {v['unknown_outputs']}）；六题技术批{t['n_ok']}/{t['n_generated']}正常、{ts['n_complete']}/6完整，{t['verdict']}，限技术历史失败样本且primary=false。{details}原32仍28完整，旧分数不改，新生成{summary['new_generations']}，无训练/新C-H/付费API；新提示与cap改变不冒充引擎提速。助手自审none/provisional。阶段{summary['overall_stage']}，不自动扩样/补旧结果；下一动作见报告。

'''
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    p=ROOT/name;prior=p.read_text()
    if entry.splitlines()[0] not in prior:p.write_text(entry+prior)
(HERE/'STAGE_ENTRY.md').write_text(entry)
archive=ROOT/'runs/b1-diagnostics-20261105-evidence.tar.gz'
assert not archive.exists()
with tarfile.open(archive,'w:gz') as tar:
    for run in (S,V,T):tar.add(run,arcname=run.name)
print(json.dumps(summary,ensure_ascii=False))
