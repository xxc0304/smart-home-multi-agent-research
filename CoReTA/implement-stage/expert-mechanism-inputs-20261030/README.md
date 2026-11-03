> 后续顺序已更新：先能力校准与普通团队基线、再多环节过程检查，之后选择干预。S/A工具保留待选；旧4＋7不再是默认下一批，见[当前v0.3计划](../../refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md)。本文件记录P1交付时点。

# 来源与应用诊断：离线输入包完成

2026-10-30。**P1离线输入、解析、评分样例和结构检查已完成。** 实际模型尚未选定，没有调用模型或训练；这份交付将设计落成了可运行的本地准备工具。

- [具体例子与条件差异](INPUT_EXAMPLE.md)：同一真实D题上的手写演示，解释S/A/G/N究竟改变什么。
- [逐字系统提示与检查提示](PROMPTS.md)。
- [本地验收结果](PREFLIGHT_OFFLINE.json)：352份独答输入、56个真实初答待依赖、来源/金标隔离、官方评分核对、长度与缺覆盖。
- [当前实验审核](EXPERIMENT_REVIEW.md)：离线部分PASS，实际启动DO_NOT_RUN，剩余依赖写明。
- [实现前选择及长度修订](DECISIONS.md)、[范围](SPEC.md)。
- [数据包入口](../../data/expert-mechanism-inputs-20261030-v0.2/README.md)。v0.1保留全文重复的过长草案，当前v0.2以索引/标题定位已有全文。

运行（CoReTA根目录）：

```powershell
.venv/Scripts/python.exe -X utf8 tools/prepare_expert_mechanism.py
.venv/Scripts/python.exe -X utf8 -m unittest discover -s tests -p test_expert_mechanism_protocol.py
.venv/Scripts/python.exe -X utf8 tools/audit_expert_mechanism_package.py
```

17项离线测试及真实任务输入检查通过；新MuSiQue模型响应还没有。旧响应回放验证共用JSON/组包路径，保留其合同/资料权限改编，不能充当新任务实际预检。原人工记录未填写。

下一步是落实实际模型与预算，做一题真实技术验收（4份初答＋7个焦点对照请求的候选小批）；它只检验接口、来源和长度，不当能力校准或机制结果。真实调用仍需按实验章程冻结并通过相应审核。
