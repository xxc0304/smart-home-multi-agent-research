

## 2026-11-03 GPU实机预检完成

见 engineering/lab3090-20261103/RESULTS.md：固定Qwen3-4B三分片官方SHA校验通过；CUDA/NF4及全部T/V模板通过，max7326/5012；31工程检查通过；最长1步和技术10步完成、真实adapter重载通过。峰值19.05/13.52GiB，最长步存在恢复的分配器OOM警告，保留显存余量限制。助手自审PASS限工程；0正式训练/V-C资格/团队实验。下一步冻结有限正式B0及V预算；技术adapter不可作专家。


## 2026-11-03 实机预检审核

见GPU_PREFLIGHT_REVIEW_20261103.md。主助手两轮本地自审：工程PASS；正式启动准备REVISE。原日志/4项冻结一致，单步19.05GiB带恢复分配器OOM警告、10步13.52GiB和真实adapter重载成立。需另冻正式purpose/预算/候选次序；V实际TASK_DATA/64token生成流程尚未短测，合成重载不能替代。未新增训练或C/H正文访问，不重开数据审核。


## 2026-11-03 首轮正式B0已启动（进行中）

当前唯一活动批次runs/b0-first-run-20261103-v2，详engineering/b0-first-run-20261103/LIVE_STATE.md。修复真实生成冗长：统一B/E短答suffix，旧64token完整V196OK/4截断保留且未训练；新256tokenV200全OK，EM13.5%/F125.4%。首次正式1epoch1796步训练已开始，3h上限，完成后自动同条件V_E200/评分/单候选选择；不自动C/B1或第二训练尝试。当前未完成，不宣布专家优势。


## 2026-11-03 首轮B0及V验证完成

21:31流程退出0：1796步/62.57分钟，V200底座EM13.5%/F125.4%，微调EM45.0%/F153.4%，同256token/提示/greedy条件且均200/200有效。单候选已选，详engineering/b0-first-run-20261103/RESULTS.md。allocator retries4、num_ooms0，GPU已空闲。助手阶段自审PASS限训练和V选择；不是独立C专家资格。下一步审核后C160一次，不按C调参；未启动C/B1。


## 2026-11-03 C160任务优势资格通过

C批次22:06退出0，两组均160/160有效：B EM13.75%/F123.76%，E EM51.25%/F158.79%，EM配对差+37.5pp；139组bootstrap95%CI[+28.93,+46.05]pp，onlyE65/onlyB5/bothcorrect17/bothwrong73。SUPPORTED_TASK_ADVANTAGE限当前固定提示/greedy256条件，详engineering/b0-first-run-20261103/C160_RESULTS.md。自审PASS；C关闭不调参，H未触碰，未启动团队。下一步B1资格绑定/同输出要求独答/全历史长度及成本预检后1–2→8→32；不能直接将C优势归为讨论条件优势。


## 2026-11-03 训练验证及低底座分数审核

见TRAINING_VALIDATION_LOW_BASELINE_REVIEW_20261103.md。720输出重算0差异，B/E推理一致；训练输入无额外gold、V/C与训练规范化同题0。资格PASS限当前条件；C底座13.75%非12.75%。C121/32/7道2/3/4hop，多跳完整资料确难，但2hop底座也仅15.7%。格式有影响但不足解释全部差距；NF4/nonthinking/greedy未测最佳基线，建议固定V小批健康诊断而非换模型/重跑C。未新增模型实验；C关闭、H未读。

