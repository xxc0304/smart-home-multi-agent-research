"""Record the one-shot speed comparison; no new generations."""
import hashlib,json,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];HERE=Path(__file__).resolve().parent
OUT=ROOT/'runs/b1-batch-speed-20261105-v1'
load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
r=load(OUT/'RESULTS.json');assert r['n_generated']==16 and r['fatal'] is None
rows=[json.loads(line) for line in (OUT/'responses.jsonl').read_text().splitlines()]
assert all(x['status']=='OK' for x in rows)
serial=sum(t['seconds'] for t in r['timings'] if t['engine']=='serial');batch=sum(t['seconds'] for t in r['timings'] if t['engine']=='batch2')
st=sum(t['output_tokens'] for t in r['timings'] if t['engine']=='serial');bt=sum(t['output_tokens'] for t in r['timings'] if t['engine']=='batch2')
changed=sorted({c['request_id'] for c in r['cross'] if not c['same_output_ids']})
report=f'''# T4 一次批处理加速对照结果

2026-11-05，助手自审none/provisional。16/16真实生成自然EOS；4固定完整工作载荷×串行/batch2×2次，交错顺序，不添加warmup生成，不改提示/模型/精度/seed/上限。

| 执行 | 8份生成总时间（不含加载） | 总输出token | token/s |
|---|---:|---:|---:|
| 原串行 |{serial:.2f}s|{st}|{st/serial:.2f}|
| batch2 |{batch:.2f}s|{bt}|{bt/batch:.2f}|

时间比{r['speedup']:.3f}，小样本时间减少{1-batch/serial:.1%}，总输出token略不同，不能当严格相同工作量或整团队提速。两引擎各自原样重复均逐token一致，实际LoRA开关/采样对应检查通过，batch每行独立Generator。峰值分配显存约串行3.69GB、batch4.65GB（字节数量级，详见TIMINGS）。

跨引擎有{len(changed)}/4载荷改变（每次重复均出现），请求{changed}。具体M2私人第一轮从“Yale Law School ...1810”变为“Yale University ...1881”，不只是标点；材料对应法学院1843，这里两段均未正确绑定关系。其余3载荷逐token相同。batch/padding/内核数值路径可能相关，本次未单独识别原因，不断言是哪一个因素。

按预先冻结门槛，测量完成PASS、作为本轮替换执行器REVISE。选择{r['selected_for_D32']}。结束本轮加速探索，不搜索新框架/参数/seed；完整32题使用已验证串行V5。这个结论不表示批处理永远不可用；后续要做均衡各臂的执行器验证与数值/分布比较。本次不是新准确率/机制实验。

所有16原文、输出token、RNG与路由、时间/显存记录保留。新生成16，无训练/新C-H/付费API，旧分数SHA不变；冻结源码已存档。
'''
(HERE/'RESULTS.md').write_text(report)
entry=f'''## 2026-11-05 T4一次加速对照结束，D32选择串行V5

见engineering/b1-batch-speed-20261105/RESULTS.md。16/16正常；串行8份{serial:.2f}s/{st}token，batch2八份{batch:.2f}s/{bt}token，小样本时间比{r['speedup']:.3f}。各自重复稳定，但1/4载荷跨执行文本/token改变（M2私人：LawSchool/1810→University/1881），不满足冻结采用门槛；测量PASS/替换REVISE，结束加速探索，按用户授权进入原串行V5完整D32分阶段批。新16生成、无训练/新C-H/付费API，非质量提升证据。助手自审none/provisional。

'''
(HERE/'STAGE_ENTRY.md').write_text(entry)
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
    p=ROOT/name;old=p.read_text()
    if entry.splitlines()[0] not in old:p.write_text(entry+old)
archive={}
for name,h in load(OUT/'FREEZE.json')['files'].items():
    assert sha(name)==h
    target=OUT/'frozen_sources'/Path(name).relative_to(ROOT)
    target.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(name,target)
    archive[name]=dict(archive=str(target),sha256=h)
(OUT/'SOURCE_ARCHIVE.json').write_text(json.dumps(archive,indent=2)+'\n')
print(json.dumps(dict(status='MEASUREMENT_COMPLETE',selected=r['selected_for_D32'],speedup=r['speedup'],changed_requests=changed)))
