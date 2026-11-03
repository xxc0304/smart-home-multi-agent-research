# 组件与实验的来源台账

核查日期：2026-10-18。阅读级别按条目注明。本轮关注可复用设计与任务，不宣称查新通过。main/master 链接是读取时的版本，实施前需把实际采用版本写入依赖锁与运行清单；本轮没有克隆、安装或复现这些仓库。

| 编号 | 原始来源与核查位置 | 实际借鉴 | CoReTA 的适配与边界 |
|---|---|---|---|
| S1 | [MetaGPT 官方 schema.py](https://github.com/FoundationAgents/MetaGPT/blob/main/metagpt/schema.py)，读取 Message 与 Task/Plan 定义 | 消息 id、发送者、接收者、动作来源、结构化内容；任务标识与依赖的表示方式 | 自写小型消息类并保留字段名，不引入整个框架。版本号、请求关联、应用结果是本项目适配，不能称为该源码已有的互补评测机制 |
| S2 | [AutoGen 0.4.9 Group Chat](https://microsoft.github.io/autogen/0.4.9/user-guide/core-user-guide/design-patterns/group-chat.html)，读取消息协议、speaker manager | 内容消息与调度信号分开，由管理端执行下一发言与停止 | 借鉴控制分离；下一动作由主解题者提出，程序检查并分发。只借设计，不依赖 AutoGen 运行时 |
| S3 | [Salemi 等 Blackboard v2 §3、案例段](https://arxiv.org/html/2510.01285v2) | 共享请求、成员可拒绝、主代理选择是否使用响应 | 原法是广播和自愿响应，且有文件/搜索能力分区。CoReTA 第一版改为指定单个成员，不能称原样复现；也不人为分配私有真值制造专长 |
| S4 | [Du 等 Multiagent Debate 官方 GSM 生成脚本](https://github.com/composable-models/llm_multiagent_debate/blob/main/gsm/gen_gsm.py)及[评分脚本](https://github.com/composable-models/llm_multiagent_debate/blob/main/gsm/eval_gsm.py) | 三个独立上下文；读取其他成员上一轮输出后更新；GSM8K 任务先例 | 沿用消息循环思路，替换旧模型调用接口。当前配置用两个交流更新轮，与该 GSM 脚本设置不完全相同；标作 controlled adaptation |
| S5 | [Together MoA 官方 moa.py](https://github.com/togethercomputer/MoA/blob/main/moa.py)与[README](https://github.com/togethercomputer/MoA) | 并行生成候选后由同一模型汇总；评测框架复用的工程做法 | 独立候选→统一汇总是 MoA-style 简化对照，不冒充完整原论文设置 |
| S6 | [AgentVerse v3 §3.2、附录 A](https://arxiv.org/html/2308.10848v3)；[官方仓库](https://github.com/OpenBMB/AgentVerse) | HumanEval 代码任务先例；作者使用的执行反馈说明代码评测可复用 | v0.3 先采用文本协作、末端离线执行，未复现其动态招募或在线测试设置 |
| S7 | [Two Heads are Better Than One v2 实验段](https://arxiv.org/html/2504.09772v2) | 同类多 Agent 工作采用 MATH-500、HumanEval/MBPP-S | 只借任务选择依据；该文有训练组件，其方法不作为本轮无需训练的直接复现目标，原分数不搬入本项目结果表 |
| S8 | [MATH-500 数据卡](https://huggingface.co/datasets/HuggingFaceH4/MATH-500)，读取字段与 README；[MATH 原仓库](https://github.com/hendrycks/math) | 500 道题的固定数学评测集 | 主评测使用 problem；answer、solution、subject、level 等由评分/分析端管理。不是新造数据集 |
| S9 | [Math-Verify 官方说明](https://github.com/huggingface/Math-Verify)、[解析实现](https://github.com/huggingface/Math-Verify/blob/main/src/math_verify/parser.py)及[pyproject](https://github.com/huggingface/Math-Verify/blob/main/pyproject.toml) | 解析预测与参考答案、等价性评分 | 读取到 main 标记 0.9.0，实施前核对可安装版本并锁定；这是末端评分器，不向 Agent 返回真值或正确性反馈 |
| S10 | [EvalPlus 官方 CLI](https://github.com/evalplus/evalplus/blob/master/docs/cli.md)、[数据加载代码](https://github.com/evalplus/evalplus/blob/master/evalplus/data/humaneval.py)、[外部样本读取](https://github.com/evalplus/evalplus/blob/master/evalplus/data/utils.py)、[评分实现](https://github.com/evalplus/evalplus/blob/master/evalplus/evaluate.py)、[论文](https://arxiv.org/abs/2305.01210) | HumanEval+ 测试与外部生成结果评分接口 | 数据加载代码标记 HumanEval+ v0.1.10；外部 JSONL 的 solution 字段表示完整源码，与 completion 续写分支区分。数据与软件包版本分开记录；参考实现与测试输入不进入 Agent |
| S11 | [GSM8K 原仓库](https://github.com/openai/grade-school-math)、[官方 GSM8K 数据卡](https://huggingface.co/datasets/openai/gsm8k)、[MBPP 官方数据目录](https://github.com/google-research/google-research/tree/master/mbpp)、[MBPP 数据卡](https://huggingface.co/datasets/google-research-datasets/mbpp) | 使用原始训练划分准备数学/代码开发题 | 配置分别为 openai/gsm8k 的 main 和 google-research-datasets/mbpp 的 sanitized；开发题与 MATH-500/HumanEval+ 评价题分离，重复题面从开发集替换 |
| S12 | [Qwen3-32B 官方模型卡](https://huggingface.co/Qwen/Qwen3-32B)与[官方 Qwen3 仓库](https://github.com/QwenLM/Qwen3) | 可固定模型身份、显式非思考模式、官方推荐采样参数 | 作为可复现第一版建议模型，非“当前最强”声明。API 可达性及服务端模式支持尚未核对；不能静默替换模型或忽略参数 |

## 字段来源的逐项区分

- `id/content/role/sent_from/send_to/cause_by`：字段名借鉴 S1；本项目用单一接收者，实际传输仍为自己的协议。
- 内容与调度分开、有限轮数与停止：借鉴 S2；LLM 输出动作、程序约束动作是本项目具体实现选择。
- 明确请求与可拒绝贡献：借鉴 S3；本项目的 `target_step_ids/current_attempt/deliverable/check_plan` 是按研究目标设计的请求内容，不声称来自统一通行标准。
- `request_id/base_version`：请求关联与乐观版本检查的工程适配，不主张算法创新。
- `disposition/changed_step_ids/application_outcome/next`：CoReTA 显式贡献应用与后续控制的候选机制接口；字段本身不是创新证明。
- 三个候选、静态交流、共同汇总与任务评分：分别借鉴 S4—S10；对照需说明适配，不借用原文性能结论。

## 保留的研究贡献候选

贡献候选是把具体协作需求、贡献检查、实际整合和下一步动作连成一个可检验协议，以及其团队效果与互补作用证据。共享状态、结构化消息、角色与反馈各有先例，不能按组件清单宣称首创。
