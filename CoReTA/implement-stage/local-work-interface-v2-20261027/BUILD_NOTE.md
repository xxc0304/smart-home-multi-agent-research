# Build note

| Rung | Feature | Acceptance command | Status |
|---|---|---|---|
| F0 | Existing full-response replay is reproducible | `python tools/analyze_local_work_calibration.py` | PASS |
| F1 | Versioned own-member feedback and shared interface guidance | `python -m unittest discover -s tests -p test_local_work_interface_v2.py` | PASS |
| F2 | Full 42-response replay, new prompt assembly and prior regression checks | `python tools/check_local_work_interface_v2.py --output runs/local-work-interface-v2-check-20261027` | PASS |
| F3 | Mixed task-fit and next experimental design | inspect source-level TASK_REVIEW and EXPERIMENT_REVIEW; no model scores | PASS (developmental scope) |
| F4 | Bounded mixed runner and failure qualification | `python tools/check_local_work_v2_batch.py --data runs/local-work-v2-mixed-data-20261027-v2 --output runs/local-work-v2-batch-check-20261027-v2` | PASS |

## Run record

Pre-implementation: read project experiment charter, current engine/flow/prompts, current result audit and implementation skill. Prior batch source is left unchanged. No commits: existing dirty research checkout contains unrelated work and experiment records.

F0: full original 42-response replay exited 0; six final deliveries match; frozen code and preparation unchanged. No network calls.

F1: 8 targeted tests pass. Initial test expected ValueError but decoder raises ProtocolError; corrected the test to match the existing contract, not the implementation.

F2: 47 accumulated tests pass; 42 complete real replies preserve final deliveries and engine events. Maximum replay input estimate including margin is 4732, total145683. This is the observed old-output load, not an upper bound on new model output. No network calls.

Updated F2 after review fixes and the discussion control: 49 accumulated tests pass; all42 original replies and six delivered results preserved. Maximum replay input estimate4682, total143883. Prior intermediate check outputs retained as superseded local checks.

F3 data: four original questions prepared, ordinary cases unchanged, dependency tables reconstructed cell-for-cell from whole-column projections; manual source arithmetic agrees with unmodified official scoring. See research/local-work-v2-mixed-20261027/{TASK_REVIEW,PLAN}.md. Original two-arm/56-slot draft retained at local-work-v2-mixed-data-20261027-v1; current three-arm/84-slot data is v2. Neither has made API calls.

F4: 84-slot real-history carrier completed offline, maximum input5375/total264642; one incomplete reply isolates its flow and ends after79 fixture calls; two consecutive incomplete replies stop after2; missing usage, output overrun and transport failure stop after1 each. Unreviewed, fixture-only, unbound-authorization and frozen-case-change paths rejected. No network calls.

Sweep round1 found successful-use attribution of unavailable IDs and unverified new oneOf provider syntax. Fixed the former with ready-rendering checks/regressions; removed the latter, keeping existing runtime validation. Ledger A14-A15 records these findings. Round2 requested on final code and task/runner additions. Same-family/provisional, not external independent approval.

Final executor checks: 50 checks pass, 42 actual prior replies replayed with unchanged results; 84-slot full historical carrier and seven failure fixtures pass at runs/local-work-v2-batch-check-20261027-v4. Separate offline scorer retains all12 planned rows and refuses fixtures; reference files are frozen outside runtime packets. No model calls and no live stubs.

Final freeze/verify exits0: runs/local-work-v2-mixed-prepared-20261027-v1, manifest713f929f2b5e30c047f540615b1edcc7b4fecbb4d95887a2df44f8adc8416867. Runtime/labels/code/config frozen; local bounded_mixed_development PREFLIGHT and EXPERIMENT_REVIEW bound. No authorization file, no paid calls. Review outcome is RUN_ALLOWED_AFTER_BATCH_AUTHORIZATION, not unrestricted run permission.

Review round2 identified all-unstarted-flow export, manual interruption/unknown-usage preservation and ledger wording; findings fixed, A18-A19 recorded. Reviewer messages verified the substantive runner fixes, but its final JSON generation failed due to usage limit. Record is SWEEP_UNAVAILABLE_FINAL_JSON, not a clean verdict. Final A10 wording, scoring export/frozen labels and explicit preflight gate verified by executor only; no third sweep or independent-approval claim.

## Deferred

New paid run, inference about stable benefit, automatic semantic condition resolution and general-purpose dependency discovery.

## Blockers

No known local implementation blocker after deterministic checks. The local draft-level execution review can pass with the explicitly disclosed review limitation; this is not external method validation. New live requests require separate batch-specific authorization. Stable-benefit inference is deferred.
