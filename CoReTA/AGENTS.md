# CoReTA project brief

- **Project:** CoReTA — Complementary Reasoning through Targeted Assistance.
- **Research focus:** Motivated by *Multi-Agent Teams Hold Experts Back*, study how teams can use task-relevant expertise while reducing unsupported compromise and harmful opinion revision, and still accept valid corrections. Complementary expertise, distributed information, and local work are derived settings and possible mechanisms; they are not substitutes for this original problem.
- **Current evidence boundary:** Several targeted-help and handoff adaptations have been tested. No new complete method has yet shown a stable final-quality advantage; do not treat a member label as calibrated expertise or a correct final answer as proof that a contribution was correctly used.
- **Target venue:** ACL 2027; plan against the main-conference call for papers. Long or short paper is not yet selected.
- **Submission deadline:** Latest ARR cycle for ACL 2027 is January 4, 2027, 23:59 AoE (UTC−12), equivalent to January 5, 2027, 19:59 China Standard Time (UTC+8). ACL commitment and decision dates are not yet announced as of October 28, 2026. See [`submission/ACL_2027.md`](submission/ACL_2027.md) and verify the official call before submission.
- **Working terms:** A *local contribution* is task-relevant evidence or work produced from information available to one member; a *receiver* is the member who considers that contribution; *discovery*, *interpretation*, *application*, and *final selection* are separate events; *ordinary collaboration* is the same-tool comparison without CoReTA-specific guidance; *complementarity* refers to useful distributed information or work, not a verified stable trait of a member.
- **Baseline status:** See [`reproduction/README.md`](reproduction/README.md) for paper-inspired adaptations and internal comparison conditions. Do not describe an adaptation as a faithful paper reproduction.

## Current research stage and comparison standard

2026-11-01 R29 CURRENT: revised B1 is now implemented in tools/b1_experiment.py, b1_controls.py, b1_runtime.py. See implement-stage/team-controls-20261101/README.md. Four arms, two work turns, common short initials/private finals,52/item, fixed first-pass seed20261102/M1, .7/.95/top_k0 and64/512 registered implementation defaults. Expected team EM primary; seeded actual EM/F1, all-member transitions and actual/expected readout loss separate. Enforces1/2→8→32 complete-prefix continuation, no rerunning old items; D32 is development. Final31 B0/B1 offline/CPU checks passed; fresh two-round same-family assumption review, post-round2 fixes executor-regression-verified, provisional (no fresh third sweep; CUDA path untested). Real Qwen/GPU/length/finite budget and actual C-qualified expert remain prerequisites, real task train/team0. Pending config refuses real execution. Next hardware preflight→B0 bounded V/C→B1 timing1/2→8→32, with batch review. Earlier “B1 code unadapted/metrics undecided/four rounds” statuses below are history, not current work. Do not reopen data semantic audit or construct a new cause framework to fill waiting time.


2026-11-01 user accepted staged cost plan: 1–2 full four-arm items for timing, included in first8 technical items, then cumulative32 ONCE for development. Supersedes proposed32x2/3328 calls. Thirty-two is not final paper N; larger independent N (200–300 planning only), repetition and finite resource budget depend on actual throughput/precision and must be frozen before runs. Preserve all four controls and sequential broadcast; no auto-launch large batch, seed shopping or outcome-based selection. B0 unchanged.

2026-11-01 R28 user confirmed the full 2x2 control structure: A private-hidden, B discussion-hidden, C private-revealed, D discussion-revealed; share the same 4 initials, each member has 2 work turns plus a private short final. Private branches see only own history and matched disclosure. Base generation count is 52/item, superseding 28/40 draft designs. Numeric output caps/decoding, primary metrics, sample/repetition and actual resource budget remain to freeze; B1 code not yet adapted. Next design step is evaluation and batch plan; do not reopen B0, two rounds or tie rule.

2026-11-01 R27 user-confirmed discussion protocol: independent short answers, share fixed initials, then hidden/revealed E branches; TWO sequential rounds (each member once), natural discussion/optional citations, randomized orders matched across branches with immediate broadcast; private final SHORT answers unseen by peers; fixed uniform tie rule. This supersedes old four-round/three-field descriptions. Only private no-communication prompt/information matching and final evaluation/budget details remain to design; do not reopen confirmed choices or B0. Code has not yet been aligned to this new B1 protocol.

2026-11-01 identity control accepted: hidden expertise is ordinary collaboration; reveal E only after common independent initials as a diagnostic branch. Disclosure is a treatment package that can affect E and B, not unique proof of identification. Match disclosure information when claiming pure communication effects; do not automatically reuse hidden solo controls for known-team causal claims. B1 prompts/private-control matching and total budget remain to freeze; expert training unchanged.

2026-11-01 user-confirmed team tie rule: uniformly sample among tied highest-vote answer classes using a preregistered seed. No expert priority, extra discussion or judge. Record ties and actual selections, report expected answer scores separately; selection losses are not cognitive revision. This confirms the tie rule only; other B1 draft items are not automatically frozen.

2026-11-01 R26 TEAM DESIGN UPDATE: user replaces four discussion rounds with 2–3; assistant recommends 2 as main, with private revision count matched. B1 controls remain proposed/not frozen; see B1_CONTROL_DESIGN.md. Old four-round code and 29/44 generation counts are historical, not permission to run. B0 expert training remains unchanged. Anchor paper already analyzes causes/behavior and ablations; do not frame novelty as "they only observed, we explain". Current batch is a bounded baseline/diagnostic anchor; later controlled mechanism responses and held-out validation must carry incremental claims.

2026-11-01 R24 CURRENT IMPLEMENTATION: the minimal answer-only trainer and V/C evaluation entry point are implemented in tools/b0_expert.py, b0_training.py and b0_answers.py. See implement-stage/expert-answer-only-20261101/README.md. Nine offline/CPU checks passed, including random tiny adapter update/save/reload and fixture generation; not Qwen/GPU or expert evidence. Fresh same-family two-round assumption sweep resolved three declarations and a final-step wall-budget bug; final 0 undeclared/provisional. Real task training/calibration remain zero. C only relationship metadata (139 groups, max4) was read; no C/H question/target bodies. The current next step is actual hardware/model/template/length/precision/4bit/throughput preflight and filled batch config. Pending config refuses execution. Do not keep listing the trainer as unimplemented or reopen data cleaning. Earlier R20–R23 statuses below are historical; current implementation record takes precedence.

2026-10-31 R20 update: the user reports a GPU will be available on November 2; type/VRAM/access window remain unverified. Use the current v0.8 EXPERIMENT_PLAN and tracker as the single active plan. The current engineering task remains the minimal one-adapter training execution path (data, assistant-only loss, save/load, explicit full-template length); this planning turn did not implement it. After actual backend checks: bounded V training, independent C qualification, E0/V0/Eself/Etalk/Vtalk comparisons on D, process-led selection of at most 1–2 interventions, then frozen holdout confirmation. C160 does not guarantee resolving a 5pp advantage; D8/32 is development, not mechanism confirmation. R18 data review stays closed; no new cleaning/literature/collaboration training to fill time. Planning PASS is not runtime readiness or research evidence. Earlier v0.6 and prior E/R plans are historical, not parallel active plans.

2026-10-31 R22 user decision (supersedes R21 format advice): train only on the short answer, with no support IDs, rationale or collaboration targets. V debugging and C160 expert qualification request only answers; judge task advantage using answer EM/F1, not explanation/citation quality. Current candidate is data/expert-training-answer-only-20261031, exported from unchanged 1796/200 selection; historical answer/support files preserved. Explanations/evidence may be requested at discussion time as needed, equally for B/E, without additional expert training. If prompt requirements change, separate that effect from peer interaction. Existing three-field discussion code remains historical/offline and must be aligned before real team runs; it is not an answer-only calibration backend. Answer-only SFT can still change other behaviors. No training or model generation occurred.

2026-10-31 R23 local design review: B0 science PASS after specifying V selection by generated-answer EM, then F1, then earlier predeclared candidate; loss is diagnostic only. Current C160 is one fixed evaluation, no automatic expansion/seed shopping after results. Runtime BLOCKED: the official answer metric accepts short text, but existing three-field parser rejects it (hand-authored interface probe, not a model result). The minimal execution task includes answer-only V/C scoring and failure handling alongside the trainer; do not build another platform or reopen data review. See B0_DESIGN_REVIEW_20261031.md. No training/model/implementation was launched in the review turn.

User decision on 2026-10-30: use the Hold Experts Back paper-style independent
answers followed by open sequential discussion, rather than the prior two-round
synchronous revision baseline. The active v0.8 plan specifies four rounds with
random speaking orders and immediate history broadcast. The API-free state machine is now implemented and checked offline; actual backend integration is pending. See implement-stage/expert-preparation-20261030/README.md.
Expert construction must stay a bounded preparation step; one task adapter is the
current proposal, not a new large training project. See the current pilot plan and
TRAINING_SETUP.md; do not claim the expert is established before calibration.



User sequencing clarification on 2026-10-30: first let the assistant analyze
the eight existing cases and explain the findings. Do not require the user to
fill human annotation forms before continuing exploratory case analysis.
Keep the prepared human-review package as an optional evidence tool; plan the
timing and scope of independent human validation against later paper claims.
Assistant analysis must remain labeled as such and must not fill or substitute
human independent records. This updates the earlier immediate-human-pilot order.

User clarification on 2026-10-30: hop count is auxiliary task metadata, not a
required partition of the research question or a requirement that an expert
outperform others in every hop stratum. Use independent calibration that covers
the target task distribution; inspect subgroups when useful to interpret an
effect. Preserve experts' own item-level errors as part of the research, rather
than screening them all out. Do not turn exploratory checks into new scope gates.

Resource update from the user's screenshot on 2026-10-30: a contact reports a
spare dual-2080-Ti machine, and the user's quoted chat reports dual 1080 Ti.
These are hardware leads, not verified runnable resources or access permission.
Check actual per-card VRAM and software before selecting deployment; a 4090
remains unconfirmed. See research/expert-team-assets-20261029/GPU_OPTIONS_ANALYSIS_20261030.md.
The following no-available-GPU statement records the earlier session status.

Resource clarification from the user on 2026-10-30: there is currently no
available GPU. An RTX 4090 is only a possible application, not a promised or
confirmed resource. Do not make obtaining that card, local Qwen training, or
any particular compute backend a required project premise. Prepare data,
evaluation and evidence independently; select a training or existing-model
execution route only after actual resources and scope are established.

User direction on 2026-10-29: do not keep narrowing the central research
question by accumulating special-case assumptions in response to related work.
Keep the original substantive problem—how multi-agent teams use task-relevant
expertise or useful contributions while avoiding harmful compromise and still
accepting valid correction—as the umbrella. Specific scenarios, conditions,
cases and metrics are investigative lenses and evaluation settings, not
automatically necessary conditions of the overall research problem. Treat the
previous partial-refutation and distributed-evidence questions as probes, not
as the selected exclusive topic. Meaningful improvement, a significant
empirical finding or a coherent reframing may motivate work even with closely
related prior studies; assess concrete value without requiring absolute novelty.
Do not equate a useful member in a single item with verified stable expertise.

User direction on 2026-10-28: prioritize a thorough literature investigation and
precise problem definition before preparing more reproduction runs or new methods.
Use `research/expertise-literature-survey-20261028/BRIEF.md` as the current brief.
Read what each close work actually does, what it demonstrates, and what remains
unknown; synthesize positive and negative evidence before selecting the next step.
Earlier suggestions to move immediately to baseline reproduction are superseded.

Follow the project `research-workflow` and the user's current sequencing: establish
the active question, systematically read and compare the literature and existing
evidence, then develop and review a concrete idea before moving to implementation,
baseline reproduction or experiments. The user's literature-first instruction
overrides the workflow's default reproduction-before-hypothesis order. Do not
automatically start a new method, model run or research stage merely because a
candidate looks promising; remain within the user's current requested scope. Within
that scope, independently carry out authorized reading, organization, analysis and
other reversible work. Record relevant findings, stage, assumptions and next steps
in the project's existing research records and handoff.

Judge novelty at the level of the concrete contribution. Shared goals, standard
components, or partially similar stages do not by themselves establish duplication.
Meaningful contributions can be a mechanism improvement, a consequential empirical
finding, a useful problem refinement, or a combination that reveals new behavior.
Compare each paper against its stated goal and evidence; do not require universal
guarantees, every component to be original, or every task to improve. Distinguish
observed failure, an untested condition, and no retrieved evidence. Missing evidence
does not establish ineffectiveness; missing a duplicate does not establish novelty.

User preference for future idea assessments: do not seek absolute originality or
discard a direction simply because related work exists. Identify concrete added
value and room to develop it, such as addressing a demonstrated limitation,
improving practical usability, meeting a new need, reframing the question, or
making a solution more effective. For an immature idea, explain specific ways to
extend, refine, or test it instead of ending with an overlap warning. Describe both
existing achievements and the proposed increment accurately; avoid treating an
untested setting by itself as proven superiority or novelty.

## Stage review and research alignment

User instruction on 2026-10-30: automatically review every meaningful small
research stage for plan execution, evidence and alignment with the central
question. Follow `STAGE_REVIEW.md`; record reviews in the active plan's
`STAGE_REVIEWS.md` and update its `WORK_TRACKER.md`. Do not wait for a reminder.
At stage start, state the goal, scope, deliverable and completion criteria;
at completion or a material scope/resource change, check actual artifacts,
deviations, supported claims, alternative explanations, resources and next step.
Use PASS / REVISE / STOP with an explicit scope and permitted next action.
Do not mark a stage complete from a draft or case extraction alone.

Keep expert-advantage utilization/harm and useful correction as the center.
Training Qwen specialists, adapters, hardware and workflow engineering are
instruments, not replacement research goals. Do not demand absolute novelty,
significant gains or a publishable contribution at every reading/preparation
checkpoint. Distinguish actual deviation from a prospective risk.
Perform routine corrections within existing authorization without adding a
user-approval loop; continue independent permitted work when one dependency is
unavailable. Mark assistant self-review honestly; it does not replace planned
independent human annotation or advisor review. A stage PASS does not replace
the experiment charter, resource availability or existing authorization.

## Experiment preparation

Before every experiment launch, automatically review both scientific meaning
and execution readiness under `EXPERIMENT_CHARTER.md`. This includes pilots,
diagnostics, added batches and revised runs. Do not wait for a user reminder or
ask permission just to perform this local review. Save a batch-specific
`EXPERIMENT_REVIEW.md` with separate verdicts and supporting evidence. Do not
launch until both gates pass; fix authorized local issues and re-review first.
These checks do not replace API/data authorization or imply independent review.

When a review finds fixable issues within the authorized scope, implement the
fixes and re-review directly; do not stop merely to ask whether to fix them.
Research-scope changes and new paid API batches still require applicable user
authorization. Preserve superseded batch records and freeze a new version.

Before launching a paid model experiment in this project, follow
`EXPERIMENT_PREFLIGHT.md`. Use real full historical responses, not only empty
arrays or hand-written valid IDs, to validate the protocol end to end. Keep
technical failures separate from semantic errors and preserve incomplete results.
Do not claim readiness from unit-test counts alone. Freeze inputs, schemas,
configuration and code; repeat local preflight after changes. Do not rerun or
reinterpret a stopped batch under a new contract as if it completed originally.

## Research workflow records

- At the start of a work session, read this file, `handoff.md`, and the newest
  entries at the top of `CURRENT_STATE.md`. Then read the relevant design,
  literature, data, or run records linked from `handoff.md`.
- Keep current hypotheses and their status in `brainstorm.md`; retain detailed
  dated design and review records under `research/` and `refine-logs/`.
- Use `related_work/` as the consolidated bibliography and reading-note index.
  Do not claim a paper PDF or LaTeX source is local unless the files exist in its
  `related_work/papers/<slug>/` folder. Keep original reading/review records in
  place and link to them.
- Use `data/` as the canonical data tree. Record provenance and task-specific
  processing in `dataset.md`; do not rename the established `data/` tree to
  match a generic template.
- `experiment/results.md` is an index of completed runs, not a replacement for
  immutable run artifacts. Preserve raw results and include null, failed, and
  incomplete runs when they affect interpretation.
- `experiment/evaluation.md` maps the shared reporting dimensions and links to
  frozen task-specific scoring. Each batch's manifest and scoring files remain
  authoritative for its exact metric.
- `experiment/run-index.md` inventories physical folders under `runs/`; folder
  labels are inferred from names and are not a count of independent experiments.
- `experiment/live-results-index.md` lists all `live`-named folders that contain
  `RESULTS.md`, including partial and interrupted reports.
- `reproduction/README.md` records paper-faithful reproduction status separately
  from internal baselines and paper-inspired adaptations.
- Update `handoff.md` when the active question, evidence, or next step changes.
  Keep `CURRENT_STATE.md` as the detailed dated history; summarize it in the
  handoff instead of rewriting old entries.
