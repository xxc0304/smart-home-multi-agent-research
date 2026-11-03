# 实验二：两轮四分支实现与验收

2026-11-01。范围：离线实现及CPU工程验证。真实MuSiQue训练、专家资格验证、团队生成均未运行；不据fixture推断研究效果。GPU/Qwen、完整讨论长度及实际成本仍待实机验证。

## 已落实的实验

| 组 | 工作方式 | 专家身份 |
|---|---|---|
| A | 私人复议，仅见自身历史 | 隐藏 |
| B | 轮流讨论，即时广播 | 隐藏 |
| C | 私人复议，仅见自身历史 | 初答后公开 |
| D | 轮流讨论，即时广播 | 初答后公开 |

四组共用4份独立短初答；每成员2次自然语言工作消息，再独立给短终答。终答不互见。每题52次生成；同题讨论顺序、对应请求种子配对，固定专家slot M1及seed20261102，工作512/初终答64新token，temperature=.7/top_p=.95/top_k=0；中性生成配置不继承checkpoint的其他采样/惩罚项，保存实际配置。它们是已登记的实现默认值，实际模型若系统性截断须统一修订技术版本后再冻结，不能据成绩调参。B0仍为仅答案监督及greedy资格测试。

主团队读数为最高票并列类均匀抽签的期望EM，同时报固定seed实际EM/F1。实际选择不读gold。专家/普通成员正误转移、纠错、专家正确但票选未采用的读出损失分开记录。B−A/D−C比较交流包，D−B/C−A比较身份提示包，不能唯一归因为从众或识别机制。区间按题的关联组配对bootstrap；32题仅开发。

## 文件

- `tools/b1_controls.py`：四组状态机、信息隔离、投票、轨迹回放与描述评分。
- `tools/b1_runtime.py`：本地HF/PEFT、单底座切adapter、资格绑定、有限预算、累计接续。
- `tools/b1_experiment.py`：CLI。旧四轮程序保留作历史，不作为本实验入口。
- `config/b1_team_pending.json`：待填配置，当前拒绝真实运行。
- `ASSUMPTIONS.md`：编码前登记的选择及修订。`DESIGN_REVIEW.md`：本地科学设计审核。
- `D_INPUT_CHECK.json`：32输入/29关联组，未读评分标签；不是数据语义复审。
- `protocol_smoke.json`：52条手写响应的工程fixture，模型调用0。

## 可现在执行的检查

以下命令在CoReTA目录执行：

```powershell
.venv-expert/Scripts/python.exe tools/b1_experiment.py --smoke implement-stage/team-controls-20261101/protocol_smoke.json
.venv-expert/Scripts/python.exe tools/b1_experiment.py check --n 32 --config config/b1_team_pending.json --output implement-stage/team-controls-20261101/D_INPUT_CHECK.json
.venv-expert/Scripts/python.exe -m unittest discover -s tests -p 'test_b1*.py' -v
```

check可成功完成离线检查，同时报告实际配置BLOCKED。不能把检查命令退出0视为GPU/研究实验就绪。CPU tiny测试只使用随机微型权重及临时adapter，含真实CPU generate；完整52请求由明确的脚本fixture验证，均无任务能力结论。

## 有硬件、真实合格专家及批次审核后执行

先沿B0入口完成实际模型/模板/长度/精度/吞吐预检、有限训练与V选模，然后独立C160验证。B1配置需填本地模型路径/revision、dtype/量化/device、完整上下文上限、模板参数、有限wall_seconds、adapter_path及B/E已有C评分JSON路径，并在实机审核后设reviewed_for_run=true。C评分绑定同底座、adapter、精度/量化及模板；不在B1自动启动C或读取C/H题文与标签。B1更长历史的长度上限独立测量，超长拒绝，不静默截断。

以下为未来命令示例，本轮未执行；填入实际配置后仍需当批EXPERIMENT_REVIEW：

```powershell
.venv-expert/Scripts/python.exe tools/b1_experiment.py run --n 2 --config config/b1_team_actual.json --output experiment/results/b1-timing
.venv-expert/Scripts/python.exe tools/b1_experiment.py score --run experiment/results/b1-timing
.venv-expert/Scripts/python.exe tools/b1_experiment.py run --n 8 --config config/b1_team_actual.json --resume-from experiment/results/b1-timing --output experiment/results/b1-tech8
.venv-expert/Scripts/python.exe tools/b1_experiment.py run --n 32 --config config/b1_team_actual.json --resume-from experiment/results/b1-tech8 --output experiment/results/b1-dev32
```

真实入口强制先1或2→8→32，后两阶段接续前阶段的完整同配置前缀，旧题不重跑；新目录可增加有限wall预算。若协议/种子/模型配置变动，另立技术版本；不完整旧题不默重跑。真实入口只支持D既定前1/2/8/32，1–2包含于8/32；更大批次尚未授权或设计。

每批保存manifest、完整请求/原响应journal、逐题快照、execution及实际生成配置/加载耗时；CUDA记录累计峰值显存。显式score才逐行解析所选前n条D标签并输出scores.json。初答/终答原文保留，评分和投票路径各只清理一次固定前缀。初答失败阻断该题全部分支，单链失败不填造依赖；OOM或模板/长度配置错误停批。输出未正常终止标OUTPUT_LIMIT，保留原文；空但正常终止的答案计弃权/错误。有限wall是软截止，模型加载/单token/保存可有额外耗时。不完整批报告计划N/实际N/完整配对N，不出完整批主结果。

下一阶段是**实机预检→获得并独立核验专家→1–2题成本与技术验收**。本阶段没有改变研究命题，也没有提前选择原因干预或新架构。
