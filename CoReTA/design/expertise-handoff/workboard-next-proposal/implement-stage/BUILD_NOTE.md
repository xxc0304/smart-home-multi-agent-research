# D0 build note

| Rung | Feature | Acceptance command | Tier | Status |
|---|---|---|---|---|
|F0|Opt-in runner walking spine, scripted journal to result|python -m unittest discover -s tests -p test_workboard_d0.py -k spine|MUST|passed|
|F1|Focus contracts, public cross-cycle records and revision links|python -m unittest discover -s tests -p test_workboard_d0.py|MUST|passed|
|F2|Offline replay entry point, negative lifecycle/source checks and v3 regression|python -m unittest discover -s tests -p test_workboard*.py|MUST|passed|

Commands run with project .venv Python. No live solves, benchmark claims or paid calls.

## Run record

- F0 exit 0: 1 offline spine check; temporary journal/state/result emitted, no model or network call.
- F1 exit 0: 2 accumulated offline checks, including focus→responses→trial→independent checks→disposition; three-member full path 19 scripted transport attempts.
- F2 first D0 suite: exit 0, 12 checks in 16.771s. After adding native HiddenBench choice coverage and removing a redundant setup, D0 suite: exit 0, 13 checks in 18.556s.
- Existing workboard family plus then-current 12 D0 cases: exit 0, 61 checks in 79.316s. Existing HiddenBench workboard suite: exit 0, 10 checks in 23.394s. Every transport in these suites is scripted/network-guarded; printed http_attempts values are simulated, not live requests. The later edit only added choice-path coverage and removed redundant test setup.
- F0/F1 persistent end-to-end replay: `runs/workboard-d0-engineering-20261022-r1/SCRIPTED_stage_responses.json` → `replay/{state.json,result.json,replay.json}`. 29 scripted transport invocations, actual HTTP 0, fixture usage explicitly not billable. No accuracy evaluation. Script generated from deterministic engineering fixture, not natural model traces.
- Compared all 12 existing src/coreta/workboard/*.py bytes against the existing HiddenBench prepared-r2 manifest: all unchanged. This reuses the project's existing freeze mechanism; no new pinning system.
- First same-family review found 1 undeclared semantic choice (navigation links), 1 stale visibility row and 1 actual defect (cited base work disappeared from later choices). D11 explicitly labels links; D12 supplies focused historical checks to later stages; D14 retains base/cited work. The cited-work regression test failed before fix (W2 missing), then final suite passed.
- Final D0 suite exit 0: 15 checks in 22.164s, including the defect regression. Final CLI replay exit 0: runs/workboard-d0-engineering-20261022-r1/replay-final/replay.json; 29 scripted invocations, 0 HTTP. The earlier replay directory is preserved as pre-review engineering output; replay-final is the final-build artifact.
- Second-round same-family review found 0 undeclared semantic assumptions, no remaining implementation defect, and one D12 wording mismatch. Reviewer confirmed all three first-round findings fixed. D12 wording was corrected to state exact after-work/focus_id/offer.responds_to filter; that last documentation edit was executor-checked only. Both raw reviewer JSON replies are preserved in SILENT_ASSUMPTION_SWEEP.json. Review remains same-family/provisional; no clean/acquittal or method-effect claim.
- No live stubs; scripted transport is an explicit offline replay input, not a production solver.

## Semantic decisions and their meaning

ASK=never. These decisions are declared defaults except D02 (authorized design) and D11 (review finding). They do not assert experimental efficacy.

|ID|Decision|
|---|---|
|D02|Same editor, offer rotation, N−1 cycles, stage output caps and four closure calls. No automatic preference for focus responses. No live runs in this build.|
|D04|Latest pending focus gets priority; all focus history and raw feedback remain public. Prior pending focuses stay pending, not automatically discarded. Disposition may address only the input active focus; null means no update.|
|D05|addressed is a model report only, never verified. Pending entries become deferred at stopping/interruption; FINAL_CHOOSE may report disposition for its input focus but cannot open a new one. All-pass/unable never marks addressed.|
|D07|Focus references are public reports, not grants to originals. Legal source IDs stay member-specific. Targets are enumerated from visible work IDs/locations plus whole_goal. Related prior works remain visible so changed versions can be reconsidered.|
|D08|Host validates references, response links and dispositions; does not judge whether a question is useful or answered correctly. No auto-deduplication of natural language questions and no automatic truth metric.|
|D10|Pending focus remains visible to all closure calls; after closure any remaining pending focus is deferred. Error exits defer pending focus even if delivery fails. Source/format errors retain existing stop semantics.|
|D11|Successful TRY can create a navigation link despite unrelated offer or reuse. relation separates active_context_only and selected_response; neither proves correct or actual semantic use. Trials failing materialization have no link.|
|D13|result.status describes protocol delivery; replay_complete/replay_error describe strict scripted replay, including unused responses. Synthetic usage is labelled.|

Interface decisions D01/D03/D06/D09/D12/D14 are named in ASSUMPTIONS.md: separate package/protocol, nullable contract extensions, public context propagation, offline replay, historical checks and retained historical work. No old runner/source mutation or new source access was introduced.

## Deferred

Live model/local repair comparisons and official manifests; semantic efficacy; source quote authentication; external tools; chooser/scheduler/closure changes. F0 scripted outputs are labelled fixtures, not placeholder solving results.

## Blockers

None recorded at start.
