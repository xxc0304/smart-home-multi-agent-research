# Formal B0 attempt1 + V review 2026-11-03

Assistant self-review, review_independence=none, acceptance_status=provisional.
Scientific meaning PASS: construct one task adapter, compare against same base on fixed V200.
This is bounded expert preparation, not expert qualification or team mechanism evidence.
T1796/V200 fixed, no re-split/no C/H. Original prefix3 used only for EOS/interface;
v1 all3 OUTPUT_LIMIT retained, v2 same3 normal EOS. No correctness-based prompt search.
Evaluation suffix strengthened existing short-answer requirement, applied identically B/E;
training examples unchanged. Scores apply to this evaluation condition only, future B1
needs matching standalone controls. No gold injected into model prompts or extracted answers.

Readiness PASS: official3-shard integrity, environment06ec4d42, CUDA/NF4/bf16,
allT/V template masks/lengths, longest7326-token actual step,10step save/reload passed.
Actual prefix outputs replay through original scorer; incomplete original cannot gain metrics,
technical v2 cannot enable primary scoring. All200 actual generation prompts fit cap7326
including64new tokens. Affected10unit checks pass; final source frozen below.

RUN_ALLOWED: V_B200 once (wall3600s); only if technically COMPLETE, train attempt1
original1796 rows,1epoch/batch1/accum1/r8/alpha16/LR2e-5/seed20261102/NF4bf16,
checkpointing, wall10800s. FullV_E200 same inference and wall3600s after COMPLETE
training and saved adapter origin expert_training. Select sole candidate by V EM/F1;
selection does not establish independent task advantage. No auto second attempt/C/B1.
Known longest allocator recovery warning retained; record reserved/retry/OOM stats.
OOM/nonfinite/timeout stops affected batch and dependent actions; no automatic retries.
No candidate from partial or technical adapters. Raw baseline/adapter outputs and null
failures remain. Prefix repeated only as clearly separate engineering/official evaluations.
Maximum active budget5h (3h train +1h eachV), no paidAPI. Previous short training
suggests ~68min loop but not guarantee; prefixV latency is small/nonrepresentative.

## v2 superseding batch — before launch
Original fullV200 produced OUTPUT_LIMIT so scored INCOMPLETE and pipeline stopped
before any formal training. Original responses/failed selection gate retained. Only
change: same B/E greedy output cap256 (previous64). No correctness-based selection,
new prompt, sample, seed, train-target or scoring change. Both groups fully evaluated
under new cap, old baseline cannot be mixed with new E. Raw entire responses scored,
no gold extraction, verbosity can still lower EM/F1. Engineering protocol revision
per existing plan allowance for systematic truncation; not a second train attempt.
Max5045+256<7326 confirmed. Prior3 real outputs replayed and full200 failures retained.
Readiness PASS for bounded v2 conditional on affected regression pass. Scientific
meaning PASS within new decoding condition only. RUN_ALLOWED V_B200 once; only if
COMPLETE launch original first formal1796/1epoch training and then V_E200, with same
3h/1h/1h budgets and stop rules. If any v2 technical incomplete, STOP this pipeline;
no further prompt/cap search in this work stage. No C/H or B1.
