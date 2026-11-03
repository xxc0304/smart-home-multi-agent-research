# 检查闭环候选离线验证

已实现独立候选 `ground_issue_loop_v2`，入口类为 `coreta.workboard.issue_loop.IssueRunner`，须搭配 `IssueContracts`、`IssuePrompts` 和本模块 `settings` 显式构造 Gateway。尚未接入付费批次执行器或建立新实验冻结件。

## 实现

- CHECKER_ACCESS、WORK_AUTHOR_ACCESS、APPLICATION_ACTOR_ACCESS 分别表示检查者、作品作者和当前应用者的资料权限。复用其他作者作品时也能区分。仅添加权限元数据，不添加私件正文或合法引用 ID。
- 检查输出列具体问题和复核结果；程序生成问题 ID。选择阶段 schema 要求对每条待处置意见填写 accept/reject/unresolved 及依据。
- TRY、FINALIZE 读取待处理问题；后续检查逐条复核。编辑者的 reject 不删除意见；有相反或 unable 的检查时不算已解决。
- 复核结果绑定作品版本，旧版本上的解决报告不会自动继承到新版本。程序只记录模型报告的解决状态，不认证语义正确。
- 保持原调用顺序和调用数量。选择阶段输出 cap 从 512 提为显式 2048，实际 token 成本尚未测量；新对照需要重新核对总预算，不能冒用 r6 冻结。

## 实际执行

工作目录 `CoReTA`，使用项目 `.venv/Scripts/python.exe`，`PYTHONPATH=src;tests`。

```powershell
.\.venv\Scripts\python.exe tools/audit_issue_loop_archive.py --output refine-logs/issue-loop-20261024/ARCHIVE_CHECK.json
.\.venv\Scripts\python.exe -m unittest test_workboard_issue_loop test_workboard_grounded test_workboard
```

最新执行：**10 项存档/实际权限构造函数检查通过；42 项测试通过（新候选 10、原前置核对 14、原流程 18）**。测试中网络被拦截；真实 API 请求 0。

新候选覆盖：完整 19 调用流程、问题跨轮到达修订者、漏回应/漏复核拒绝、空问题流程、作者与应用者不同的复用、编辑驳回保留、终稿检查冲突保留、版本绑定，以及总判断不得把仍存在的问题表述为 no_issue_found。

存档检查使用真实 005-r1 请求及作品记录，并调用本次实际运行代码中的 `attach_access_context` 构造修订权限视图；产物见 ARCHIVE_CHECK.json。它确认原检查者为 A3/S03、作者为 A2/S02，W6 漏列 O5、W7 补列等事实，保留原数据。

## 能支持的结论

代码能够承载明确权限与逐条问题反馈，遗漏回应会在请求解析阶段被拒绝，问题历史可审阅。脚本模型输出和存档事实检查不能证明真实模型减少误报、改正募资权衡或提高准确率。终稿才新发现的问题在固定调用预算下仍可能未修复；系统会保留其状态。

下一步审核该候选的语义职责、格式复杂度和预算，再冻结最小真实对照。旧 005 的错误结果不因本次代码修改而改变。
