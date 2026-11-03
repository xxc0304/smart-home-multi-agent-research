> 2026-10-22来源边界修正：SOURCE_ACCESS区分直接原件与公开报告，转述元数据仅导航；两法同规则，错误引用不自动改。208项离线通过，旧r2原始失败仍拒绝，明确诊断副本验证合法载体引用；新prepared-r3冻结未执行，真实HTTP0。见[来源修正记录](../../../../refine-logs/workboard-pilot-20261022/SOURCE_ACCESS_FIX.md)。

> 2026-10-22动作接口已修复并完成离线验收：成功reuse/new允许可选reason；200项检查通过，原始失败响应原样回放通过；六种完整脚本路径及16项复制案例本地准备。新准备包r2已冻结未执行，旧live-r1状态不变，真实HTTP0。见[修复记录](../../../../refine-logs/workboard-pilot-20261022/ACTION_INTERFACE_FIX.md)。

> 2026-10-22后续审核与真实试跑：新增共享初稿、强普通讨论和匹配预算，196项离线通过；首个自然FINALIZE因reuse的非空reason被拒，整批停止。普通讨论回退答案正确，CoReTA未运行。见 ../../../../refine-logs/workboard-pilot-20261022/RESULTS_AND_DIAGNOSIS.md；核心运行源码冻结未变，接口修订尚未实施。

> 2026-10-22后续状态：18项工作板/184项扩展离线检查通过，12项真实schema复制通过。历史实现交付时的“未运行”记录保留下方；当前验证范围见[VALIDATION_20261022.md](VALIDATION_20261022.md)。尚无真实解题能力结果。

# 实现记录

状态：独立模块已写入，两轮源码与假设审查已结束。没有运行验收或能力结果。

| 部分 | 交付 | 验收状态 |
|---|---|---|
| F0 | 独立入口、模型传输、产物落盘的完整路径 | 源码已写入/未运行 |
| F1 | 不可变候选、位置与回退 | 源码已写入/未运行 |
| F2 | 主动贡献、轮转与实际试用 | 源码已写入/未运行 |
| F3 | 双检查、现成版本选择与收尾 | 源码已写入/未运行 |
| F4 | 原始调用、预算、中断与实现选择审查 | 源码已写入/审查完成/未运行 |

本轮按更高优先级要求不新增或运行测试，因此不把技能的逐级运行关卡标绿；交付状态是实现后待验证。没有调用DeepSeek解题API；独立上下文源码审查不计为能力实验。旧运行器和已有结果不覆盖。

## 影响结果解释的选择（全文）

| ID | 未确定处 | 选择 | Class | Source |
|---|---|---|---|---|
| A06 | 错误如何影响结果含义 | 初始化结构错误可记录后继续其他成员；其他协议/传输/上下文错误停止流程并交F，标记interrupted，不记正常完成；F为空才无交付 | semantic | default |
| A07 | 信息分享 | 仅初始资料分散、解题通信可共享的任务；公开offer所带摘录是模型提交内容，引用存在不代表摘录真实；不自动给别人原件 | semantic | default |
| A08 | 什么算完整 | adapter只检查交付形状；排名须覆盖全部候选，文本为非空交付；没有内容真值判断，未决/错误答案仍可能形状完整 | semantic | default |
| A09 | 基线与评分 | 本次只交付新方法入口，不声称现有旧基线已完成公平预算适配；不新增评分、不用新结果进入旧scorer | semantic | default |
| A14 | logical seed含义 | 沿用传输层默认17作为日志标识，不传采样seed，也不承诺可重复采样 | semantic | default |
| A15 | 无实际改动的试用 | 允许reuse当前版本；当两候选相同记录selection_unchanged，不把它当新知识已有效应用 | semantic | default |
| A16 | 拒绝理由返回是否等于解决 | 成功向原提供者发送下一次观察后只标记reason_delivered_to_provider，不推断理解、纠正或缺项解决 | semantic | default |
| A19 | 收尾直接使用未入选贡献或间接采用初稿 | 复用非编辑原稿先找作者；否则按已公开O由新到旧匹配本次申报来源，再按已有W由新到旧匹配其非编辑作者；无来源才轮转选依据检查者，不限于先前TRY入选者 | semantic | sweep |
| A20 | 复用不可变旧稿时本次来源如何传递 | 本次declared_sources作为APPLICATION_SOURCE_REFS随两检查包发送；不篡改原Work的历史声明，来源仍只是本次模型申报 | semantic | sweep |

## Deferred

状态转移验收、真实服务schema兼容、跨任务adapter接入、基线公平预算适配及能力实验。

## Blockers

尚无实际运行证据；不能据此声称流程已跑通。

## 入口与文件

源码：`src/coreta/workboard/`，共7个Python文件。入口为`python -m coreta.workboard prepare|run`。准备只输出INITIAL输入/schema/request，明确不是完整流程验收；真实run需要显式--live和既有API配置。

从CoReTA目录执行的后续准备示例（本轮未执行）：

```powershell
$env:PYTHONPATH = (Join-Path (Get-Location) 'src')
.\.venv\Scripts\python.exe -m coreta.workboard prepare --pack data/task-packs/student-president-dev-v1 --condition distributed --output runs/workboard-v3-initial-preparation
```

现有学生会长包条件名为distributed/concentrated_A1/full/none，旧月球包另有自己的条件名，CLI要求显式指定。

开发默认三人最多19、四人最多29次网络尝试，恢复/重试均0；每阶段输出上限和既有timeout只是工程保护值，不构成正式对比实验的预算冻结。

## 源码审查结论

两轮同家族provisional审查。首轮发现4项：来源选择漏未入选O/间接W；本次来源未送入检查；检查无法读引用原稿；收尾可复用局部稿。全部先记入A19-A22再修复，复审无新增发现，不构成实现正确性保证。原始记录见round-1-assumption-sweep.json与SILENT_ASSUMPTION_SWEEP.json。

全部运行关卡仍未执行，未添加测试，未发DeepSeek请求；没有准备包、解题结果或能力指标。本轮最后仅为提示增加本次APPLICATION_SOURCE_REFS与Work历史声明的区分说明，未改状态逻辑。新代码未提交，旧实现和实验记录保留。

## 下一阶段

先进行离线状态流转和输入隔离验收，再单独确认DeepSeek结构化接口兼容；通过后冻结真实任务、强讨论对照和预算。当前不能直接发起能力对比批次。
