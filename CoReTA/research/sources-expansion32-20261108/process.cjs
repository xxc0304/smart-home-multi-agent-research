const fs=require('fs'),path=require('path');
const here=__dirname,root=path.resolve(here,'../..'),run=path.join(root,'runs/sources-expansion32-20261108-v1');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const rows=fs.readFileSync(path.join(run,'responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const tasks=load(path.join(here,'tasks.json')),labels=load(path.join(here,'labels.json')),scores=load(path.join(run,'scores.json'));
const summary=load(path.join(here,'SUMMARY.json')),ids=new Set();
for(const k of ['E_minus_B','E_minus_S'])for(const side of ['gained_task_seed_units','lost_task_seed_units'])for(const [n,s]of summary[k][side])ids.add(n+':'+s);
const selected=[...ids].map(k=>k.split(':').map(Number)).sort((a,b)=>a[0]-b[0]||a[1]-b[1]);
const units=selected.map(([n,s])=>{const rr=rows.filter(r=>r.task_id===n&&r.unit_seed===s);const map=new Map();for(const r of rr){if(!map.has(r.text))map.set(r.text,{text:r.text,at:[]});map.get(r.text).at.push({call:r.call,actor:r.actor,stage:r.stage,arm:r.arm,round:r.round});}return {task_id:n,seed:s,scores:scores.filter(r=>r.task_id===n&&r.unit_seed===s).map(r=>({arm:r.arm,score:r.score,M1:r.M1_correct,initial:r.initial_answers,final:r.final_answers})),rows:rr.length,unique:[...map.values()],source:tasks.find(t=>t.id===n),gold:labels[n].correct};});
fs.writeFileSync(path.join(here,'PROCESS_CASES.json'),JSON.stringify(units,null,2)+'\n');
if(process.argv[2]==='inventory'){
 console.log(JSON.stringify({units:units.length,source_tasks:[...new Set(units.map(u=>u.task_id))],responses:units.reduce((s,u)=>s+u.rows,0),unique_characters:units.reduce((s,u)=>s+u.unique.reduce((v,r)=>v+r.text.length,0),0),case_sizes:units.map(u=>({task:u.task_id,seed:u.seed,unique:u.unique.length,chars:u.unique.reduce((s,r)=>s+r.text.length,0)}))},null,2));
}else if(['case','sentences','compact'].includes(process.argv[2])){
 const n=+process.argv[3],s=+process.argv[4];let u=units.find(u=>u.task_id===n&&u.seed===s);if(!u){const rr=rows.filter(r=>r.task_id===n&&r.unit_seed===s);const map=new Map();for(const r of rr){if(!map.has(r.text))map.set(r.text,{text:r.text,at:[]});map.get(r.text).at.push({call:r.call,actor:r.actor,stage:r.stage,arm:r.arm,round:r.round});}u={task_id:n,seed:s,source:tasks.find(t=>t.id===n),gold:labels[n].correct,scores:scores.filter(r=>r.task_id===n&&r.unit_seed===s),unique:[...map.values()]};}
 console.log(JSON.stringify({task:u.task_id,seed:u.seed,source:u.source,gold:u.gold,scores:u.scores}));
 if(['sentences','compact'].includes(process.argv[2])){
  const dict=[],seen=new Map(),timeline=[];
  const rr=rows.filter(r=>r.task_id===n&&r.unit_seed===s);
  for(const r of rr){const pieces=r.text.split(/(?<=[.!?])\s+|\r?\n+/).filter(x=>x.trim());const si=pieces.map(text=>{if(!seen.has(text)){seen.set(text,dict.length);dict.push(text);}return seen.get(text);});timeline.push({c:r.call,a:r.actor,k:r.stage==='work'?r.arm[0]+r.round:r.stage==='final'?r.arm[0]+'f':r.stage==='initial'?'i':r.stage==='facts'?'facts':'exchange',answer:r.answer,s:si});}
  if(process.argv[2]==='compact'){
   for(let i=0;i<dict.length;i++)console.log(i+' '+dict[i]);
   for(const r of timeline)console.log([r.c,r.a,r.k,r.answer===null?'?':Object.keys(u.source.options).indexOf(r.answer)+1,r.s.join(',')].join('|'));
  }else console.log(JSON.stringify({sentence_dictionary:dict,timeline}));
 }else for(const r of u.unique)console.log(JSON.stringify(r));
}
