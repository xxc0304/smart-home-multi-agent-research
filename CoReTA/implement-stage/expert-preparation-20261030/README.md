> 2026-10-31 R22：此包记录的是历史答案+支持训练导出与三字段讨论实现。当前专家训练候选已改为data/expert-training-answer-only-20261031/，V/C仅答案，详见当前v0.8及B0；本包旧格式不直接构成当前资格测试后端。原始资产保留，讨论协议后续对齐，未训练或调用模型。

# 专家训练数据与四轮讨论离线交付

本阶段只准备专家研究对象与普通讨论基线。**没有训练、GPU部署或新实验模型调用，不能由工程验收推断专家成立或团队机制成立。**

- [训练数据报告](../../data/expert-training-20261030-v1/SPLIT_REPORT.json)：T2000导出1800训练、200训练侧验证，七项跨侧关联检查为零；C/D/H原分配不变。248个关联组中最大1207题；V仅两种题形，不能当全任务代表。训练器尚未接入。
- [新讨论程序](../../tools/expert_discussion.py)：四独答→共享初答→四轮随机顺序即时广播→四私有终答；另有只复用E初答的四次无消息重思＋终答。每题24＋5次生成，不含C/V。
- [评价程序](../../tools/expert_discussion_scoring.py)：官方EM/F1、支持分数；初答投票/终答投票、各成员转移及E无消息参照分开。票数不足过半仍按最高票，最高票并列均匀抽样，不看gold别名；选中成员的支持仅为代表，不当全队证据。随机实现值和期望分数分开。
- [离线预检](PREFLIGHT_OFFLINE.json)：模拟轨迹及旧响应兼容回放；不是新MuSiQue讨论。参考长度压力样例最大输入10,395 token（不含真实聊天模板、输出和隐藏推理），8K不能视为四轮流程通用足够，也不据此保证16K实机可用。

## 使用

在CoReTA目录运行：

```powershell
.venv/Scripts/python.exe tools/prepare_expert_training.py
.venv/Scripts/python.exe tools/prepare_expert_discussion.py --verify
.venv/Scripts/python.exe -m unittest discover -s tests -p test_expert*.py -v
```

训练数据在`data/expert-training-20261030-v1/`。`*.messages.jsonl`含assistant监督，只供训练/验证loss；生成式验证使用`validation.inputs.jsonl`，评分侧另读`validation.targets.jsonl`。host的id不可拼入模型提示。无截断、分解监督或伪造推理链，计划仅对assistant计算loss；实际mask/模板必须等训练器接入后检查。

`DiscussionSession`不包含模型客户端。调用`next_request()`获取请求，外部执行后用相同request_id `submit()`，每次只推进一步；失败保留原文并停题，不自动补请求/跳过。实际响应需对应原始文件；fixture对象/轨迹显式标记且禁止主结果。`SoloSession.from_team()`复制E自己的初答，不传入同伴内容。

不提供solo时仅返回团队描述性分数、禁止主比较；solo未完成时无主汇总。完整team/solo配对仍只是评分输入合格，不证明专家成立、因果机制成立或已获实验执行授权。

构造时必须明确身份披露、专家actor、seed、投票规则。当前只实现一种开放问答投票候选，不等于研究合同已冻结。公开身份仅在初答固定后出现。**真实模型、输出/思考预算、模板和全历史上下文、有效优势标准、训练时间上限仍需运行前审核。**

[关键选择](ASSUMPTIONS.md) · [实现记录](BUILD_NOTE.md)。新程序不覆盖旧S/A局部重放工具；两者不可混称同一协议。
