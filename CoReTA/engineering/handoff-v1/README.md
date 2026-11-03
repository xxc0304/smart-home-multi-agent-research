# 局部贡献协议 v1：实现入口

**补充验证完成：74项离线测试、8个后段压力场景、5次真实接口格式复制检查通过。** 详见[补充记录](FORMAT_READINESS_20261021.md)。尚未启动六个开发求解run，没有模型能力收益结果。原固定角色代码/数学流程保持原入口；新协议使用独立模块。

上次发现的字符串排序漏洞已修复为受约束数组与确定性渲染；三个系统统一使用已有本地tokenizer估计输入，保留32768预算。可按[首批六单元计划](PILOT_PLAN_20261021.json)开始开发试跑，接口复制检查不代表真实求解格式成功率。

## 已实现的范围

| 模块 | 职责 |
|---|---|
| `inputs.py` | 白名单读取选定条件的成员packet，核对公共题目、资料归属、本人可见引用；不读取offline答案 |
| `contracts.py` | 提取协议阶段输出及完整排序/讨论schema，只携带必要定义，动态限定成员/可见引用/允许动作，严格解析JSON |
| `prompts.py` | 复用设计提示词，将APPLY/REVIEW适配为完整排序；普通讨论使用独立阶段提示 |
| `gateway.py` | 复用DeepSeekClient的Responses传输和原始日志；统一网络尝试、超时、一次格式恢复 |
| `runtime.py` | 局部贡献→应用→核查，按需ask/check/probe→回复→应用；追加保存C/W/Q/V，保留未决与实际终止状态 |
| `ranking.py` | 单独离线解析和L1评分，不参与实时推理 |
| `__main__.py` | prepare、run、score三种命令；普通讨论及独立初答使用相同资料加载器 |

代码目录：`CoReTA/src/coreta/handoff/`。编码前决策及范围见[IMPLEMENTATION.md](IMPLEMENTATION.md)。

## 命令示例（PowerShell）

在`C:/Users/QVQ/Documents/ChatGPT/agent-research/CoReTA`目录下使用已有虚拟环境。运行目录必须不存在，避免覆盖旧结果。现有环境应已安装本地coreta包及其jsonschema依赖；当前导入与离线入口已验证；默认读取项目已有本地tokenizer。

### 1. 只导出初始输入与提示，不发网络请求

```powershell
.\.venv\Scripts\python.exe -m coreta.handoff prepare --condition distributed_r0 --system coreta --output runs/handoff-moon-prepared-001
```

输出三份成员初始输入、阶段提示和schema及manifest。仅导出初始阶段，不是完整模拟运行，不产生成功率。

### 2. 实际求解（会产生DeepSeek API调用）

```powershell
.\.venv\Scripts\python.exe -m coreta.handoff run --live --condition distributed_r0 --system coreta --task-ordinal 1 --output runs/handoff-moon-coreta-001
.\.venv\Scripts\python.exe -m coreta.handoff run --live --condition distributed_r0 --system ordinary_discussion --task-ordinal 1 --output runs/handoff-moon-discussion-001
```

只有`run --live`发模型请求。缺少环境变量`DEEPSEEK_API_KEY`时明确失败，不创建求解目录。密钥不在命令参数、manifest或日志中。沿用官方`deepseek-flash`配置，未重新检查服务端别名或API当前可用性。

每系统单独一个任务deadline和20次总尝试上限，包含传输重试与格式恢复。CoReTA的通常路径5次首尝试，普通讨论通常10次首尝试；实际资源量不相等，不自动宣称同成本收益。

集中配置改`--condition concentrated_A1`。后续可按相同方法使用其他资料轮换；task-ordinal=1取A2作为driver，禁止按真实分数选driver。

### 3. 另采完整独立初答

```powershell
.\.venv\Scripts\python.exe -m coreta.handoff run --live --condition distributed_r0 --system independent --output runs/handoff-moon-independent-001
```

三名成员各自新上下文，模型调用中没有别人的答案。结果不回填CoReTA。当前未实现跨run共享初答银行，普通讨论自己采初答，因此不能称三种方法已共享同一批随机初答；同packet和模型配置不保证随机输出相同。

### 4. 事后单独评分（不发网络请求）

```powershell
.\.venv\Scripts\python.exe -m coreta.handoff score --run runs/handoff-moon-coreta-001 --output runs/handoff-moon-coreta-001.score.json
```

`score`才读取`offline/evaluator.json`，结果另存、不改求解artifact、不反馈模型。对`independent`运行评分各成员；对其他运行评分最终排序，并附本run已有完整初答。独立初答跨run配对尚未实现，恢复/退化比例输出null，不把缺失初答当全错。

## 结果文件

- `manifest.json`：模型与调度设置、成员输入/实现/提示schema哈希、driver、逻辑种子及输入计数模式。
- `requests.jsonl`、`responses.jsonl`：原始请求/响应、阶段/成员、延迟与token用量；研究者文件可能包含多人私有资料，不能整体回传成员。
- `stages.jsonl`、`stage_errors.jsonl`：阶段成功输出及格式/引用错误。
- `events.jsonl`、`state.json`：贡献、请求、回复、应用、核查与完整工作版本。
- `result.json`：最近完整候选、status、stop_reason、未决、最后核查及其对应W版本、调用与用量。普通讨论没有CoReTA核查，状态如实为未核查交付。
- 实现异常另写`implementation_error.json`并保留state，不伪装成模型解题失败。

退出码0只表示调度正常终止，不表示排名正确。协议失败或硬预算耗尽退出2，保留已有候选，离线评分仍按相同规则处理。输入错误由命令行明确报错。

## 尚未建立的证据

已通过74项聚焦离线测试，另有5次真实接口复制检查；它们不构成架构有效性结果。下一步是固定六单元开发试跑，检查实际知识使用和误差。

程序只管显式结构、来源记录与有界流程；是否发现真实缺口、回复是否正确、修订是否合理仍由模型决定。字段存在不认证互补成功。
