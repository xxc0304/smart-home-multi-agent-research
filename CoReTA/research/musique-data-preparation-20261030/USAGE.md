# 数据与评分使用

在CoReTA根目录执行。无需GPU；使用已有虚拟环境的tokenizers。`-X utf8`确保上游未修改评分代码的文件编码一致。

```powershell
# 原始公开归档已下载；需要重取时才执行，不能执行上游下载脚本中的清理命令。
.venv/Scripts/python.exe -X utf8 research/musique-data-preparation-20261030/download_official.py
# 全量字段、重复与基础输入token审计；CPU分词需一定时间，不调用LLM。
.venv/Scripts/python.exe -X utf8 research/musique-data-preparation-20261030/audit_corpus.py
# 只按数据结构和固定哈希顺序分配，不读取任何模型输出。
.venv/Scripts/python.exe -X utf8 research/musique-data-preparation-20261030/build_pack.py
# 校验真实导出内容、哈希、跨集合支持资料与官方评分样例。
.venv/Scripts/python.exe -X utf8 research/musique-data-preparation-20261030/verify_pack.py
```

推理侧只读 `data/external/musique-v1.0-20261030/inputs/<角色>.jsonl`。允许的字段只有日志ID、question、paragraphs（idx/title/paragraph_text）。不要把完整原始文件、corpus_index、分解、答案、is_supporting、角色清单、题号中的跳数或scoring目录发送给模型。`audit_corpus.prompt()`已经排除ID；聊天包装、输出schema和讨论协议仍待模型批次确定。

示例prompt是仅用于审计长度的基础任务指令，不是已完成端到端预检的正式团队提示。正式输出合同建议与评分兼容：

```json
{"id":"日志ID，由程序关联","predicted_answer":"模型答案","predicted_support_idxs":[0,3],"predicted_answerable":true}
```

id应由程序回填关联，不要求模型看到结构性题号。Ans全为可回答题；是否还要模型输出answerable或由程序固定为true，须在正式批次合同中决定。上游Ans指标不会因为predicted_answerable=false自动把答案分数归零；不得把该字段另解为已验证的拒答指标。

对已有预测文件评分：

```powershell
.venv/Scripts/python.exe -X utf8 research/musique-data-preparation-20261030/score_predictions.py --predictions 你的预测文件.jsonl --targets data/external/musique-v1.0-20261030/scoring/D_development.jsonl
```

评分前严格核ID、字段和合法整数证据编号，再按ID对齐官方评分顺序。缺失/多余/重复ID、非法编号或字段会退出为INVALID，不产总体分数；不会从分母偷偷删掉失败记录。未来生成批次的重试、技术失败报告与完整分母另按实验章程冻结；这里没有替未来批次选择有利失败处理。

`examples/*fixture*.jsonl`是从已暴露dev金标人工构造的评分输入，用来核对别名、对错答案及支持段集合。不要把它们当成模型能力、专家优势或真实实验结果。官方指标为答案EM/F1和支持段F1，返回0–1并保留3位小数；正式统计需要逐题未舍入分数及任务依赖分组，尚待另行实现/核验。

H是内部公共dev留出候选池，不是官方隐藏测试；目录隔离是数据使用约定，不是文件系统权限封锁。以后人工查看H例子或用H结果调参都要追加暴露登记并重新审查，不能继续称未使用留出。
