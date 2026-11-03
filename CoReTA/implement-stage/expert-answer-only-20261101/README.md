# 实验一最小执行包

2026-11-01。当前代码可执行仅答案数据检查、模板/loss准备、单adapter训练、V/C逐题生成、官方答案EM/F1评分、V选模和配对区间。已用CPU随机tiny Llama核adapter更新、保存重载、一次实际fixture生成；不是Qwen、MuSiQue效果或CUDA/QLoRA验证。真实任务训练/校准为0。

入口：[b0_expert.py](../../tools/b0_expert.py)。训练实现：[b0_training.py](../../tools/b0_training.py)；评分/统计：[b0_answers.py](../../tools/b0_answers.py)。原三字段讨论程序保留，没有用于本次资格评价。

## 已固定的研究规则

- 1796题与V200沿当前已选数据；训练assistant只包含答案及模板结束符。输入/padding不参与loss，无静默截断；模板prefix不精确对齐就停止，不猜loss边界。
- 短答案去首尾空白和一次固定Answer:/答案:前缀，其余全文作为答案；调用原MuSiQue官方EM/F1，别名只留评分侧。不从输出中按gold挑词，不要求依据/引用/理由字段。
- B0首轮V/C用greedy、最多64个新token、seed20261102，B/E相同。具体thinking模板参数需选检查点后明确。这不决定后续三个普通成员的讨论采样策略。
- V按EM→F1→预登记候选的较早顺序选择，`select --reports`须按训练前登记顺序传入。仅loss变化不选专家；只从完整同条件V报告选择，不用C调参。
- C160仅固定一次；元数据关联组已固定139组、最大4题。10000次组配对bootstrap，seed20261102，95%百分位区间，组内按题加权；逐题bootstrap仅敏感性。不把多次发言当独立样本。
- “SUPPORTED_TASK_ADVANTAGE”仅在完整真实C、E/B同推理条件、EM正差且组区间下界>0时输出；5–10pp仍是期望而非通用门槛。少于10组/最大组占半数的精度警示阻止自动强资格，当前C不触发；CI反映题目关联，不涵盖所有模型随机性。
- 无静默重试。后端失败保留，独立题可继续；OOM停止当前批。输出到长度/时间限制未出现结束符记OUTPUT_LIMIT。任何缺失/限制记录导致资格报告INCOMPLETE，不删题后算主比较，不把技术失败混成语义错。
- walltime为训练步/生成边界检查的有限预算，允许当前计算步/单token及保存操作带来少量超时，不是操作系统硬杀计时器。超时/非有限loss或梯度保留状态，partial adapter不作为候选。技术短步adapter也不能作真实专家。

## 当前环境与尚待实机的配置

CPU工程验证隔离在`.venv-expert`，未改旧`.venv`。实际测试版本见[CPU_ENVIRONMENT.lock.txt](CPU_ENVIRONMENT.lock.txt)，包括PyTorch CPU版、Transformers、PEFT和Accelerate。**该lock不是GPU安装命令**；GPU机器应按CUDA环境安装PyTorch，若选4bit再安装/验bitsandbytes，然后核实际库版本。未下载预训练模型权重。

[config/b0_answer_only_pending.json](../../config/b0_answer_only_pending.json)是待填模板，空项会拒绝运行，不会默认4090或8B。实机确认后另存一份运行配置，填写：本地模型绝对路径、明确revision、device/dtype/quantization、完整max_length、template_kwargs、target_modules、梯度累积/检查点、wall_seconds，并在批次意义/工程审核后设置reviewed_for_run。不要把CPU fixture设置带入实际实验。

模型使用本地目录，加载时local_files_only=True、trust_remote_code=False；本包不下载权重，不租卡/收费调用。模型结构或模板不兼容时明确失败，不绕过检查。

## 命令顺序（从CoReTA目录运行）

已完成的离线命令：

```powershell
.venv-expert/Scripts/python.exe tools/b0_expert.py check-data --output implement-stage/expert-answer-only-20261101/DATA_CHECKS.json
.venv-expert/Scripts/python.exe tools/b0_expert.py prepare-metadata --output implement-stage/expert-answer-only-20261101/C_GROUPS.json
.venv-expert/Scripts/python.exe -m unittest discover -s tests -p test_b0_expert.py -v
```

以下是设备到位并填写/审核`config/b0_runtime.json`后使用的步骤，**本轮没有执行**。目录示例须在第一次训练前登记，不能据结果重排候选：

```powershell
# 全1796/V200用实际tokenizer检查完整模板，任何超长不裁剪
python tools/b0_expert.py tokenize-check --config config/b0_runtime.json --output runs/b0/token_lengths.json
# 技术验收，不产生可用专家候选
python tools/b0_expert.py train --config config/b0_runtime.json --technical-steps 10 --output runs/b0/technical_preflight
# 审核技术记录、实测耗时显存、固定训练上限后执行正式候选
python tools/b0_expert.py train --config config/b0_runtime.json --output runs/b0/attempt1
python tools/b0_expert.py generate --config config/b0_runtime.json --role V --condition B --output runs/b0/V_B
python tools/b0_expert.py generate --config config/b0_runtime.json --role V --condition E --adapter runs/b0/attempt1/adapter --output runs/b0/V_E1
python tools/b0_expert.py score --run runs/b0/V_B --output runs/b0/V_B_score.json
python tools/b0_expert.py score --run runs/b0/V_E1 --output runs/b0/V_E1_score.json
python tools/b0_expert.py select --reports runs/b0/V_E1_score.json --output runs/b0/selected.json
```

只有V选择最终候选、专家资格批次审核完成后，才显式执行C；不会默认读取C正文/答案。若有第二个预登记候选，在V比较，最多两次主要训练尝试。C命令中的adapter必须是选定候选；示例假设为attempt1：

```powershell
python tools/b0_expert.py generate --config config/b0_runtime.json --role C --condition B --output runs/b0/C_B
python tools/b0_expert.py generate --config config/b0_runtime.json --role C --condition E --adapter runs/b0/attempt1/adapter --output runs/b0/C_E
python tools/b0_expert.py score --run runs/b0/C_B --output runs/b0/C_B_score.json
python tools/b0_expert.py score --run runs/b0/C_E --output runs/b0/C_E_score.json
python tools/b0_expert.py compare --baseline runs/b0/C_B_score.json --expert runs/b0/C_E_score.json --groups implement-stage/expert-answer-only-20261101/C_GROUPS.json --output runs/b0/C_comparison.json
```

输出目录必须是新目录，已有原始响应不覆盖；中断保留其记录，不自动续跑或拼接成完成。训练保存来源元数据，E加载核同底座路径/revision和fixture/purpose，避免技术adapter当专家。

## 验收与审核边界

见[BUILD_NOTE.md](BUILD_NOTE.md)、[ASSUMPTIONS.md](ASSUMPTIONS.md)。本地测试中的预测、随机模型权重和训练loss是工程fixture，不能进入论文结果。实际Qwen模板/长输入显存、GPU/4bit训练、实际步耗时、V/C效果仍需实机验证；本阶段通过仅允许后续准备和短步验收，不等于获得专家。

实现参考：[HF Trainer](https://huggingface.co/docs/transformers/en/main_classes/trainer)、[HF Chat templates](https://huggingface.co/docs/transformers/en/chat_templating)、[PEFT LoRA](https://huggingface.co/docs/peft/en/developer_guides/lora)。本轮按实际安装版本修正接口，并记录环境；没有把文档示例当实机兼容证明。
