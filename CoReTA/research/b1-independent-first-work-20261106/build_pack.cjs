const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const rel='runs/b1-dev80-20261106-v1';
const sourcePaths=new Set([`${rel}/INPUTS.json`,'research/b1-dev80-analysis-20261106/ANALYSIS.json']);
const inputs=JSON.parse(fs.readFileSync(path.join(ROOT,rel,'INPUTS.json'),'utf8'));
const analysis=JSON.parse(fs.readFileSync(path.join(ROOT,'research/b1-dev80-analysis-20261106/ANALYSIS.json'),'utf8'));
const salt='coreta-first-work-natural-20261106-v1|';
const excluded={
71:'Garfield Peak同时属Collegiate Peaks/Sawatch/Rocky多层山系，目标粒度非唯一。',
44:'材料是政府合署办公楼，不明确支持城市为县首府；capital/seat桥接弱。',
53:'broadcaster与and the hound拼接题意不完整，依赖Fox标题词串桥接。',
67:'Orsini意大利/英国home country指代不明，目标1934来自英国材料。',
9:'谁in charge未定时间，材料只说上一任联盟首席部长，核心时间指代不足。',
13:'Alberto Lista支持段未给出生地，关联博物馆缺链。',
35:'制造公司DaimlerChrysler与Chrysler创办者不是同一组织，缺少公司归属桥接。',
50:'父子Dodgson同名且材料父子关系桥接不足。',
54:'Tehran市与Tehran省/Ray县范围不同，题目城市归属链不足。',
61:'出生地either Ghent or Kassel；湖横跨县不能唯一支持出生地边界关系。',
66:'first invaded by British与Norman首次登陆、王权介入不等价，历史事件界定歧义。',
58:'Marvin与Anna共同写歌不证明配偶关系。',
48:'Nile/continent/中间航程/加勒比的核心桥接在题面和资料中不完整。',
7:'Hong Kong制作电影不自动证明故事based in香港。',
29:'首任军官/Commandant不等同创办者；海军与海军陆战队双制作方未消歧。',
12:'同建筑有CSIC总部不等同博物馆所属，且已有缩写表述边界。',
59:'发现最高峰和发现尸体时间存在核心歧义。'};
const notes={17:'边界由Colgate跨县线推得；非穷尽所有邻县。',14:'按材料当前货币metical的引入理解；保留first currency轻度措辞边界。',68:'UN Women为UN实体，机构层级是材料内局部推断。',73:'按给定材料Harris早期唱片标签回答；非全职业生涯唯一唱片公司。',77:'wipe out按defunct理解。',78:'按给定历史材料29州评分，不引入当前州数。'};
const purpose={0:'普通成员先形成正确机构年份，专家初答错误；检验有效纠正保留。',21:'同父关系可推出姐妹，公开拒绝推断；目标关系绑定。',26:'乐队总销量被误读为专辑销量，且有团队损失候选。',31:'村庄所属国家被误读成村庄是国家；同时旧讨论团队改善，防只挑损害。',34:'第一/第二位主席，普通成员能纠正专家错误工作。',38:'私人工作正确而末答错；检验阶段问题是否误当讨论瓶颈。',52:'市与县，局部消息对照已改变E工作但未跑下游。',63:'Carnival专辑与嘉年华活动误读；旧团队仍对，检验工作改善是否必要。'};
const ranked=analysis.cases.map(x=>({index:x.index,id:x.id,key:sha(salt+x.id)})).sort((a,b)=>a.key.localeCompare(b.key));
const reviewed=[],coverage=[];
for(const r of ranked){
 const x=analysis.cases.find(x=>x.index===r.index),p=`${rel}/trials/${String(r.index).padStart(3,'0')}.json`;
 sourcePaths.add(p);const t=JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
 reviewed.push({...r,question:t.task.question,eligible:!(r.index in excluded),reason:excluded[r.index]||notes[r.index]||'题目目标与材料支持链可判定。',support_paragraphs:t.task.paragraphs.filter(p=>x.target.paragraphs.find(z=>z.idx===p.idx)?.is_supporting),target:x.target});
 if(!(r.index in excluded))coverage.push(r.index);
 if(coverage.length===24)break;
}
const selected=[...new Set([...coverage,...Object.keys(purpose).map(Number)])];
if(selected.length!==25||reviewed.length!==41||reviewed.filter(x=>!x.eligible).length!==17)throw Error('selection mismatch');
const tasks=selected.map(index=>{
 const p=`${rel}/trials/${String(index).padStart(3,'0')}.json`;sourcePaths.add(p);
 const t=JSON.parse(fs.readFileSync(path.join(ROOT,p),'utf8'));
 return {index,id:t.task.id,task:t.task,source_path:p,coverage:coverage.includes(index),mechanism:index in purpose,mechanism_reason:purpose[index]||null,quality_note:notes[index]||'题目目标与材料支持链可判定。'};
});
const pack={version:'B1_INDEPENDENT_E_FIRST_WORK_V1',salt,scope:'INPUT_SCREENED_REUSED_DEVELOPMENT_NOT_BLIND_OR_HOLDOUT',coverage_indices:coverage,mechanism_indices:Object.keys(purpose).map(Number),unique_questions:25,repeats:[0,100000000],tasks,groups:Object.fromEntries(tasks.map(x=>[x.id,inputs.groups[x.id]])),source_sha256:Object.fromEntries([...sourcePaths].map(p=>[p,sha(fs.readFileSync(path.join(ROOT,p)))]))};
fs.writeFileSync(path.join(__dirname,'INPUTS.json'),JSON.stringify(pack,null,2)+'\n');
fs.writeFileSync(path.join(__dirname,'LABELS.json'),JSON.stringify({targets:Object.fromEntries(tasks.map(x=>[x.id,analysis.cases.find(z=>z.id===x.id).target]))},null,2)+'\n');
fs.writeFileSync(path.join(__dirname,'SELECTION_REVIEW.json'),JSON.stringify({reviewer:'assistant',independence:'none/provisional',criterion:'Input-only missing/incorrect bridge or core referent/granularity ambiguity; no filtering by old/new correctness. Previously exposed development data.',reviewed,mechanism:purpose},null,2)+'\n');
console.log(JSON.stringify({coverage,mechanism:Object.keys(purpose).map(Number),unique_questions:25,audited:reviewed.length,skipped:17,max_calls:3200,max_output_tokens:2355200}));
