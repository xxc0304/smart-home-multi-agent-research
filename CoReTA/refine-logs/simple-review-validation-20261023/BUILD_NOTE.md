# Current/plain comparison preparation

## Latest run status — user hold

2026-10-23: User explicitly authorized this 32-call batch; launched runs/simple-review-live-20261023-r1. User then requested waiting before experiments. The runner had stopped on its first technical error: attempt4 returned completed server output containing extra data after JSON (SCHEMA_ERROR), not truncation. Actual HTTP attempts4, parsed outputs3, remaining28 not started; input51880/output2705 tokens, unknown usage0. No retry or repair. Raw progress remains stopped_on_first_error; subsequent experiments are on hold at the user's request. Preparation-only/no-HTTP statements below describe the earlier state.

2026-10-23. No primaryruntime changes. New prepareCLI tools/workboard_simple_review_probe.py reuses tools/workboard_review_probe.py's existing32-call bounded runner. Conditions C=currentpriorB, S=plain genericstageprefix. Whole packet/schema suffix byte-identical; existing private-source boundaries intact. Explicitly package-level intervention, not a one-sentence warning ablation; no finalanswer inference.

Two offline tests: initial run1fail due to test substring'son' matching'personally', not implementation contamination. Corrected assertion to word boundary; rerun2tests passed3.998s. Checks exactcurrentpayload, onlyprefixchange, schema/config/privateaccess equality, no task-specific advice in prefix, and actual32 scripted calls via shared runner with0HTTP/no feedback injection. Original runner's firsterror/unknownusage/stalepreparation checks already verified in prior5test suite; not rerun absent runner changes.

Prepared runs/simple-review-prepared-20261023-r1,32maximumHTTP98304outputcap. P01–P05 declared before code. Manual004regrade completed separately; PRIOR_004_REGRADE.md explains corrected counts and limits. Independent implementationreview pending; livebatch not launched and no new API requests yet.

Independent fresh gpt-6-astra xhigh review completed read-only:undeclared0/stale0/defects0,provisional_no_findings,same-family/provisional. Verified all8CexactpriorB and all8S suffix/otherfields equal,actualidentity/access/schema,32schedule/zero-retry/first-error-stop,compatible sharedrunner and frozenhashes. This engineering review did not independently rejudge semantic004labels. Full verbatim JSON in IMPLEMENTATION_REVIEW.json. All authorized offline work complete; new32-call external run requires current-round data/destination authorization under earlier automatic-approval rulings. No current-round real calls have been made.

2026-10-23 format-layer update: see FORMAT_FIX.md. New preparation runs/simple-review-prepared-20261023-r2 validated offline. 9 offline tests pass; actual fourth response contains two distinct objects and remains rejected. No live calls; user hold remains. Prior implementation review applies only to the earlier version.
