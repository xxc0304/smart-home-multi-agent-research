const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const body=`## 2026-11-07 用户纠正研究顺序：现象核验优先，方法筛选提前

见research/phenomenon-first-reset-20261107/DECISION.md。用户指出应先确认常出现且有价值的现象再提方法。助手复核承认：最近100题以B_relation-B_check团队EM为主，实质是改善效果筛选，在可靠语义发生率/影响/独立样本稳定性未清前走快；不事后全部改称现象普查。工程准备通过不替代问题成熟度，增加过夜题量时应优先现象覆盖核验。既有四基线/轨迹与有限负结果保留，不能证明已选定高价值主现象。

当前下一任务改为已有基线现象核验：D80共同75与新56分别统计，先固定专家私人→讨论损益、团队利用不足、已公开有效判断是否被采用/保留、有益普通贡献的可核验口径；分开自身漂移、表述/粒度、题面歧义与读出。报总题/机会分母/不同题/关联组/损失收益及区间，定向8/25/四格只做病例和稳定性、不估总体频率。助手先做候选表及核读范围，独立人工后续落实，不新增用户即刻填表门槛。

先按频率、后果、可复现与替代解释、专家相关性和近邻增量选主现象；严重低频也可有价值，不设拍脑袋比例门槛。现象依据充分后才小规模机制诊断，再由机制决定方法，最后独立确认；诊断干预不以增益为唯一判据。上一报告的机制方案退为后续。暂不新增方法/提示改进批次、训练/C-H评估或重跑。PASS顺序修正与计划记录，REVISE现象成熟/可立即推进方法主张；助手none/provisional。本轮无新生成，原报告/评分/投票不改。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];
const frozen=Object.keys(JSON.parse(fs.readFileSync(path.join(root,'runs/b1-grounded-revision-20261107-v1/FREEZE.json'))).files);
for(const f of files)if(frozen.some(p=>p.endsWith('/'+f)))throw Error('Frozen record '+f);
const changes=[];for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=sha(p);if(!t.includes(body.split('\n')[0]))fs.writeFileSync(p,body+t);changes.push({path:f,before,after:sha(p)});}
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({date:'2026-11-07',reviewer:'assistant',independence:'none/provisional',changes,decision_sha256:sha(path.join(__dirname,'DECISION.md')),new_model_calls:0,run_files_modified:false},null,2)+'\n');console.log(JSON.stringify({records:changes.length,new_model_calls:0,current_priority:'PHENOMENON_CENSUS_AND_VALUE_BEFORE_NEW_METHODS'}));
