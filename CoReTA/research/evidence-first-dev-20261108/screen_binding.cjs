const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'../..');
const tasks=JSON.parse(fs.readFileSync(path.join(__dirname,'tasks.json'),'utf8'));
const rows=['evidence-first-dev-20261108-v1','evidence-first-remainder-20261108-v1'].flatMap(run=>fs.readFileSync(path.join(root,'runs',run,'responses.jsonl'),'utf8').trim().split('\n').map(x=>({...JSON.parse(x),run})));
const last=rows.filter(r=>r.stage==='work'&&r.round===4);const candidates=[];
for(const r of last){const t=tasks.find(t=>t.id===r.task_id);const body=r.text.split(/ANSWER\s*:/i)[0];
 const mentioned=Object.entries(t.options).map(([id,name])=>({id,name,pos:body.toLowerCase().lastIndexOf(name.toLowerCase())})).filter(x=>x.pos>=0).sort((a,b)=>b.pos-a.pos);
 if(r.answer&&mentioned.length&&mentioned[0].id!==r.answer)candidates.push({task:r.task_id,arm:r.arm,actor:r.actor,call:r.call,run:r.run,answer:r.answer,last_name:mentioned[0].name,last_name_id:mentioned[0].id,text:r.text});
}
fs.writeFileSync(path.join(__dirname,'BINDING_SCREEN.json'),JSON.stringify({note:'Last-mentioned name heuristic only; requires reading full text; not semantic score replacement.',last_work_count:last.length,candidates},null,2));
console.log(JSON.stringify({last_work_count:last.length,candidates}));
