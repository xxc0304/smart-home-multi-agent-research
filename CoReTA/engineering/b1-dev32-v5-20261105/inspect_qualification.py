"""Read only model/qualification metadata and fingerprints, no C generation."""
import hashlib,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
load=lambda p:json.loads(Path(p).read_text());sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
cfg=load(ROOT/'runs/b1-concise-readable-tech6-20261105-v1/config.json')
rows={}
for label,path in [('configured',cfg['adapter_path'])]+[(k,load(cfg[k])['manifest']['adapter']) for k in ('baseline_C_score','expert_C_score')]:
    row=dict(path=path)
    if path:
        original=Path(path);p=(ROOT/original).resolve() if not original.is_absolute() else original.resolve()
        row.update(resolved_from_SSH_cwd=str(original.resolve()),resolved_from_project=str(p),exists=p.exists(),files={f.name:sha(f) for f in p.iterdir() if f.is_file()} if p.exists() else {})
    rows[label]=row
scores={k:dict(path=cfg[k],sha256=sha(cfg[k]),manifest_adapter=load(cfg[k])['manifest']['adapter']) for k in ('baseline_C_score','expert_C_score')}
freeze=load(ROOT/'engineering/b1-preflight-20261103/TIMING_FREEZE.json')['files']
checks={name:sha(name)==h for name,h in freeze.items() if '/b0-C160-' in name or '/attempt1/adapter/' in name}
result=dict(adapters=rows,scores=scores,original_qualification_and_adapter_hashes_unchanged=checks,all_original_qualification_hashes_match=all(checks.values()),same_adapter_under_project_root=rows['configured']['resolved_from_project']==rows['expert_C_score']['resolved_from_project'],prior_qualification=load(ROOT/'runs/b1-dev32-final-20261104-v2/manifest.json')['qualification'])
(Path(__file__).with_name('QUALIFICATION_PATH_AUDIT.json')).write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result))
