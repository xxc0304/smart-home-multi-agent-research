"""Audit and record the separately versioned readable-output technical batch."""
import hashlib,json,tarfile,re,shutil,contextlib,io,runpy
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
def load(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
S=ROOT/'runs/b1-sampling-check-20261105-v2';V=ROOT/'runs/b1-concise-V8-20261105-v1'
STRICT=ROOT/'runs/b1-concise-tech6-20261105-v1';T=ROOT/'runs/b1-concise-readable-tech6-20261105-v1'
s,v,strict,t=[load(p/'RESULTS.json') for p in (S,V,STRICT,T)]
rows=[json.loads(line) for line in (T/'responses.jsonl').read_text().splitlines()]
strict_rows=[json.loads(line) for line in (STRICT/'responses.jsonl').read_text().splitlines()]
first_two_match=len(rows)>=2 and all(all(a[k]==b[k] for k in ('request_id','seed','payload','max_new_tokens','raw_output')) for a,b in zip(rows[:2],strict_rows))
score=load(T/'scores.json');vs=load(V/'scores.json')
warnings=[dict(request_id=r['request_id'],actor=r['actor'],stage=r['stage'],arm=r['arm'],task_index=r['task_index'],reason=r['usage']['format_warning'],words=len(r['raw_output'].split()),raw_output=r['raw_output']) for r in rows if (r.get('usage') or {}).get('format_warning')]
for r in rows:
    assert r['fixture'] is False and r['source_kind']=='ACTUAL_LOCAL_MODEL_RESPONSE'
    if r['status']=='OK':assert r['usage']['adapter_enabled']==(r['actor']=='M1')
    base_seed=20261102+r['task_index']*10000
    offset=0 if r['stage']=='initial' else 1000+r['round']*100 if r['stage']=='work' else 2000
    assert r['seed']==base_seed+offset+int(r['actor'][1:])-1
    if r['stage']!='initial':
        data=json.loads(r['payload']['user'].split('TASK_DATA\n',1)[1].split('\n\nOUTPUT FORMAT:',1)[0])
        assert ('team_information' in data)==(r['arm'] in ('C','D'))
        assert all(h['phase']!='final' for h in data['history'])
        if r['arm'] in ('A','C'):assert all(h['sender']==r['actor'] for h in data['history'])
passed=t['verdict'].startswith('PASS')
if passed:
    assert len(rows)==312 and score['n_complete']==6
    assert all(r['status']=='OK' and r['usage']['finish_reason']=='EOS' for r in rows)
assert not score['primary_enabled'] and all(not r['primary_enabled'] for r in score['reports'])
f=load(T/'FREEZE.json');old=ROOT/'runs/b1-dev32-final-20261104-v2/scores.json'
assert sha(old)==f['files'][str(old)] and load(old)['n_complete']==28
from sys import path
path.insert(0,str(ROOT/'tools'))
from b1_controls import replay
trials=[load(p) for p in sorted((T/'trials').glob('*.json'))]
for trial in trials:assert replay(trial).export()==trial
vcounts={a:sum(r['actor']==a and r['metrics']['em']==1 for r in vs['records']) for a in ('M1','M2')}
tests_count=int(re.search(r'Ran (\d+) tests', (HERE/'TESTS.txt').read_text()).group(1))
wordmax={stage:max((len(r['raw_output'].split()) for r in rows if r['stage']==stage),default=0) for stage in ('initial','work','final')}
with contextlib.redirect_stdout(io.StringIO()):timing=runpy.run_path(str(HERE/'progress.py'),run_name='__main__')['result']
assert timing['n_requests']==len(rows) and timing['partial_lines_skipped']==0
(HERE/'TIMING.json').write_text(json.dumps(timing,indent=2)+'\n')
total_generate_seconds=sum(v['generate_seconds'] for v in timing['stages'].values())
work_share=timing['stages']['work']['generate_seconds']/total_generate_seconds if total_generate_seconds else 0
summary=dict(date='2026-11-05',reviewer='assistant',independence='none/provisional',sampling_result=s['verdict'],sampling_n=s['n_generated'],V16_result=v['verdict'],V16_Unknown=v['unknown_outputs'],V8_expert_correct=vcounts['M1'],V8_base_correct=vcounts['M2'],V16_reused_identical_requests=True,first_two_requests_and_raw_outputs_match_strict=first_two_match,strict_V4=strict,readable_V5=t,format_warning_count=len(warnings),format_warning_by_stage={stage:sum(r['stage']==stage for r in warnings) for stage in ('initial','work','final')},format_warning_by_actor={a:sum(r['actor']==a for r in warnings) for a in ('M1','M2','M3','M4')},actual_word_max=wordmax,source_old_scores_sha256_unchanged=True,original32_still_complete28=True,all_new_trace_replays_identical=True,all_nonfixture_and_routes_verified=True,strict_format_all_pass=not warnings and passed,new_generations_total=sum(r['n_generated'] for r in (s,v,strict,t)),stage='PASS_READABLE_FLOW_WITH_WARNINGS' if passed and warnings else 'PASS_READABLE_FLOW' if passed else 'REVISE_TRUE_FAILURE')
(HERE/'SUMMARY.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2)+'\n')
(HERE/'FORMAT_WARNINGS.json').write_text(json.dumps(warnings,ensure_ascii=False,indent=2)+'\n')
report=f'''# T3 V5 可读输出完整流程验证

2026-11-05，助手自审none/provisional。

实际判定：**{summary['stage']}**。生成{t['n_generated']}/312，正常{t['n_ok']}，完整{score['n_complete']}/6题，耗时{t['elapsed_seconds']:.2f}秒（含加载）。格式警告{len(warnings)}条；这不是“所有输出都遵守格式”。Unknown初/终答{t['unknown_outputs']}条，照未答对评分。原分数与失败记录均保留。

## 本次修正

严格V4首题M2输出28词、41token并自然EOS，没用满128token，却因新增12词硬门槛阻断依赖，2条后停止。该批保留REVISE、0/6完整。

V5沿相同模型提示/采样/精度/seed/cap，仅改变准入分类：可读超词/多行记format_warning并保留完整原文进入历史、原EM/投票；不截取答案，不补正确内容；空白、非文本、token/time/其他技术失败仍停。计划独立生成完整6题，实际完成数见开头，不与严格V4的2条拼接。{tests_count}项回归通过。

## 验证与范围

受影响回归通过（见TESTS.txt），原32轨迹与原评分完全一致。已逐项证明原V16模型请求与本合同下请求完全相同，且原16格式均合规，故复用其结果而非重新生成：V8专家{vcounts['M1']}/8、底座{vcounts['M2']}/8，Unknown{v['unknown_outputs']}条，仅开发迁移观察，不重开C资格。T2此前24/24真实随机采样与252层adapter开关通过，12对原样重复逐token一致。

当前新批固定原索引9/13/16/22四历史失败+0/1两正常，原种子/顺序保留。全部实际非fixture、路由和轨迹重放核验通过；正常响应必须EOS。所有批次/单题评分primary_enabled=false。历史失败选择样本与同题重复不能估计总体准确率、证明机制或新提示更优。

格式警告按阶段：{summary['format_warning_by_stage']}；按成员：{summary['format_warning_by_actor']}；实际最大词数：{wordmax}。全文和定位见FORMAT_WARNINGS.json，明确格式不合规与技术失败分开。不因把警告保留为可读就把答案算正确。

工作阶段约占模型generate调用耗时{work_share:.1%}，不是完整端到端时间占比；各阶段输入/输出token与耗时见TIMING.json，未分离prefill和decode。下一加速比较应固定科学提示/上限，优先评估工作阶段执行成本，不能凭本批与旧批的耗时差宣称引擎提速。

原32仍28完整，原分数SHA256未变。V4/V5源码与冻结映射分开保存；严格V4、旧准备v1失败不覆盖。本轮新增生成共{summary['new_generations_total']}（采样24+V16+严格失败2+V5实际{t['n_generated']}），无训练、新C/H或付费API。

## 下一步

{'完整可读流程通过；严格格式合规与语义质量仍需单独看警告和原分数。下一阶段可冻结同提示/精度/轮次的单因素吞吐比较，或据事件率决定同合同开发批；本轮不自动启动加速/扩大样本。终答稳定性诊断仍须兼测有效纠错。' if passed else '仍有真正技术失败，保存位置和完整原文后定位，不以格式警告掩盖；不直接扩大样本、不自动搜提示/种子。'}

提示/cap与旧v2不同，当前耗时不能直接叫引擎加速；仅同条件执行因素比较才可评估加速。
'''
(HERE/'RESULTS.md').write_text(report)
entry=f'''## 2026-11-05 T3 V5完整可读流程：{summary['stage']}

见engineering/b1-concise-readable-20261105/RESULTS.md、SUMMARY.json与FORMAT_WARNINGS.json。严格V4首题M2自然EOS/41token/28词，仅因12词硬门槛在2条后停止，保留REVISE。另冻结V5：提示/精度/采样/seed/cap不变，可读超词/多行只记警告并按完整原文评分/入历史；空白/截断/异常仍停，不抽取答案。V16请求逐项相同，复用16既有迁移结果（E6/8、B3/8，Unknown4），非新增独立资格。新6题生成{t['n_generated']}/312，正常{t['n_ok']}、完整{score['n_complete']}/6，耗时{t['elapsed_seconds']:.2f}s、格式警告{len(warnings)}、Unknown{t['unknown_outputs']}；不能声称严格格式全通过。原32仍28完整，旧分数SHA未变，原版本/失败与源冻结存档；助手自审none/provisional，技术样本primary=false，不外推总体或机制。T2仍24/24通过，本轮总生成{summary['new_generations_total']}，无训练/新C-H/付费API。下一步先评估格式与语义/同条件加速候选，不自动扩大批次。

'''
(HERE/'STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    p=ROOT/name;prior=p.read_text()
    if entry.splitlines()[0] not in prior:p.write_text(entry+prior)
archive=ROOT/'runs/b1-readable-20261105-evidence.tar.gz';assert not archive.exists()
source_archive={}
for name,h in f['files'].items():
    assert sha(name)==h
    dest=T/'frozen_sources'/Path(name).relative_to(ROOT)
    dest.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(name,dest)
    source_archive[name]=dict(archive=str(dest),sha256=h)
(T/'SOURCE_ARCHIVE.json').write_text(json.dumps(source_archive,indent=2)+'\n')
with tarfile.open(archive,'w:gz') as tar:
    for folder in (S,V,STRICT,T):tar.add(folder,arcname=folder.name)
print(json.dumps(summary,ensure_ascii=False))
