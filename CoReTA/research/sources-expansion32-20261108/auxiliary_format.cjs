// Retrospective narrow exact aliases. Does not modify frozen scores or responses.
const fs=require('fs'),path=require('path');const here=__dirname,root=path.resolve(here,'../..');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const tasks=load(path.join(here,'tasks.json')),gold=load(path.join(here,'labels.json'));
const rows=fs.readFileSync(path.join(root,'runs/sources-expansion32-20261108-v1/responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const original=load(path.join(root,'runs/sources-expansion32-20261108-v1/scores.json'));
const aliases={38:Object.fromEntries(Object.keys(tasks.find(t=>t.id===38).options).map(v=>[v.split(' (')[0],v])),62:{'AI hardware startup':'Option B: AI hardware startup'}};
const units=[];
for(const s of original){
 const finals=rows.filter(r=>r.task_id===s.task_id&&r.unit_seed===s.unit_seed&&r.arm===s.arm&&r.stage==='final');
 const names=finals.map(r=>r.answer===null?(aliases[s.task_id]?.[r.text.trim()]||null):r.answer);
 if(names.some(n=>n===null))throw Error('unknown_outside_frozen_exact_retrospective_aliases');
 let score;if(s.arm==='S_same_sources_m1')score=+(names[0]===gold[s.task_id].correct);else{
  const counts=new Map();for(const n of names)counts.set(n,(counts.get(n)||0)+1);const max=Math.max(...counts.values());const winners=[...counts].filter(([n,c])=>c===max).map(([n])=>n);score=winners.includes(gold[s.task_id].correct)?1/winners.length:0;
 }
 units.push({task_id:s.task_id,seed:s.unit_seed,arm:s.arm,score,strict_score:s.score,was_strict_unknown:s.score===null});
}
const result={primary:false,rule_status:'posthoc exploratory exact-name correspondence only; no raw/frozen-score modification',aliases,
 n_tasks:32,n_task_seed_units:64,means:Object.fromEntries(['B_ordinary','E_facts','S_same_sources_m1'].map(a=>[a,units.filter(s=>s.arm===a).reduce((v,s)=>v+s.score,0)/64])),
 recovered_units:units.filter(s=>s.was_strict_unknown),limits:'Alias table was defined after reading these outputs. Cannot claim prespecified full32 scoring or independent semantic validation.'};
fs.writeFileSync(path.join(here,'AUXILIARY_FORMAT_REVIEW.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result,null,2));
