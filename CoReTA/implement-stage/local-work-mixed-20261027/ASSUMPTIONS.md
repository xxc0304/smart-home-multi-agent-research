# Assumption Ledger

ASK mode: never. Declared before dependent code.

| ID | Under-determined | Chosen | Class | Source |
|---|---|---|---|---|
| M-001 | Main task population | Arithmetic questions in official TAT-QA train, excluding all contexts of the six prior engineering questions; no filter on answer_from/dependency/difficulty | semantic | default |
| M-002 | Main sample | Python Random(20261027).sample eligible questions, n=12; retain all selected questions, no result-dependent replacement; cluster results if shared context | semantic | default |
| M-003 | Supplemental diagnosis | Two separately labelled table/text dependency questions, UIDs 281ec4c8-1632-40e9-bdf2-8ceac4303d61 and 0d3a1b7b-890b-455a-b55a-082bb5fe6ceb, selected by original-material inspection, not model outputs | semantic | default |
| M-004 | Reporting | Main 12 and extra 2 reported separately; no 14-item pooled natural-population score; ordinary tasks retained even when no need for local-work mechanism | semantic | user |
| M-005 | Resource access | Complete table vs all original paragraphs for two members; full-source single Agent; final member alternates A1/A2 across cases, paired identically in both multi-agent arms | semantic | default |
| M-006 | Common tool | All arms can request bounded arithmetic on supplied numeric values; original-source handle disclosure, result rendering, optional local-work/binding interface shared; ordinary arm may spontaneously use any available operation | semantic | default |
| M-007 | Intervention | Explicit local-work continuation instructions versus ordinary useful collaboration instructions; initial sources/schedule/tools shared between the two multi-agent arms | semantic | default |
| M-008 | Schedule/budget | Multi-agent 3 waves x2 members + final=7 replies; single-agent 6 solve/refine steps + final=7 replies. Both caps 6x2048+1536=13824, with identical per-response tool limits; equal envelopes are not equality of input cost or actual compute | semantic | default |
| M-009 | Offline flow failure | Save complete wave requests before replies; core-unreadable/missing response blocks dependent later waves; preserve valid same-wave siblings and all raw; invalid optional actions are isolated | interface | default |
| M-010 | Response core | Nonblank message; source_ids/calculations/work/bindings optional. Absent work becomes empty only as declared adapter normalization; malformed optional components retained with notices; no facts/values inferred | interface | default |
| M-011 | Data selection leakage | Main uses only arithmetic task-type eligibility; supplementary manual selection only for diagnostics. Answer/derivation/scale/annotation never enter runtime prompts. No hand-authored task work or correct connection in model packages | semantic | default |
| M-012 | Offline success | Synthetic replies test scheduling/interface only; original old-output replay remains old-contract coverage, no autonomous new-format success claimed | semantic | user |
| M-013 | Effect metrics | Final official numeric answer and scale preferred; paired wins/losses, nonanswers, optional-action damage and cost separately. No invented tolerance or pooling diagnostic cases into main score | semantic | default |
| M-014 | Model launch | This build has no network transport, no auto-rerun and no new paid authorization; future protocol calibration needs explicit review/freeze/authorization | semantic | user |
| M-015 | Official evaluation dependencies | Install numpy/pandas/scipy in project venv to execute unmodified upstream metric; record versions, do not substitute a custom numeric tolerance | interface | default |
| M-016 | Optional-component admission | Preserve original raw; shared adapter normalizes only absent work to [], rejects malformed optional lists with explicit notices, never fills task facts | interface | default |
| M-017 | General-flow provenance | File replay records caller-supplied provenance label (default unverified), never certifies it; engineered fixtures explicitly labelled and never counted as autonomous model outputs or method scores | semantic | sweep |
| M-018 | Arithmetic result rendering | Both generic calculator C-results and local-work W-results can be explicitly referenced at final delivery in every arm; no privileged candidate-only rendering | interface | default |
| M-019 | Scale handling | Preserve model scale and score with official evaluator; wrapper does not guess/correct units from gold or from a numeric answer | semantic | default |
| M-020 | Terminal core vs annotations | Required answer/scale/nonblank reasoning; result_id optional and defaults only to null. Malformed reference or extra annotations retained as notices without discarding valid explicit answer | interface | default |
| M-021 | Semantic nonanswer | Null or blank/whitespace answer is a semantic nonanswer, not a JSON failure; numeric zero remains a real answer, original delivered fields retained | semantic | default |
| M-022 | File read failures | UTF-8-only response files; no implicit codec guessing. Persist all current-wave requests before any response read, preserve undecodable raw bytes and read error, process valid same-wave siblings, stop dependent later waves | interface | sweep |

## Notes

The two-agent setting tests information complementarity, not trained specialty. Uniform question sampling is over the specified train arithmetic population; it is not a representative all-domain or full TAT-QA result. The main sample may contain few strong cross-source dependencies; do not fix its composition after inspection. Supplementary cases are deliberately not part of the main population estimate. Development/confirmation must be split by context later.

M-008 revised before updating the scheduler: the initially planned three long single-agent calls gave fewer opportunities to use the bounded tool interface. Use the same seven calls and per-call tools/caps instead, giving the full-information baseline sufficient continuation opportunities. Report extra repeated full-context input rather than claiming all resource costs are identical.
