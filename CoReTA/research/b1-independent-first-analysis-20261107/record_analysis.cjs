const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const read=n=>JSON.parse(fs.readFileSync(path.join(__dirname,n),'utf8'));
const audit=read('POST_RUN_AUDIT.json');if(audit.verdict!=='PASS_RECORDS_REQUESTS_AND_SCORES')throw Error('Audit failed');
for(const [p,h]of Object.entries(audit.original_run_file_hashes)){
 const local=path.join(ROOT,p.replace('/data2/xiaoxinchen/agent-research/CoReTA/',''));
 if(sha(fs.readFileSync(local))!==h)throw Error('Source differs: '+p);
}
const coverage={reviewer:'assistant',independence:'none/provisional',expert_public_work_records:200,unique_expert_public_full_texts:142,all_expert_texts_read:true,private_final_records:1000,unique_final_texts_by_question:80,all_final_short_texts_read:true,full_B_and_Bdelay_work_pairs:[{index:77,rep:1},{index:18,rep:1},{index:17,rep:0}],full_Bdelay_work_paths:[{index:52,rep:0},{index:26,rep:0}],additional_read_scope:[{index:0,rep:1,conditions:['B','B_delay'],stages:'all first-round work and second E work'},{index:34,rep:0,conditions:['B','B_delay'],stages:'all first-round work and second E work'}],not_claimed:'All 800 public work texts or private-work full semantic annotation; exported CASE files are not automatically fully read.',labels_scope:'Task-target candidate endorsement only, not full grounding/internal reasoning quality.'};
fs.writeFileSync(path.join(__dirname,'SEMANTIC_REVIEW_COVERAGE.json'),JSON.stringify(coverage,null,2)+'\n');
const heading='## 2026-11-07 首次独立工作分析完成：小幅团队收益，优势形成与采用仍需区分';
const entry=`${heading}

见research/b1-independent-first-analysis-20261107/REPORT.md、POST_RUN_AUDIT.json、ANALYSIS.json、PROCESS_ANALYSIS.json、E_WORK_LABELS.json及STAGE_REVIEW.md。25题×2seed×5支完整；3133物理=3200逻辑-67同批共享，全部EOS；5h23m02s、366543输出token。独立重建3200请求/权限/顺序和50首次屏蔽+50恢复，逐条token解码/实际路由/长度、官方评分与主bootstrap通过，冻结和原件未变；全档本机SHA 2c180be16f9d4df62081bd904e9fa97676a65d7b78d50ad84898d883eb6ec696。

主24覆盖题48单位：A/B/C/D/B_delay团队41.67/62.50/50/62.50/66.67%，E终答56.25/62.50/56.25/62.50/64.58%；E初答60.42%。主B_delay-B +4.17pp、CI[0,10.42]，仅原第78和19题各seed1改善，0官方EM降低；seed0两方法16/24，seed1 14→16/24。两收益中E末答均不变，队友从1896/Anuman改为1934/Hall，公开贡献利用是直接线索；第19首次裸Hall本来对，关系句后下游才接通，不只候选正确性。第18题seed0 E个人终答变对但公开工作仍不对、团队仍错，不能称公开正确被拒。八机制16单位B/B_delay均14/16、逐对无变化；7与主样本重合不重复。

全200E工作去重142全文/1000末答按题去重80全文核读；辅助标签非独立全推理认证。首次E正确候选29→37、第二28→32；11首次改善中7下一轮丢失（第27一次，第24/79/53各两seed），3首次变坏。第53两seed独立先Los Angeles仍被恢复后错误县名替代，最后全错；第1题seed1屏蔽普通先对意见让E先1810，普通指正后E恢复1843，纠正机会保留，非必要性已证。部分普通完整核读范围另存SEMANTIC_REVIEW_COVERAGE，不冒称800工作全标。

本批讨论团队点估计高于私人E，但区间宽/算力不同/筛选开发样本；不能沿用旧80的相反数值也不普遍化。官方团队高于同讨论E的部分来自第63题完整日期vs年份评分，不能当实质普通纠正。清楚等价短串辅助B66.67/B_delay70.83仍差4.17；时段边界计入可变3.65且E净差0，所以不称完全无损。B_delay逻辑生成时少2.98%、输出少1.01%，非大幅加速。

判断：保留轻量首次独立作诊断基线，未建立稳定新方法、专家特有或多数心理机制。下一优先事先固定有限额外seed检查24覆盖样本重复性；若仍集中少数病例，再针对正确目标关系如何传递、何种依据允许后续替代设计具体消息对照，保留第1/35普通纠正反例，不只保护专家。PASS本次记录/统计/探索性过程分析，机制泛化/算法/独立确认REVISE。本轮0新生成/训练/C-H评估，原评分/金标/投票未改，未启动下一批。

`;
const targets=['handoff.md','CURRENT_STATE.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md','experiment/results.md'];
for(const p of targets){const f=path.join(ROOT,p),old=fs.readFileSync(f,'utf8');if(!old.includes(heading))fs.writeFileSync(f,entry+old);}
const files=fs.readdirSync(__dirname).filter(p=>/\.(md|json|py|cjs)$/.test(p)&&p!=='ARTIFACT_HASHES.json');
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(files.map(p=>({path:p,sha256:sha(fs.readFileSync(path.join(__dirname,p)))})),null,2)+'\n');
console.log(JSON.stringify({sourceFilesVerified:Object.keys(audit.original_run_file_hashes).length,recordsUpdated:7,artifactFiles:files.length,newModelCalls:0}));
