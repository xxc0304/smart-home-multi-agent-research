# Research Output Manifest

2026-10-30八例助手分析：[总判断](research/expert-case-analysis-20261030/REPORT.md)、[逐例](research/expert-case-analysis-20261030/CASE_ANALYSIS.md)、56处原文/JSON与结构比较脚本、[R6](refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md#r6)。新增033选项/理由矛盾、004/023最终历史固定、019早期正确候选与来源编号歧义，保留正反例。先助手分析、人工按主张安排；原核验文件未填/未改，无新模型/训练或新样本。

2026-10-30 W05独立核验包：[开始说明](research/expert-annotation-pilot-20261030/REVIEWER_START.md)、[规范v0.1](research/expert-annotation-pilot-20261030/CODEBOOK.md)、205事件/8例材料、A/B空表、分歧表、源映射与SHA、字面引文/记录完整性检查。[R5助手自审](refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md#r5)限材料PASS，0人工完成。用户跳数澄清已持久化，保留专家自身错误；无模型/训练/收费执行。

2026-10-30完整MuSiQue数据准备：[报告](research/musique-data-preparation-20261030/REPORT.md)、全量审计、来源与代码/文件哈希、C160/D80/H确认候选2360/T可选2000、暴露映射、输入/gold分离、官方评分源码及控制样例核验。[R4助手自审](refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md#r4)PASS限离线准备；C/D分布与依赖仍须处理，人工/模型/成本未完成。当前无GPU，未训练或生成，下一步独立案例核验规范与8例盲标包。

2026-10-30“研究问题—专家任务—证据对齐”交付：[入口](research/expert-task-alignment-20261030/README.md)、8例29事件核验/JSON与脚本、3任务比较、8篇近邻矩阵、单专家最小方案、来源与阶段检查。真实MuSiQue raw60条及无gold输入/目标存data/external，Qwen3-4B只有固定revision分词器；没有权重、训练或问答生成。[第二次阶段自审](refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md#r2)限离线交付PASS，完整数据/分组/独立试标与模型预检尚待。

2026-10-30按用户要求增加[小阶段审核机制](STAGE_REVIEW.md)，写入AGENTS/实验章程/工作计划；[首次审核与下一阶段任务](refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md)明确W01自审范围PASS、W02/W04 REVISE、P0未结项及研究问题—任务—证据对齐。训练与GPU为工具/资源，不替代研究主线；无新模型运行。

2026-10-29专家团队资产核对：[ASSET_AVAILABILITY](research/expert-team-assets-20261029/ASSET_AVAILABILITY.md)、[8案例卡](research/expert-team-assets-20261029/CASE_SEED_8.md)与完整CASE_SEED_8.json、LOCAL_ASSET_AUDIT.json；公开源码快照和本地可重跑检查脚本同目录。PBT实际LFS170MB/10主Arrow、HiddenBench两份全信息650×2结果分别规范存data/external，来源登记dataset.md；既有hidden_generated不移动。170本地槽位核关键字段，作者hidden570×2核字段；8案例仅7题、非盲标、非因果/能力专家结论。工作表W01已核对、人工复核待做；W04已提取，0新模型运行。

140当前修复版单次查验完成：复用原三份错误初稿，inspection_format_v1，7逻辑/4HTTP/0修复，正常complete且reviewed，最终(16/19,5/19)评分0。综合发现旧q非法后重新消元，但把(1,-1)处x²y/xy²符号写反；建设者重复，检查者一度算得g1=-3却错误改判0，全部关闭。合法P/Q在交付点均1320/6859非零，正确点(5/19,16/19)均0。格式问题与数学失败已分开；不继续重跑。下一候选方向是通用原始约束重建及反例优先检查，需先设计对照，未改架构。见 [140完整诊断](engineering/MATH140_FORMAT_DIAGNOSIS_20261020.md)。


检查格式修复已完成，独立 inspection_format_v1：按schema生成准确字段清单，区分checks.scope与closure_reviews，并提供JSON语法行列/offset反馈；严格契约、复核和重试上限保持。完整134项测试通过。固定同六题真实回归6/6正常complete、评分6/6，42逻辑/25HTTP/1修复，无降级；592语法错误经具体定位反馈修复，156无修复完成。旧字段混用错误未出现。单次已见工程回归不证明能力提升或稳定失败率下降；尚未复测完整30题，未重跑140。见 [检查格式修复报告](engineering/INSPECTION_FORMAT_REPORT_20261019.md)。


步骤元数据修复已完成，独立 closure_diff_v1：程序记录真实差异，保留模型声明，不自动关闭问题。五个历史失败更新重放通过，完整125项测试通过。冻结六题真实回归全部评分1，五条complete、一条156因额外scope字段降级，原changed_step_ids错误零次；42逻辑/26HTTP/2修复。592废弃草稿异议经依赖核验后关闭。新变体尚未复测完整30题，未新增全员失败恢复。见 [修复与回归报告](engineering/STEP_DIFF_FIX_REPORT_20261019.md)。


保留评估：src/coreta/closure_feedback.py、run_closure_feedback.py、tests/test_closure_feedback.py；CLOSURE_FEEDBACK_TESTS_20261019.txt（114通过）、CLOSURE_FEEDBACK_CHANGELOG_20261019.md。tools/retention_evaluation.py、RETENTION_PLAN/SCORES/SUMMARY/REPORT_20261019；30道已有正确初稿题全部保留、140已见回归仍失败，6条协议降级。RETENTION_SYNTHESIS_DIAGNOSTIC_20261019.json为事后离线阶段分析，不是基线主终点。

评价范围纠正：engineering/EVALUATION_SCOPE_AND_NET_GAIN_AUDIT_20261019.md，确认30道初稿至少一份通过题尚未运行完整架构；提出同版本G−L净覆盖及保留能力评价，不要求全对。仅本地审核，无新实验或协议修改。

扩展筛选：tools/math_expanded_screen.py、MATH_EXPANDED_SCREEN_PLAN/PREFLIGHT/SCORES/SUMMARY/CONTRACT_REVIEW/REPORT_20261019（32题，1清晰全错、1不完整）；MATH140_FAILURE_ADJUDICATION_20261019.md。恢复诊断：tools/math140_recovery.py、MATH140_RECOVERY_PLAN/RESULTS/SUMMARY/REPORT_20261019；五条件全0，后置复核降级；所有原始轨迹与失败保留。

本轮：603_CONTRIBUTION_PROVENANCE_20261019.md；src/coreta/precheck.py、run_precheck.py、design/precheck_prompts.json、tests/test_precheck.py（完整110项）；PRECHECK_CALIBRATION_PLAN/SUMMARY_20261019.json、PRECHECK_CONTROL_REPORT_20261019.md（603控制0分）；固定MATH训练源data/source/math-train-21a5633及tools/math_train_screen.py、MATH_TRAIN_SCREEN_PLAN/PREFLIGHT/SCORES/SUMMARY/REPORT/CONTRACT_REVIEW_20261019（12题、0题全员失败）。均为开发诊断，不是一般能力结论。

v0.5审核补齐：engineering/CLOSURE_IMPLEMENTATION_AUDIT_20261019.md、CLOSURE_AUDIT_TESTS_20261019.txt（107项通过）、frozen_sources/closure-v0.5-before-null-fix-20261019.py；仅修复ClosureClient空值异常。基线校准：tools/calibrate_closure_baselines.py、CLOSURE_BASELINE_CALIBRATION_PLAN/SUMMARY/REPORT_20261019；同初稿三个正常完成基线均0，原CoReTA1。NEXT_DIFFICULT_TASK_PROTOCOL_20261019.md为未冻结新任务协议草案。

v0.5交付：src/coreta/closure.py、run_closure.py；config/deepseek_flash_closure.json；design/closure_prompts.json；tests/test_closure.py（新增14/完整105项通过）；engineering/CLOSURE_IMPLEMENTATION_AND_CALIBRATION_20261019.md与CLOSURE_CALIBRATION_PLAN/SCORES/SUMMARY_20261019.json。603新初稿全错、交付通过，单次已见校准，无一般能力或基线优势结论。

实现前规格：design/CLOSURE_REVIEW_SPEC_20261019.md，候选应用后复核v0.5草案（预算、状态、版本、异议、交付、截断及对照设计）；尚未实施或运行。

603实验：engineering/LUDIC_COMPARISON_{PLAN,SCORES,TRACES,SUMMARY,REPORT}_20261019；四条件均未通过，普通讨论降级，20次新增HTTP；包含CoReTA准确反对意见被无依据关闭及final未复核改码的过程诊断。

最新补齐：engineering/REFERENCE_SCREEN_IMPLEMENTATION_20261019.md（91项检查）；DIFFICULTY_SCREEN_PLAN/SCORES/SUMMARY/REPORT_20261019（24题72初稿，20题全通过、4题全失败）；DIFFICULTY_SCREEN_CONTRACT_REVIEW_20261019.md（全池统一复核）；SEMANTIC_CHECK_CASE_641_20261019.md（错误背书过程案例）。未追加完整协作比较。

最新审查：engineering/RECENT_WORK_AUDIT_20261019.md（两轮原始记录核对、难度校准缺失、641错误检查背书、引用修复验证边界；无新模型调用）。

| Timestamp | Skill | File | Stage | Description |
|-----------|-------|------|-------|-------------|
| 2026-10-18 22:21:21 +08:00 | /research-refine | refine-logs/PROBLEM_ANCHOR.md | implementation | 本轮不可变研究锚点 |
| 2026-10-18 22:21:21 +08:00 | /research-refine | refine-logs/REFINE_STATE_20261018_222121.json | implementation | 初始化状态快照 |
| 2026-10-18 22:21:21 +08:00 | /research-refine | refine-logs/REFINE_STATE.json | implementation | 初始化最新状态 |
| 2026-10-18 23:29:06 +0800 | /research-refine | CURRENT_STATE.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/ARTIFACTS.sha256 | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/coreta.schema.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/DESIGN_CHECKS.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/examples/public_task.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/examples/README.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/examples/synthetic_trace.jsonl | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/PROMPTS.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | design/v0.3/README.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /experiment-plan | design/v0.3/run_config.proposed.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | DISCUSSION_REVIEW_AND_PLAN_20261018.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | README.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /experiment-plan | refine-logs/EXPERIMENT_PLAN.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /experiment-plan | refine-logs/EXPERIMENT_PLAN_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /experiment-plan | refine-logs/EXPERIMENT_TRACKER_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/FINAL_PROPOSAL.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/FINAL_PROPOSAL_20261018_232000.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/FINAL_PROPOSAL_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/PROBLEM_ANCHOR.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REFINE_STATE.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REFINE_STATE_20261018_222121.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REFINE_STATE_20261018_232906.json | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REFINEMENT_REPORT.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REFINEMENT_REPORT_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REVIEW_SUMMARY.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/REVIEW_SUMMARY_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/round-0-initial-proposal.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/round-1-refinement.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/round-1-review.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/round-2-review.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/score-history.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/SOURCE_LEDGER.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:29:06 +0800 | /research-refine | refine-logs/SOURCE_LEDGER_20261018_232906.md | implementation | v0.3 design delivery; no model experiment |
| 2026-10-18 23:40:40 +0800 | /research-review local | V03_DESIGN_REVIEW_20261018_234040.md | review | local design audit; three scoped findings; no execution |
| 2026-10-19 +0800 | design supplement | refine-logs/FINAL_PROPOSAL.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | refine-logs/EXPERIMENT_PLAN.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | refine-logs/EXPERIMENT_TRACKER.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/PROMPTS.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/CONTRIBUTION_ANNOTATION.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/SUPPLEMENT_20261019.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/README.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/ARTIFACTS.sha256 | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | CURRENT_STATE.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | refine-logs/FINAL_PROPOSAL_20261019_supplement.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | refine-logs/EXPERIMENT_PLAN_20261019_supplement.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | design/v0.3/PROMPTS_20261019_supplement.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | design supplement | CURRENT_STATE_20261019_supplement.md | design | address three local review findings; no execution |
| 2026-10-19 +0800 | core implementation | src/coreta/__init__.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/analyze.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/model_client.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/prompts.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/protocol.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/run.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/schemas.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/state.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | src/coreta/tasks.py | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | pyproject.toml | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | config/deepseek_flash.json | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | IMPLEMENTATION.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | IMPLEMENTATION_DECISIONS.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | CURRENT_STATE.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | README.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | design/v0.3/README.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | design/v0.3/run_config.proposed.json | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | design/v0.3/ARTIFACTS.sha256 | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | refine-logs/FINAL_PROPOSAL.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | refine-logs/EXPERIMENT_PLAN.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | core implementation | refine-logs/EXPERIMENT_TRACKER.md | implementation | code authored; no installation, tests or model calls |
| 2026-10-19 +0800 | E0 engineering | src/coreta/scoring.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | src/coreta/scoring_worker.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | src/coreta/model_client.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | src/coreta/protocol.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | src/coreta/analyze.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | tests/test_protocol.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | tests/test_scoring.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | tools/run_e0_checks.py | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | scoring/Dockerfile | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | scoring/README.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | engineering/E0_STATUS_20261019.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | engineering/E0_REPORT_20261019.json | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | engineering/requirements.windows-e0.lock.txt | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | pyproject.toml | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | IMPLEMENTATION_DECISIONS.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | IMPLEMENTATION.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | CURRENT_STATE.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | README.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | design/v0.3/README.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | refine-logs/EXPERIMENT_PLAN.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | refine-logs/EXPERIMENT_TRACKER.md | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | E0 engineering | design/v0.3/ARTIFACTS.sha256 | engineering | 41 local tests pass; Linux scoring pending; no model API calls |
| 2026-10-19 +0800 | docker and development setup | src/coreta/batch.py | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | src/coreta/run.py | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | tests/test_batch.py | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | tools/prepare_development.py | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | tools/install_wsl_prerequisite.ps1 | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | tools/enable_docker_platform.ps1 | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/DOCKER_SETUP_20261019.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/DEVELOPMENT_DATA_MANIFEST_20261019.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/DEVELOPMENT_ENGINEERING_PLAN_20261019.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/DEVELOPMENT_PILOT_PLAN_20261019.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/E0_REPORT_DOCKER_STAGE_20261019.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/requirements.windows-docker-stage.lock.txt | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/docker-setup-20261019/docker-install-result.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/docker-setup-20261019/wsl-msi-result.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/docker-setup-20261019/platform-enable-result.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | engineering/docker-setup-20261019/wsl-installed-check.json | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | CURRENT_STATE.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | IMPLEMENTATION.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | IMPLEMENTATION_DECISIONS.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | pyproject.toml | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | README.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | scoring/README.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 +0800 | docker and development setup | refine-logs/EXPERIMENT_TRACKER.md | implementation | Docker/WSL installed; reboot pending; 47 tests pass; no model calls |
| 2026-10-19 09:44 +0800 | reboot environment check | engineering/REBOOT_CHECK_20261019.md | environment | kernel boot predates feature enablement; full Restart still needed; no boot changes |
| 2026-10-19 09:44 +0800 | reboot environment check | engineering/docker-setup-20261019/hypervisor-boot-check.json | environment | kernel boot predates feature enablement; full Restart still needed; no boot changes |
| 2026-10-19 09:44 +0800 | reboot environment check | engineering/docker-setup-20261019/reboot-evidence.json | environment | kernel boot predates feature enablement; full Restart still needed; no boot changes |
| 2026-10-19 09:44 +0800 | reboot environment check | tools/check_hypervisor_boot.ps1 | environment | kernel boot predates feature enablement; full Restart still needed; no boot changes |
| 2026-10-19 09:44 +0800 | reboot environment check | CURRENT_STATE.md | environment | kernel boot predates feature enablement; full Restart still needed; no boot changes |
| 2026-10-19 +0800 | Linux scoring verification | .dockerignore | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | scoring/Dockerfile | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | scoring/README.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | src/coreta/scoring.py | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | src/coreta/scoring_worker.py | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | tests/test_scoring.py | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | tools/check_scoring_container.py | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/LINUX_SCORING_READY_20261019.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/DOCKER_ENGINE_READY_20261019.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/SCORING_IMAGE_20261019.txt | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/requirements.linux-scoring.lock.txt | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/E0_REPORT_LINUX_STAGE_20261019.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/container-check-20261019-final/report.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/container-check-20261019-final/container_environment.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/container-check-20261019-final/development_math_preflight.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | engineering/container-check-20261019-final/math_fixture_scores.json | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | CURRENT_STATE.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | README.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | IMPLEMENTATION.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | IMPLEMENTATION_DECISIONS.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | refine-logs/EXPERIMENT_TRACKER.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | Linux scoring verification | design/v0.3/README.md | engineering | 49 unit tests and 7 container checks pass; 50 development golds ready; no model calls |
| 2026-10-19 +0800 | preparation audit | engineering/PRE_EXPERIMENT_AUDIT_20261019.md | review | single-task integration ready; batch blockers identified; metadata GET only; no generation |
| 2026-10-19 +0800 | preparation audit | engineering/DEEPSEEK_METADATA_CHECK_20261019.json | review | single-task integration ready; batch blockers identified; metadata GET only; no generation |
| 2026-10-19 +0800 | preparation audit | CURRENT_STATE.md | review | single-task integration ready; batch blockers identified; metadata GET only; no generation |
| 2026-10-19 +0800 | preparation fixes and integration | engineering/PREPARATION_FIXES_20261019.md | engineering | 52 checks; 13 live HTTP requests; math pass/code fail; no comparative claim |
| 2026-10-19 +0800 | preparation fixes and integration | engineering/LIVE_INTEGRATION_20261019.json | engineering | 52 checks; 13 live HTTP requests; math pass/code fail; no comparative claim |
| 2026-10-19 +0800 | preparation fixes and integration | engineering/E0_FIXES_20261019.json | engineering | 52 checks; 13 live HTTP requests; math pass/code fail; no comparative claim |
| 2026-10-19 +0800 | preparation fixes and integration | engineering/DEVELOPMENT_ENGINEERING_TOKENIZER_PLAN_20261019.json | engineering | 52 checks; 13 live HTTP requests; math pass/code fail; no comparative claim |
| 2026-10-19 +0800 | preparation fixes and integration | engineering/DEVELOPMENT_PILOT_TOKENIZER_PLAN_20261019.json | engineering | 52 checks; 13 live HTTP requests; math pass/code fail; no comparative claim |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_REPORT_20261019.md | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_RESULTS_20261019.json | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_SCORES_20261019.json | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_EXECUTION_20261019.json | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_EARLY_FINISH_20261019.json | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | engineering/DEVELOPMENT_PILOT_LAUNCH_20261019.json | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 development pilot | tools/summarize_development_pilot.py | experiment | all60 trajectories and120 metric rows; 284 HTTP attempts; all conditions tie; no help requests |
| 2026-10-19 +0800 | E1 audit and diagnosis | PILOT_REVIEW_AND_DIAGNOSIS_20261019.md | review | local review; 60 initial drafts scored offline; 100 source records reviewed; no new generation |
| 2026-10-19 +0800 | E1 audit and diagnosis | engineering/PILOT_CASE_DIAGNOSIS_20261019.json | review | local review; 60 initial drafts scored offline; 100 source records reviewed; no new generation |
| 2026-10-19 +0800 | E1 audit and diagnosis | engineering/PILOT_INITIAL_DRAFT_DIAGNOSTIC_20261019.json | review | local review; 60 initial drafts scored offline; 100 source records reviewed; no new generation |
| 2026-10-19 +0800 | E1 audit and diagnosis | engineering/DEVELOPMENT_POOL_QUALITY_AUDIT_20261019.json | review | local review; 60 initial drafts scored offline; 100 source records reviewed; no new generation |
| 2026-10-19 +0800 | E1 audit and diagnosis | tools/diagnose_pilot_drafts.py | review | local review; 60 initial drafts scored offline; 100 source records reviewed; no new generation |
| 2026-10-19 +0800 | user correction and complementarity diagnosis | COMPLEMENTARITY_DIAGNOSIS_20261019.md | review | local joint completion is central; existing whole-solution oracle does not measure local complementarity; no new generation |
| 2026-10-19 +0800 | design implementation behavior audit | DESIGN_IMPLEMENTATION_BEHAVIOR_DIAGNOSIS_20261019.md | review | 20 archived traces; formal flow matches; incorrect review arithmetic propagated and change omitted in799; no new generation |
| 2026-10-19 +0800 | design implementation behavior audit | engineering/PILOT_DESIGN_EXECUTION_AUDIT_20261019.json | review | 20 archived traces; formal flow matches; incorrect review arithmetic propagated and change omitted in799; no new generation |
| 2026-10-19 +0800 | design implementation behavior audit | tools/audit_pilot_execution.py | review | 20 archived traces; formal flow matches; incorrect review arithmetic propagated and change omitted in799; no new generation |
| 2026-10-19 +0800 | complementarity chain inspection | DESIGN_IMPLEMENTATION_BEHAVIOR_DIAGNOSIS_20261019.md | review | initial fusion, bootstrap and finalizer inspected; 9 code updates unchanged; finalizer763 matches existing A2; no new generation |
| 2026-10-19 +0800 | complementarity chain inspection | engineering/PILOT_DESIGN_EXECUTION_AUDIT_20261019.json | review | initial fusion, bootstrap and finalizer inspected; 9 code updates unchanged; finalizer763 matches existing A2; no new generation |
| 2026-10-19 +0800 | complementarity chain inspection | tools/audit_pilot_execution.py | review | initial fusion, bootstrap and finalizer inspected; 9 code updates unchanged; finalizer763 matches existing A2; no new generation |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/COMPLEMENTARITY_RESEARCH_BRIEF_20261019.md | research | frozen RQs and primary-source scope; no runtime changes |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/literature_mechanisms_20261019.md | research | official workflow and work-product code inspected; version boundaries recorded |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/literature_coordination_20261019.md | research | representation, information partition and filtering mechanisms; limitations recorded |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/literature_failures_20261019.md | research | negative evidence and all-initial-wrong evidence distinguished |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/COMPLEMENTARITY_MECHANISM_REVIEW_20261019.md | research | 17 works; primary-source ledger and cross-mechanism synthesis; no replication claim |
| 2026-10-19 +0800 | literature-grounded complementarity design | research/CORETA_REVISION_FROM_LITERATURE_20261019.md | design | concrete draft revision; not frozen or implemented; no model calls |
| 2026-10-19 +0800 | retrieval and revision audit | research/RETRIEVAL_AND_REVISION_AUDIT_20261019.md | review | construction, bridging, stopping and behavioral delta need specification; no runtime changes or experiments |
| 2026-10-19 +0800 | concrete stage and state design | design/REVISION_STAGE_AND_STATE_SPEC_20261019.md | design | fixed constructive stage, issue handling, bridging and constrained stopping; 14 normal-call cap; not implemented or experimentally verified |
| 2026-10-19 +0800 | constructive revision implementation | src/coreta/revision.py | implementation | opt-in single-task runner and contracts; not tested or model-validated |
| 2026-10-19 +0800 | constructive revision implementation | src/coreta/run_revision.py | implementation | separate live-gated entry; old runner preserved |
| 2026-10-19 +0800 | constructive revision implementation | design/revision_prompts.json | implementation | versioned constructive stage prompts; no online tools |
| 2026-10-19 +0800 | constructive revision implementation | design/REVISION_IMPLEMENTATION_20261019.md | implementation | implementation choices and pending verification/batch boundaries |
| 2026-10-19 +0800 | revision offline validation | tests/test_revision.py | verification | 24 deterministic revision checks; no model or capability evidence |
| 2026-10-19 +0800 | revision offline validation | engineering/REVISION_OFFLINE_VALIDATION_20261019.md | verification | 76 checks passed including52 legacy; changed-step constraint strengthened; no live requests |
| 2026-10-19 +0800 | revision offline validation | engineering/REVISION_OFFLINE_TEST_OUTPUT_20261019.txt | verification | raw unittest output:76 passed |
| 2026-10-19 +0800 | revision live integration | engineering/REVISION_LIVE_PLAN_20261019.json | engineering | math6388/code607 selected before generation; no comparative claim |
| 2026-10-19 +0800 | revision live repair | engineering/REVISION_LIVE_REPAIR_PLAN_20261019.md | engineering | preserve failed code trace; one bounded same-task rerun; issue reuse and context projection |
| 2026-10-19 +0800 | revision live integration | engineering/REVISION_LIVE_INTEGRATION_20261019.md | engineering | two tasks; code first degraded then repaired;33HTTP attempts total; no all-wrong recovery |
| 2026-10-19 +0800 | revision offline scoring | tools/score_revision_integration.py | engineering | Docker only; all three drafts and pre/final scored; no evaluator feedback to model |
| 2026-10-19 +0800 | revision offline scoring | engineering/REVISION_LIVE_SCORES_20261019.json | engineering | 15 artifact scores across3 produced trajectories; all pass; not15 independent tasks |
| 2026-10-19 +0800 | revision trace review | engineering/REVISION_LIVE_TRACE_SUMMARY_20261019.json | engineering | flow, issue registry and input estimates retained |
| 2026-10-19 +0800 | post-live regression | engineering/REVISION_POST_LIVE_TEST_OUTPUT_20261019.txt | verification | 78 passed;26 revision plus52 legacy |
| 2026-10-19 +0800 | revision paired comparison | design/REVISION_COMPARISON_PROTOCOL_20261019.md | design | four conditions, identical initial bank, independent trajectory visibility and frozen selected-subset boundaries |
| 2026-10-19 +0800 | revision paired comparison | tools/revision_pilot.py | engineering | before-generation plan and source hashes;8 bounded jobs; no automatic resume |
| 2026-10-19 +0800 | revision paired comparison | engineering/REVISION_COMPARISON_PLAN_20261019.json | experiment | math6913/code736 selected by public prompt length after nonpilot/static-review filter; proxy not difficulty proof |
| 2026-10-19 +0800 | revision paired comparison | tools/score_revision_pilot.py | engineering | offline Docker scoring and initial-payload equality checks |
| 2026-10-19 +0800 | revision paired comparison | engineering/REVISION_COMPARISON_REPORT_20261019.md | experiment | 8 trajectories completed; all four conditions tie; all shared initials pass; no capability gain observed |
| 2026-10-19 +0800 | revision paired comparison | engineering/REVISION_COMPARISON_SUMMARY_20261019.json | experiment | 64 logical calls,47 HTTP,1 repair; initial equality verified |
| 2026-10-19 +0800 | revision paired comparison | engineering/REVISION_COMPARISON_SCORES_20261019.json | experiment |22 artifacts pass across2 tasks, not22 independent samples |
| 2026-10-19 +0800 | revision paired comparison | engineering/REVISION_COMPARISON_TRACES_20261019.json | experiment | per-condition stages, hashes, AST comparison and application changes |
| 2026-10-19 +0800 | revision comparison regression | engineering/REVISION_COMPARISON_TEST_OUTPUT_20261019.txt | verification |83 passed;31 revision plus52 legacy |
| 2026-10-19 +0800 | archived failure review | engineering/ARCHIVED_FAILURE_INVENTORY_20261019.json | review |11 failed initial records across4 tasks; original scores retained |
| 2026-10-19 +0800 | archived failure review | research/ARCHIVED_FAILURE_CONTRACT_REVIEW_20261019.md | review | percentage/integer count, row-column, cyclic domain and bool interface distinctions |
| 2026-10-19 +0800 | archived failure retest | tools/retest_archived_failures.py | engineering | frozen original task756 four-condition retest; unchanged public/evaluation contracts |
| 2026-10-19 +0800 | archived failure retest | engineering/ARCHIVED_FAILURE_RETEST_PLAN_20261019.json | experiment | selected before generation;38 normal-call ceiling; diagnostic subset |
| 2026-10-19 +0800 | archived failure retest | engineering/ARCHIVED_FAILURE_RETEST_REPORT_20261019.md | experiment | new initials1/1/0; all four finals pass; no all-wrong recovery or accuracy gain |
| 2026-10-19 +0800 | archived failure retest | engineering/ARCHIVED_FAILURE_RETEST_SCORES_20261019.json | experiment |11 artifact scores; A2 initial fails and all final outputs pass |
| 2026-10-19 +0800 | archived failure retest | engineering/ARCHIVED_FAILURE_RETEST_RESULTS_20261019.json | experiment | four completed trajectories;32 logical calls,23 HTTP,0 repairs |
| 2026-10-19 +0800 | three original failure retest | tools/retest_three_failures.py | engineering | original tasks and scoring; frozen12 jobs; preserve degraded cases |
| 2026-10-19 +0800 | three original failure retest | engineering/THREE_FAILURES_PLAN_20261019.json | experiment | three user-requested old failures;114 normal-call ceiling; no protocol edits |
| 2026-10-19 +0800 | three original failure retest | engineering/THREE_FAILURES_REPORT_20261019.md | experiment | CoReTA0/3; math independent-refine1 via alternate last-box answer;802 constructive reference failure |
| 2026-10-19 +0800 | three original failure retest | engineering/THREE_FAILURES_SUMMARY_20261019.json | experiment |94 logical calls,68HTTP,1 repair;11 complete1degraded; shared initials equal |
| 2026-10-19 +0800 | three original failure retest | engineering/THREE_FAILURES_SCORES_20261019.json | experiment |33 artifact scores; raw scores unmodified |
| 2026-10-19 +0800 | three original failure retest | engineering/THREE_FAILURES_TRACES_20261019.json | experiment |12 trajectories with final outputs, errors and stage paths |
| 2026-10-19 +0800 | reference alias repair | src/coreta/state.py | implementation | current-candidate step references now expose source-event and version aliases |
| 2026-10-19 +0800 | reference repair diagnostics | src/coreta/schemas.py | implementation | invalid references identify offending values and visible same-step alternatives |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_REVIEW_20261019.md | review | six untried tasks; public prompt and frozen score contract checked before generation |
| 2026-10-19 +0800 | clear-task comparison | tools/clean_task_comparison.py | engineering | frozen four-condition runner, shared drafts, Docker-only offline scoring; degradation retained |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_COMPARISON_PLAN_20261019.json | experiment | six reviewed tasks,24 jobs,228 normal-call upper bound; source/data hashes frozen |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_COMPARISON_REPORT_20261019.md | experiment | all18 initial drafts and all48 pre/final artifacts pass; no all-initial-wrong recovery case |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_COMPARISON_SUMMARY_20261019.json | experiment |192 logical calls,139 HTTP attempts,1 repair; all24 trajectories completed |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_COMPARISON_SCORES_20261019.json | experiment |66 artifacts, all original-score pass; no effect estimate |
| 2026-10-19 +0800 | clear-task comparison | engineering/CLEAN_TASK_COMPARISON_TRACES_20261019.json | experiment | per-condition stages and actions; six complete CoReTA S/B/C/U paths |
| 2026-10-19 +0800 | challenge task curation | engineering/CHALLENGE_TASK_REVIEW_20261019.md | review | four multi-step GSM8K and three algorithmic MBPP tasks reviewed before generation |
| 2026-10-19 +0800 | challenge task curation | tools/prepare_challenge_tasks.py | engineering | extracts new train-only public/evaluation slice, checks prior/prompt/holdout duplicates and freezes hashes |
| 2026-10-19 +0800 | challenge task curation | data/complementarity-challenge-20261019/manifest.json | dataset | seven untouched train tasks; MATH-500/HumanEval+ source prompts checked for duplicates; no model calls |
| 2026-10-19 +0800 | challenge comparison | tools/challenge_comparison.py | engineering | frozen four-condition run/scoring driver; preserves degraded trajectories |
| 2026-10-19 +0800 | challenge comparison | engineering/CHALLENGE_COMPARISON_PLAN_20261019.json | experiment | seven tasks,28 jobs,266-call ceiling; data, code and task hashes frozen |
| 2026-10-19 +0800 | challenge comparison | engineering/CHALLENGE_COMPARISON_REPORT_20261019.md | experiment | 21 initial drafts and all56 pre/final artifacts pass; no all-initial-wrong case |
| 2026-10-19 +0800 | challenge comparison | engineering/CHALLENGE_COMPARISON_SUMMARY_20261019.json | experiment |224 logical calls,162 HTTP attempts,1 repair; all28 trajectories completed |
| 2026-10-19 +0800 | challenge comparison | engineering/CHALLENGE_COMPARISON_SCORES_20261019.json | experiment |77 artifacts all original-score pass; no effect estimate |
| 2026-10-19 +0800 | challenge comparison | engineering/CHALLENGE_COMPARISON_TRACES_20261019.json | experiment | all seven CoReTA S/B/C/U chains completed, with one repaired inspection response |

| 2026-10-20 +0800 | task-anchored audit design | design/TASK_ANCHORED_AUDIT_DESIGN_20261020_001456.md | design | v0.2: append-only issue evidence, explicit rational mismatch gate, repair/rebuttal paths, budget and paired pilot definitions |
| 2026-10-20 +0800 | task-anchored audit design | design/TASK_ANCHORED_AUDIT_DESIGN.md | superseded pointer | fixed latest copy subsequently updated to v0.3; see newer manifest entry |

| 2026-10-20 +0800 | task-anchored audit design | design/TASK_ANCHORED_AUDIT_DESIGN_20261020_001804.md | design | v0.3: aligns closure runner B→U→C, 14-call total, exact-equality-only gate; ready for local interface/state-machine implementation |
| 2026-10-20 +0800 | task-anchored audit design | design/TASK_ANCHORED_AUDIT_DESIGN.md | latest | same content as timestamped v0.3 design |

| 2026-10-20 +0800 | design correction | design/TASK_ANCHORED_AUDIT_DESIGN_20261020_001456.md | superseded | v0.2 contained an incorrect runner order/call description; corrected by v0.3 after source-level review |


| 2026-10-20 +0800 | task audit implementation | src/coreta/task_audit.py | implementation | opt-in task-only facts, append-only audit evidence, dual closure paths and 14-stage budget |
| 2026-10-20 +0800 | task audit entry | src/coreta/run_task_audit.py | implementation | explicit live entry, source snapshots and inherited draft cache compatibility |
| 2026-10-20 +0800 | task audit prompts | design/task_audit_prompts.json | implementation | preserved system/draft strings; task facts and structured post-application audit |
| 2026-10-20 +0800 | task audit schema | design/task_audit.schema.json | contract | generated coreta/0.6-task-audit machine contract |
| 2026-10-20 +0800 | task audit fixtures | tests/test_task_audit.py | verification | 16 meaningful offline checks; scripted outputs are not capability evidence |
| 2026-10-20 +0800 | task audit validation | engineering/TASK_AUDIT_VALIDATION_20261020.txt | verification | all150 tests pass; CLI help and no-live guard checked |
| 2026-10-20 +0800 | task audit implementation summary | engineering/TASK_AUDIT_IMPLEMENTATION_SUMMARY_20261020.json | verification | 176 frozen legacy hashes match; new source hashes; zero external requests |
| 2026-10-20 +0800 | task audit retained evidence | engineering/TASK_AUDIT_FIXTURE_EVIDENCE_20261020.json | fixture | supplied 0/-3 and resolved verdict retained as runtime open; synthetic only |
| 2026-10-20 +0800 | task audit implementation report | engineering/TASK_AUDIT_IMPLEMENTATION_20261020.md | report | implementation complete; real MATH140 regression pending |

| 2026-10-20 +0800 | MATH140 task audit driver | tools/math140_task_audit_regression.py | engineering | frozen one-invocation build/run/score; exact old three drafts |
| 2026-10-20 +0800 | MATH140 task audit plan | engineering/MATH140_TASK_AUDIT_PLAN_20261020.json | plan | frozen before generation;14 logical calls max, no reruns |
| 2026-10-20 +0800 | MATH140 task audit result | runs/math140-task-audit-20261020/4276ec64c178dafa/result.json | experiment | failed at TaskFacts spans;4 logical calls,2 API attempts,1 repair; no B/U/C |
| 2026-10-20 +0800 | MATH140 task audit score | engineering/MATH140_TASK_AUDIT_SCORES_20261020.json | experiment | fixed Docker score0; delivered unchanged A0 draft; frozen hashes match |
| 2026-10-20 +0800 | MATH140 task audit diagnosis | engineering/MATH140_TASK_AUDIT_DIAGNOSIS_20261020.json | diagnosis | repair output10/10 prompt quotes uniquely match but0/12 declared locators valid |
| 2026-10-20 +0800 | MATH140 task audit report | engineering/MATH140_TASK_AUDIT_REPORT_20261020.md | report | source-location interface blocked collaboration; no mechanism-effect claim |

| 2026-10-20 +0800 | task audit result/revision review | engineering/TASK_AUDIT_RESULT_AND_REVISION_REVIEW_20261020.md | review | validates run records; finds grouped-fact coverage gap; specifies bounded exact source-binding revision |
| 2026-10-20 +0800 | task audit review checks | engineering/MATH140_TASK_AUDIT_REVIEW_CHECKS_20261020.json | review |23 frozen hashes match; public-task-only request material; synthetic coverage counterexample |

| 2026-10-20 +0800 | source binding v2 | src/coreta/task_audit_binding.py | implementation | exact quote resolution, locked successful facts, targeted patch and declared-item coverage |
| 2026-10-20 +0800 | source binding entry | src/coreta/run_task_audit_binding.py | implementation | separate opt-in v2 runner with frozen v1 reuse and14 logical stage cap |
| 2026-10-20 +0800 | source binding prompts | design/source_binding_prompts.json | implementation | no model offsets/pointers; independent item IDs; patch-only repair |
| 2026-10-20 +0800 | source binding schema | design/source_binding.schema.json | contract | coreta/0.7-source-binding; incoming facts, patch and runtime bound facts |
| 2026-10-20 +0800 | source binding tests | tests/test_source_binding.py | verification |22 new checks, including real saved-response replay and grouped-item counterexample |
| 2026-10-20 +0800 | source binding replay tool | tools/replay_source_bindings.py | engineering | explicit schema migration for provenance-only offline replay |
| 2026-10-20 +0800 | source binding replay | engineering/SOURCE_BINDING_REPLAY_20261020.json | verification | first9/10, second10/10; targeted F02 patch preserves9 locked facts; not model evidence |
| 2026-10-20 +0800 | source binding validation | engineering/SOURCE_BINDING_VALIDATION_20261020.txt | verification |172 tests pass plus entry help/no-live checks |
| 2026-10-20 +0800 | source binding summary | engineering/SOURCE_BINDING_IMPLEMENTATION_SUMMARY_20261020.json | verification | new source hashes and23 frozen v1 hashes; zero external API requests |
| 2026-10-20 +0800 | source binding report | engineering/SOURCE_BINDING_IMPLEMENTATION_20261020.md | report | local modification/validation complete; real v2 MATH140 regression pending |
| 2026-10-20 +0800 | source binding regression plan | engineering/MATH140_SOURCE_BINDING_PLAN_20261020.json | engineering regression | score1; degraded at apply; synthesis answer hit, no C audit |
| 2026-10-20 +0800 | source binding regression scores | engineering/MATH140_SOURCE_BINDING_SCORES_20261020.json | engineering regression | score1; degraded at apply; synthesis answer hit, no C audit |
| 2026-10-20 +0800 | source binding regression diagnosis | engineering/MATH140_SOURCE_BINDING_DIAGNOSIS_20261020.json | engineering regression | score1; degraded at apply; synthesis answer hit, no C audit |
| 2026-10-20 +0800 | source binding regression report | engineering/MATH140_SOURCE_BINDING_REPORT_20261020.md | engineering regression | score1; degraded at apply; synthesis answer hit, no C audit |
| 2026-10-20 +0800 | closure reference v3 | src/coreta/closure_reference.py | implementation/verification | explicit per-issue audit ID contract; offline only |
| 2026-10-20 +0800 | closure reference v3 | src/coreta/run_closure_reference.py | implementation/verification | explicit per-issue audit ID contract; offline only |
| 2026-10-20 +0800 | closure reference v3 | tests/test_closure_reference.py | implementation/verification | explicit per-issue audit ID contract; offline only |
| 2026-10-20 +0800 | closure reference v3 | engineering/CLOSURE_REFERENCE_VALIDATION_20261020.json | implementation/verification | explicit per-issue audit ID contract; offline only |
| 2026-10-20 +0800 | closure reference v3 | engineering/CLOSURE_REFERENCE_IMPLEMENTATION_20261020.md | implementation/verification | explicit per-issue audit ID contract; offline only |
| 2026-10-20 +0800 | MATH140 reference v3 regression | tools/math140_closure_reference_regression.py | engineering | C finds counterexamples; correct work uncommitted; final score0 |
| 2026-10-20 +0800 | MATH140 reference v3 regression | engineering/MATH140_CLOSURE_REFERENCE_PLAN_20261020.json | engineering | C finds counterexamples; correct work uncommitted; final score0 |
| 2026-10-20 +0800 | MATH140 reference v3 regression | engineering/MATH140_CLOSURE_REFERENCE_SCORES_20261020.json | engineering | C finds counterexamples; correct work uncommitted; final score0 |
| 2026-10-20 +0800 | MATH140 reference v3 regression | engineering/MATH140_CLOSURE_REFERENCE_DIAGNOSIS_20261020.json | engineering | C finds counterexamples; correct work uncommitted; final score0 |
| 2026-10-20 +0800 | MATH140 reference v3 regression | engineering/MATH140_CLOSURE_REFERENCE_REPORT_20261020.md | engineering | C finds counterexamples; correct work uncommitted; final score0 |
| 2026-10-20 +0800 | audit delivery v4 | src/coreta/audit_delivery.py | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | audit delivery v4 | src/coreta/run_audit_delivery.py | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | audit delivery v4 | config/deepseek_flash_delivery.json | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | audit delivery v4 | tests/test_audit_delivery.py | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | audit delivery v4 | engineering/AUDIT_DELIVERY_VALIDATION_20261020.json | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | audit delivery v4 | engineering/AUDIT_DELIVERY_IMPLEMENTATION_20261020.md | repair/verification | visible audit IDs and lossless bounded repair; offline only |
| 2026-10-20 +0800 | MATH140 delivery v4 regression | engineering/MATH140_AUDIT_DELIVERY_PLAN_20261020.json | engineering | inspect truncated twice; final0; no accepted audit |
| 2026-10-20 +0800 | MATH140 delivery v4 regression | engineering/MATH140_AUDIT_DELIVERY_SCORES_20261020.json | engineering | inspect truncated twice; final0; no accepted audit |
| 2026-10-20 +0800 | MATH140 delivery v4 regression | engineering/MATH140_AUDIT_DELIVERY_DIAGNOSIS_20261020.json | engineering | inspect truncated twice; final0; no accepted audit |
| 2026-10-20 +0800 | MATH140 delivery v4 regression | engineering/MATH140_AUDIT_DELIVERY_REPORT_20261020.md | engineering | inspect truncated twice; final0; no accepted audit |
| 2026-10-20 +0800 | inspection recovery v5 | src/coreta/inspection_recovery.py | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | inspection recovery v5 | src/coreta/run_inspection_recovery.py | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | inspection recovery v5 | config/deepseek_flash_inspection.json | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | inspection recovery v5 | tests/test_inspection_recovery.py | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | inspection recovery v5 | engineering/INSPECTION_RECOVERY_VALIDATION_20261020.json | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | inspection recovery v5 | engineering/INSPECTION_RECOVERY_IMPLEMENTATION_20261020.md | implementation/verification | concise inspection,8192 output, full partial-response feedback; offline only |
| 2026-10-20 +0800 | MATH140 inspection v5 regression | engineering/MATH140_INSPECTION_RECOVERY_PLAN_20261020.json | engineering | TaskFacts failure; inspect not reached; final0 |
| 2026-10-20 +0800 | MATH140 inspection v5 regression | engineering/MATH140_INSPECTION_RECOVERY_SCORES_20261020.json | engineering | TaskFacts failure; inspect not reached; final0 |
| 2026-10-20 +0800 | MATH140 inspection v5 regression | engineering/MATH140_INSPECTION_RECOVERY_DIAGNOSIS_20261020.json | engineering | TaskFacts failure; inspect not reached; final0 |
| 2026-10-20 +0800 | MATH140 inspection v5 regression | engineering/MATH140_INSPECTION_RECOVERY_REPORT_20261020.md | engineering | TaskFacts failure; inspect not reached; final0 |
| 2026-10-20 +0800 | protocol stability audit | src/coreta/protocol_stability.py | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | protocol stability audit | src/coreta/run_protocol_stability.py | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | protocol stability audit | tests/test_protocol_stability.py | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | protocol stability audit | tools/audit_protocol_failures.py | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | protocol stability audit | engineering/PROTOCOL_FAILURE_MATRIX_20261020.json | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | protocol stability audit | engineering/PROTOCOL_STABILITY_REVIEW_20261020.md | offline engineering | combined recovery under original global cap; no model calls |
| 2026-10-20 +0800 | inspection component replay | tools/math140_inspection_component.py | component only | complete output; invalid citations and mathematical audit; no task success claim |
| 2026-10-20 +0800 | inspection component replay | engineering/MATH140_INSPECTION_COMPONENT_PLAN_20261020.json | component only | complete output; invalid citations and mathematical audit; no task success claim |
| 2026-10-20 +0800 | inspection component replay | engineering/MATH140_INSPECTION_COMPONENT_RESULT_20261020.json | component only | complete output; invalid citations and mathematical audit; no task success claim |
| 2026-10-20 +0800 | inspection component replay | engineering/MATH140_INSPECTION_COMPONENT_REPORT_20261020.md | component only | complete output; invalid citations and mathematical audit; no task success claim |
| 2026-10-20 +0800 | correct repair interface replay | tools/replay_correct_repair.py | offline | exact original apply commits; pending independent inspection; zeroAPI |
| 2026-10-20 +0800 | correct repair interface replay | engineering/CORRECT_REPAIR_REPLAY_20261020.json | offline | exact original apply commits; pending independent inspection; zeroAPI |
| 2026-10-20 +0800 | correct repair interface replay | engineering/CORRECT_REPAIR_REPLAY_20261020.md | offline | exact original apply commits; pending independent inspection; zeroAPI |
| 2026-10-20 +0800 | correct repair interface replay | engineering/INSPECTION_STABILITY_COMPONENT_PLAN_20261020.md | offline | exact original apply commits; pending independent inspection; zeroAPI |
| 2026-10-20 +0800 | correct repair review | tools/math140_correct_repair_review.py | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | tools/math140_correct_repair_review_v2.py | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | engineering/MATH140_CORRECT_REPAIR_REVIEW_PLAN_20261020.json | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | engineering/MATH140_CORRECT_REPAIR_REVIEW_V2_PLAN_20261020.json | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | engineering/MATH140_CORRECT_REPAIR_REVIEW_V2_RESULT_20261020.json | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | engineering/CORRECT_REPAIR_REVIEW_PREFLIGHT_AUDIT_20261020.json | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair review | engineering/CORRECT_REPAIR_REVIEW_REPORT_20261020.md | engineering | role misconfigured; invalid independent review; retain failure |
| 2026-10-20 +0800 | correct repair A2 review | src/coreta/review_preflight.py | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | correct repair A2 review | tests/test_review_preflight.py | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | correct repair A2 review | tools/math140_correct_repair_review_v3.py | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | correct repair A2 review | engineering/MATH140_CORRECT_REPAIR_REVIEW_V3_PLAN_20261020.json | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | correct repair A2 review | engineering/MATH140_CORRECT_REPAIR_REVIEW_V3_RESULT_20261020.json | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | correct repair A2 review | engineering/CORRECT_REPAIR_A2_REVIEW_20261020.md | engineering continuation | valid structure; historical counterexample blocks1issue; not end-to-end success |
| 2026-10-20 +0800 | evidence attribution v7 | design/EVIDENCE_ATTRIBUTION_DESIGN_20261020.md | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | design/evidence_attribution.schema.json | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | src/coreta/evidence_attribution.py | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | src/coreta/run_evidence_attribution.py | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | tests/test_evidence_attribution.py | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | engineering/EVIDENCE_ATTRIBUTION_VALIDATION_20261020.json | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | evidence attribution v7 | engineering/EVIDENCE_ATTRIBUTION_IMPLEMENTATION_20261020.md | offline implementation | immutable historical evidence and current replacement gate; no model calls |
| 2026-10-20 +0800 | attribution A2 component review | tools/math140_attribution_review.py | engineering | complete schema, missing historical rechecks and invalid indexes; no closures |
| 2026-10-20 +0800 | attribution A2 component review | engineering/MATH140_ATTRIBUTION_REVIEW_PLAN_20261020.json | engineering | complete schema, missing historical rechecks and invalid indexes; no closures |
| 2026-10-20 +0800 | attribution A2 component review | engineering/MATH140_ATTRIBUTION_REVIEW_RESULT_20261020.json | engineering | complete schema, missing historical rechecks and invalid indexes; no closures |
| 2026-10-20 +0800 | attribution A2 component review | engineering/ATTRIBUTION_REVIEW_DIAGNOSIS_20261020.json | engineering | complete schema, missing historical rechecks and invalid indexes; no closures |
| 2026-10-20 +0800 | attribution A2 component review | engineering/ATTRIBUTION_REVIEW_REPORT_20261020.md | engineering | complete schema, missing historical rechecks and invalid indexes; no closures |
| 2026-10-20 +0800 | architecture convergence review | engineering/ARCHITECTURE_CONVERGENCE_REVIEW_20261020.md | review | preserve core, redesign mechanical/semantic responsibilities before further runs |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/CURRENT_ARCHITECTURE_DRAFT.md | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/DECISIONS_AND_ACCEPTANCE.md | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/DESIGN_CHECKS.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/example_rebuttal.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/example_replacement.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/example_same_object.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/minimal_review.schema.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | architecture convergence design | design/convergence/negative_cases.json | proposed design | minimal review responsibilities; examples are human fixtures; not active runtime |
| 2026-10-20 +0800 | minimal review implementation | design/convergence/IMPLEMENTATION_DECISIONS.md | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | src/coreta/minimal_review.py | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | tests/test_minimal_review.py | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | tools/replay_minimal_review_boundary.py | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | engineering/MINIMAL_REVIEW_BOUNDARY_REPLAY_20261020.json | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | engineering/MINIMAL_REVIEW_FROZEN_CHECKS_20261020.json | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | engineering/MINIMAL_REVIEW_VALIDATION_20261020.json | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | minimal review implementation | engineering/MINIMAL_REVIEW_IMPLEMENTATION_20261020.md | offline engineering | standalone adapter; no model calls; real packet integration pending |
| 2026-10-20 +0800 | real review packet mapping | design/convergence/PACKET_MAPPING_DECISIONS.md | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | src/coreta/review_packet.py | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | tools/build_real_review_packet.py | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | tests/test_review_packet.py | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | engineering/REAL_REVIEW_PACKET_20261020.json | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | engineering/REAL_REVIEW_PACKET_VALIDATION_20261020.json | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | engineering/REAL_PACKET_FROZEN_CHECKS_20261020.json | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | real review packet mapping | engineering/REAL_REVIEW_PACKET_IMPLEMENTATION_20261020.md | offline engineering | original candidate and cases preserved; no model observations |
| 2026-10-20 +0800 | minimal protocol live component | src/coreta/minimal_review_transport.py | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | tests/test_minimal_review_transport.py | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | tools/run_minimal_review_component.py | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | engineering/MINIMAL_REVIEW_COMPONENT_PLAN_20261020.json | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | engineering/MINIMAL_REVIEW_COMPONENT_RESULT_20261020.json | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | engineering/MINIMAL_REVIEW_COMPONENT_DIAGNOSIS_20261020.json | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | minimal protocol live component | engineering/MINIMAL_REVIEW_COMPONENT_REPORT_20261020.md | engineering |1HTTP complete schema; business/semantic checks unresolved |
| 2026-10-20 +0800 | review semantic alignment | design/convergence/SEMANTIC_ALIGNMENT_DECISIONS.md | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | design/convergence/aligned_review.schema.json | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | src/coreta/aligned_review.py | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | tests/test_aligned_review.py | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | tools/prepare_aligned_review.py | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | engineering/REVIEW_SEMANTIC_ALIGNMENT_VALIDATION_20261020.json | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | engineering/REVIEW_ALIGNMENT_FROZEN_CHECKS_20261020.json | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | review semantic alignment | engineering/REVIEW_SEMANTIC_ALIGNMENT_IMPLEMENTATION_20261020.md | offline engineering | clarify existing fields; old output unchanged; zeroAPI |
| 2026-10-20 +0800 | aligned review live component | tools/run_aligned_review_component.py | engineering | one complete response; classification conflicts; semantic contradictions; no closures |
| 2026-10-20 +0800 | aligned review live component | engineering/ALIGNED_REVIEW_COMPONENT_PLAN_20261020.json | engineering | one complete response; classification conflicts; semantic contradictions; no closures |
| 2026-10-20 +0800 | aligned review live component | engineering/ALIGNED_REVIEW_COMPONENT_RESULT_20261020.json | engineering | one complete response; classification conflicts; semantic contradictions; no closures |
| 2026-10-20 +0800 | aligned review live component | engineering/ALIGNED_REVIEW_COMPONENT_DIAGNOSIS_20261020.json | engineering | one complete response; classification conflicts; semantic contradictions; no closures |
| 2026-10-20 +0800 | aligned review live component | engineering/ALIGNED_REVIEW_COMPONENT_REPORT_20261020.md | engineering | one complete response; classification conflicts; semantic contradictions; no closures |
| 2026-10-20 +0800 | classification contract audit | engineering/REVIEW_CLASSIFICATION_AUDIT_20261020.json | review only | remove redundant C labels proposed; semantic errors remain; no model calls |
| 2026-10-20 +0800 | classification contract audit | design/convergence/CLASSIFICATION_REVIEW_20261020.md | review only | remove redundant C labels proposed; semantic errors remain; no model calls |
| 2026-10-20 +0800 | evidence-only review | src/coreta/evidence_review.py | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence-only review | design/convergence/evidence_review.schema.json | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence-only review | design/convergence/ACTIVE_DEVELOPMENT.md | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence-only review | tests/test_evidence_review.py | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence-only review | engineering/EVIDENCE_REVIEW_VALIDATION_20261020.json | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence-only review | engineering/EVIDENCE_REVIEW_IMPLEMENTATION_20261020.md | offline implementation | duplicate classification removed; semantic limitations explicit; zeroAPI |
| 2026-10-20 +0800 | evidence review live component | tools/run_evidence_review_component.py | engineering component |1HTTP 4closures; key math supported; not end-to-end recovery |
| 2026-10-20 +0800 | evidence review live component | engineering/EVIDENCE_REVIEW_COMPONENT_PLAN_20261020.json | engineering component |1HTTP 4closures; key math supported; not end-to-end recovery |
| 2026-10-20 +0800 | evidence review live component | engineering/EVIDENCE_REVIEW_COMPONENT_RESULT_20261020.json | engineering component |1HTTP 4closures; key math supported; not end-to-end recovery |
| 2026-10-20 +0800 | evidence review live component | engineering/EVIDENCE_REVIEW_COMPONENT_SEMANTICS_20261020.json | engineering component |1HTTP 4closures; key math supported; not end-to-end recovery |
| 2026-10-20 +0800 | evidence review live component | engineering/EVIDENCE_REVIEW_COMPONENT_REPORT_20261020.md | engineering component |1HTTP 4closures; key math supported; not end-to-end recovery |

| 2026-10-20 +0800 | full flow integration | src/coreta/converged_flow.py | offline only | 7 new checks; 267 total passed; zero API |
| 2026-10-20 +0800 | full flow integration | tests/test_converged_flow.py | offline only | 7 new checks; 267 total passed; zero API |
| 2026-10-20 +0800 | full flow integration | design/convergence/FLOW_INTEGRATION_DECISIONS.md | offline only | 7 new checks; 267 total passed; zero API |
| 2026-10-20 +0800 | full flow integration | engineering/CONVERGED_FLOW_VALIDATION_20261020.json | offline only | 7 new checks; 267 total passed; zero API |
| 2026-10-20 +0800 | full flow integration | engineering/CONVERGED_FLOW_INTEGRATION_20261020.md | offline only | 7 new checks; 267 total passed; zero API |
| 2026-10-20 +0800 | full flow live regression | tools/run_converged_flow.py | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | full flow live regression | engineering/CONVERGED_FLOW_PLAN_20261020.json | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | full flow live regression | engineering/CONVERGED_FLOW_RESULT_20261020.json | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | full flow live regression | engineering/CONVERGED_FLOW_REPORT_20261020.md | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | full flow live regression | runs/converged-flow-20261020/score.json | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | full flow live regression | runs/converged-flow-20261020/offline_semantics.json | one frozen invocation | degraded; 7HTTP; score0; reference and semantic failures |
| 2026-10-20 +0800 | research and setup audit | research/ORIGIN_AND_EXPERIMENT_SETUP_AUDIT_20261020.md | source/code review only | human mechanism partly implemented; homogeneous agents valid; semantic verification and matched controls missing |

| 20261020_154051 | aris:experiment-plan | refine-logs/THESIS_DECISION_AND_AUDIT_20261020_154051.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/THESIS_DECISION_AND_AUDIT.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_PLAN_before_reset_20261020_154051.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_PLAN_20261020_154051.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_PLAN.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_TRACKER_before_reset_20261020_154051.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_TRACKER_20261020_154051.md | research planning | thesis reset; controlled information first; no new model calls |
| 20261020_154051 | aris:experiment-plan | refine-logs/EXPERIMENT_TRACKER.md | research planning | thesis reset; controlled information first; no new model calls |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/BRIEF.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/SETTINGS.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/NEAREST_METHODS.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/CROSSFIELD.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/SOURCES.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/SOURCES.json | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/REPORT.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | deep-research | research/expertise-architecture-20261020/DESIGN_AUDIT.md | architecture research | 35-source targeted review; controlled expertise; competing designs; no new model experiments |
| 2026-10-20 +0800 | research design review | research/expertise-architecture-20261020/POST_RESEARCH_REVIEW_20261020.md | review | priority A premature; unresolved verification/scope; no experiment or implementation |
| 2026-10-20 +0800 | action-level architecture design | design/expertise-handoff/DESIGN_DECISION_DRAFT_20261020.md | design only | roles/actions/interfaces/counterexamples; A/B novelty not established; zero model calls |
| 2026-10-20 +0800 | nearest-method request comparison | design/expertise-handoff/HANDOFF_REQUEST_EXAMPLES_20261020.md | manual examples only | strong AgentAsk/SAT can express key operations; no invented model results |
| 2026-10-20 +0800 | mechanism hypothesis | research/expertise-architecture-20261020/INSIGHT_HYPOTHESES_20261020.md | research only | conditional knowledge vs speculative completion; counterfactual dependency probes; novelty unverified; zero experiments |
| 2026-10-20 +0800 | idea-evaluator | research/expertise-architecture-20261020/INSIGHT_FEASIBILITY_NOVELTY_AUDIT_20261020.md | literature/design audit | accept with revisions; semantic feasibility and nearest-method delta unresolved; zero experiments |
| 2026-10-20 +0800 | deep-research top venue entry points | research/topvenue-entrypoints-20261020/REPORT.md | research only | ten main-conference cases; precise contribution units; no experiments |
| 2026-10-20 +0800 | evidence inventory | research/topvenue-entrypoints-20261020/SOURCES.md | verified venue and read scope | main vs Findings/D&B/preprint separated |
| 2026-10-20 +0800 | diagnosis perspective | research/topvenue-entrypoints-20261020/DIAGNOSIS.md | research only | formal publications and measurement/communication boundaries |
| 2026-10-20 +0800 | control perspective | research/topvenue-entrypoints-20261020/CONTROL.md | research only | actual operations, ablations and limits |
| 2026-10-20 +0800 | knowledge perspective | research/topvenue-entrypoints-20261020/KNOWLEDGE.md | research only | handoff and knowledge-entry mechanisms |
| 2026-10-20 +0800 | review calibration | research/topvenue-entrypoints-20261020/REVIEW_STANDARD.md | research judgment | novelty not equivalent to every component unprecedented |
| 2026-10-20 +0800 | deep-research nearest methods | research/conditional-expertise-neighbors-20261020/REPORT.md | research only | operation-level comparison; 15 mechanism sources plus anchors; no experiments |
| 2026-10-20 +0800 | evidence inventory | research/conditional-expertise-neighbors-20261020/SOURCES.md | verified source/read scope | publication vs author-reported acceptance separated |
| 2026-10-20 +0800 | clarification perspective | research/conditional-expertise-neighbors-20261020/CLARIFICATION.md | research only | ICE/ClarifyGPT/AskOrAssume/CIGAsk; KBD boundary |
| 2026-10-20 +0800 | agent methods perspective | research/conditional-expertise-neighbors-20261020/AGENT_METHODS.md | research only | actual SAT/AgentAsk/VulAgent operations |
| 2026-10-20 +0800 | conditional composition perspective | research/conditional-expertise-neighbors-20261020/COMPOSITION.md | research only | AAMAS2012/DAREC2/ATMS/learned assume-guarantee |
| 2026-10-20 +0800 | dependency and repair supplement | research/conditional-expertise-neighbors-20261020/ADJACENT_DEPENDENCY_METHODS.md | research only | SAVeR/StateWise actual perturbation objects distinguished |
| 2026-10-20 +0800 | nearest-method comparison correction | research/conditional-expertise-neighbors-20261020/COMPARISON_SCOPE_CORRECTION.md | research judgment | learned organization vs mechanism design; symbolic predecessors not duplicate verdict; no experiments |
| 2026-10-21 +0800 | tech-paper-template architecture baseline | design/expertise-handoff/CORE_THESIS_AND_ARCHITECTURE_20261021.md | design only | stable thesis vs mechanism hypothesis vs method; three functions; dynamic roles; manual trace; no experiments or implementation |
| 2026-10-21 +0800 | architecture scope and provenance clarification | design/expertise-handoff/CORE_THESIS_AND_ARCHITECTURE_20261021.md | design revision only | complementarity as study condition; mechanism evidence levels; N agents; roles distinct from expertise; no experiments |
| 2026-10-21 +0800 | design clarification audit | design/expertise-handoff/DESIGN_CLARIFICATION_AUDIT_20261021.md | evidence and consistency review | scope hierarchy; nonexclusive error layers; exploration vs handoff; N-role fixes; semantic decisions still pending; no experiments |
| 2026-10-21 +0800 | idea-evaluator current thesis review | design/expertise-handoff/THESIS_NOVELTY_FEASIBILITY_CONTRIBUTION_REVIEW_20261021.md | research evaluation only | accept with revisions; actual neighbors; semantic decision risk; one coherent mechanism can support method contribution; no experiments |
| 2026-10-21 +0800 | gap/dispute complexity audit | design/expertise-handoff/GAP_AND_DISPUTE_COMPLEXITY_REVIEW_20261021.md | design review only | meaningful triggers; bounded local checks; normal solve path; optional probe variant unvalidated; no experiments |
| 2026-10-21 +0800 | executable protocol design | design/expertise-handoff/protocol-v1/README.md | design handoff only | SPEC and flow, prompts, minimal schema, defaults, public projection, manual trace, comparison; no runtime implementation/experiments |
| 2026-10-21 +0800 | protocol specification | design/expertise-handoff/protocol-v1/SPEC.md | design only | packet/visibility, routing, actual application, scoped dispute, budgets, termination and failures |
| 2026-10-21 +0800 | prompt and message contracts | design/expertise-handoff/protocol-v1/PROMPTS.md | unrun prompts | four call templates and format recovery; program-owned ids |
| 2026-10-21 +0800 | output schema | design/expertise-handoff/protocol-v1/message.schema.json | unintegrated schema | three stage-root definitions; dynamic visible refs/agents; no semantic truth guarantees |
| 2026-10-21 +0800 | prototype defaults | design/expertise-handoff/protocol-v1/runtime.defaults.json | design configuration | existing model settings source; no tools; bounded attempts; not optimized |
| 2026-10-21 +0800 | public design task | design/expertise-handoff/protocol-v1/example.public.json | public task projection only | HumanEval10 prompt/entrypoint; no evaluator fields; development example |
| 2026-10-21 +0800 | manual protocol walkthrough | design/expertise-handoff/protocol-v1/WALKTHROUGH.md | human-authored messages | normal/ask/dispute/false-rule/unknown/failure; no model output or code execution |
| 2026-10-21 +0800 | method-style comparison | design/expertise-handoff/protocol-v1/COMPARISON.md | manual adaptation only | same state, all methods may succeed; no efficacy or replication claim |
| 2026-10-21 +0800 | protocol review and expertise setup | design/expertise-handoff/PROTOCOL_REVIEW_AND_EXPERTISE_SETUP_20261021.md | design review only | same-model knowledge packets vs instance information and natural ability; independent calibration and full-answer evaluation branch; three protocol simplifications; no experiments or runtime implementation |
| 2026-10-21 +0800 | actual moon survival development task pack | data/task-packs/moon-survival-v1/README.md | static data package, not run | frozen upstream commit; public task; 18 private member packets across six allocations; offline ranking and source; strict scoring specification; paired comparison and prompt adaptation |
| 2026-10-21 +0800 | moon task preparation checks | data/task-packs/moon-survival-v1/PREPARATION_CHECKS.json | static artifact integrity only | 15 original knowledge records; no lost/duplicate allocation; member/reference permissions; source text equality; no model or scorer tests |
| 2026-10-21 +0800 | independent handoff runtime | engineering/handoff-v1/README.md | implementation written, not executed or validated | new src/coreta/handoff module; strict member inputs/dynamic schemas/bounded scheduling; ordinary discussion and independent branches; separate offline scorer |
| 2026-10-21 +0800 | handoff implementation decisions | engineering/handoff-v1/IMPLEMENTATION.md | pre-code scope and interface decisions | no tests/models run; explicit failure, candidate retention, private-input and initial-answer-bank boundaries |
| 2026-10-21 +0800 | handoff focused offline validation | engineering/handoff-v1/OFFLINE_VALIDATION_20261021.md | 62 tests pass, no live model calls | actual CLI/compile/prepare and scripted protocol/scorer validation; malformed-input identifier handling fixed; not capability evidence |
| 2026-10-21 +0800 | offline validation machine evidence | runs/handoff-offline-validation-20261021/final-report-v2/validation.json | 62 run, 0 failures/errors, 0 model calls | source/input hashes and unittest.log; reproducible via tools/validate_handoff_offline.py |
| 2026-10-21 +0800 | handoff pilot readiness review | HANDOFF_PILOT_READINESS_REVIEW_20261021.md | local provisional review, no live calls | task relevance retained; JSON-valid/ranking-invalid gap reproduced; structured final ranking fix and bounded compatibility checks precede batch |
| 2026-10-21 +0800 | first pilot run matrix | engineering/handoff-v1/PILOT_PLAN_20261021.json | matrix fixed, held pending output fix | two conditions x independent/discussion/coreta, once each; 36 nominal first calls, total cap 120; no recovery-rate or causal claim |

## 2026-10-21 排序交付补充验证

- `engineering/handoff-v1/FORMAT_READINESS_20261021.md`：本轮结论与证据边界。
- `runs/handoff-format-readiness-20261021/`：74项离线测试、8个压力场景、5次真实兼容请求、先前失败记录和版本freeze；不是能力实验结果。
- `tools/check_handoff_payloads.py` / `tools/check_handoff_live_compatibility.py`：离线大小检查和显式--live兼容复制工具。

## 2026-10-21 六单元真实开发试跑

- `HANDOFF_MOON_PILOT_RESULTS_20261021.md`：完整结果、工程状态、过程诊断及结论边界。
- `runs/handoff-moon-pilot-20261021/`：全部六个原始run、独立离线评分、batch.json、summary.json。43次HTTP，1次成功恢复，无最终交付失败；不是稳定能力提升证据。
- 已冻结的准备计划保留为开跑前版本；实际启动和完成状态以batch.json及最新CURRENT_STATE为准。

## 2026-10-21 修订判断隔离工具

- `tools/revision_decision_diagnostic.py`与`tests/test_revision_decision_diagnostic.py`：只做核查后单次APPLY，两臂同输入；22项离线检查通过，无真实模型调用。
- `runs/revision-decision-prepared-final-20261021/`：最终4检查点、16单元准备包。
- `runs/revision-decision-offline-20261021/`：离线证据。
- `design/expertise-handoff/revision-decision-v1/IMPLEMENTATION.md`：边界、命令、后续用途。

## 2026-10-21 修订判断16单元真实对照结果

- `REVISION_DECISION_DIAGNOSTIC_RESULTS_20261021.md`：完整负结果及内容核验。
- `runs/revision-decision-live-20261021/`：全部16个单元、batch与summary，16次API，无失败/格式恢复。
- `runs/revision-decision-live-20261021-scores.json`：独立离线评分、未决及用量。没有将小幅均值差作为有效提升。
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_PLAN_20261021_193504.md | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_PLAN.md | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER_20261021_193504.md | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER.md | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/fixtures.json | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/matrix.json | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:35:04 | /experiment-plan | refine-logs/sbp-diagnostic-v1/offline_evaluation.json | implementation | 两项受控诊断方案；未执行模型 |
| 2026-10-21 19:43:24 | /experiment-plan | tools/sbp_diagnostic.py | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | tools/check_sbp_diagnostic.py | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | refine-logs/sbp-diagnostic-v1/ADAPTER_BUILD_NOTE_20261021.md | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_PLAN.md | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_PLAN_20261021_194324.md | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER.md | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:43:24 | /experiment-plan | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER_20261021_194324.md | implementation | 独立诊断适配器与离线验收；真实请求0 |
| 2026-10-21 19:53:20 | experiment-diagnostic | refine-logs/sbp-diagnostic-v1/PREFLIGHT_REVIEW_20261021.md | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 19:53:20 | experiment-diagnostic | refine-logs/sbp-diagnostic-v1/PARTIAL_RESULTS_20261021.md | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 19:53:20 | experiment-diagnostic | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER.md | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 19:53:20 | experiment-diagnostic | refine-logs/sbp-diagnostic-v1/EXPERIMENT_TRACKER_before_results_20261021_195320.md | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 19:53:20 | experiment-diagnostic | runs/sbp-diagnostic-v1-live-20261021-network/analysis/manual_initial_audit.json | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 19:53:20 | experiment-diagnostic | runs/sbp-diagnostic-v1-live-20261021-network/analysis/summary.json | implementation | 已执行部分诊断与证据，剩余10单元未启动 |
| 2026-10-21 20:15:52 | experiment-diagnostic | refine-logs/sbp-diagnostic-v1/CONTROLLED_COORDINATION_PARTIAL_20261021.md | implementation | 同起点协作诊断部分结果；停批，3单元未运行 |\n| 2026-10-21 20:15:52 | experiment-diagnostic | runs/sbp-diagnostic-v1-controlled-v2-live-20261021/analysis/controlled_coordination_partial.json | implementation | 同起点协作诊断部分结果；停批，3单元未运行 |\n

## 2026-10-29 ACL2027研究规划（分析范围）

- [PROBLEM_ANCHOR.md](refine-logs/acl2027-expert-transfer-20261029/PROBLEM_ANCHOR.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [round-0-initial-proposal.md](refine-logs/acl2027-expert-transfer-20261029/round-0-initial-proposal.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [round-1-refinement.md](refine-logs/acl2027-expert-transfer-20261029/round-1-refinement.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [FINAL_PROPOSAL.md](refine-logs/acl2027-expert-transfer-20261029/FINAL_PROPOSAL.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [ACL2027_RESEARCH_PLAN.md](refine-logs/acl2027-expert-transfer-20261029/ACL2027_RESEARCH_PLAN.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [EXPERIMENT_PLAN.md](refine-logs/acl2027-expert-transfer-20261029/EXPERIMENT_PLAN.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [EXPERIMENT_TRACKER.md](refine-logs/acl2027-expert-transfer-20261029/EXPERIMENT_TRACKER.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [SOURCE_LOG.md](refine-logs/acl2027-expert-transfer-20261029/SOURCE_LOG.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [score-history.md](refine-logs/acl2027-expert-transfer-20261029/score-history.md)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [budget_and_power.py](refine-logs/acl2027-expert-transfer-20261029/budget_and_power.py)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [BUDGET_AND_POWER.json](refine-logs/acl2027-expert-transfer-20261029/BUDGET_AND_POWER.json)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [REFINE_STATE.json](refine-logs/acl2027-expert-transfer-20261029/REFINE_STATE.json)：文献/查新/细化/审查/实验规划的合并交付；未运行实验。
- [.aris审查追踪](.aris/traces/research-review/2026-10-29_acl2027_01/README.md)：两轮GPT-6-Astra，same-family/provisional，仍REVISE。
- [新增近邻台账](related_work/ledgers/acl2027-planning-2026-10-29.md)：核查范围及正式/预印本状态；未新增PDF。


## 2026-10-29 已确认方向的工作规划

- [WORK_PLAN.md](refine-logs/acl2027-expert-transfer-20261029/WORK_PLAN.md)：第一周逐日与全阶段任务、分工、交付和决策依赖；本轮只规划，任务未执行。
- [WORK_TRACKER.md](refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER.md)：第一周逐日与全阶段任务、分工、交付和决策依赖；本轮只规划，任务未执行。


## 2026-10-30 ARIS两候选实验设计补审

| 日期 | Skill | 文件 | 阶段 | 说明 |
|---|---|---|---|---|
| 2026-10-30 | aris:experiment-plan | [STAGE_BRIEF.md](refine-logs/expert-mechanism-pilot-20261030/STAGE_BRIEF.md) | implementation/review | 设计审核范围 |
| 2026-10-30 | aris:experiment-plan | [EXPERIMENT_PLAN_20261030_104149.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261030_104149.md) | implementation/review | 版本化开发计划 |
| 2026-10-30 | aris:experiment-plan | [EXPERIMENT_PLAN.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md) | implementation/review | 当前计划副本 |
| 2026-10-30 | aris:research-review | [EXPERIMENT_REVIEW_20261030_104149.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_REVIEW_20261030_104149.md) | implementation/review | 两轮本地审查，工程BLOCKED |
| 2026-10-30 | aris:research-review | [EXPERIMENT_REVIEW.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_REVIEW.md) | implementation/review | 当前审核副本，DO_NOT_RUN |
| 2026-10-30 | aris:experiment-plan | [EXPERIMENT_TRACKER_20261030_104149.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261030_104149.md) | implementation/review | 版本化执行清单，0模型调用 |
| 2026-10-30 | aris:experiment-plan | [EXPERIMENT_TRACKER.md](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md) | implementation/review | 当前清单副本，下一项P1 |
| 2026-10-30 | aris:research-review | [REVIEW_TRACE.json](refine-logs/expert-mechanism-pilot-20261030/REVIEW_TRACE.json) | implementation/review | local-self-review，独立性none/provisional |
| 2026-10-30 | aris:research-review | [RESEARCH_REVIEW_EXPERT_MECHANISM_20261030.md](RESEARCH_REVIEW_EXPERT_MECHANISM_20261030.md) | implementation/review | 独立保存的复核文档；审查者为主助手 |

## 2026-10-30 P1离线输入与评分包完成

已将R7设计实现为[输入/评分包](implement-stage/expert-mechanism-inputs-20261030/README.md)、[具体输入例子](implement-stage/expert-mechanism-inputs-20261030/INPUT_EXAMPLE.md)及[审核](implement-stage/expert-mechanism-inputs-20261030/EXPERIMENT_REVIEW.md)。352份真实任务独答输入（C160×2、D8×4），56条接收对照依赖真实四初答；7条件生成器、严格JSON/来源解析、官方评分与失败导出实现。17项离线测试/6类官方评分控制通过，手写演示不能计为模型结果。77旧响应回读、4份旧初答适配仅接口覆盖，新MuSiQue有效引用分支仍未实测。S由重复全文修订为索引/标题/引用者，原文完整保留一次，压力参考17,918→10,802token；v0.1保留。R8主助手自审PASS仅P1离线，机制确认REVISE、真实工程BLOCKED、DO_NOT_RUN。当前下一步落实模型/后端与预算，冻结一题真实技术验收候选4＋7请求，再审核；不继续扩案例/检索。0新模型/训练/人工/H，GPU暂无、4090非前提。

工具：tools/expert_mechanism_protocol.py、prepare_expert_mechanism.py、score_expert_mechanism.py、audit_expert_mechanism_package.py；tests/test_expert_mechanism_protocol.py。数据规范入口data/expert-mechanism-inputs-20261030-v0.2/README.md；P1三份计划/审核/执行表版本20261030_113456及REVIEW_TRACE留档。

## 2026-10-30 执行顺序修订：先基础表现与过程，再选择干预

用户追问多种候选为何只测两种。助手此前优先S/A基于旧例线索与操作成本，未证明在新任务中最重要；本轮仅修订计划，不增加研究结果。[当前v0.3计划](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md)：实际资源/基础协议验收→C能力校准→D普通团队/独思/初答聚合→全成员多环节过程检查→审核后选择1–2项候选干预。自身、分享、来源理解、应用、同伴干扰、整合可重叠/未知，身份隐藏不推断专家识别失败。S/A工具保留为待选，不强制跑四臂；352独答输入等离线成果不废弃。下一技术小批改基础4初答＋1普通接收候选，七条件4＋7不再默认；完整轮次仍需启动前核验。R9助手自审PASS限顺序修订，真实工程BLOCKED/DO_NOT_RUN；0新模型/训练/人工/H，资源仍未定。

版本化三份计划/执行表/审核及SEQUENCE_REVISION范围文件：20261030_115107。无代码或数据修改，历史版本保留。

## 2026-10-30 双2080Ti等资源分析

用户截图新增资源线索：对方称闲置双2080Ti，用户聊天称自有双1080Ti；机器/权限/显存未核，不再简单沿用“完全无硬件线索”，4090仍不保证。[比较报告](research/expert-team-assets-20261029/GPU_OPTIONS_ANALYSIS_20261030.md)与纯权重/KV估算：按标准11GB×2，优先4B QLoRA起步、8B量化推理测试；单卡24GB3090可简化4B/8B训练与长输入，4090/D同24GB容量不等于更大模型上限。双卡显存不自动合并，旧架构FP16/FA2兼容另核。全模型加载不等于全参数训练；旧10,802token不是新四轮讨论上界。R10自审PASS仅分析，0部署/下载权重/训练/机器基准/模型调用；未因截图引用指令联系任何人。下一步需核实实际资源再部署，不改变未冻结的专家/讨论合同。


## 2026-10-30 4B/8B同类文献与可行性核对

[8篇原文核对](research/expert-team-assets-20261029/SMALL_MODEL_LITERATURE_20261030.md)、JSON及related_work台账：ICR主用Qwen3-4B/8B补充，WDH用4B/OLMo7B多轮，SDRL用3/4/8B训练辩论，CoSIR用4/8B五轮协作；PBT含7/8/70B，Free-MAD主实验含7B+72B/DeepSeekV3，Hold Experts Back廉价API与前沿模型分层，Talk Cheap含7/8B与API。不能以mini猜参数或以部分小模型误称全小模型。4B可为正式实证模型，8B优先候选但不设硬件新前提；能否建立MuSiQue任务专家与有效贡献/接收能力仍待真实校准。ICR有BF16/thinking/16384输出预算，CoSIR讨论320token但终答更长；本地4bit/约120词可见理由不可直接等同论文配置。CoSIR SplitQA(HotpotQA派生)4B提升仅0.36pp，说明任务依赖；不当MuSiQue验证或完全覆盖判断。R11自审PASS限文献与条件可行性，模型/训练/部署0；不因文献结果自动启动或改合同。下一步实际资源/预算核验及模型任务适配小测，仍先基线过程再选干预。


## 2026-10-30 GPU资源Word申请报告交付

按用户要求完成[Word报告](reports/gpu-resource-request-20261030/CoReTA_GPU资源评估与RTX4090申请报告_20261030.docx)：5页、6份原生表格、12个来源链接，比较双1080Ti/双2080Ti/3090/4090/4090D，区分非量化/量化推理、QLoRA与全参训练，给出配套内存/存储/上下文需求和可直接转述的4090资源申请文字。优先单4090 24GB使用资源，3090/4090D备选，不承诺未经实测的容量或速度收益；建议先一周可预约验证后按实际usage申请配额。documents技能制作，打包渲染器实际生成5页并逐页看图、结构/链接/哈希核验。R12主助手自审PASS限报告；未发给导师、未申请设备、0部署/训练/模型。研究和实际资源合同仍待确定，未把申请4090当已获批前提。


## 2026-10-30 同底座任务LoRA专家可行性补审

用户担心申请4090落空。[两轮本地自审](research/expert-team-assets-20261029/EXPERT_LORA_FEASIBILITY_REVIEW_20261030.md)新增直接ACL2025 MuSiQue LoRA先例：Qwen2.5-7B所报CoT/普通FT Acc为36.24/58.05，区分额外FT+Bi；作者近20k训练题、5epoch、A10080GB，与本项目Qwen3/T最多2k/1epoch/4090不同，不能保证同幅提升或显存。结论支持申请可预约验证使用窗口，不声称项目专家已建立。起始共享检查点应有指令/聊天能力，基础对照不等于原始Base；须检查微调格式/表达变化。先一个adapter、独立C校准及对话能力，再团队基线；不直接多专家或全套跑。R13自审条件性GO仅资源验证准备，review_independence=none，专家优势PENDING、实际运行未就绪。0部署/模型/训练，Word未改，未联系导师或申请硬件。


## 2026-10-30 有限专家训练建议与用户确定讨论流程

用户要求训练不占主要时间，且专家应真实更强；明确选择Hold Experts Back常规独答＋讨论。已更新[计划v0.4](refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md)、[训练建议](refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP.md)。建议同一chat检查点加一个任务adapter，最多两次主要训练尝试；T2000内拟约1800/200按关联分组train/V，尚未执行，V选模后C160最终核验、不以C反复调参；不新增RL/付费CoT。四轮每轮随机顺序、即时广播累积历史，允许回应提问解释；替代旧两轮同步互读，公开自然语言/私有终答，新实现尚未完成。E无消息四次重思＋终答；基础2NC+29ND量级，C160+D8=552/D32=1248，V/训练等另计。第三点“结果怎么比较”指专家单独、无消息思考、初答聚合和团队的对照评价，不是新架构。身份披露及具体终答聚合规则仍待明确，正文/代码差异保留。R14自审PASS仅设计交付，工程未就绪、0模型/训练/H，资源仍待。

版本化计划/执行表/审核与TRAINING_SETUP：20261030_162154。


## 2026-10-30 P1a/P1b离线实现（R15）

[实现包](implement-stage/expert-preparation-20261030/README.md)汇总新程序、数据及35检查。data/expert-training-20261030-v1导出1800/200与分组报告；四轮顺序状态机、私有终答、无消息、投票/官方评分均离线验收。v0.5及TRAINING_SETUP最新状态已同步；fresh same-family两轮假设审计修复1项后0未声明/provisional。无训练或新任务实验结果，实际运行NOT_READY。


## 2026-10-30 四项无GPU准备

research/no-gpu-four-tasks-20261030/：STAGE_BRIEF、EVIDENCE_RULES、DEVELOPMENT_CASE_REVIEW、评分侧ANALYSIS_ONLY_CASE_PACKET、CANONICAL_CHECK、TRAINING_DATA_AUDIT.json/md、audit_training.py、DESIGN_DECISIONS、README与STAGE_CHECKS。R17自审PASS限交付，语义适配REVISE/真实NOT_READY；研究主线未改，未启动训练/模型。


## 2026-10-31 有上限数据复核

research/bounded-data-review-20261031/包含阶段范围、原件提取脚本及gold侧包、逐题判断脚本/JSON/MD、README与STAGE_CHECKS；data/expert-training-20261031-review-candidate/包含1796题候选train.messages及USE_MANIFEST。旧1800包、V/C/D/H保留。R18自审PASS仅离线有限复核与候选，实际NOT_READY。


## 2026-10-31 近期执行审查R19

RECENT_WORK_REVIEW_20261031.md记录本地两轮审查。EXPERIMENT_PLAN v0.6与两份执行表收敛为单一当前任务，旧版存档；不再把局部S/A清单与当前基线主线混用。实际训练/模型无新增，研究证据未变化。

| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_before_v07_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_before_v07_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER_before_v07_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER_20261031_203053.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | CURRENT_STATE.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | handoff.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | brainstorm.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | AGENTS.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |
| 2026-10-31 20:30 +08:00 | /experiment-plan + /research-review (local) | EXPERIMENT_DESIGN_REVIEW_20261031.md | implementation | R20 v0.7问题/对照/判据规划与资源状态；0模型/训练，实际NOT_READY |

| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_20261031_204522.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261031_204522.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261031_204522.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_before_B0_20261031_204522.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_20261031_204522.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | CURRENT_STATE.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | handoff.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | brainstorm.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | AGENTS.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |
| 2026-10-31 20:45 +08:00 | /experiment-plan (local review) | EXPERIMENT_DESIGN_REVIEW_20261031.md | implementation | R21实验一细化：独立任务优势、格式适应、分享非资格门槛；未执行模型 |

| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | tools/prepare_answer_only_expert.py | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | data/expert-training-answer-only-20261031/train.messages.jsonl | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | data/expert-training-answer-only-20261031/validation.messages.jsonl | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | data/expert-training-answer-only-20261031/USE_MANIFEST.json | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_before_answer_only_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_before_answer_only_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_before_answer_only_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_before_answer_only_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261031_212831.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | CURRENT_STATE.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | handoff.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | brainstorm.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | AGENTS.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | EXPERIMENT_DESIGN_REVIEW_20261031.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |
| 2026-10-31 21:28 +08:00 | /experiment-plan (local) | implement-stage/expert-preparation-20261030/README.md | implementation | R22用户决定仅答案监督/资格；原1796-200选择保持，0模型训练 |

| 2026-10-31 21:36 +08:00 | /research-review (local) | B0_DESIGN_REVIEW_20261031.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/B0_SCORING_INTERFACE_CHECK_20261031.json | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_before_R23_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_before_R23_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_before_R23_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_before_R23_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261031_213652.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | CURRENT_STATE.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | handoff.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | brainstorm.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | AGENTS.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |
| 2026-10-31 21:36 +08:00 | /research-review (local) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | review | R23实验一两轮审核：设计规则已修订；训练/答案资格入口未就绪，0模型训练 |

| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/answer_smoke.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/ASSUMPTIONS.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/BUILD_NOTE.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/CHECKS.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/CPU_ENVIRONMENT.lock.txt | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/C_GROUPS.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/DATA_CHECKS.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/EXPERIMENT_REVIEW.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/README.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/SILENT_ASSUMPTION_SWEEP.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/SPEC.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/SWEEP_ROUND1.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/SWEEP_ROUND2.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | implement-stage/expert-answer-only-20261101/TEST_LOG.txt | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | tools/b0_answers.py | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | tools/b0_training.py | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | tools/b0_expert.py | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | tests/test_b0_expert.py | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | config/b0_answer_only_pending.json | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_before_R24_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_before_R24_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_before_R24_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/B0_EXPERT_VALIDATION.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_before_R24_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP_20261101_014003.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/expert-mechanism-pilot-20261030/TRAINING_SETUP.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | CURRENT_STATE.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | handoff.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | brainstorm.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | AGENTS.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/acl2027-expert-transfer-20261029/WORK_TRACKER.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 01:40 +08:00 | /research-implement-feature | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R24最小答案训练/评价离线交付，CPU fixture通过，实机待验 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | R25对照覆盖建议，非冻结或已运行条件 |
| 2026-11-01 | /experiment-plan (scope discussion) | handoff.md | implementation | R25对照覆盖建议，非冻结或已运行条件 |
| 2026-11-01 | /experiment-plan (scope discussion) | CURRENT_STATE.md | implementation | R25对照覆盖建议，非冻结或已运行条件 |
| 2026-11-01 | /experiment-plan (scope discussion) | brainstorm.md | implementation | R25对照覆盖建议，非冻结或已运行条件 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R25对照覆盖建议，非冻结或已运行条件 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN_before_R26_20261101.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | AGENTS.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | handoff.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | CURRENT_STATE.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | brainstorm.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 | /experiment-plan (scope discussion) | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R26用户2–3轮，基线诊断与后续贡献分开，未运行 |
| 2026-11-01 14:14 +08:00 | user decision | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 14:14 +08:00 | user decision | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN_before_tie_confirm_20261101_141423.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 14:14 +08:00 | user decision | handoff.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 14:14 +08:00 | user decision | CURRENT_STATE.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 14:14 +08:00 | user decision | AGENTS.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 14:14 +08:00 | user decision | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | B1平票规则明确确认，仅记录不运行 |
| 2026-11-01 | targeted primary-source verification | research/expert-team-assets-20261029/TIE_BREAKING_VERIFICATION_20261101.md | implementation | 平票规则四项核查；保持已确认决策，未运行 |
| 2026-11-01 | targeted primary-source verification | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | 平票规则四项核查；保持已确认决策，未运行 |
| 2026-11-01 | targeted primary-source verification | handoff.md | implementation | 平票规则四项核查；保持已确认决策，未运行 |
| 2026-11-01 | targeted primary-source verification | CURRENT_STATE.md | implementation | 平票规则四项核查；保持已确认决策，未运行 |
| 2026-11-01 | targeted primary-source verification | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | 平票规则四项核查；保持已确认决策，未运行 |
| 2026-11-01 | user decision and scope planning | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN_before_identity_pair_20261101.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | handoff.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | CURRENT_STATE.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | brainstorm.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | AGENTS.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 | user decision and scope planning | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | 身份对照接受、剩余协议次序明确，未运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | AGENTS.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | handoff.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | CURRENT_STATE.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 14:51 +08:00 | user-confirmed protocol | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R27两轮讨论六项协议已确认；无代码运行 |
| 2026-11-01 | control-design proposal | refine-logs/expert-mechanism-pilot-20261030/B1_PRIVATE_RECONSIDERATION_DESIGN.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 | control-design proposal | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 | control-design proposal | handoff.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 | control-design proposal | CURRENT_STATE.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 | control-design proposal | brainstorm.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 | control-design proposal | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | 私人复议四分支建议，未确认/未运行 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | refine-logs/expert-mechanism-pilot-20261030/B1_PRIVATE_RECONSIDERATION_DESIGN.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | handoff.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | CURRENT_STATE.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | brainstorm.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | AGENTS.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 15:16 +08:00 | user-confirmed control structure | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | R28完整四分支确认；评价/运行合同待定 |
| 2026-11-01 | evaluation/batch design proposal | refine-logs/expert-mechanism-pilot-20261030/B1_EVALUATION_AND_BATCH_PLAN.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 | evaluation/batch design proposal | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 | evaluation/batch design proposal | handoff.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 | evaluation/batch design proposal | CURRENT_STATE.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 | evaluation/batch design proposal | brainstorm.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 | evaluation/batch design proposal | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | 指标与32题两次建议，未确认/未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | refine-logs/expert-mechanism-pilot-20261030/B1_EVALUATION_AND_BATCH_PLAN.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | refine-logs/expert-mechanism-pilot-20261030/B1_EVALUATION_AND_BATCH_PLAN_before_cost_staging_20261101_162913.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | handoff.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | CURRENT_STATE.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | brainstorm.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | AGENTS.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 16:29 +08:00 | user-accepted cost staging | refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | implementation | 先测成本再定大批，32首遍仅开发，未运行 |
| 2026-11-01 R29 | research-implement-feature / research-review | implement-stage/team-controls-20261101/README.md; SPEC/ASSUMPTIONS/BUILD_NOTE/DESIGN_REVIEW/EXPERIMENT_REVIEW/CHECKS/TEST_LOG; SWEEP_ROUND1/2及SILENT_ASSUMPTION_SWEEP.json; D_INPUT_CHECK/protocol_smoke/previous | implementation | 两轮四分支离线实现；31项通过；same-family/provisional，末轮后执行者修订回归；真实任务训练/团队0 |
| 2026-11-01 R29 | implementation | tools/b1_controls.py; tools/b1_runtime.py; tools/b1_experiment.py; tests/test_b1_controls.py; tests/test_b1_runtime.py; config/b1_team_pending.json | implementation | 私人隔离/完整原始记录/固定平票/单模型adapter/资格绑定/前缀接续；实际配置BLOCKED |
| 2026-11-01 R29 | stage review | AGENTS.md; CURRENT_STATE.md; handoff.md; brainstorm.md; refine-logs/expert-mechanism-pilot-20261030/{EXPERIMENT_PLAN,EXPERIMENT_TRACKER,B1_CONTROL_DESIGN,B1_EVALUATION_AND_BATCH_PLAN}.md; refine-logs/acl2027-expert-transfer-20261029/{WORK_TRACKER,STAGE_REVIEWS}.md | implementation | 当前v0.9，下一步实机预检→B0/V/C→1/2→8→32；历史快照保留 |
| 2026-11-01 R30 | aris:novelty-check | .aris/traces/novelty-check/20261101_motivation_delta/assessment.md及审查trace; refine-logs/acl2027-expert-transfer-20261029/STAGE_REVIEWS.md | assessment | 定点复核贡献空间，PROCEED；现行实验顺序不变，无任务运行；非穷尽查新 |
