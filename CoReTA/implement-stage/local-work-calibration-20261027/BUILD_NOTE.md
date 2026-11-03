# Calibration build

Effort balanced, draft, ASK never. Four rungs, no paid request.

| Rung | Deliverable | Check | Status |
|---|---|---|---|
| F0 | Two-case/six-flow runtime schedule | run_local_work_calibration.py freeze --prepared runs/local-work-calibration-spine-20261027-v1 | PASS |
| F1 | Gated transport/budget/checkpoint runner | check_local_work_calibration.py --stage runner --output runs/local-work-calibration-check-20261027-v1 | PASS |
| F2 | Full historical carriers, generated-field/error/usage/guard fixtures | check_local_work_calibration.py --stage all --output runs/local-work-calibration-check-20261027-v1 | PASS |
| F3 | Scientific/readiness verdict and frozen preflight | run_local_work_calibration.py verify --prepared runs/local-work-calibration-prepared-20261027-v1 | PASS |

## Run record

Previous mixed preparation finished39 checks,12 historical replays, zero model calls; round2 same-family sweep found all three reported issues resolved, semantic_undeclared=0. Both reviews recorded; no method effectiveness inferred. Reuse ComparisonFlow and DeepSeekClient instead of new transport.

F0 initially caught an unclosed list in the new schedule constructor, fixed before successful local freeze; no API involved. F0 then exited0 and wrote a labelled spine freeze, not a release. F1/F2 complete local checker v1 exited0: valid42/42fixture calls; one bad core/incomplete envelope isolate firstflow and continue independent flows37 attempts; two unreadable, transport error, missing usage, over-output each stop after2 attempts. Authorization/tamper gates reject before live call. Full historical carrier42-stage flow fits estimated122978 total input, maximum3942 per request; old full contract replay12. No natural new-schema generations and no model network calls. Fixture numbers never treated as scores.

Removed the F0 incomplete-source exception from production freeze; final release requires all named sources. New files tools/run_local_work_calibration.py and tools/check_local_work_calibration.py; reuse named local_work engine/comparison, old model_client and tokenizer.

Review round1 found fixture-only gates accepted by live verifier and malformed HTTP JSON body not retained. Ledger C-014/C-015 declared fixes before code. Added scope isolation and batch-only HTTP body-preserving adapter, leaving shared historical model_client unchanged. Full checker v3/v4 passed with body checks. Round2 confirmed these fixes but found the checker left a temporary live-shaped gate on disk. Fixed by restoring fixture gate in finally; full checker v5 and final artifact scope assertions passed. Last review still reported one gap; final fix verified by executor only after two-round review budget. No claim of independent acquittal. Verbatim replies plus post-review fix record saved in SILENT_ASSUMPTION_SWEEP.json.

Final input total changed before release to688128 (=42x16384), preserving per-request ceiling; v1 snapshots correctly reject current changed config. v5 checks valid42, onebad37, global/system failures2, zero API; max full historical carrier estimate3942, total122978. Previous39 local-work/mixed unit checks reran green after source changes. Final release freeze and batch review still to be recorded.

Final release prepared-v1 manifest273f74a32951c0db969f1e1c94d03eae3ff32b1b50f868cd8c92430e3845d8ce. Bound preflight plus explicit science/readiness review scope bounded_protocol_calibration verified exit0; natural new-schema coverage0 disclosed. Saved reviewed human-readable scope and machine gate. No authorization record created, no live API call. All MUST rungs ran; model effectiveness and final external authorization remain outside build. No live stubs; deterministic transport fixtures expressly engineering-only.

## Deferred

Actual API call pending user batch-specific authorization; full14-task development matrix; natural-output efficacy; cross-domain confirmation. No per-rung commits in existing heavily dirty/untracked repository.

## Blockers

First new-schema live output remains absent. Review must explicitly treat next batch as bounded protocol qualification; no claim format guaranteed.
