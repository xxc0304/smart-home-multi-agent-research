# V20 precision diagnostic: prelaunch review

Assistant self-review, 2026-11-03; review_independence=none/provisional.

Goal: distinguish a possible quantization contribution to the weak baseline from team-process effects. No team or general-capability claim. First20 existing V IDs, already development/selection data, selected by fixed order rather than scores. No correct conditions, gold extraction or expert adapter is supplied to generation. C/H are not read.

Scientific meaning: PASS. NF4 and unquantized BF16 use the same model revision, messages, template, greedy256 generation and official scorer. Precision is the sole intended intervention; latency/memory and numerical answer changes are outcomes. This is a sensitivity check, not a method comparison or optimal baseline search. No effect is also a valid outcome; 20 items do not support population estimates or rule out all quantization effects.

Preparation: PASS within this finite scope. Actual remote PREFLIGHT.json confirms first20 ordered IDs, same historical input lengths, max3696 input tokens plus256 below7326, replayed real raw-answer scores identical, missing/OUTPUT_LIMIT export INCOMPLETE with null means, free GPU25048449024 bytes. Existing CUDA/bfloat16 environment is available; no package installation or weight download. Frozen runtime, config, scorer, source and target bytes and prompt-token hashes bind both arms.

Freeze SHA256: b58fd1958987d885479ae2abc12154fd2432e21756e293b1d984b7f04b028304.

Stop/budget: baseline NF4 then BF16 in separate processes; no more than20 generations each/40 total. Generation+load elapsed budget600 seconds per arm, subprocess hard cutoff660 seconds including import/teardown allowance; outer pipeline hard timeout1800 seconds. This explicitly clarifies the PLAN wording of600 seconds: process overhead has a bounded60-second allowance, not additional generations. Any technical failure/incomplete arm stops the pipeline; no retries, replacement questions, expansions or automatic B1. Original runs remain unchanged; all new/partial answers and missing IDs remain in this separate run directory. Output-limit is technical incompleteness, wrong answers are semantic outcomes. No new structured-output/citation protocol is introduced, so its unused JSON/receiver boundaries are not relevant to this answer-only diagnostic.

Overall: RUN_ALLOWED for this V20 diagnostic only. User authorization: begin the stated finite diagnostic in this chat; dedicated SSH access separately authorized. This is not authorization for paid API batches, training, new models or B1. Preserve the two current precision conditions even if one is worse. On completion export paired EM/F1, historical NF4 answer agreement, status/cost/memory and stage self-review, then record the bounded next action.
