const fs=require('fs');
const path=require('path');
const crypto=require('crypto');
const root=path.resolve(__dirname,'../..');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const inputs=JSON.parse(fs.readFileSync(path.join(__dirname,'INPUT_HASHES.json'),'utf8'));
for(const r of inputs)if(sha(fs.readFileSync(path.join(root,r.path)))!==r.sha256)throw Error('Input changed: '+r.path);
const heading='## 2026-11-06 最近实验方向审核完成：配对补齐，转向首次公开贡献与真实下游';
const entry=`${heading}

见research/research-direction-review-20261106/REPORT.md、DECISION_TABLE.md及MATCHED_EVIDENCE.json。已实际补完19条候选的身份匹配私人/公开两次E工作；16/19初答已正确公开，不能说正确知识第一次在末答出现。私人末次17/19肯定官方目标候选（非全推理认证），原较清楚9条中8条；第20题私人自身也不稳定，第48题私人本就错，第68题匹配串却含错误国家桥接。选中19路径团队3改善/4降低/12不变，E私答16→19，不能从工作变化直接推团队伤害或总体频率。15讨论漏选中13条初答已公开正确，沿用逐条E工作语义分流，不冒称全普通消息新标注。全部讨论E初错终对13路径中9私人也对，另外4含表述/桥接/粒度边界；第1/35题仍有普通先给正确目标或纠正E工作再恢复的清楚过程，第70题局部区分先由普通提出。全核第1/27/35/70题B工作与必要资料，原文ID已绑定。

方向判断：核心保持专家任务优势转团队收益与有效纠正；近期由局部异常直接推新机制实验的顺序需纠正。D80讨论对E净改善/持平，不称普遍拖累；D16定向高终答成功、P0残留/角色包不对称/即时个人final且无下游，P0/P1 55/64、P2 54/64，不支持通用核查有效。末步实质翻转主要私人，128末步仅候选。19配对不再待办。

下一优先准备单一闭环对照：保留四基线，先针对隐藏讨论B增加仅E首次工作暂不接触全部同伴历史、随后恢复正常两轮互动的分支；同工作次数/顺序/私答/投票，在首次暴露前分叉并真实重生成受影响下游。检验公开贡献及团队收益，同时保留普通有效纠正，非强迫专家坚持。自然覆盖效果样本与定向机制病例分列，具体N/seed/预算与章程审核另冻结。若只改善表述/工作而不改善团队不称方法有效；若互补空间不足再小规模评异质设置。助手自审none/provisional；PASS本轮离线审核，机制/方法与启动就绪REVISE。本轮0新生成，无训练/C-H/原评分或投票改动。

`;
const targets=['handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md','experiment/results.md'];
for(const p of targets){const f=path.join(root,p),old=fs.readFileSync(f,'utf8');if(!old.includes(heading))fs.writeFileSync(f,entry+old);}
const names=['BRIEF.md','build_evidence.cjs','MATCHED_EVIDENCE.json','INPUT_HASHES.json','DECISION_TABLE.md','REPORT.md','STAGE_REVIEW.md','record_review.cjs'];
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(names.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(__dirname,p)))})),null,2)+'\n');
console.log(JSON.stringify({input_files_unchanged:inputs.length,records_updated:targets.length,new_model_calls:0}));
