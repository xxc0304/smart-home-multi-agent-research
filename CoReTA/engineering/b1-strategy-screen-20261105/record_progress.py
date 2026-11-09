from pathlib import Path
root=Path(__file__).resolve().parents[2]
entry=Path(__file__).with_name('RUNNING_STAGE_ENTRY.md').read_text(encoding='utf-8')
for name in ('handoff.md','CURRENT_STATE.md','brainstorm.md','experiment/results.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'):
    p=root/name;old=p.read_text(encoding='utf-8')
    if entry.splitlines()[0] not in old:p.write_text(entry+old,encoding='utf-8')
