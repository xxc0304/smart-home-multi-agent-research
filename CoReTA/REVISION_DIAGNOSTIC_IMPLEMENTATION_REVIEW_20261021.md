# 修订判断隔离工具代码审核

> 后续落实：本页两项记录问题已修复，新增评分及中断回归后25项离线检查通过，无真实API。见`design/expertise-handoff/revision-decision-v1/IMPLEMENTATION.md`的最新更新及`runs/revision-decision-offline-fixes-20261021/`。本页保留原审核发现。

日期：2026-10-21。本地研究与代码审核，无外部审稿者。`review_independence: same-family`，`acceptance_status: provisional`。本轮未修改工具、生产运行器或准备包，零真实API请求。

## 结论

主体实现符合“同一历史检查点、只改变APPLY提示”的局部诊断目标。未发现未来答案泄漏、资料越权、两臂不对称的额外求助或调用上限失效。可以保留实现，不需要重新设计。

发现两处可复现的记录缺口，建议在真实对照前小幅补齐。它们不改变模型输入和比较逻辑，也不意味着现有22项验证无效；现有测试没有覆盖到这两条输出路径。

## 已核对的正确部分

- 最终准备包的源码、成员packet和生成文件哈希均一致；四个历史检查点均有完整提示/schema吻合核对。
- 22项离线检查再次全部通过，使用脚本传输，不是模型效果实验。
- prefix重建在指定核查后停止，V1无V2/W2，检查点无W3；执行只加载driver私有正文和已公开内容。
- 两臂同packet、同schema、同模型、同上限，只在comparison臂追加固定指导；输入估计6911—8201，低于32768。
- 两臂共同禁止请求是为了隔离单次修订，不是取消完整架构的按需求助。它因此只能检验新提示下的采纳判断，不能检验求助收益。
- 复用生产Runner.apply，核查引用必须被应用或明确拒绝；允许保持候选、修改、返回null并保留旧候选与未决，没有硬编码“必须修改”或“必须相信检查者”。
- 结构失败仍单独标stage_failure和fallback_after_failure；没有把旧候选排序合法直接记成新修订成功。
- 单元/整批尝试上限及首失败停批均有检查；无显式--live不会运行。

## 发现一：[P2] 评分汇总遗漏计划要求的未决与用量

位置：`tools/revision_decision_diagnostic.py`的score，约297—317行。

DIAGNOSTIC_PLAN将retained_unresolved与usage列为主要记录，但score只导出误差、变化方向、调用数、格式恢复及阶段失败等，没有复制result里的unresolved、usage_records与usage_complete。

已用不发网络的脚本响应复现：result保存未决哨兵和用量，评分文件不包含它们。原始数据仍可从每单元result读取，不是数据丢失或分数造假。但只读评分汇总时，无法分辨“有依据地拒绝修改”“保留未决候选”和“无视意见维持原样”；也不方便判断用量完整性。

最小修复：在score行记录中带出未决列表、用量记录/完整性；保留现有stage_failure与candidate_origin。不要用未决数量或模型说明自动认证语义质量。补一项实际score路径回归即可，无需新组件。

## 发现二：[P2] 中断状态仍为running

位置：`tools/revision_decision_diagnostic.py`的run，约263—294行。

run只捕获Exception。KeyboardInterrupt不在其中，finally会保存ended_at，但status仍为running。离线注入一次KeyboardInterrupt，实际得到`status=running`且有ended_at；未触发任何API。

最小修复：显式记录interrupted并继续传播中断，保留已完成单元和实际尝试计数，不自动续跑或重发。每个单元结束时顺手保存batch进度，可使长调用期间的进度文件与stdout一致；不必新增恢复框架。补中断状态回归。

证据：`runs/revision-decision-review-20261021/offline-audit.json`。其中用量和排序均属于离线脚本样本，不能作为模型结果。

## 研究解释边界

本次真正增加的是实验工具和一个提示增量，尚未改变生产架构。两次重复、四个检查点来自同两条已知轨迹，不能称16道题或正式主实验。

若comparison较好，可支持“这个提示在已知局部修订上值得继续检验”；不能直接证明找到了普通讨论成功的原因或形成了新的架构创新。若只是更少修改，应结合保留的缺陷、合理纠正是否被拒绝以及未决信息判读，不能将保持原样自动计作有效保护。现有L1连续指标有用，但不能替代内容核验。

当前阶段不必增加第三裁判、固定作者回应、相同长度的空提示或新的大规模对照来满足局部诊断启动；这些不是本次已确认缺陷的修复。先补两个记录问题，再按原16单元设计执行，版本变化后重新prepare，不能绕过已有匹配检查。
