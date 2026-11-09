const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),RUN=path.join(ROOT,'runs/b1-independent-first-work-20261106-v1');
const read=p=>JSON.parse(fs.readFileSync(path.join(RUN,p),'utf8'));
const pack=read('INPUTS.json'),scores=read('scores.json'),labels=read('LABELS.json').targets;
const conds=['A','B','C','D','B_delay'];const sha=t=>crypto.createHash('sha256').update(t).digest('hex');
const items=pack.tasks.flatMap(e=>[0,1].map(rep=>({entry:e,item:read(`trials/${String(e.index).padStart(3,'0')}-r${rep}.json`),score:scores.rows.find(r=>r.index===e.index&&r.rep===rep)})));
const mean=a=>a.reduce((x,y)=>x+y,0)/a.length;
function stats(es){const n=es.length;return{units:n,questions:new Set(es.map(x=>x.entry.id)).size,groups:new Set(es.map(x=>pack.groups[x.entry.id])).size,initial:Object.fromEntries(['M1','M2','M3','M4'].map(a=>[a,mean(es.map(x=>x.score.initial[a].em))])),conditions:Object.fromEntries(conds.map(c=>[c,{teamEM:mean(es.map(x=>x.score.conditions[c].expected_em)),teamF1:mean(es.map(x=>x.score.conditions[c].expected_f1)),actualEM:mean(es.map(x=>x.score.conditions[c].actual_em)),expertEM:mean(es.map(x=>x.score.conditions[c].expert_em)),expertF1:mean(es.map(x=>x.score.conditions[c].members.M1.f1)),ordinaryEM:mean(es.flatMap(x=>['M2','M3','M4'].map(a=>x.score.conditions[c].members[a].em))),expertHarm:es.filter(x=>x.score.conditions[c].expert_harm).length,expertCorrection:es.filter(x=>x.score.conditions[c].expert_correction).length,ordinaryHarm:es.flatMap(x=>['M2','M3','M4'].map(a=>x.score.initial[a].em===1&&x.score.conditions[c].members[a].em===0)).filter(Boolean).length,ordinaryCorrection:es.flatMap(x=>['M2','M3','M4'].map(a=>x.score.initial[a].em===0&&x.score.conditions[c].members[a].em===1)).filter(Boolean).length,oracleEM:mean(es.map(x=>Object.values(x.score.conditions[c].members).some(m=>m.em===1)?1:0)),oracleReadoutLoss:es.reduce((s,x)=>s+(Object.values(x.score.conditions[c].members).some(m=>m.em===1)?1:0)-x.score.conditions[c].expected_em,0),ties:es.filter(x=>x.score.conditions[c].vote.tie).length,baseThreeRawSame:es.filter(x=>new Set(['M2','M3','M4'].map(a=>x.item.branches[c].finals[a])).size===1).length}]))};}
const coverage=items.filter(x=>x.entry.coverage),mechanism=items.filter(x=>x.entry.mechanism);
const summaries={coverage:stats(coverage),seed0:stats(coverage.filter(x=>x.item.rep===0)),seed1:stats(coverage.filter(x=>x.item.rep===1)),mechanism:stats(mechanism),union:stats(items)};
const unique=new Map();
for(const x of items)for(const c of ['B','B_delay'])for(const r of x.item.branches[c].records.filter(r=>r.actor==='M1'&&r.stage==='work')){
 const key=[x.entry.id,r.raw_output].join('|');
 if(!unique.has(key))unique.set(key,{uid:unique.size,index:x.entry.index,question:x.entry.task.question,gold:labels[x.entry.id].answer,text:r.raw_output,sha256:sha(r.raw_output),refs:[]});
 unique.get(key).refs.push({index:x.entry.index,rep:x.item.rep,condition:c,round:r.round,request_id:r.request_id});
}
const ework=[...unique.values()];
fs.writeFileSync(path.join(__dirname,'E_WORK_UNIQUE.json'),JSON.stringify(ework,null,2)+'\n');
const uidMap=new Map(ework.flatMap(x=>x.refs.map(r=>[r.request_id,x.uid])));
const pairs=items.map(x=>{const es=c=>x.item.branches[c].records.filter(r=>r.actor==='M1'&&r.stage==='work').map(r=>({uid:uidMap.get(r.request_id),request_id:r.request_id,text:r.raw_output,tokens:r.usage.output_tokens}));const b=x.score.conditions.B,d=x.score.conditions.B_delay;return{index:x.entry.index,number:x.entry.index+1,rep:x.item.rep,coverage:x.entry.coverage,mechanism:x.entry.mechanism,question:x.entry.task.question,gold:labels[x.entry.id].answer,initials:x.item.initials,initialEM:Object.fromEntries(Object.entries(x.score.initial).map(([a,v])=>[a,v.em])),expertWorkB:es('B'),expertWorkDelay:es('B_delay'),team:[b.expected_em,d.expected_em],expert:[b.expert_em,d.expert_em],finalsB:x.item.branches.B.finals,finalsDelay:x.item.branches.B_delay.finals,teamDelta:d.expected_em-b.expected_em,expertDelta:d.expert_em-b.expert_em,finalTextChanges:['M1','M2','M3','M4'].filter(a=>x.item.branches.B.finals[a]!==x.item.branches.B_delay.finals[a])};});
const cost={};for(const c of conds){const rs=items.flatMap(x=>x.item.branches[c].records);cost[c]={logicalBranchRequests:rs.length,inputTokens:rs.reduce((s,r)=>s+r.usage.input_tokens,0),outputTokens:rs.reduce((s,r)=>s+r.usage.output_tokens,0),generationSeconds:rs.reduce((s,r)=>s+r.usage.elapsed_seconds,0),firstE:rs.filter(r=>r.actor==='M1'&&r.stage==='work'&&r.round===1).map(r=>({input:r.usage.input_tokens,output:r.usage.output_tokens,seconds:r.usage.elapsed_seconds}))};}
const out={scope:'INPUT_SCREENED_REUSED_DEVELOPMENT_ASSISTANT_EXPLORATION',new_model_calls:0,summaries,cost,pairs,uniqueExpertWorkTexts:ework.length,expertWorkRecords:items.length*4,changes:pairs.filter(x=>x.teamDelta||x.expertDelta),allFinalTextChangedPairs:pairs.filter(x=>x.finalTextChanges.length).map(x=>({index:x.index,rep:x.rep,actors:x.finalTextChanges}))};
fs.writeFileSync(path.join(__dirname,'ANALYSIS.json'),JSON.stringify(out,null,2)+'\n');
for(const i of [...new Set([77,18,17,...pack.mechanism_indices])]){
 const lines=[`# 第${i+1}题（index${i}）完整B与B_delay过程`,''];
 for(const x of items.filter(x=>x.entry.index===i)){
 lines.push(`## Seed ${x.item.rep}`,`Question: ${x.entry.task.question}`,`Gold: ${labels[x.entry.id].answer}`,`Initial: ${JSON.stringify(x.item.initials)}`);
 for(const c of ['B','B_delay']){lines.push(`### ${c}`);for(const r of x.item.branches[c].records)lines.push(`#### ${r.request_id} ${r.actor} ${r.stage} round${r.round}`,r.raw_output,'');lines.push(`Team expected EM: ${x.score.conditions[c].expected_em}`);}
 }
 fs.writeFileSync(path.join(__dirname,`CASE_${String(i).padStart(3,'0')}.md`),lines.join('\n')+'\n');}
console.log(JSON.stringify({summaries,changes:out.changes.map(x=>({index:x.index,rep:x.rep,team:x.team,expert:x.expert})),uniqueExpertWorkTexts:ework.length,allFinalTextChangedPairs:out.allFinalTextChangedPairs,cost:Object.fromEntries(conds.map(c=>[c,{...cost[c],firstE:undefined}]))},null,2));
