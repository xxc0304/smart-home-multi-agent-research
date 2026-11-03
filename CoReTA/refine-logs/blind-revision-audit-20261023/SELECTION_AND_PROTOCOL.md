# Revision validity audit protocol

2026-10-23. User approved independent validity review and a few cross-task cases. Scope is offline review, no new DeepSeek requests or primary-runtime edits.

Five existing before/after pairs, purposively selected for contrasting kinds of revision across four task IDs. Source map kept separate from the reviewer input. Review input includes full task, all original packets for auditor access, before/after work and open points, actual authors; omits official gold, model review outputs, experimental conditions, previous results and executor interpretation. File order shuffled with seed53 for presentation only. Artifacts kept verbatim, so protocol vocabulary/versions may be recognizable: masked condition/prior-score review, not fully anonymized or double blind. Reviewer sees all materials as auditor, not as a protocol member; it is not an online agent gaining other members' private sources.

Selected pairs:

* hb-dev-034 natural D0 W4→W6: primary previously diagnosed failure.
* hb-dev-001 r1 W6→W7: access evidence and same-truck linkage; distinguish source status from content.
* hb-dev-001 r2 W5→W6: scope correction and retained route choice, includes potentially useful caution.
* hb-dev-050 r1 W4→W5: newly released source, existing shared facts, proposed conditional actions.
* hb-dev-004 r1 W3→W4: vehicle constraint and owner/driver ambiguity.

This is a development case audit, not a random sample, held-out evaluation, error prevalence estimate, or new benchmark coverage. Four IDs are all choice tasks within the same benchmark; two route pairs are same task ID. Do not count five as five independent domains. Valid revisions and mixed/uncertain cases must be retained; a source owner's claim is not automatically environmental truth, and the earlier artifact is not presumed correct.

Independent review uses research-review skill, fresh gpt-6-astra ultra context. Prompt provides only BLIND_CASES.json path and neutral source/revision questions; reviewer prohibited from reading reports or PRIVATE_MAPPING. review_independence=same-family, acceptance_status=provisional. It can substantiate/correct executor labels but does not establish universal semantic gold.

Track reviewer disagreement with earlier interpretation openly. Any further task expansion should predefine sampling and validity criteria before seeing outcomes. No keyword score or final choice match substitutes for claim-level source judgment.
