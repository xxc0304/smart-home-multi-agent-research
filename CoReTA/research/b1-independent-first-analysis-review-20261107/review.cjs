const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const prior='research/b1-independent-first-analysis-20261107',run='runs/b1-independent-first-work-20261106-v1';
for(const r of read(prior+'/ARTIFACT_HASHES.json'))if(sha(fs.readFileSync(path.join(ROOT,prior,r.path)))!==r.sha256)throw Error('Previous analysis changed: '+r.path);
const pack=read(run+'/INPUTS.json'),s=read(run+'/scores.json'),proc=read(prior+'/PROCESS_ANALYSIS.json');
const sources=[prior+'/REPORT.md',prior+'/ARTIFACT_HASHES.json',prior+'/PROCESS_ANALYSIS.json',run+'/INPUTS.json',run+'/scores.json','tools/b1_controls.py','research/b1-independent-first-work-20261106/experiment.py'];
const orderChanges=[];
for(const e of pack.tasks){const paths=[0,1].map(r=>`${run}/trials/${String(e.index).padStart(3,'0')}-r${r}.json`);sources.push(...paths);const [a,b]=paths.map(p=>read(p).branches.B);orderChanges.push({index:e.index,initialOrderChanged:JSON.stringify(a.initial_order)!==JSON.stringify(b.initial_order),firstRoundChanged:JSON.stringify(a.orders[0])!==JSON.stringify(b.orders[0]),anyRoundChanged:JSON.stringify(a.orders)!==JSON.stringify(b.orders),orders:[a.orders,b.orders]});}
const changes=proc.summaries.coverage.firstChanges;
const evidence={scope:'REVIEW_OF_EXISTING_ANALYSIS_NOT_NEW_EXPERIMENT',reviewer:'assistant',independence:'none/provisional',new_model_calls:0,previous_analysis_hashes_verified:true,primary:s.summaries.coverage.primary,firstCandidateGains:changes.filter(x=>x.b!=='C'&&x.d==='C').length,firstCandidateLosses:changes.filter(x=>x.b==='C'&&x.d!=='C').length,laterLost:proc.summaries.coverage.firstImprovementLostBeforeFinal.length,orderChangeCounts:{n:25,initial:orderChanges.filter(x=>x.initialOrderChanged).length,firstRound:orderChanges.filter(x=>x.firstRoundChanged).length,anyRound:orderChanges.filter(x=>x.anyRoundChanged).length},orderChanges};
fs.writeFileSync(path.join(__dirname,'EVIDENCE.json'),JSON.stringify(evidence,null,2)+'\n');
fs.writeFileSync(path.join(__dirname,'INPUT_HASHES.json'),JSON.stringify(sources.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(ROOT,p)))})),null,2)+'\n');
const heading='## 2026-11-07 分析复审：B_delay定义及采样/顺序混合的补充';
const entry=`${heading}

见research/b1-independent-first-analysis-review-20261107/AUDIT.md与EVIDENCE.json。原分析全部28文件hash未变，主+4.17pp/两单位/仅第二重复、11首次改善/3变坏/7后来丢失复核一致。B_delay只是第五实验条件：保留原独立短初答，仅M1首次工作临时删全部同伴历史，在原发言位置公开，然后恢复完整两轮讨论；无新增调用次数、坚持或优先投票，不是全团队换流程。统计和局部总效应保留，稳定方法/专家特有/普遍无损/内部信念解释仍不成立。

新补充：两次重复同一个seed同时控制采样、初答展示与两轮发言顺序；25/25题展示顺序、首轮和两轮组合均变。每次内B/B_delay顺序匹配，主配对不失效，但“只在第二seed获益”不能单归采样随机性。上次直接建议追加seed不够具体，下一设计先解耦采样seed与顺序seed：采样检查固定顺序，顺序作用另设预定组合，继续覆盖/机制分列。PASS本次复审与含义澄清；只允许准备上述有限设计，未启动新批，无生成/训练/C-H新评估；助手自审none/provisional，原分析和评分保留。

`;
for(const p of ['handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md']){const f=path.join(ROOT,p),old=fs.readFileSync(f,'utf8');if(!old.includes(heading))fs.writeFileSync(f,entry+old);}
const files=['AUDIT.md','EVIDENCE.json','INPUT_HASHES.json','review.cjs'];
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(files.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(__dirname,p)))})),null,2)+'\n');
console.log(JSON.stringify({primary:evidence.primary,orderChangeCounts:evidence.orderChangeCounts,priorAnalysisUnchanged:true,new_model_calls:0}));
