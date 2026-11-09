const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),read=p=>JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
const rows=read('research/b1-phenomenon-prioritization-20261107/ROWS.json');
const positive=rows.filter(r=>['new:27','new:28','new:45'].includes(r.key)).map(r=>{
 const w=r.arms.B.records.filter(z=>z.stage==='work'),p=w.findIndex(z=>z.actor==='M1');
 return {key:r.key,id:r.id,question:r.task.question,initials:r.initials,finals:r.arms.B.finals,prior_ordinary_work:w.slice(0,p),expert_first_work:w[p],scope:'Compatible with ordinary contribution preceding expert correction; shared task/initials and no matched intervention mean this is not causal proof. Bridge27 retains upstream uncertainty; actor28 local relation and Liszt45 are positive boundaries.'};
});
fs.writeFileSync(path.join(__dirname,'POSITIVE_BOUNDARIES.json'),JSON.stringify(positive,null,2));
const note='## 2026-11-09 自然专家依据可用性审核完成\n\nP18：research/expert-natural-evidence-audit-20261109/REPORT.md。原80隐藏B79有效、新56原seed56/第二seed55，190路径135不同有效题；全部136不同题登记并保留缺失，不将seed/成员当独立题。21正式专家末答对/团队漏选来自19题：6表述边界、11公开未清楚讲对、其余短答/撤回或源边界；51候选102专家公开工作重新核读、绑定原文/hash。补入旧四组不全但B有效4题，old53晚公开Fox/10July1981正确局部关系而四末答都错，M1最后发言、无普通后续工作、四末答均确含该原文；单题交付候选非专家被反驳。old69国家/城市区分清楚但上游起源链弱。保留普通先对/专家后纠正27/28/45边界，不作因果传授证明。原12–16题自然正确依据对照材料前提不足，HOLD不人工补解析/凑题/新GPU；下一需具体设计自然专家说明生成与同预算/暴露时点，解释错也保留。新增模型调用0，源hash不变，助手审核provisional非独立人工。\n\n';
for(const f of ['handoff.md','CURRENT_STATE.md'])fs.writeFileSync(path.join(ROOT,f),note+fs.readFileSync(path.join(ROOT,f),'utf8'));
fs.appendFileSync(path.join(ROOT,'brainstorm.md'),'\n2026-11-09 P18：候选瓶颈应分专家公开内容形成、接收者关系应用、末答交付/投票。自然依据审核190隐藏B路径中21正式漏选并非21有效解释被拒；old53晚正确局部关系丢失、old69上游弱与两县短答须分开。原12–16题直接自然依据对照输入不足，未启动；下一模型自然说明和同预算时点控制尚待具体设计。保留27/28/45普通贡献正向边界，不预设跟专家。详见research/expert-natural-evidence-audit-20261109/REPORT.md。\n');
const files=fs.readdirSync(__dirname).filter(f=>fs.statSync(path.join(__dirname,f)).isFile()&&f!=='ARTIFACT_HASHES.json');
fs.writeFileSync(path.join(__dirname,'ARTIFACT_HASHES.json'),JSON.stringify(Object.fromEntries(files.map(f=>[f,crypto.createHash('sha256').update(fs.readFileSync(path.join(__dirname,f))).digest('hex')])),null,2));
console.log('P18_RECORDED_NO_MODEL_CALLS');
