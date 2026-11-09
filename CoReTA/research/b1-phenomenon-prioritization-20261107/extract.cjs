// Offline frozen-data inventory; does not alter model inputs, scores, or votes.
const fs=require('fs'),path=require('path'),crypto=require('crypto');
const root=path.resolve(__dirname,'../..');const used=new Set();
function read(p){used.add(p);return JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));}
const write=(p,x)=>fs.writeFileSync(path.join(__dirname,p),typeof x==='string'?x:JSON.stringify(x,null,2)+'\n');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(path.join(root,p))).digest('hex');
const old=read('research/b1-dev80-analysis-20261106/ANALYSIS.json');
const op=read('runs/b1-dev80-20261106-v1/INPUTS.json');
const np=read('runs/b1-grounded-revision-20261107-v1/INPUTS.json');
const ns=read('runs/b1-grounded-revision-20261107-v1/scores.json');
const nl=read('runs/b1-grounded-revision-20261107-v1/LABELS.json');
read('research/b1-d80-phenomenon-census-20261106/LAST_WORK_LABELS.json');
read('research/b1-grounded-revision-analysis-20261107/FRESH_E2_LABELS.json');
const rows=[];
for(const r of old.cases.filter(r=>r.complete)){
 const t=read(`runs/b1-dev80-20261106-v1/trials/${String(r.index).padStart(3,'0')}.json`);
 rows.push({cohort:'D80',index:r.index,key:`old:${r.index}`,id:r.id,group:op.groups[r.id],task:t.task,target:r.target,initials:r.initials,initialScores:r.initial_scores,arms:Object.fromEntries(['A','B','C','D'].map(c=>[c,{score:r.arms[c].score,finals:r.arms[c].finals,records:t.records.filter(z=>z.arm===c),orders:t.orders}]))});
}
for(const r of ns.rows.filter(r=>r.cohort==='fresh')){
 const e=np.tasks.find(e=>e.id===r.id),t=read(`runs/b1-grounded-revision-20261107-v1/trials/${String(e.index).padStart(3,'0')}.json`);
 rows.push({cohort:'fresh56',index:e.index,key:`new:${e.index}`,id:r.id,group:np.groups[r.id],strict:e.strict_training_answer_isolation,task:e.task,target:nl.targets[r.id],initials:t.initials,initialScores:r.initial,arms:Object.fromEntries(['A','B','C','D'].map(c=>[c,{score:r.conditions[c],finals:t.branches[c].finals,records:t.branches[c].records,orders:t.branches[c].orders}]))});
}
if(rows.length!==131||new Set(rows.map(r=>r.id)).size!==131||rows.some(r=>r.group===undefined))throw Error('Cohort or dependency-group inconsistency');
write('SOURCE_HASHES.json',{before:Object.fromEntries([...used].map(p=>[p,sha(p)])),new_model_calls:0});
write('INDEX.json',rows.map(r=>({key:r.key,id:r.id,group:r.group,strict:r.strict,question:r.task.question,gold:r.target.answer,aliases:r.target.answer_aliases,initials:r.initials,initialEM:Object.fromEntries(Object.entries(r.initialScores).map(([a,s])=>[a,s.em])),arms:Object.fromEntries(Object.entries(r.arms).map(([c,x])=>[c,{E:x.score.expert_em,T:x.score.expected_em,finals:x.finals,memberEM:Object.fromEntries(Object.entries(x.score.members).map(([a,s])=>[a,s.em]))}]))})));
const selections={};
for(const r of rows){const flags=[];for(const [p,d] of [['A','B'],['C','D']])if(r.arms[p].score.expert_em!==r.arms[d].score.expert_em)flags.push(`${d}-${p}:${r.arms[d].score.expert_em?'gain':'harm'}`);for(const c of ['B','D'])if(r.arms[c].score.expert_em&&r.arms[c].score.expected_em<1)flags.push(`${c}:E_final_readout`);if(flags.length)selections[r.key]=flags;}
write('SELECTION.json',selections);
function dossier(r,cs,mode='E'){
 const supporting=new Set(r.target.paragraphs.filter(p=>p.is_supporting).map(p=>p.idx));
 let out=`\n## ${r.key} ${r.id}\nQ: ${r.task.question}\nGold: ${r.target.answer}; aliases: ${JSON.stringify(r.target.answer_aliases)}\nInitial: ${JSON.stringify(r.initials)}\n`;
 out+='Source supporting paragraphs (full supplied context remains in immutable trial/input):\n';
 for(const p of r.task.paragraphs.filter(p=>supporting.has(p.idx)))out+=`[${p.idx} ${p.title}] ${p.paragraph_text}\n`;
 for(const c of cs){const a=r.arms[c];out+=`### ${c}: E=${a.score.expert_em}, T=${a.score.expected_em}; finals=${JSON.stringify(a.finals)}\n`;for(const z of a.records.filter(z=>z.stage==='work'&&(mode==='all'||z.actor==='M1')))out+=`[${z.request_id} ${z.actor}/r${z.round}] ${z.raw_output}\n`;}
 return out;
}
for(const cohort of ['D80','fresh56']){
 const rs=rows.filter(r=>r.cohort===cohort);
 write(`FINALS_${cohort}.txt`,rs.map(r=>{const m={};for(const c of ['A','B','C','D'])for(const [a,s]of Object.entries(r.arms[c].score.members)){const k=s.answer;if(!m[k])m[k]=[];m[k].push(`${c}${a}:${s.em}`);}return`${r.key} Q:${r.task.question}\nG:${r.target.answer} alias:${JSON.stringify(r.target.answer_aliases)}\nI:${JSON.stringify(r.initials)}\n${JSON.stringify(m)}\n`;}).join('\n'));
 write(`EVENTS_${cohort}.md`,rs.filter(r=>selections[r.key]).map(r=>dossier(r,['A','B','C','D'])).join('\n'));
}
write('FRESH_PRIVATE_FAILURE_WORK.md',rows.filter(r=>r.cohort==='fresh56').map(r=>{const cs=['A','C'].filter(c=>!r.arms[c].score.expert_em);return cs.length?dossier(r,cs):'';}).join('\n'));
// Equal-score controls: deterministic hash order among no-E-change/no-readout items,
// select three stable-correct and three stable-wrong per cohort; outcome strata explicit.
const controls=[];
for(const cohort of ['D80','fresh56'])for(const hit of [0,1]){
 const eligible=rows.filter(r=>r.cohort===cohort&&!selections[r.key]&&['A','B','C','D'].every(c=>r.arms[c].score.expert_em===hit)).sort((a,b)=>crypto.createHash('sha256').update(a.id).digest('hex').localeCompare(crypto.createHash('sha256').update(b.id).digest('hex')));
 controls.push(...eligible.slice(0,3).map(r=>({key:r.key,stableE:hit,selection:'deterministic hash order within explicit equal-score strata; diagnostic controls, not random prevalence sample'})));
}
write('CONTROLS.json',controls);write('CONTROLS.md',controls.map(c=>dossier(rows.find(r=>r.key===c.key),['A','B'])).join('\n'));
// A reusable loader for this stage only; exclude large payload/token IDs from derived copies.
write('ROWS.json',rows.map(r=>({...r,arms:Object.fromEntries(Object.entries(r.arms).map(([c,a])=>[c,{...a,records:a.records.map(z=>({request_id:z.request_id,stage:z.stage,round:z.round,actor:z.actor,raw_output:z.raw_output,status:z.status}))}]))})));
console.log(JSON.stringify({n:rows.length,groups:Object.fromEntries(['D80','fresh56'].map(c=>[c,new Set(rows.filter(r=>r.cohort===c).map(r=>r.group)).size])),selected:Object.keys(selections).length,controls:controls.map(c=>c.key),files:[...used].length}));
