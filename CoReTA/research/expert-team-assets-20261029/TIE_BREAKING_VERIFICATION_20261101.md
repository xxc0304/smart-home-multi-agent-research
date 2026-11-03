# 平票处理定点核查

核查日期2026-11-01。仅检原论文、官方代码和现有本地官方仓库；非全面文献统计。不从搜索摘要或第三方项目推断论文规则。未改当前平票决策、代码或运行实验。

## 可追溯证据

| 工作 | 实际核到的规则 | 证据与范围 |
|---|---|---|
| Multi-Agent Teams Hold Experts Back，v4 | 讨论后各自终答，投票并列均匀随机打破 | [附录A.1 Phase4](https://arxiv.org/html/2602.01011v4#A1.SS1)，正文明确ties broken uniformly at random。此条是论文协议，不代表逐个代码路径都已证实一致 |
| Debate or Vote，NeurIPS2025 | 数值/选择题投票取最高计数，多个最高时random.choice(most_common) | [官方evaluator.py](https://github.com/deeplearning-wisc/debate-or-vote/blob/main/src/evaluator.py#L44)，核到evaluate_arithmetics行44–66、evaluate_mcq行69–96及base variants；不是宣称所有任务聚合均如此，摘要任务代码另用ROUGE相关选择 |
| Voting or Consensus? Decision-Making in Multi-Agent Debate，Findings ACL2025 | 平票追加一轮讨论后重投，超过轮数上限未决时采用第一名agent的方案 | [§3.2及附录C，PDF pp.3/17](https://aclanthology.org/2025.findings-acl.606.pdf)。不能把这一工作简化为随机打破；其投票程序和我们直接计数答案的程序也有差别 |
| When Debate Helps，arXiv2610.04686v1 | 终轮没有唯一票数胜者时由base-model judge综合候选 | [附录A.2](https://arxiv.org/html/2610.04686v1)，本地官方code/src/when_debate_helps/debate.py的tied_indices/judge_ties路径和metrics.py的majority_answer。可关闭judge，未决返回None；不能把团队成员选择时的随机种子误当最终答案平票规则 |

Debate or Vote代码经GitHub连接器直接读取官方仓库当前main；该动态分支可能更新，本记录不宣称与所有历史实验版本相同。When Debate Helps为已保存v1及本地官方代码，不在此断言已独立核验的会议接收记录。

## 对本项目的判断

当前均匀随机规则合理地承担普通、无身份偏好的固定轮数读出基线，且来源论文有直接协议先例，不是孤立的临时约定。它不保证最优准确率，也不能自动证明团队不理解专家；它的随机损失必须与成员自身改答分开。

我们固定主讨论轮数，因平票追加讨论会使困难题得到额外生成机会；增加judge会引入额外模型处理；优先专家会主动改变专家利用机制。因此保持当前规则，另报平票率/实际选择/期望答案得分，后续若研究读出改进再比较其他策略。

2:2且仅一个候选正确时，随机期望答案EM为0.5；这是离线评分对随机读出分布求平均，不用gold决定实际选择。种子预登记只是保证可复现，不能单凭它消除抽签方差。不能按多个seed的最好结果挑选报告；也不把平票本身记为认知错误。

范围：本次核实四个直接相关例子，不能据此推断随机规则在全领域占多数。实验二其他未冻结项、实验一训练、预算及真实运行状态不变。
