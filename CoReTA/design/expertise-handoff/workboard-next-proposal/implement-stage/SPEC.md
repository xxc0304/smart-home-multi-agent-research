# D0 implementation

Target: implement DISAGREEMENT_MECHANISM_SPEC_20261022.md as an opt-in Python variant, with offline scripted acceptance checks and a replay entry point. Inputs: existing member packets and stage responses. Outputs: workboard journal/result plus focus-to-offer-to-work disposition records; truth remains not_certified. No new live calls, scoring, tools or official experiment manifests.

Base commit: 00338a49953246eaeff582e1a16f4c2959b77374. Existing workboard source/tests are untracked in this checkout; review the named files directly, not just git diff. Frozen v3 source is not edited.

Success: `.venv/Scripts/python.exe -m unittest discover -s tests -p test_workboard_d0.py` and existing workboard/HiddenBench checks. F0 uses scripted responses, explicitly engineering fixtures, never ability results. Execution decisions are in ASSUMPTIONS.md before dependent code. ASK=never, balanced/draft.
