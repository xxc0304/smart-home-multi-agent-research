# B0 attempt1 V results — 2026-11-03

Actual pipeline completed2026-11-03T21:31:20+08:00, exit0. Raw root on server: runs/b0-first-run-20261103-v2.

Training COMPLETE,1796steps/1epoch,3754.49s(62.57min). peakallocated20590870016B(19.18GiB),peakreserved24222105600B(22.56GiB),allocator retries4,num_ooms0. No traceback/nonfinite. GPU idle after pipeline.

Same fixed V200 under matched256token/greedy/short-answer-suffix configuration:
B EM0.135 F10.2539589213329843,200/200 valid COMPLETE.
E1 EM0.45 F10.5342469654528478,200/200 valid COMPLETE; evaluation171.04s.
EM delta+31.5percentage points,F1delta+28.03percentage points.
Sole candidate selected: runs/b0-first-run-20261103-v2/attempt1/adapter.

Assistant stage self-review PASS for completed finite first training, real same-condition V evaluation and sole-candidate selection. Current output is selected task-adapter candidate, not independentC-qualified expert. V is development/model-selection data; no confidence interval or causal ability-isolation claim from these two means. B/E output-format compliance and answer-content effects not separated. Raw baseline old64token incomplete batch retained; not mixed into comparison.

Next action requires batch review: independentC160 baseline/selectedE once with same frozen inference; no C-based tuning or automatic expansion. C and B1 not launched by this pipeline. Keep first attempt artifacts immutable; no second training needed merely because budget allows it.
