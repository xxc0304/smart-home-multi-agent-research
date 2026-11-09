const fs=require('fs'),path=require('path'),crypto=require('crypto');const root=path.resolve(__dirname,'../..'),sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const block=`## 56题新seed复核后审完成：私人优势缩小复现，专家改善与团队转化分开

见research/b1-stage-advantage-review-20261107/COMPLETED_REVIEW.md、COMPLETION_AUDIT.json、TWO_SEED_ANALYSIS.json。56全部处理/54四组完整，2855尝试=返回=2912−9−48，2853EOS+2超限：index26 D/r1/M4工作1024余9依赖跳过；index37 M4初答256余四组48跳过。4小时26分37秒/310556输出token，进程结束；无自动重试/系统故障。全部请求状态机重建、种子/原顺序/252层路由/token解码/长度/56评分行及219分支/冻结通过；实际最大6957<16384，档案SHA cb67f8c49b47c97212e3cc77af851297c2a52df75b51cddafef44b0c82f3209c全部成员本机核验。

主配对同54题/45关联组：原/新seed初答E64.81/普通30.25、64.81/30.86；A私人61.11/63.58、62.96/59.88；C57.41/61.11、61.11/55.56。新A优势缩小30.86pp（组描述区间[-52.54,-9.52]），C缩小28.40pp，主要普通上升而非E大幅下降。冻结明确表述/F1/宽口径、缺失算术包络仍支持缩小，不认定专家总体等效/失效；同题两seed不算112题。新私人A工作E15.08token/普通217.14，短输出差异重复，未隔离长度/提示/训练原因。

原/新同题B-A专家+11.11/+16.67pp，团队仅+3.24/+4.17pp；平均团队+3.70pp组区间[-2.82,11.06]，不能称稳定净增益。新index6 E持续公开Crawford、普通把原县当相邻目标，团队错，是短正确答案未转为共同正确关系判断候选，非完整推理被拒/因果从众；原seed该题成功。index17/49/54公开错误/撤回后私答对，不能都叫正确专家被忽视。index43 E错而普通保留English团队对，私人E链也错认母亲；index35私人正确工作后终答换错复现。过程只选8题E工作+资料、index6普通工作，不是全量语义机制普查。

PASS完成与限定跨seed复核，REVISE总体等效/心理因果/普遍拖累/方法有效。沿最新性能导向，下一离线至多两张具体组织决策假设卡、区分预测、简单强对照和预算，不无限追加普查/seed，不自动新模型调用、训练/C-H评估或重跑失败。助手自审none/provisional，非独立人工。

`;
const files=['CORE_RESEARCH_BRIEF.md','CURRENT_STATE.md','handoff.md','brainstorm.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/WORK_TRACKER.md','refine-logs/expert-mechanism-pilot-20261030/STAGE_REVIEWS.md','refine-logs/expert-mechanism-pilot-20261030/NEXT_TASKS_20261104.md'];
const changes=[];for(const f of files){const p=path.join(root,f),t=fs.readFileSync(p,'utf8'),before=sha(p);if(!t.includes(block.split('\n')[0]))fs.writeFileSync(p,block+t);changes.push({path:f,before,after:sha(p)});}
fs.writeFileSync(path.join(__dirname,'COMPLETION_RECORD_UPDATE.json'),JSON.stringify({scope:'COMPLETE_RUN_AND_LIMITED_REPLICATION_AUDIT',changes,new_model_calls:0},null,2)+'\n');
const filesHash=Object.fromEntries(fs.readdirSync(__dirname).filter(n=>n!=='ARTIFACT_HASHES.json').map(n=>[n,sha(path.join(__dirname,n))]));fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify({files:filesHash,scope:'COMPLETE_AUDIT_AND_ANALYSIS',independence:'none/provisional'},null,2)+'\n');console.log(JSON.stringify({records:changes.length,artifacts:Object.keys(filesHash).length}));
