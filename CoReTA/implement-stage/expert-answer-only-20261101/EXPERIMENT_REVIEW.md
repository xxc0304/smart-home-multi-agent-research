# R24：仅答案训练与资格流程离线验收

2026-11-01；主助手阶段自审，另有research-implement-feature要求的fresh同家族两轮假设审查，same-family/provisional，非导师/跨家族认证。

目标：将已确定的答案SFT、V选模和C配对评价变成最小执行入口，不启动真实专家训练。范围：固定数据接口、assistant-only loss/无截断、adapter更新保存重载、逐题原始响应、答案metric、组bootstrap、失败/预算、待填配置。真实GPU/模型/完整长输入与资源预算不在CPU验收的通过范围。

## 研究意义

PASS仅离线准备：实现直接服务“独立任务优势是否成立”，没有加入支持/理由/协作监督，不把工具成功当专家证据。原1796/V200和已关闭质量核验保持，不访问H题/标签，C只读既有关系元数据（139组、最大4），不生成C答案。理由/分享弱不筛专家。B0采用greedy不预定后续团队采样。

## 工程证据

- DATA_CHECKS.json：真实1796/V200接口通过，数据不重分组/重清洗。
- TEST_LOG.txt/CHECKS.json：9项相关单元和CPU集成检查通过。随机tiny Llama+本地tokenizer实际2步LoRA，base embedding不变、adapter更新、保存重载logits一致；实际fixture生成留原文；长输入拒绝、padding不参与loss、超时保留中断，缺项不出完整比较，别名/EM/F1及V选模/统计均覆盖。
- 配置尚未填实机字段时拒绝执行，不猜卡型/模型/预算。本机隔离CPU环境已安装，原环境不改；未下载预训练模型权重。4bit依赖未安装/未验证，CUDA未验证。
- fresh同家族审查首轮3项未声明（2 semantic/1 interface）及最后step预算边界：补A16–A19、修复超时后仍登记完成的路径；二轮0未声明/0过时行，结论仅provisional。原文两轮JSON保留。

## 分开判定

**本阶段离线交付PASS。真实实验工程准备BLOCKED，总体真实训练/校准DO_NOT_RUN。** 实际卡型/显存、Qwen版本/revision、template_kwargs与完整长度、target modules/有效batch/精度、CUDA/4bit及吞吐/walltime仍需11月2日起实机预检。当前不得用CPU fixture速度估GPU时间，不得称任务专家已经存在。

允许下一动作：核实机器、按README填写独立运行配置、做实际tokenizer全长检查与有限技术短步，按本项目章程记录该批预检及预算后训练。无自动租卡、收费API、新数据抽查或协作训练。科学配置不因缺硬件重新讨论；已有通过的离线项不重复全套审核，仅检改变部分。
