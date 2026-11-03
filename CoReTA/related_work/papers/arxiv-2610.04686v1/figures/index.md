# 图表索引

来源 `paper.pdf`（27 页）：图 4 张、表 20 张。全部裁剪拼在 `figures/_contact.png`，一次看完。

> 讲到哪张图就把那个 PNG 发给用户；讲之前自己先看一眼——caption 不会告诉你图是怎么排的。
> 裁得不对：`crop.py paper.pdf --page P --grid` 看带刻度的整页，再 `crop.py paper.pdf --page P x0 y0 x1 y1 -o figures/fig-NN.png` 重裁（坐标是页面比例 0–1）。

## 图 1 · 第 2 页 · `figures/fig-01.png`
**caption**：Figure 1: Overview of the supply-readout view. Transparent regions denote questions for which individual sampled agents can surface the correct answer; solid regions denote questions recovered by the final readout. Top: Overlapping sampled agents provide redundant proposal coverage, so majority vote keeps a small shared region and can reinforce a repeated wrong answer. Bottom: Diverse agents provide complementary proposal coverage; after debate, LVD uses verification-aware evidence to recover a surfaced correct minority answer.
· label `fig:teaser` · paper.tex L71 · 源文件 `figures/Teaser_May_7.pdf` · 正文引用：§1 Introduction (L95)

## 图 2 · 第 4 页 · `figures/fig-02.png`
**caption**：Figure 2: Motivating observations. (a) Qwen2.5-3B-Instruct shows null-like debate dynamics with little gain over vote, while Qwen3-4B-Instruct shows positive gain across rounds. (b) Under the same neural-thicket supply regime, Debate readout improves over vote, while the proposal-hit upper bound remains higher, indicating recoverable headroom. (c) Final debate lift is positively correlated with initial proposal-hit headroom, suggesting that debate is supply-constrained. Together, these observations motivate a supply-readout account: debate helps when correct minority proposals are surfaced and the readout can recover them through verification-aware dynamics.
· label `fig:motivating_observations` · paper.tex L214 · 源文件 `figures/motivating_observations.pdf` · 正文引用：§2.1 Proposal Setup and the Martingale Null (L206)；§2.1 Proposal Setup and the Martingale Null (L260)；§2.1 Proposal Setup and the Martingale Null (L265)；§A.1 Implementation Details for \figreffig:mo (L1040)

## 图 3 · 第 9 页 · `figures/fig-03.png`
**caption**：Figure 3: Label-based five-round dynamics. Solid lines show round-level accuracy before finalization; dashed hollow legend entries marked “Oracle” show proposal-hit coverage. Later rounds can improve vote accuracy while reducing answer diversity, so final gains depend on recovering correct proposals before coverage collapses. The label-free counterpart is in Fig. 4.
· label `fig:r5_debate_dynamics_label_based` · paper.tex L872 · 源文件 `figures/r5_debate_dynamics_label_based.pdf` · 正文引用：§5 Experiments (L885)；§A.12 Complete Round-Level Statistics (L1891)；§A.12 Complete Round-Level Statistics (L1899)

## 图 4 · 第 23 页 · `figures/fig-04.png`
**caption**：Figure 4: Label-free five-round dynamics. This appendix counterpart to Fig. 3 shows methods that do not use labeled training diagnostics for society selection. Solid lines show round-level majority- vote accuracy before finalization; dashed hollow legend entries marked “Oracle” show proposal-hit coverage.
· label `fig:r5_debate_dynamics_label_free` · paper.tex L1887 · 源文件 `figures/r5_debate_dynamics_label_free.pdf` · 正文引用：§5 Experiments (L879)；§A.12 Complete Round-Level Statistics (L1900)

## 表 1 · 第 7 页 · `figures/tab-01.png`
**caption**：Table 1: Accuracy (%) on Qwen3-4B-Instruct and OLMo-3-7B-Instruct under a unified computation budget. SC and Neural thicket vote rows use vote20; debate rows use round-3 (R3) majority vote from matched five-round, four-agent traces. MMLU-Redux is split into five 60-example subjects. Avg is the unweighted mean over the eight displayed columns, and Avg Ranking is the mean within-block method rank. Boldface and underline denote the best and second-best result per column within each method block and model. Gray rows mark our proposed agent pool construction methods.
· label `tab:main_results, tab:call_aligned_r3, tab:olmo_main_r3_call_aligned` · paper.tex L571 · 正文引用：§5 Experiments (L771)；§5 Experiments (L782)；§A.5 Five-Run Stochastic Robustness (L1184)；§A.10 Dynamics and Conversion Controls (L1688)

## 表 2 · 第 8 页 · `figures/tab-02.png`
**caption**：Table 2: AMC12-selected seed transfer to MMLU-Redux. Init, R3, and R5 report pre-debate, round-3, and round-5 metrics over the same four agents. Final is the R5 vote-then-judge readout; Lift is Final minus Init Vote. Values are percentages except N. Gray rows mark our greedy construction methods.
· label `tab:amc12_mmlu_transfer_r5` · paper.tex L803 · 正文引用：§5 Experiments (L862)；§A.11 Secondary Construction and Transfer Diag (L1720)

## 表 3 · 第 10 页 · `figures/tab-03.png`
**caption**：Table 3: Controlled fixed-proposal evidence for verification-aware readout. Trace effect is the answer- margin shift from an original correct peer response relative to neutral context; c W is its median equivalent controlled support over recovery cases. T −F is the gold-margin difference between answer-stripped correct and wrong rationales. ∆Acc is correct-support accuracy minus neutral accuracy at d = 3. All entries use the main readout configuration; secondary configuration controls are reported in the appendix.
· label `tab:lvd_controlled_probes` · paper.tex L941 · 正文引用：§5 Experiments (L937)

## 表 4 · 第 14 页 · `figures/tab-04.png`
**caption**：Table 4: Compute used by the reported experiment families. Profiling times vary with dataset size and output length; downstream times vary with the backbone, dataset, and number of debate rounds.
· label `tab:compute_resources` · paper.tex L1094 · 正文引用：§A.3 Compute Resources (L1090)

## 表 5 · 第 15 页 · `figures/tab-05.png`
**caption**：Table 5: Licenses and stated terms for existing model and dataset assets.
· label `tab:asset_licenses` · paper.tex L1142 · 正文引用：§A.4 Existing-Asset Licenses (L1138)

## 表 6 · 第 15 页 · `figures/tab-06.png`
**caption**：Table 6: Five-run stochastic robustness under a common decoding configuration. Panel (a) reports mean ± SD across five generation seeds; bold marks the highest mean within each backbone and column, not statistical significance. Panel (b) reports paired comparisons of the five matched run-level eight-column averages. Effects and confidence intervals are in percentage points. Comparisons near the nominal p = .05 threshold should be interpreted cautiously. (a) Per-benchmark accuracy and eight-column average.
· label `tab:stochastic_robustness` · paper.tex L1194 · 正文引用：§A.5 Five-Run Stochastic Robustness (L1187)

## 表 7 · 第 16 页 · `figures/tab-07.png`
**caption**：Table 7: Seed-quality diagnostics for the main-table backbones. Values are percentages on the profiling split. Base ref. is the same-split unperturbed pass@1 reference. The Used column marks scales retained for downstream construction.
· label `tab:seed_profiling_details` · paper.tex L1286 · 正文引用：§A.7 Seed Profiling Details (L1267)；§A.11 Secondary Construction and Transfer Diag (L1836)

## 表 8 · 第 18 页 · `figures/tab-08.png`
**caption**：Table 8: Original peer-response effects and equivalent conclusion-only support over recovery cases. Trace effects are means with 95% confidence intervals; c W is the median interpolated equivalent support. The final column reports the correct-support minus wrong-support answer margin under the Verify prompt at each dose.
· label `tab:lvd_equivalent_support_full` · paper.tex L1440

## 表 9 · 第 18 页 · `figures/tab-09.png`
**caption**：Table 9: Truth sensitivity of answer-stripped trace rationales. Entries are mean margin changes with 95% confidence intervals, shown as Standard / Verify.
· label `tab:lvd_answer_stripped_full` · paper.tex L1466

## 表 10 · 第 18 页 · `figures/tab-10.png`
**caption**：Table 10: Free-generation accuracy after three peer messages. Each entry evaluates the same 50 questions. Correct support is bolded.
· label `tab:lvd_free_generation_full` · paper.tex L1495

## 表 11 · 第 19 页 · `figures/tab-11.png`
**caption**：Table 11: Round-level prompt-style dynamics averaged over the 15 matched dataset-method cells. R0 is identical because both controls use the same seed answers before debate. ∆is Standard minus Verify. All values are percentages.
· label `tab:r5_prompt_style_dynamics` · paper.tex L1555 · 正文引用：§A.9 Controlled Readout Probe Details (L1528)

## 表 12 · 第 19 页 · `figures/tab-12.png`
**caption**：Table 12: Prompt-style control for the five-round new-seed debate runs. Verify Final is the completed verify_then_answer debate prompt; Standard Final repeats the same datasets, seed banks, verifier settings, and vote_then_judge_tiebreak finalizer with the normal standard debate prompt. ∆ is Standard Final minus Verify Final. All accuracy values are percentages.
· label `tab:r5_prompt_style_control` · paper.tex L1577 · 正文引用：§A.9 Controlled Readout Probe Details (L1529)

## 表 13 · 第 20 页 · `figures/tab-13.png`
**caption**：Table 13: Immediate-finalizer and interaction control. Panel (a) compares the R0 and R5 states by method. The final column is R5 Vote+Judge minus R0 Vote+Judge; confidence intervals resample questions within each benchmark before recomputing the unweighted macro average. Panel (b) applies the same finalizer at every saved stage and averages over all four societies and five benchmarks. All accuracy, hit, gain, tie, and unanimity values are percentages.
· label `tab:immediate_finalizer_control` · paper.tex L1632

## 表 14 · 第 20 页 · `figures/tab-14.png`
**caption**：Table 14: Association between initial headroom H = P0 −V0 and final lift G = F −V0 on the two backbones. The MMLU row reports a 95% paired question-bootstrap interval for Pearson r.
· label `tab:backbone_headroom_conversion` · paper.tex L1691

## 表 15 · 第 21 页 · `figures/tab-15.png`
**caption**：Table 15: AMC12-to-MMLU-Redux transfer decomposition. Recovery rate is conditional on R0 headroom; the contribution columns are unconditional percentage points.
· label `tab:transfer_decomposition` · paper.tex L1726

## 表 16 · 第 21 页 · `figures/tab-16.png`
**caption**：Table 16: Complementarity and held-out coverage on Qwen3-4B MATH500. Panel (a) uses the 200-question construction split. Panel (b) freezes each four-agent society and evaluates cumulative R0 proposal-hit coverage on 300 held-out questions; agents are listed in selection order, and tied construction accuracies share the minimum rank.
· label `tab:complementary_coverage` · paper.tex L1762

## 表 17 · 第 22 页 · `figures/tab-17.png`
**caption**：Table 17: Sensitivity to candidate-pool size N and construction-set size m. Each arrow follows the increasing values shown in the column header.
· label `tab:construction_sensitivity` · paper.tex L1811 · 正文引用：§A.11 Secondary Construction and Transfer Diag (L1808)

## 表 18 · 第 22 页 · `figures/tab-18.png`
**caption**：Table 18: Fixed-society Qwen3-4B MMLU-Redux results. Hidden-Prefix and TopAcc report mean ± SD across 10 paired generation seeds; AC-Greedy and SC-Greedy are the submitted fixed runs and are included only as reference points.
· label `tab:hidden_prefix_construction` · paper.tex L1853

## 表 19 · 第 24 页 · `figures/tab-19.png`
**caption**：Table 19: Round-level recovery diagnostics averaged over the five benchmarks. For each round, Vote and Hit are the round-specific majority-vote and proposal-hit accuracies, while Final is the end-of-run vote_then_judge_tiebreak accuracy. We define H = P −V , G = D−V , ρ = G/H, R = Pr(D = 1 | P = 1, V = 0), I = Pr(D = 1 | P = 0, V = 0), and L = Pr(D = 0 | V = 1), where D is the final decision. All values except ρ are percentages; averages are unweighted over benchmarks.
· label `tab:round_recovery_diagnostics` · paper.tex L1949 · 正文引用：§A.12.1 Average Recovery Diagnostics (L1999)

## 表 20 · 第 25 页 · `figures/tab-20.png`
**caption**：Table 20: Five-round debate results for the new seed teams. Final is accuracy after vote_then_judge_tiebreak; Lift is Final minus Init Vote. Bold marks the best final accuracy within each dataset. Average rows report the unweighted mean across the five benchmarks.
· label `tab:r5_new_seed_debate` · paper.tex L2014 · 正文引用：§A.12.2 Five-Round New-Seed Debate Results (L2052)
