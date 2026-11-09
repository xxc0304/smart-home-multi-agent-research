# B1 matched solo and two-item timing — stage start

2026-11-03. Goal: test whether the C-qualified task adapter retains an observed independent-answer advantage under the actual B1 initial prompt/sampling/output requirements, then validate the full four-arm execution and cost. Expert utilization, harmful changes and useful correction remain the research center.

First use the fixed first20 V inputs, no outcome-based selection, matched B/E prompt and request seed, B1 nonthinking sampling .7/.95/top_k0 and64-token answer cap. At most40 generations,600s soft/900s hard. V is already development data; this is descriptive transfer/technical diagnostic, not another independent qualification. Keep original C scores closed and untouched; H is not read. No training, external API or weight downloads.

Review historical real full answers through the B1 state machine, explicit failure/truncation export, test C score/adapter binding and temporary baseline adapter disabling/restoration. Tokenize full selected D2 histories with separate synthetic occupancy stress; synthetic messages are length stress, not semantic model evidence. Set full context16384 if the actual model and measured loads support it. Refuse overlength rather than truncate. Preserve all runtime/config/code/data bindings.

Only after the solo diagnostic and affected engineering review pass, freeze a two-item first-prefix D timing run: same four arms, two rounds, neutral initial/private final short answers, matched stage/actor seeds, seeded uniform tie rule;52/item,104 generations maximum.1800s soft/2400s hard. No retries or automatic8/32 expansion during this timing stage. Incomplete or systematic truncation is preserved and reviewed under a distinct version; do not rerun old items silently or filter by correctness.

Deliver: preflight evidence, frozen manifests, batch EXPERIMENT_REVIEW, raw requests/responses, exact prefix scoring, cost/memory, adapter route witness and stage self-review; update existing handoff/tracker. Completion means actual evidence, including incomplete results when applicable. No claim of team mechanism or general loss from just two items. Review independence=none/provisional.
