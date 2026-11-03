# 图表索引

来源 `paper.pdf`（20 页）：图 10 张、表 7 张。全部裁剪拼在 `figures/_contact.png`，一次看完。

> 讲到哪张图就把那个 PNG 发给用户；讲之前自己先看一眼——caption 不会告诉你图是怎么排的。
> 裁得不对：`crop.py paper.pdf --page P --grid` 看带刻度的整页，再 `crop.py paper.pdf --page P x0 y0 x1 y1 -o figures/fig-NN.png` 重裁（坐标是页面比例 0–1）。

## 图 1 · 第 3 页 · `figures/fig-01.png`
**caption**：Figure 1. Overview of the four-phase research methodology, encompassing (A) data generation, (B) qualitative analysis and taxonomy development, (C) quantitative auditing design, and (D) quantitative auditing and reporting.
· label `fig:overview_methodology` · paper.tex L37 · 源文件 `figures/overview_methodology.pdf` · 正文引用：§3 Methodology (L35)

## 图 2 · 第 4 页 · `figures/fig-02.png`
**caption**：Figure 2. An overview of the AuditTrail framework, comprising four mechanisms designed to quantify and record the multi-agent collaborative process.
· label `fig:audit_mechanism_illustration` · paper.tex L65 · 源文件 `figures/audit_mechanism_illustration.pdf` · 正文引用：§3.3 Quantitative Auditing Design (L63)

## 图 3 · 第 6 页 · `figures/fig-03.png`
**caption**：Figure 3. A comprehensive taxonomy of collaborative failure modes in medical multi-agent systems. The taxonomy is structured chronologically across four phases of a collaborative task. Phase 1 (Task Comprehension) identifies initial errors from gaps in the base model’s capabilities and incorrect problem scoping. Phase 2 (Collaboration Process) details dysfunctions during agent interaction, such as convergence towards a flawed consensus and ineffective dissent handling. Phase 3 (Final Decision-Making) addresses breakdowns in viewpoint aggregation and information loss. Phase 4 (Framework Design) covers overarching issues in architectural design and evaluation benchmarks.
· label `fig:taxonomy_detailed_failure` · paper.tex L101 · 源文件 `figures/taxonomy_detailed_failure.pdf` · 正文引用：§5 A Taxonomy of Collaborative Failure Mode (L99)

## 图 4 · 第 7 页 · `figures/fig-04.png`
**caption**：Figure 4. A comprehensive taxonomy of collaborative success modes in medical multi-agent systems. The taxonomy is structured thematically into three core mechanisms of success. S1 (Consensus via Evidentiary Corroboration) encompasses scenarios where agents achieve a correct outcome by reinforcing and validating initial correct judgments through multi-perspective evidence. S2 (Error Correction via Interaction) details the processes where the collaboration actively corrects an initial error, such as when an expert agent’s opinion overrides an incorrect majority or when clarifying definitions resolves a misunderstanding. S3 (Agent-Driven Self-Correction) captures instances of intra-agent reflection, where an agent proactively identifies and rectifies its own flawed arguments during the collaborative process.
· label `fig:taxonomy_detailed_success` · paper.tex L108 · 源文件 `figures/taxonomy_detailed_success.pdf` · 正文引用：§5 A Taxonomy of Collaborative Failure Mode (L99)

## 图 5 · 第 7 页 · `figures/fig-05.png`
**caption**：Figure 5. Distribution of identified failure modes across the four chronological phases of the collaborative process.
· label `fig:taxonomy_distribution` · paper.tex L117 · 源文件 `figures/taxonomy_distribution.pdf` · 正文引用：§5 A Taxonomy of Collaborative Failure Mode (L115)；§6.1 Distribution of Failure and Success (L190)

## 图 6 · 第 9 页 · `figures/fig-06.png`
**caption**：Figure 6. Distribution of root causes for (a) unsuccessful and (b) successful collaborative outcomes.
· label `fig:pie_failure, fig:pie_success, fig:outcome_distribution` · paper.tex L194 · 源文件 `figures/pie_failure.pdf`、`figures/pie_success.pdf` · 正文引用：§6.1 Distribution of Failure and Success (L211)；§6.1 Distribution of Failure and Success (L192)

## 图 7 · 第 10 页 · `figures/fig-07.png`（整页，需要时手动裁）
**caption**：Figure 7. Key evidential unit (KEU) retention rate across collaborative stages and interaction rounds.
· label `fig:stage_keu_retention` · paper.tex L219 · 源文件 `figures/stage_keu_retention.pdf` · 正文引用：§6.2 Analysis of collaborative dynamics (L217)

## 图 8 · 第 11 页 · `figures/fig-08.png`（整页，需要时手动裁）
**caption**：Figure 8. Three metrics tracking collaboration and diagnostic quality across the interaction stages.
· label `fig:stage_collaboration_quality` · paper.tex L255 · 源文件 `figures/stage_collaboration_quality.pdf` · 正文引用：§6.2 Analysis of collaborative dynamics (L253)

## 图 9 · 第 12 页 · `figures/fig-09.png`
**caption**：Figure 9. Rates of four viewpoint shift patterns across collaborative stages and interaction rounds.
· label `fig:stage_viewpoint_shift` · paper.tex L333 · 源文件 `figures/stage_viewpoint_shift.pdf` · 正文引用：§6.2 Analysis of collaborative dynamics (L331)

## 图 10 · 第 13 页 · `figures/fig-10.png`（整页，需要时手动裁）
**caption**：Figure 10. Conflict resolution dropout rate across collaborative stages and interaction rounds.
· label `fig:stage_ccp_dropout` · paper.tex L371 · 源文件 `figures/stage_ccp_dropout.pdf` · 正文引用：§6.2 Analysis of collaborative dynamics (L369)

## 表 1 · 第 9 页 · `figures/tab-01.png`
**caption**：Table 1. Overall performance (accuracy (%)) of evaluated frameworks across six medical QA/VQA datasets.
· label `tab:benchmarked_datasets_performance` · paper.tex L168 · 正文引用：§6 Quantitative Analysis of Failure Modes (L166)

## 表 2 · 第 10 页 · `figures/tab-02.png`
**caption**：Table 2. Key evidential unit (KEU) missing rate (%). The percentage of critical facts lost between the initial proposal and the final conclusion. Higher values indicate more severe information loss.
· label `tab:keu_missing` · paper.tex L226 · 正文引用：§6.2 Analysis of collaborative dynamics (L217)

## 表 3 · 第 11 页 · `figures/tab-03.png`
**caption**：Table 3. Clinical priority mismatch rate (%). the proportion of agent outputs across the entire collaboration that do not carry the highest clinical risk level. Higher values indicate poorer risk awareness.
· label `tab:priority_mismatch` · paper.tex L262 · 正文引用：§6.2 Analysis of collaborative dynamics (L253)

## 表 4 · 第 12 页 · `figures/tab-04.png`
**caption**：Table 4. Domain specific activation rate (%). The frequency of domain agents providing unique, role-specific insights instead of generic responses. Higher values indicate more effective role-playing.
· label `tab:domain_activation` · paper.tex L283 · 正文引用：§6.2 Analysis of collaborative dynamics (L253)

## 表 5 · 第 12 页 · `figures/tab-05.png`
**caption**：Table 5. Bypassing evidence with voting-based decision rate (%). The frequency of failing to select the optimal evidence-backed argument, instead defaulting to a decision based on a simple majority vote. Higher values indicate less evidence-based reasoning.
· label `tab:voting_decision` · paper.tex L304 · 正文引用：§6.2 Analysis of collaborative dynamics (L253)

## 表 6 · 第 13 页 · `figures/tab-06.png`
**caption**：Table 6. Viewpoint shift dynamics (%). The frequency of occurrence for four collaborative patterns: M1 (successful minority correction), M2 (negative majority assimilation), M3 (robust majority resilience), and M4 (minority-induced derailment).
· label `tab:viewpoint_shift` · paper.tex L340 · 正文引用：§6.2 Analysis of collaborative dynamics (L331)

## 表 7 · 第 13 页 · `figures/tab-07.png`
**caption**：Table 7. Conflict resolution dropout rate (%). The percentage of identified critical conflicts that remained unaddressed in the final output. Higher values indicate poorer conflict resolution.
· label `tab:conflict_dropout` · paper.tex L378 · 正文引用：§6.2 Analysis of collaborative dynamics (L369)
