# Bounded mixed-task calibration preparation

Target: prepare one ordinary task plus one supplemental cross-source task with all three comparison arms, and a gated zero-retry runner. No live API call during this build.

Inputs: mixed-prepared task main-01 and diagnostic-01, current ComparisonFlow, existing DeepSeekClient and tokenizer, historical full replies for carrier replay. Output: fresh frozen prepared directory, full local fixture runs, preflight and scientific/readiness review, explicit next authorization scope.

Success: PYTHONPATH=src;tools; `.venv/Scripts/python.exe tools/check_local_work_calibration.py --output runs/local-work-calibration-check-20261027-v1`.

Base commit00338a49953246eaeff582e1a16f4c2959b77374; dirty repository, only named new files participate. Existing live results unchanged. No model authenticity or gain inferred from fixture execution.
