# 本轮范围：离线输入与评分包

2026-10-30。Base commit：00338a49953246eaeff582e1a16f4c2959b77374，已有未提交研究材料保留。

目标：实现上一阶段P1的逐字提示、同题四核心条件/G/N参照、来源定位、评分样例与本地检查。复用已有MuSiQue C160/D80输入、官方评分源码和旧实验真实响应；H不用。现行数据输出置data/expert-mechanism-inputs-20261030-v0.2，代码置tools；v0.1保留实测过长的全文重复草案。

成功命令：`.venv/Scripts/python.exe -X utf8 tools/prepare_expert_mechanism.py`，以及`.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_expert_mechanism_protocol.py`。

输出：真实任务的独答提示、待初答依赖清单、明确标记的演示对照输入、独立评分目标/评分样例、参考token统计、真实历史接口回放和阶段报告。没有新任务模型初答时不伪造可运行的完整对照批次。

本轮不接API、不载模型、不训练、不执行校准或科学实验。模型/预算与新任务真实响应仍为启动前依赖。
