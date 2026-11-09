const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 2026-11-07 候选现象核验完成：私人终答失配优先排查，保留专家互动主线

见research/b1-phenomenon-prioritization-20261107/REPORT.md、RESULTS.json、ANNOTATIONS.json和STAGE_REVIEW.md。旧共同75题/62关联组、新56/46组分别核验，131不同ID；524条E最后工作（267既有标签文本/SHA校验复用，257新增判读），54配对专家EM转移、21读出候选及全部77个最后工作C/终答EM0差异均列判定。12同分诊断控制、3道普通工作定向反例不作代表样本。C为目标候选承诺，非整链/信念或来源质量认证。

私人正确目标候选到不同目标末答：旧16/150路径、9/75题/8关联组；新12/112、8/56题/6组。讨论本口径未见清楚同类换目标（150/112路径；非总体为0）。隐藏E改善旧8条中4、新9条中4含私人末步失配；揭示旧5中4、新13中7。不可把全部改善算同伴新知识。B-A正式E损益旧4/44正确机会降、8/31错误机会升；新4/35降、9/21升，含语义/题面边界。旧15/新6条E正确团队漏选，多数未清楚公开正确判断或表述边界；旧69/B仅清楚局部未采用候选且起源桥接弱，不再当高频主机制。

优先级明确：先诊断私人终答失配这个跨批混杂，不自动升为论文核心；主线仍专家判断在互动中的保留/受损及有益普通纠正，公开讲对被拒直接证据不足暂缓。普通总体末步率、adapter/上下文/提示效应未隔离，不宣称心理原因或一般规律。旧16已发现，新12为新增覆盖。524专家终答含精确E第二工作和原问题/全文材料、路由状态/原输出一致，786普通讨论终答能见E第二工作，138来源哈希不变；未见漏传或串位，不排除其他设置原因。

PASS本阶段证据/排序交付，REVISE主现象确认/因果/普遍增益与有效方法。允许补普通末步离线对照和准备有区分预测的小诊断；最多48终答回放仍提案未冻结启动，不自动百题方法、训练、新C-H评估或整批重跑。无新模型调用，助手自审none/provisional，非独立人工复核。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];
const changes=[];for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=sha(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:sha(p)});}
fs.writeFileSync(path.join(__dirname,'RECORD_UPDATE.json'),JSON.stringify({scope:'COMPLETED_OFFLINE_PRIORITIZATION_NOT_NEW_EXPERIMENT_OR_FULL_SEMANTIC_CENSUS',date:'2026-11-07',changes,new_model_calls:0},null,2)+'\n');
const hashes=Object.fromEntries(fs.readdirSync(__dirname).filter(f=>f!=='ARTIFACT_HASHES.json').map(f=>[f,sha(path.join(__dirname,f))]));
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify({files:hashes,reviewer:'assistant',independence:'none/provisional',new_model_calls:0},null,2)+'\n');
console.log(JSON.stringify({records:changes.length,artifacts:Object.keys(hashes).length,new_model_calls:0}));
