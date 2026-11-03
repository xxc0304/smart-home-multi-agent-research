# Workboard D0

An opt-in variant of workboard-v3. CHOOSE may create a nullable next_check; later OBSERVE offers may link responds_to; TRY receives the question and prior application feedback. Both existing checkers see the focus, and CHOOSE/FINAL_CHOOSE may report a disposition. Reports never certify truth. Pending questions are deferred at termination, including interrupted runs.

The default v3 runner and source files are unchanged. D0 preserves the editor, rotation, cycle budget, check order, output caps and four closing calls. It does not add execution tools or authenticate source quotations. Historical focus IDs do not grant access to other members' original materials. Active focus and response selection can still be wrong or miss useful contributions.

Offline checks, from the CoReTA project directory:

```powershell
.venv/Scripts/python.exe -m unittest discover -s tests -p test_workboard_d0.py
```

Replay a saved engineering script into a **new** output directory:

```powershell
.venv/Scripts/python.exe -m coreta.workboard_d0 --pack data/task-packs/student-president-dev-v1 --task-type ranking --script runs/workboard-d0-engineering-20261022-r1/SCRIPTED_stage_responses.json --output runs/workboard-d0-engineering-replay-new
```

The CLI has no live mode. Script rows are `{stage, member, output}`; stage/member mismatches stop replay. Result files label scripted attempts and fixture usage. Choice packets are supported with `--task-type choice`. Normal model transports can be supplied through the existing Gateway API by a future separately prepared experiment launcher; this build does not prepare or run one.

The 15 offline acceptance checks cover native 3/4-member choice paths, focus propagation and historical version visibility (including a cited base work), independent checker snapshots, invalid references/dispositions, private-source boundaries, last-cycle deferral, unable/all-pass/interruption, navigation-only links for unrelated reuse, and replay without overwrite or unused responses. They establish executable engineering paths, not model compliance, provider schema compatibility or effectiveness.

Design and decisions: `design/expertise-handoff/workboard-next-proposal/implement-stage/`. Semantic choices include one prioritized latest-pending focus, no automatic preference for its responses, model-reported addressed status, and no additional repair calls at the end.
