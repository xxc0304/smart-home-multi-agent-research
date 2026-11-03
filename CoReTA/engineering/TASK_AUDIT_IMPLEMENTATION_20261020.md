# 任务约束审计机制：实现与本地验证

日期：2026-10-20。实现条件：`task_audit_v1`。状态：代码和本地验证完成；真实 MATH140 回归与新题实验尚未执行。本轮外部模型请求为 0。

## 实现结果

新增独立运行器 `src/coreta/task_audit.py` 和入口 `python -m coreta.run_task_audit`，基于实际 `inspection_format_v1` 的 closure runner 执行三初稿、TaskFacts、综合、最多三轮 B→U→C。C 后直接交付当前候选，最多14次逻辑调用；scheduler cap15只适配继承的预留槽。没有额外 final 调用。

- TaskFacts 单独请求只携带公共题面。最多32条事实，默认输出上限4096 tokens；可在 `generation.max_output_tokens.task_facts` 显式配置。程序核对 Python Unicode code point 原文跨度或公共字段 JSON Pointer，保留模型声明的覆盖范围。
- C 的完整结构化检查先写事件日志，再保存逐条审计记录。程序保留 `model_verdict` 和 `model_outcome`，另派生 `effective_outcome`。明确 counterexample 或规范有理数精确等式不一致会进入现有 issue 注册表的 blocking issue；correctness-critical unable 进入待查状态。
- 语义、角色、引用、版本或关闭判决冲突都形成持久诊断，不能让整份结构合法的检查重试。纯 JSON/结构错误仍保留原响应并做有界修复。
- Repair 要求 artifact 或目标步骤实际变化；只改 summary、版本号或声明 changed_step_ids 不满足条件。Rebuttal 允许候选不变，但要具体反驳原记录。两种路径都引用完整原始 evidence record IDs，由不同于 B 和 U 的 C 复核。
- C 对可合法绑定的原始案例必须重新检查同一个 fact/input；无效 fact ID 本身可被反驳，仍要求引用原记录并提交对该 issue 的有效新审计，不强制复制无效引用。新反例在该次检查中不能自我关闭。
- 候选后续改变会使已经关闭的 blocking issue 回到需要复核的状态。第三轮 C 首次发现的反例保留开放，运行以 budget_exhausted 结束。

原始 system/draft 提示、Candidate schema 和默认模型配置未改变。新增 TaskFacts 的4096输出默认值在新入口的 manifest 中单列，避免改变旧初稿缓存的完整 config 指纹。已通过测试确认旧初稿银行可以原样复用。C 的上下文包含公共题面、TaskFacts、应用后候选、相关贡献和完整开放 issue，省略全部初稿；省略的来源不会被当作可见引用。

运行时分配 record_id、auditor、事件时间和稳定 issue ID；模型只提交审计内容、已有 issue 关联和关闭提案。完整机器契约保存在 `design/task_audit.schema.json`，提示保存在 `design/task_audit_prompts.json`。

## 本地验证

新增16项检查，全套150项测试通过。完整命令和原始输出见 `TASK_AUDIT_VALIDATION_20261020.txt`；结构摘要及源文件 SHA256 见 `TASK_AUDIT_IMPLEMENTATION_SUMMARY_20261020.json`。

验证覆盖：

1. `expected=0, observed=-3` 同时带 `model_outcome=match` 和 closure `resolved` 时，程序保存原值和原 verdict，issue 保持开放，C 只请求一次、没有语义冲突重试。
2. Repair 和 Rebuttal 分别经过 pending_check 和 C 复核；原始证据不被覆盖。无原记录 ID、元数据假修复、漏掉原案例复查均不能关闭。
3. 规范有理数精确等式才进入数值比较。不同关系、近似/不可解析表达式不冒充程序验证；显式 counterexample 仍能入账。
4. 角色重叠、错误 hash、不可见目标、未知事实、虚假覆盖声明会留下诊断并阻止关闭；错误事实引用本身可经独立反驳处理。
5. 最短路径8次逻辑调用，最坏路径14次；第三轮新反例保留，没有 final 或第四轮。初稿缓存复用后仍按部署口径计入三次初稿逻辑调用，实际请求另列。
6. TaskFacts 检查 Unicode 字符跨度及代码任务公共 entry_point 字段。MATH140 的八个给定点按原题实际空格提取原文跨度，均可匹配；旧 C 中的 −3 被人工转换为结构化 fixture，入账为开放 finding。

另保存可阅读的合成证据 `TASK_AUDIT_FIXTURE_EVIDENCE_20261020.json`：其中 model `resolved` 和 runtime `open` 并存，两个原始审计记录都保留。这里的数值由本地构造，不是新模型生成结果。

入口 `--help` 正常；不提供 `--live` 会在创建输出目录和模型调用前退出。原 MATH140 冻结计划中的176个文件哈希全部匹配，旧运行代码、提示、原始数据和历史结果未被覆盖。

## 复现入口

在项目根目录运行本地验证：

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe -m coreta.run_task_audit --help
```

真实运行入口支持 `--task`、`--output`、`--config`、`--tokenizer`、`--draft-bank` 和 `--seed`；只有显式 `--live` 才发送请求。后续140回归应先冻结运行计划、来源哈希、原三份初稿与单次运行政策，再执行真实请求。

## 结论及下一步

当前确认的是“已提交的结构化反例能够约束状态流转”。程序不能保证模型发现错误，也不能证明模型填写的 expected/observed 或题意解释正确；手工推导错误仍可能共同发生。全套测试通过不构成 CoReTA 解题提升证据。

下一步是 MATH140 单次已见工程回归：复用原三份错误初稿，只提供公共题面；观察是否真实发现反例、是否进入下一轮处理与复核、最终是否正确。该回归仍不计入新题能力证据，随后再冻结新题对照。
