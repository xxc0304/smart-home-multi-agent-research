from pathlib import Path
import json
ROOT=Path(__file__).resolve().parents[2]
v4=ROOT/'runs/b1-output-contract-probe-20261104-v4'
r=json.loads((v4/'RESULTS.json').read_text());assert r['n_eos']==r['n_word_contract_pass']==4
entry='''## 2026-11-04 四题截断原因/记录修复及独立探针通过

见engineering/b1-output-repair-20261104/RESULTS.md。四题均已记录，非丢失；1初答256/3工作512用满且无EOS，冗长/重复导致，80个后续依赖未调用。新增32行MISSINGNESS_LEDGER；修复finish原因分辨token/time/unknown并保留EOS/cap信息，27回归通过，旧源码快照保留。独立V3四请求均EOS但短答超词限；V4明确答案实体与简洁工作，四请求均EOS/词限通过，生成7/80/112/58token，19.55秒，共8次技术生成，无gold筛选。只验证格式，第一条短实体仍不能当语义正确。原32成绩不改，仍28完整/primary=false；未把4条新输出拼回旧批，未重跑四题完整四组。下一步若采用新合同须统一四组另冻完整验证；同底座正常性/随机后端与相关错误尚不能由本次探针解决。不训练/读C-H/付费API。助手自审PASS限原因/记录及四请求验证，非新科学成绩。

'''
for name in ('handoff.md','CURRENT_STATE.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md'):
 p=ROOT/name;old=p.read_text(encoding='utf-8')
 if '## 2026-11-04 四题截断原因/记录修复及独立探针通过' not in old:p.write_text(entry+old,encoding='utf-8')
print('REPAIR_SCOPE_RECORDED')
