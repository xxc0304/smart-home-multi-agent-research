# Offline local-work composition prototype

Target: implement DESIGN.md in research/local-work-composition-20261027 as a small offline artifact, not a paid model experiment.

Inputs: official TAT-QA training data, split by original table versus paragraphs; scripted engineering events; unmodified historical model replies for shared JSON/source-interface replay.

Outputs: a source-preserving task adapter; local work/value/input-binding state; arithmetic execution with condition propagation and invalidation; per-member prompts; runnable offline trace and audit under runs/local-work-offline-20261027-v1/.

Success command: `.venv/Scripts/python.exe tools/check_local_work.py --output runs/local-work-offline-20261027-v1` (PYTHONPATH=src;tools).

Base commit: 00338a49953246eaeff582e1a16f4c2959b77374. Repository contains extensive pre-existing untracked and modified work; only explicitly listed new files belong to this build. No unrelated changes or broad commit.

Scope cuts: no network model transport, no live results, no trained routing, no arbitrary Python execution, no full ATMS, no claim that scripted operations were discovered by agents. First operator family is numeric arithmetic; time/planning support deferred.
