# Complementarity: failure mechanisms and evaluation evidence

Date: 2026-10-19. Scope: primary-source reading for the CoReTA redesign. No implementation or experiments changed. All passages below are paraphrases. Reading depth means relevant full-text sections inspected, not every appendix independently audited. No claim here establishes a universal limit on collaboration.

## 1. Du et al. — Improving Factuality and Reasoning in Language Models through Multiagent Debate

**Identity verified:** Yilun Du, Shuang Li, Antonio Torralba, Joshua B. Tenenbaum, Igor Mordatch; arXiv 2305.14325 (2023; ICML 2024 publication should be cited separately if needed).

**Source/read depth:** [full text v1](https://arxiv.org/html/2305.14325v1), §§2.1, 3.1, design-choice analysis, Figs.4/11, Table1. Author-linked [project](https://composable-models.github.io/llm_debate/).

**Mechanism:** independent initial solutions, then synchronized rounds in which each model receives peers' previous responses and revises its own. Main reasoning comparison uses three agents and two rounds; controls include single generation, self-reflection and initial-answer majority vote. Tasks include arithmetic, GSM8K and chess. Table1 GSM8K: single77%, majority81%, debate85%.

**Evidence boundary:** the paper explicitly supplies all-initially-wrong→correct cases. This directly rebuts defining complementarity as selecting an initially correct member. However, Fig.4 omits intermediate reasoning; the cases do not isolate which local contributions were necessary or exclude additional self-reasoning as an explanation. No universal all-wrong recovery rate established in the inspected sections.

**CoReTA inference:** preserve all-wrong recovery as a target; collect local contribution provenance and compare interaction against continued independent reasoning. Mandatory debate in this paper actually executes revision rounds, unlike our optional help branch.

## 2. Choi, Zhu, Li — Debate or Vote: Which Yields Better Decisions in Multi-Agent Large Language Models?

**Identity verified:** Hyeong Kyu Choi, Xiaojin Zhu, Yixuan Li; arXiv2508.17536 (2025).

**Source/read depth:** [full text](https://arxiv.org/html/2508.17536v1), §§2–5, Table1, appendix headings; author-linked [code](https://github.com/deeplearning-wisc/debate-or-vote) exists as paper link, implementation not inspected.

**Setup:** five homogeneous agents; decentralized, sparse, centralized debate; 2/3/5 rounds versus voting initial answers. Qwen2.5-7B and Llama3.1-8B main comparison across seven benchmarks; larger/heterogeneous extensions also reported. Voting accounts for much of observed improvement and often matches or exceeds debate.

**Mechanism lesson:** exchanging whole answers does not itself establish new complementary reasoning. Their oracle intervention freezes an answer once known correct; it demonstrates value of preserving good signals but uses gold labels and is not deployable. Their martingale result assumes a particular Dirichlet–multinomial Bayesian update process: it is not an impossibility theorem for newly generated local insights or tool evidence.

**CoReTA inference:** reuse identical initial drafts in comparison conditions, preserve independent aggregation control, measure corrections and corruptions separately. Cost matching can be a later robustness analysis; attributing extra reasoning to interaction needs a continued-independent-reasoning control even before cost claims.

## 3. Kaesberg et al. — Voting or Consensus? Decision-Making in Multi-Agent Debate

**Identity verified:** Lars Benedikt Kaesberg, Jonas Becker, Jan Philip Wahle, Terry Ruas, Bela Gipp; Findings ACL2025, pp.11640–11671, DOI10.18653/v1/2025.findings-acl.606.

**Source/read depth:** [official PDF](https://aclanthology.org/2025.findings-acl.606.pdf), §§3.1–3.3, 4.2–4.3, Table1, AppendixB. Author-linked [code](https://github.com/lkaesberg/decision-protocols), code not inspected.

**Mechanism:** three task-generated personas, same Llama3 base per discussion; seven voting/consensus protocols. All-Agents Drafting enforces independent initial proposals. Collective Improvement blocks within-round communication and reveals only previous-turn solutions, preserving independent parallel updates rather than sequential agreement. CI is designed for voting, not consensus negotiation.

**Evaluation:** six datasets, three repeated runs; decision-protocol comparison holds other parameters fixed. StrategyQA Table1 reports baseline58.3%, CI65.7%; critical style alone59.4%, reasoning-only sharing51.9%. Thus simply demanding criticism or suppressing final answers is not supported as a generic cure.

**CoReTA inference:** shared access to all drafts can bias subsequent checks, but A0 currently seeing all drafts is not by itself a proven defect. Test limited/local visibility and independent checking as explicit alternatives. Embedding diversity and accuracy do not demonstrate local joint synthesis or all-wrong recovery causally.

## 4. Cemri et al. — Why Do Multi-Agent LLM Systems Fail?

**Identity verified:** Mert Cemri, Melissa Z. Pan, Shuyi Yang, Lakshya A. Agrawal, Bhavya Chopra, Rishabh Tiwari, Kurt Keutzer, Aditya Parameswaran, Dan Klein, Kannan Ramchandran, Matei Zaharia, Joseph E. Gonzalez, Ion Stoica; arXiv2503.13657.

**Source/read depth:** [full text v3](https://arxiv.org/html/2503.13657v3), §§4–5 and AppendixH/Table5; [official project](https://sites.google.com/berkeley.edu/mast/home), [dataset/code](https://github.com/multi-agent-systems-failure-taxonomy/MAST), code not inspected.

**Findings:** taxonomy separates specification, inter-agent alignment, verification/termination failures. A verifier can perform shallow or incorrect verification. This supports diagnosing both model mistakes and organizational rules that permit their propagation.

**Interventions:** AG2 math case compares improved verification prompt with solver/coder/verifier topology; only verifier can terminate. 200 GSM-Plus problems, six repetitions. Topology improvement is model-dependent (GPT4 not significant; GPT4o significant). ChatDev adds cyclic review until CTO confirmation, with maximum cutoff; evaluated on32 ProgramDev-v0 tasks and HumanEval. ProgramDev25.0%→40.6%, HumanEval89.6%→91.5%.

**CoReTA inference:** separate the action of proposing completion from reviewing completion; check actual objective-level evidence. Do not assume adding a named verifier guarantees truth or that more cyclic review always improves capability. Study supports structural intervention, not a ready-made universal protocol.

## 5. Parmar et al. — When Helping Hurts and How to Fix It: Multi-Agent Debate for Data Cleaning

**Identity verified:** Chirag Parmar, Akshat Mehta, Henglin Wu, Jagadish Ramamurthy, Shweta Medhekar; arXiv2606.02866v1, June2026 **preprint**, no peer-review status established.

**Source/read depth:** [full text](https://arxiv.org/html/2606.02866), §§6–7, Tables9/19, AppendicesI/J/L. Code not retrieved/verified.

**Mechanism:** Generator proposes JSON cleaning operations; Critic checks evidence and recommends acceptance/revision. Text-only feedback can invent problems and cause valid operations to be retracted. Proposed combination: executable critic evidence plus generator acceptance conditional on evidence.

**Evaluation:** four model families, three benchmarks; separate single-agent, tool-assisted self-verification, text debate, and code-grounded/evidence-gated debate. Table9 paired Claude subset(n84): baselineFC0.814; textdebate0.743; groundedcritic0.817; groundedcritic+gate0.867. Prompt-only evidence-gating comparisons(n50/cell) are explicitly nonsignificant. AppendixJ reports sampling diversity without useful aggregation because samples share blind spots.

**Caution:** paper has numerical inconsistencies across Table9/Fig9 (+5.3 versus+5.5pp); cite Table9 locally, avoid broad universal predictions. Factorial interpretation confounds the combined code+gating treatment; not every component is independently identified. Evidence is domain-specific, not proof all-initially-wrong local synthesis.

**CoReTA inference:** our erroneous-example absorption resembles the documented risk. Proposed evidence checks need concrete reproducible computations/assumptions; schema-valid reviews and “accepted/resolved” labels are insufficient. Hidden benchmark tests remain evaluator-only.

## Cross-paper implications (research recommendations, not established CoReTA results)

1. **Avoid the wrong target.** All agents initially failing does not rule out team recovery; Du et al. directly reports examples. Initial-correctness coverage is diagnostic only.
2. **Do not force helping as a success metric.** Branch execution establishes exposure, not capability. Test requests against identifiable unresolved subproblems, and allow justified completion.
3. **Separate three outcomes.** Existing-good-answer selection; genuine new correct reasoning; multiple local contributions connected into a correct solution. Current literature often reports the first two without identifying the third.
4. **Evaluate rescue and damage.** Record wrong→right, right→wrong, unchanged outcomes, and local claims introduced/corrected/corrupted, not merely final accuracy and number of messages.
5. **Use causal controls for mechanism claims.** Shared initial draft bank; continued solo/independent reasoning; initial aggregation; peer contribution omitted/replaced; review/evidence/connection ablations. Contribution removal is imperfect because substitute context can change generation, so use repeated outcomes and trace evidence together.
6. **Preserve independence selectively.** Independent draft generation is already present. Candidate visibility and review context are design variables; no reviewed work proves that hiding everything is best.
7. **Keep task integrity separate from mechanism diagnosis.** Difficulty and clear evaluation are necessary to see improvements; do not select tasks after observing CoReTA wins or select only natural-help traces.
8. **Most transferable changes are content/decision rules.** Evidence-grounded contribution, independent verification, explicit completion review, real change records. Merely multiplying roles, demanding criticism, or adding rounds is insufficiently justified.

## Reading limitations

No official repository implementation was inspected in this scout pass. The papers above therefore support architecture/evaluation patterns, not claims that a particular request JSON or function can be copied verbatim. New information-theoretic coordination work is being inspected independently by the root researcher; synergy statistics should not be equated automatically with traceable local joint completion.
