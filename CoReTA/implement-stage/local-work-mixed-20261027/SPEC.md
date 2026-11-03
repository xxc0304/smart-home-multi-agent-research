# Mixed evaluation preparation and common-tool comparison

Target: extend the offline local-work prototype to a mixed-task preparation and executable file-replay comparison. No paid API calls or network model transport.

Inputs: official TAT-QA train data; original six engineering contexts excluded; deterministic main sample; two explicitly supplemental dependency diagnostics; supplied raw response files for offline replay.

Outputs: separated runtime/offline task packages and selection record; ordinary/local-work/single-agent request and replay flow with shared arithmetic tool; tests and batch-specific scientific/readiness review.

Success: `.venv/Scripts/python.exe tools/prepare_local_work_mixed.py --output runs/local-work-mixed-prepared-20261027-v1` with PYTHONPATH=src;tools and PYTHONIOENCODING=utf-8.

Base commit: 00338a49953246eaeff582e1a16f4c2959b77374. Existing dirty/untracked work retained. Read named new files, not empty git diff, for review. Do not commit unrelated files.

Scope: bounded preparation/file replay; no model gain claim, no unseen task-family claim, no paid-run readiness certification from synthetic outputs.
