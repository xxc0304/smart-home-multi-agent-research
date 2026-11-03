# Local-work prototype build

Effort: balanced; ASK=never; assurance=draft. No paid API or model transport.

| Rung | Feature | Acceptance command (PYTHONPATH=src;tools) | Tier | Status |
|---|---|---|---|---|
| F0 | Offline entrypoint -> labelled trace | python tools/check_local_work.py --stage spine --output runs/local-work-offline-20261027-v1 | MUST | PASS |
| F1 | Official-data adapter, source isolation | python tools/check_local_work.py --stage data --output runs/local-work-offline-20261027-v1 | MUST | PASS |
| F2 | Work/value nodes, owner bindings, arithmetic continuation, invalidation | python tools/check_local_work.py --stage engine --output runs/local-work-offline-20261027-v1 | MUST | PASS |
| F3 | Invalid inputs, historical common-interface replay, preparation report | python tools/check_local_work.py --stage all --output runs/local-work-offline-20261027-v1 | MUST | PASS |

## Run record

Base commit recorded in SPEC. Existing response decoder and source handling inspected; reuse strict JSON/schema decoder from coreta.handoff.contracts. Existing candidate constraint executors assume per-task field vocabularies; do not repurpose them as automatic work discovery. Source download initially blocked by sandbox network; read-only public download escalation requested, no local research content uploaded.

F0 exited 0 and created SPINE_SMOKE.json. Official train JSON (12,845,647 bytes) and README downloaded successfully. Separate data-inspection print hit Windows GBK output on a euro symbol; set PYTHONIOENCODING=utf-8 for subsequent commands. This was not a model response or an experimental format failure.

F1 exited 0, exported six train questions with complete native table/text and separate offline references; F0 remained green. Data inspection shows table-text includes unit-only dependencies, so annotation is not treated as proof of meaningful work dependency. First engineering trace uses original task-05 table total 1344.1 and paragraph committed 1137.4, manually scripted and labelled accordingly. Prompt packs land with F2, once the actual state/schema exists.

F2 exited 0; F1/F0 rechecked exit 0. F3 exited 0 with 19 engineering checks, 12 complete historical old-contract/source-carrier replays, 12 new initial request packs. Maximum initial instructions length 4299 characters; not a token budget bound or evidence about maximum continuation inputs. All old outputs are correctly incompatible with new work schema, recorded as missing generation coverage, not falsely passed as new-interface outputs.

Current code files: src/coreta/local_work/{__init__,data,engine,prompts}.py; tools/{check_local_work,local_work_offline_trace,replay_local_work_history}.py; tests/test_local_work.py. No prior experiment artifacts or core runtime were edited. Network model calls 0.

Sweep round 1 found two real gaps: stale-snapshot provider metadata could be accepted, and all consumer revisions unnecessarily cleared inputs. Added reproductions: four new/revised assertions failed against old code (3 failures/1 error), then passed after fixes. Final full check exited 0 with 22 checks and unchanged 12 old-contract replays. Ledger updated before the fixes. Sweep round 2 reran both scenarios and reported no remaining undeclared decisions/stale rows, semantic_undeclared=0. Same-family/provisional only, not an independent correctness or effectiveness certificate. Both verbatim review JSON replies retained in SILENT_ASSUMPTION_SWEEP.json.

## Deferred

- Natural generation of work/bindings and live team comparison: requires separate frozen model batch, scientific/readiness review and authorization.
- Time, boolean filtering, unrestricted code, learned routing, support-environment enumeration.
- Per-rung commits: repository has extensive pre-existing untracked research; preserve working tree and explicit file list instead of sweeping unrelated files into a commit.

## Blockers

No paid-run readiness claim. New-schema natural generation, strong baseline runner, frozen experiment/limits/authorization are deferred, not covered by these offline checks.
