# 构建记录

| Rung | 内容 | 验收 | Tier | 状态 |
|---|---|---|---|---|
| F0 | CLI到fixture评分产物 | b0_answers.py --smoke | MUST | PASS |
| F1 | 真实训练数据与模板loss边界 | unittest data/mask | MUST | PASS |
| F2 | HF/PEFT训练、adapter重载及生成 | CPU tiny fixture +配置缺项拒绝 | MUST | PASS |
| F3 | 官方答案评分、配对统计、V选模、失败 | unittest metrics/stats/manifest | MUST | PASS |
| F4 | 配置/实机预检说明/审核 | 离线真实数据检查+同家族假设审查 | MUST | PASS |

## Run record
## Deferred
真实Qwen/GPU、硬件吞吐与本轮任务训练/校准；不在无卡阶段伪称通过。
## Blockers
旧环境未改；独立CPU环境已安装并完成fixture。实际Qwen/GPU/4bit与运行预算尚待实机，待填配置故意不允许运行。

## 实际核验

F0：旧.venv运行b0_answers.py --smoke，exit0，answer_smoke.json明确fixture。
F1/F2：独立CPU环境安装torch/transformers/peft/accelerate，不下载任何预训练权重；随机tiny Llama与本地tokenizer，实际2步adapter训练，base embedding未变、LoRA更新、保存加载logits一致；超长拒绝、timeout中断产物保留。修复新版chat template返回dict与warmup_ratio接口变化后通过。
F3：9项单元/集成检查通过，含官方别名/EM/F1、无gold捞答案、缺项不完整、组bootstrap可重复、推理条件不一致拒绝、V选模/禁止C选模；实际fixture生成写入原始响应。CPU小模型不是Qwen或任务专家证据。
实际数据：1796+200接口检查通过，无C/D/H题/标签访问；C只用既有ID/关联元数据得到139组，最大4。
当前真实训练/校准0；CPU fixture训练不计为研究实验。当前无GPU设备/4bit验证，不装GPU库，不声称CUDA兼容。

## Git范围

已有根工作树和项目历史未提交产物较多；本次未提交或重置，评审按指定新增文件本身及列表检查，不用空git diff假装覆盖未跟踪代码。唯一.gitignore追加.venv-expert，保留原有改动。

## Phase4 审查与修订

首轮同家族审查3项未声明（2 semantic/1 interface）：bootstrap题数权重、候选参数顺序合同、自动资格标志含义，现补A16/A17/A19，来源sweep；另A18及代码修复最后训练步超预算仍写COMPLETE的边界。原文存SWEEP_ROUND1.json。回归9项通过；最终二轮记录另存。A11–A15为实现时补充而非冒称全部编码前已经声明。

## 尚未完成的实机验收

具体卡型/显存/访问窗口、Qwen检查点/revision及模板、完整长度显存、CUDA/4bit、有效batch和target modules、真实吞吐及walltime上限。没有发布/提交、租卡、真实训练或C预测，不扩大数据核查。

最终第二轮：0 undeclared、0 stale_rows；same-family/provisional。SILENT_ASSUMPTION_SWEEP.json是二轮原文副本。真实Qwen/GPU边界保持，全部MUST工程项仅在CPU/离线范围通过。
