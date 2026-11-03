# C160 qualification results — 2026-11-03

Pipeline completed22:06:04+08:00,exit0. Server raw root: CoReTA/runs/b0-C160-20261103.

Both160/160 COMPLETE, no missing/outputlimit; same inference as V-selected candidate:
base EM0.1375(22/160),F10.23764232920445036;
selectedE EM0.5125(82/160),F10.5878869047619047.
PairedEMdifference0.375,139-group paired bootstrap10000(seed20261102),95percentileCI[0.2893081761006289,0.4605283094098883]. Item sensitivityCI[0.29375,0.4625]. Largestgroup4,precisionwarningsnone.
Paired outcomes: bothcorrect17,onlyE65,onlyB5,bothwrong73.
Qualification: SUPPORTED_TASK_ADVANTAGE under this fixed MuSiQue answer-only evaluation condition.
Adapter: runs/b0-first-run-20261103-v2/attempt1/adapter; samefixedQwen3-4B/NF4bf16/greedy256/shortanswer suffix. No second training attempt, no C-based change, expansion or rerun.

Stage assistant self-review PASS: actual complete real-model same-condition C, fixed original160 IDs and groups, scorer and paired report agree; earlier frozen candidate used. No C-labelled prompt inputs. Raw records retained, GPUidle after run. Self-review not independent human/cross-family review.

Supported: selected adapter has positive task-answer advantage over base on this C160 under the registered configuration; qualifies for planned team study. Not supported: pure reasoning-only improvement, new knowledge vs formatting attribution, communication expertise, broad generalization or team benefit. CI captures this grouped sample uncertainty, not all seeds/model variation or pretraining contamination.

C160 has now been used once and is closed for tuning. Preserve E-only wrong5 and bothwrong73, not oracle-perfect experts; do not filter team's items by E correctness. H remains untouched by this batch.

Next: review B1 runtime/C-binding and independent same-output-requirement controls, full-history length/cost; only then1–2full four-arm timing items→first8→cumulative32 development. C used256shortanswer suffix while existing B1 uses64and discussion prompts: qualify underC does not guarantee same advantage underB1 prompts. Check matched E0/B0 at discussion requirements before interpreting team losses. No B1 runs launched in this C batch.
