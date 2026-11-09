// Offline inventory only. Keyword hits are screening cues, never semantic labels.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const ROOT=path.resolve(__dirname,'../..'),H=__dirname,used=new Map();
function read(p){const b=fs.readFileSync(path.join(ROOT,p));used.set(p,crypto.createHash('sha256').update(b).digest('hex'));return JSON.parse(b);}
const write=(p,x)=>fs.writeFileSync(path.join(H,p),typeof x==='string'?x:JSON.stringify(x,null,2)+'\n');
const old=read('research/b1-phenomenon-prioritization-20261107/ROWS.json');
const sc=read('research/b1-stage-advantage-review-20261107/COMPLETED_scores.json');
const target=read('runs/b1-grounded-revision-20261107-v1/LABELS.json').targets;
const rows=old.map(r=>({...r,source:r.cohort==='D80'?`runs/b1-dev80-20261106-v1/trials/${String(r.index).padStart(3,'0')}.json`:`runs/b1-grounded-revision-20261107-v1/trials/${String(r.index).padStart(3,'0')}.json`,seed:0}));
const oa=read('research/b1-dev80-analysis-20261106/ANALYSIS.json'),oi=read('runs/b1-dev80-20261106-v1/INPUTS.json');
for(const r of oa.cases.filter(r=>!r.complete)){
 const source=`runs/b1-dev80-20261106-v1/trials/${String(r.index).padStart(3,'0')}.json`,t=read(source);
 rows.push({key:`old:${r.index}`,cohort:'D80',index:r.index,seed:0,id:r.id,group:oi.groups[r.id],task:t.task,target:r.target,initials:t.initials,initialScores:r.initial_scores,source,arms:Object.fromEntries(['A','B','C','D'].map(a=>[a,{score:r.arms[a].score,finals:t.finals[a],records:t.records.filter(z=>z.arm===a)}]))});
}
for(const s of sc.rows){
 const source=`runs/b1-stage-advantage-seed1-20261107-v1/trials/${String(s.index).padStart(3,'0')}.json`,t=read(source);
 rows.push({key:`seed1:${s.index}`,cohort:'fresh56_seed1',index:s.index,seed:1,id:s.id,group:s.group,task:t.task,target:target[s.id],initials:t.initials,initialScores:s.initial,source,arms:Object.fromEntries(['A','B','C','D'].map(a=>[a,{score:s.arms[a],finals:t.finals[a],records:t.records.filter(z=>z.arm===a)}]))});
}
// Validate every derived earlier row against its immutable raw trial.
for(const r of rows.filter(r=>r.seed===0)){
 const t=read(r.source),raw=t.branches?null:t;
 const records=t.branches?t.branches.B.records:t.records.filter(z=>z.arm==='B');
 if(r.id!==(t.task?.id||t.id)||JSON.stringify(r.arms.B.finals)!==JSON.stringify(t.branches?t.branches.B.finals:t.finals.B))throw Error('Wrong raw source/finals '+r.key);
 const d=r.arms.B.records;for(const z of d){const q=records.find(x=>x.request_id===z.request_id);if(!q||q.raw_output!==z.raw_output)throw Error('Derived raw mismatch');}
}
const norm=s=>String(s).toLowerCase().replace(/[^\p{L}\p{N}]+/gu,' ').trim();
const entries=[];
for(const r of rows)for(const arm of ['B','D']){
 const a=r.arms[arm],s=a.score;if(!s?.complete)continue;
 const ework=a.records.filter(z=>z.actor==='M1'&&z.stage==='work');
 const aliases=[r.target.answer,...(r.target.answer_aliases||[])].filter(Boolean).map(norm);
 const hit=ework.some(z=>aliases.some(a=>(' '+norm(z.raw_output)+' ').includes(' '+a+' ')));
 entries.push({key:r.key,cohort:r.cohort,index:r.index,seed:r.seed,id:r.id,group:r.group,arm,source:r.source,question:r.task.question,gold:r.target.answer,aliases:r.target.answer_aliases||[],expertFinal:s.expert_em,team:s.expected_em,initialExpert:r.initialScores?.M1?.em,ordinaryCorrect:Object.values(s.members).slice(1).filter(z=>z.em===1).length,finals:a.finals,keywordHit:hit,expertWork:ework.map(z=>({request_id:z.request_id,round:z.round,text:z.raw_output,words:z.raw_output.trim().split(/\s+/).length})),screen: s.expert_em===1&&s.expected_em<1?'EXPERT_FINAL_TEAM_LOSS':s.expert_em===0&&s.expected_em>0?'ORDINARY_CORRECT_EXPERT_WRONG':s.expected_em<1&&(hit||r.initialScores?.M1?.em===1)?'OTHER_TEAM_LOSS_WITH_TARGET_CUE':'OTHER'});
}
write('INDEX.json',entries);
const chosen=entries.filter(e=>e.arm==='B'&&e.screen!=='OTHER');
write('CANDIDATE_TEXTS.md',chosen.map(e=>`## ${e.key}/${e.arm} ${e.screen}\nQ ${e.question}\nG ${e.gold}; aliases ${JSON.stringify(e.aliases)}\nFinals ${JSON.stringify(e.finals)}\n${e.expertWork.map(z=>`[r${z.round} ${z.request_id}] ${z.text}`).join('\n')}\n`).join('\n'));
write('SOURCE_HASHES.json',{new_model_calls:0,files:Object.fromEntries(used)});
const summary={new_model_calls:0,distinct_ids:new Set(rows.map(r=>r.id)).size,cohorts:{}};
for(const c of [...new Set(entries.map(e=>e.cohort))]){const es=entries.filter(e=>e.cohort===c&&e.arm==='B');summary.cohorts[c]={B_complete:es.length,expert_final_team_loss:es.filter(e=>e.screen==='EXPERT_FINAL_TEAM_LOSS').map(e=>e.index),ordinary_correct_expert_wrong:es.filter(e=>e.screen==='ORDINARY_CORRECT_EXPERT_WRONG').map(e=>e.index),other_cues:es.filter(e=>e.screen==='OTHER_TEAM_LOSS_WITH_TARGET_CUE').map(e=>e.index),expert_work_le10_words:es.flatMap(e=>e.expertWork).filter(w=>w.words<=10).length,expert_work_count:es.flatMap(e=>e.expertWork).length};}
write('SUMMARY.json',summary);console.log(JSON.stringify(summary,null,2));
