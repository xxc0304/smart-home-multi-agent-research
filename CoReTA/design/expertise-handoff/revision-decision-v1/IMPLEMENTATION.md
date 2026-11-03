# 隔离对照工具实现与离线验证

日期：2026-10-21。状态：工具与最终输入包已完成；没有真实模型调用，没有修订规则效果结果。

## 最新修复更新

审核指出的两处记录缺口已修复：score带出unresolved、has_unresolved、usage_records、usage_complete和uncertain_usage_attempts，阶段失败与旧候选回退标记继续保留；run每完成一个单元保存进度，KeyboardInterrupt记录interrupted、已完成单元及包括部分单元在内的实际尝试数，然后继续抛出中断，不自动续跑。

新增实际score路径和中断路径回归后共25项离线检查通过。最新证据为`runs/revision-decision-offline-fixes-20261021/`，最新准备包为`runs/revision-decision-prepared-v2-20261021/`。此前final及早期preparation包因源码变更均已过时，运行时会被拒绝；下文22项记录保留为上一轮范围。没有改变提示增量、比较单元、模型或预算，也没有启动真实对照。

## 实现边界

工具：`CoReTA/tools/revision_decision_diagnostic.py`。

- `prepare`：从历史事件前缀及其已完成贡献重建检查点，不从最终state/result拷贝。将重建提示恢复为原历史预算元数据后，与当时下一次APPLY的实际请求和schema逐字核对；通过后仅将两臂共同诊断预算改为每单元4次、禁止额外请求。
- `run --live`：按照预设顺序执行16个单次APPLY，两臂只差确定的APPLY提示增量。复用原Runner.apply、Gateway和动态契约；不重跑贡献或生成新核查，不增加生产角色或固定讨论轮次。每单元最多4次含传输/格式恢复的尝试，整批最多64次。任何单元失败即停批，保留日志；非完成批次命令退出2。此停止规则比等待复现共性故障更保守。
- `score`：单独离线读取参考排序，计算每单元修订前后误差和变化方向；不回传模型。阶段失败可保留旧候选，但报告独立标记stage_failure与fallback_after_failure，不将旧候选可评分解释为新修订成功。

现有生产运行器、旧六单元结果和68个原冻结文件均未改动。新增实验工具隔离使用新提示，不改变已完成实验的版本。

## 最终准备包

`CoReTA/runs/revision-decision-prepared-final-20261021/`。

含4份snapshot、各两份提示、16个执行单元的顺序、配置及源文件/准备文件哈希。四个snapshot分别为集中/分散条件的V1和V2之后、下一次APPLY之前。后续工作解、后续核查、原离线误差及参考排名不进入模型输入。私有正文只保留driver自己可见的资料；其他成员公开C贡献仍可含其已经共享的内容。

`runs/revision-decision-preparation-20261021/`是编码早期的准备记录，源码继续修改后不再有效；运行验证会拒绝其旧哈希。后续只使用上述final准备包。

## 22项离线检查

证据：`CoReTA/runs/revision-decision-offline-20261021/validation.json`及`unittest.log`。22项全部通过，零真实模型请求。

覆盖：

- 4份重建输入与历史请求吻合；V1快照无W2/V2，所有快照无W3；追加未来哨兵不改变已截取前缀。
- 仅装入driver原始私有资料；准备和执行不解析最终state/result或evaluator作为输入。旧freeze中的参考文件仅按原有完整性记录校验字节哈希，不提取排名。
- 两臂共用相同packet/schema/预算，仅实验臂追加精确提示片段；全部输入在32768估计预算内。
- 16个单元均衡，第二重复交换两臂执行顺序；不声称API支持相同随机采样种子。
- 可保持、修改或明确拒绝建议；null候选保留旧解和未决。脚本允许这些行为不代表模型会正确选择。
- 缺失核查处理引用和非法排序被拦截，最多一次格式恢复；不能额外发请求。
- 传输失败、格式失败、使用量不确定均保留；合并重试最多4次。批次首失败停止，16单元最坏64次尝试；这些批次检查使用替代函数，没有真实网络。
- 没有显式--live则拒绝运行，不创建运行目录；准备文件被改动则拒绝执行。

本轮没有重跑旧74项测试，因为生产代码未改动；已有68个冻结文件校验未变。

## 后续命令（尚未执行付费运行）

在`C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA`下：

```powershell
.\.venv\Scripts\python.exe tools/revision_decision_diagnostic.py run --live --prepared runs/revision-decision-prepared-v2-20261021 --output runs/revision-decision-live-20261021
.\.venv\Scripts\python.exe tools/revision_decision_diagnostic.py score --batch runs/revision-decision-live-20261021 --output runs/revision-decision-live-20261021-scores.json
```

所有输出目标须不存在；工具不覆盖或自动续跑。源文件若继续修改，应重新准备输入并记录新版本，不能绕过匹配检查。

这16个单元是旧失败轨迹的回顾性诊断，四个检查点只来自两个任务轨迹，不是四道独立题。不能据保持旧解就宣称成功，也不能由它推断专家利用增益或架构创新；还需看实际修订内容和未用于设计的新任务结果。
