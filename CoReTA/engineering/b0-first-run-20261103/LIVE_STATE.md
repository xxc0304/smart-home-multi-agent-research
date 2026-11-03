# First formal B0 batch started — 2026-11-03

Current live root: /data2/xiaoxinchen/agent-research/CoReTA/runs/b0-first-run-20261103-v2/
Tmux: coreta_b0_attempt1_v2_20261103. Script engineering/b0-first-run-20261103/run_formal_v2.sh.

User confirmed Qwen3-4B and authorized next steps. Same fixed revision1cfa9a7/NF4bf16/r8alpha16/LR2e-5/batch1accum1/checkpointing,1796T/200V,seed20261102. Formal candidate1epoch1796 steps,3h soft budget; each V1h; no second attempt/C/B1 automatic launch.

Preflight outcome: original Vfirst3 all64token OUTPUT_LIMIT. Evaluation-only short-answer suffix applied identically B/E; same3 allEOS. No reference-answer-based tuning. Original full64tokenV baseline196OK/4OUTPUT_LIMIT,primary metrics disabled, pipeline stopped before train; preserve that directory. New v2greedy256token decoding freezes same B/E conditions and scoring on entire raw text; no answer extraction or cap search beyond this stage. ActualV maxinput5045+256 fits7326. Training messages unchanged, so evaluation-prompt conditioning is part of measured comparison; future team independent controls must match output requirements.

New v2V_B200 COMPLETE,200OK,EM0.135/F10.2539589213329843. These are V development baseline results, not independent qualification or collaboration evidence; no parameter change made because of scores.
Formal training actually started after completion gate, initial5/1796 observed at ~2.3s/step after startup. Completion not yet known. Pipeline conditional on COMPLETE train then runsV_E200, scores and selects sole candidate. Any incomplete stops; no C/H bodies or Cqualification runs. Technical adapters not reused. Known long-context allocator recovery warning retained, extra peakreserved/retry/OOM telemetry added.

Source/config/data freeze, self-review and both historical/new outputs retained in batch directories. New10unit regression PASS; environment spec06ec4d42 unchanged/warm reuse. Review independence=none, provisional. No paidAPI. Next handoff: read actual training_status and V_Escore/selected when they exist; don't claim expert advantage before independentC.
