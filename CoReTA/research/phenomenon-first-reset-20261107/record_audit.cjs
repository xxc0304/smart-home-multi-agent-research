const fs=require('fs'),path=require('path'),crypto=require('crypto');const root=path.resolve(__dirname,'../..');const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 2026-11-07 现象优先讨论复审：保留调整，避免归零与过度线性化

见research/phenomenon-first-reset-20261107/AUDIT.md及EVIDENCE_SNAPSHOT.json。已复算原D80/新56：隐藏团队53.67对独立E58.67、67.86对62.50；私人E对/讨论错4/75与4/56，反向8/75与9/56；E终答对团队漏选9/75与3/56含语义边界。以上是正式EM候选，不是已完整语义核验机制率。存在证据已积累，尚缺主现象取舍/可靠范围/机制与新增贡献；不称零现象。

当前仍优先既有资料的候选现象证据与价值表，最多2–3候选，必须给排序/推荐/反证与覆盖范围；不无限审核或堆分类。频率与损失、可复现、专家相关性和近邻增量共同判断。少量解释性诊断可以与测量迭代，未要求所有频率先完全确认；本次不启动新实验，限制仍是现象对象不清的大规模方法筛选。100题有限提示负结果有效，不能由零增益倒推无意义，但此前扩批资源优先级需要修正。上一DECISION容易被读成严格线性的顺序，以本复审澄清为准；原始记录和评分保留。PASS本次审核/数值快照，主现象与全量语义普查未完成，助手none/provisional。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];const changes=[];
for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=hash(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:hash(p)});}
fs.writeFileSync(path.join(__dirname,'AUDIT_RECORD_UPDATE.json'),JSON.stringify({date:'2026-11-07',scope:'DISCUSSION_AND_EVIDENCE_MATURITY_REVIEW_NOT_FULL_CENSUS',changes,new_model_calls:0,files:Object.fromEntries(['AUDIT.md','EVIDENCE_SNAPSHOT.json','evidence_snapshot.cjs'].map(f=>[f,hash(path.join(__dirname,f))]))},null,2)+'\n');console.log(JSON.stringify({records:changes.length,new_model_calls:0,census_complete:false}));
