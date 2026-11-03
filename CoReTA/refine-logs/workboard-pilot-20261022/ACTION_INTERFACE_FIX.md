# 动作接口修复与离线验收

日期：2026-10-22。基准提交：00338a49953246eaeff582e1a16f4c2959b77374；工作区已有未提交研究文件，本次为局部增量。决策先记入实现账本A34/A35，再改代码。

## 修复内容

旧自然试跑最后返回reuse W26、work=null和实际use_record，同时给reason一段解释。JSON/schema合法，额外动作校验因reason非null而拒绝。这次修复允许TRY/FINALIZE的reuse/new带可选理由（null或非空字符串），两种方法共用契约与明确的动作提示。

理由仅是响应中的说明，不改变候选选择、检查者分配、候选原文、实际使用记录或来源声明。reuse仍必须给可见合法候选且不能携带新work；new必须给work且不能同时指定另一候选；use_record仍必需。unable仅TRY允许，必须说明原因且不能伪造应用记录、产物或应用来源。OBSERVE的pass/offer互斥保留。没有放宽候选/来源枚举或交付物形状要求。

## 已完成的验证

1. **原始响应离线回放**：tools/replay_workboard_action.py读取旧失败的原始FINALIZE输出，不删reason、不改候选；按当前schema及动作校验通过，仍为W26。三个历史输入文件哈希前后一致，旧result仍为interrupted。该回放不重新执行模型、不完成旧批次。
2. **200项离线回归通过**：0失败、0错误、0跳过，真实HTTP为0。新增成功/拒绝案例覆盖可选解释、空/非字符串reason、缺使用记录、无效候选/来源、互斥冲突及unable限制。
3. **完整运行器脚本路径**：普通讨论FINALIZE reuse/new两组合；CoReTA TRY reuse/new × FINALIZE reuse/new四组合。六组合均带非空reason，独立临时目录，分别完成25次脚本调用，实际产物未被解释字段改写。它们是脚本工程检查，不是六次模型实验。
4. **服务复制检查准备**：新增4项带理由动作案例，共16项本地schema/动作校验通过；本轮未向服务发送复制请求。固定复制也不能证明自然解题稳定性。
5. **独立代码复核**：同家族provisional审查无阻断项；初轮指出FINALIZE.new完整路径覆盖不足，已补齐，增量复核未发现新增问题。不能据此作整体正确性保证。

日志：runs/workboard-action-fix-20261022-r1/下的summary.json、unittest.log、historical_replay.json、schema-prepared/compatibility.json及review.json。

可复现命令（CoReTA目录，PYTHONPATH=src;tests）：

```powershell
./.venv/Scripts/python.exe -m unittest test_workboard test_workboard_pilot test_handoff test_application_ranking test_application_v2
```

## 当前状态与下一步

新准备包runs/workboard-pilot-prepared-20261022-r2/已冻结当前源码、输入、共同初稿生成请求与预算；尚未运行。研究主线、集中/分散条件、四成员同模型不同资料、两法共享实际初稿、每法25后续调用/61440输出上限及首技术异常停批规则均未变。

旧live-r1保持停止，不能把本次离线通过改记为旧实验完成。本轮新增解题模型调用0，新增能力对比结果0。下一步可按新快照单独启动有界配对试跑，先观察真实交接是否正常完成，再讨论协作效果；自然端到端稳健性仍须由该运行检验。HiddenBench/Schedule正式评价不在这次修复验收范围。
