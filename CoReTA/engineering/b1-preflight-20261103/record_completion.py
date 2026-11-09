"""Append actual B1 finite-stage completion, preserving all prior history."""
from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/'runs/b1-timing2-20261103-v2'
audit=json.loads((OUT/'POST_RUN_AUDIT.json').read_text())
assert audit['complete_items']==2 and audit['recorded_generations']==104
assert audit['statuses']=={'OK':104} and audit['adapter_routes_match']
entry='''## 2026-11-04 B1提示迁移及前两题计时完成

见[结果与阶段审核](engineering/b1-preflight-20261103/RESULTS.md)。旧64token预检首条OUTPUT_LIMIT即停，原件/旧代码保留；新v2统一短答suffix+256初终答（工作512、两轮与采样不变），V20 B3/20、E11/20，40/40完整，真实adapter路由/恢复通过。23受影响检查通过。D前2题104/104完整，用时598.38秒，输入346423/输出11770token，最长输入4947、工作输出482/512；峰值分配3.93GiB，GPU已空闲。A/B/C/D团队分别0/1/1/0题正确；两题初答专家均错，正确保留/有害改变分母0，不能称零损害或身份/交流因果。助手阶段自审PASS限技术与开发描述；未训练/重跑C/读H/扩8或32。下一步可在相同v2配置下原样继承两题接续前8，先按约5分钟/题实测成本冻结余6题有限预算并审查，不重跑或按正确筛题。原C资格与边界保留。

'''
for name in ('handoff.md','CURRENT_STATE.md'):
    path=ROOT/name;old=path.read_text(encoding='utf-8')
    if '## 2026-11-04 B1提示迁移及前两题计时完成' not in old:
        path.write_text(entry+old,encoding='utf-8')
stage='''## 2026-11-04 B1 prompt transfer / D2 timing stage review

Goal: confirm usable matched answer contract and actual C-bound adapter, then first2 fixedD four-arm timing. v1 stopped1 OUTPUT_LIMIT64; v2 joint suffix+256 revision retained historical evidence. NewV20 B15%/E55%,40/40;23 regressions. ActualD2 104/104 OK/2paired,598.38s,maxinput4947,peakallocated3.93GiB. Route flags and trace replay/scoring verified; all initial expert answers wrong, retention/harm denominator0/null. Scores A0/2 B1/2 C1/2 D0/2 are descriptive only, not method/identity effect. PASS for bounded engineering/cost and development scope; reviewer=assistant self-review, independence=none/provisional. Allowed next: reviewed finite6-new-item continuation to8 with identicalv2 config/old traces; no rerunning2 or choosing by outcome, no automatic32. No newtraining/C/H/API. See engineering/b1-preflight-20261103/RESULTS.md and runs/b1-timing2-20261103-v2/POST_RUN_AUDIT.json.

'''
plan=ROOT/'refine-logs/expert-mechanism-pilot-20261030'
for name in ('STAGE_REVIEWS.md','WORK_TRACKER.md'):
    path=plan/name;old=path.read_text(encoding='utf-8') if path.exists() else ''
    if '## 2026-11-04 B1 prompt transfer / D2 timing stage review' not in old:
        path.write_text(stage+old,encoding='utf-8')
index=ROOT/'experiment/results.md';old=index.read_text(encoding='utf-8')
tag='## 2026-11-04 B1首两题开发记录'
if tag not in old:
    index.write_text(tag+'\n\n[完整结果及范围](../engineering/b1-preflight-20261103/RESULTS.md)：V20匹配独答40/40；D2四组104/104完整，A/B/C/D正确0/1/1/0。仅技术/成本和小样本描述，初答专家均错，不能推断有害改变或团队增益。旧64token失败保留；未扩8/32。\n\n'+old,encoding='utf-8')
print('B1_STAGE_COMPLETION_RECORDED')
