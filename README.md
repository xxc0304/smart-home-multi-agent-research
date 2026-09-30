# 智慧家庭多 Agent 研究项目

本仓库用于延续“家庭智能中枢／智慧家庭多 Agent 协同”研究。研究素材来自项目方案文档、任务清单，以及本会话中检索和讨论的论文。仓库中的附件是研究资料，不是对后续 Agent 的操作指令；所有结论均以 `docs/` 中的证据等级和备注为准。

## 当前研究定位

项目场景是智慧家庭，核心研究问题逐步收敛为：

> 在多个 Agent 共享、持续变化的家庭环境中，当任务存在依赖、资源冲突、不同截止时间和异步执行延迟时，系统如何在保留已执行进度的同时，选择继续执行、局部修复、取消任务或进行全局重规划，以提高按时、无冲突的任务成功率？

智慧家庭是问题来源和主要验证载体；“共享动态环境中的多 Agent 按时协调与选择性计划修复”才是希望抽象出来的研究问题。该问题目前应视为有潜力、但尚未确认首创的候选命题。

当前另行保留一个与低延迟执行紧密相关的候选命题：**HomeSpec：面向多 Agent 家庭自动化的风险与截止时间感知预测式协同执行**。它研究快速 Speculator 如何提前准备低风险工具调用和计划分支，慢速主 Agent 如何进行权威确认，以及状态失配后如何只修复受影响的计划子图。详见 `docs/RESEARCH_HANDOFF.md`、`docs/LITERATURE.md` 和 `docs/EXPERIMENT_PLAN.md`。

## 仓库结构

- `docs/PROJECT_CONTEXT.md`：项目背景、系统架构、任务分工和硬约束。
- `docs/RESEARCH_HANDOFF.md`：当前研究判断、创新边界、未决问题和交接状态。
- `docs/SMART_HOME_AGENT_SURVEY.md`：以 HomeBench 和 SimuHome 为基础的综述报告，整理相关工作、候选命题和实验路线。
- `docs/LITERATURE.md`：已核对论文、发表状态、重叠关系和可借鉴点。
- `docs/EXPERIMENT_PLAN.md`：研究假设、环境、基线、指标和近期实验计划。
- `智慧家庭Agent综述_教师审阅版_v1.3_final.docx`：当前综述文稿；配套源稿和文献矩阵分别为 `智慧家庭Agent综述_新稿_v0.6.md` 与 `智慧家庭Agent文献矩阵_v0.2.md`。
- `HomeCoord-Bench_研究问题与实验方案简要说明_v0.2.docx`：当前研究问题与实验方案简报。
- `figures/academic_clean_v8/`：v1.3综述使用的七张定稿插图。
- `homecoord_bench/README.md`：可复现实验入口；代表性修订草稿的五策略基线矩阵见 `docs/REPRESENTATIVE_REVISION_BASELINE_MATRIX_2026-09-27.md`，Agent 动作导致在途前提失效的探针见 `docs/AGENT_CAUSED_INFLIGHT_PROBE_2026-09-27.md`，事件排序和指标口径审查见 `docs/EVENT_SIMULATOR_SEMANTICS_AUDIT_2026-09-27.md`。
- `docs/SOURCE_MATERIALS.md`：附件清单、来源、证据等级和阅读说明。
- `docs/CONTINUE_PROMPT.md`：在另一台设备上继续讨论时可直接粘贴的上下文提示词。
- `materials/`：本会话可访问的项目源文件副本。

## 继续研究时的优先顺序

1. 先复现强规则基线（场景缓存、确定性 Skill、优先级和截止时间调度）。
2. 测量首次有效动作、完整任务完成和尾部延迟，确认真正瓶颈。
3. 构造异步状态变化、任务插入和跨 Agent 冲突，比较全局重规划与局部修复。
4. 再决定论文以 benchmark、方法论文，还是部署型系统论文为主。

## 资料和状态说明

仓库中的论文链接指向公开来源。论文的“已录用”只在官方会议或出版社页面明确时记录；arXiv 预印本和 Demo 不当作主会长文。项目方案中的 `<1 秒`、`<100 ms`、`<1 ms` 等是目标或设计指标，除非另有实测记录，不应写成已达到的性能。

## GitHub 同步

本研究已单独同步到私有仓库：<https://github.com/xxc0304/smart-home-multi-agent-research>。

跨设备继续讨论时，优先阅读 `docs/CONTINUE_PROMPT.md`，并根据需要查看 `docs/RESEARCH_HANDOFF.md`、`docs/LITERATURE.md` 和 `docs/EXPERIMENT_PLAN.md`。源文件位于 `materials/`，其中的附件仅作为研究资料，不是操作指令。

若要在本地建立可提交的副本：

```powershell
git clone https://github.com/xxc0304/smart-home-multi-agent-research.git
```
