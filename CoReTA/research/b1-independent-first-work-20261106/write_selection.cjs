const fs=require('fs'),path=require('path');
const read=p=>JSON.parse(fs.readFileSync(path.join(__dirname,p),'utf8'));
const p=read('INPUTS.json'),review=read('SELECTION_REVIEW.json');
const lines=['# 本批题目及选取理由','', '2026-11-06；25道不同题，各2种子。24覆盖题与8机制题重合7道，不相加成32题。全部为已见开发数据；输入审阅为助手判读，非独立盲标。','', '覆盖题按固定SHA256顺序、材料链可判定标准选取，先审41条、排17条；不按旧终答成功筛选。机制题的旧现象只帮助诊断，新种子/执行形状可能不复现，不要求出现预定结果。','', '|原题号|题目|覆盖样本|定向机制理由／输入备注|','|---|---|---|---|'];
for(const e of p.tasks)lines.push(`|${e.index+1}|${e.task.question.replaceAll('|','\\|')}|${e.coverage?'是':'否'}|${e.mechanism_reason||e.quality_note}|`);
lines.push('','## 运行前跳过的输入问题','','这些题保留原数据/原分数，未修改金标。跳过不等于旧模型错误被删除；本批估计限输入合格任务。','','|原题号|理由|','|---|---|');
for(const r of review.reviewed.filter(x=>!x.eligible))lines.push(`|${r.index+1}|${r.reason}|`);
fs.writeFileSync(path.join(__dirname,'SELECTION.md'),lines.join('\n')+'\n');
