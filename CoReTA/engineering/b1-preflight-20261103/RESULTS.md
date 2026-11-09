# B1 prompt transfer and first two timing items

Started2026-11-03; post-run audit2026-11-04 00:04:59+08:00. Assistant self-review, independence=none/provisional.

## Actual execution

- Original v1 stopped after1 baseline answer exhausted64 tokens while explaining the question. It has no complete mean and no team run. Raw output, incomplete report and old code are retained.
- Joint output-contract revision v2: fixed strict B0 short-answer suffix plus256-token initial/final cap, identical for all actors/arms; work512, sampling.7/.95/top_k0, seed20261102/M1, two rounds, information matching and voting unchanged. Not a pure cap ablation. No further prompt search occurred.
- New fixed V20 matched solo:40/40 complete, baseline EM3/20(15%)/F121.09%, expert11/20(55%)/F164.17%,38.34s. Same initial payload and per-task seed, adapter toggled. This is development prompt-transfer evidence, not another C qualification. Real active/disabled/restored route witnessed; restored logits identical.23 affected engineering regressions pass.
- Two fixed D items:104/104 normal outputs,2/2 complete paired traces;598.38s(~9.97min). No output limits, retries, technical failure, OOM or silent input truncation. All104 recorded adapter flags match actor M1 versus baseline members. Actual complete traces replay and rescore identically.
- Overall this stage:145 task generations =1 preserved v1 failure+40 v2 solo+104 team. No training, second expert, C rerun, H task access, paid API, weight downloads or automatic8/32 expansion.

## Timing and capacity

Input tokens346423, output11770 across104 team requests. Maximum actual input4947, below16384; maximum work output482/512. Initial8 outputs total32tokens/4.94s; work64 outputs11610tokens/560.53s; final32 outputs128tokens/25.03s. Peak allocated3.93GiB/reserved5.13GiB. GPU afterward2MiB/0% utilization. These are measured costs on two items, not guarantees for longer tasks. Mean roughly5min/item suggests another6 items may take roughly30min, with variation and loading overhead; freeze a separate finite budget before extension.

## Scores: two items only

| Arm | Work | Expertise identity | Team correct | Expert final correct |
|---|---|---|---:|---:|
| A | Private reconsideration | Hidden |0/2|0/2|
| B | Sequential discussion | Hidden |1/2|1/2|
| C | Private reconsideration | Revealed |1/2|0/2|
| D | Sequential discussion | Revealed |0/2|0/2|

Expected and seeded actual team EM agree here; no winning-class ties occurred. Both initial expert answers and all ordinary initial answers were incorrect on these two items. Therefore this batch has no initially-correct expert cases: expert harmful-change denominator is0, retention/harm rates are null, not evidence of zero harm.

On the first item, hidden discussion B ended with all four answering1843 correctly (expert initially1810). Private/revealed C voted1843 while the expert remained1810; private/hidden A contained a correct member final but did not select it. Revealed discussion D converged to1810 incorrectly. On the second item all four arm votes remained incorrect. These are observed answer/selection patterns only; no detailed content-based causal annotation has been performed. They do not establish disclosure harms, discussion superiority, reliable expert use, or overall team benefit. Keep the failure and both initial expert errors; do not select later items by correctness.

## Stage verdict and next action

PASS for prompt-transfer diagnostic and the bounded first-two technical/cost stage. Existing C qualification remains unchanged under its original bounds. v2 is technically eligible for same-config prefix continuation to first8, preserving these two items exactly rather than rerunning them. Freeze/review a finite remaining6-item budget using measured costs before launch;32 remains a later cumulative first pass, not a confirmatory paper sample. No extra batch was started here.

Scientific scope is limited: V was already development data and the new output contract changed both prompt/cap; D n=2 supplies no stable effect/causal estimate. Full-history synthetic stress8362 tokens was separately labeled, while actual max4947 is direct evidence for these two items only. No claim of universal max-length safety. Original64 protocol and all pre-existing server uncommitted work are preserved. No GitHub push was performed.

Evidence: `evidence/b1-preflight-v20-20261103-v1`, `evidence/b1-preflight-v20-20261103-v2`, `evidence/b1-timing2-20261103-v2`; server originals in corresponding `runs/` paths. See bound prelaunch reviews/freezes, POST_RUN_AUDIT.json, raw requests/responses, full trials, scores, actual generation policy and memory/cost exports. The C-binding and v2 prompt contract changes are covered by23 regressions, including changed-contract resume rejection.
