const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'../..');
const runs=['evidence-first-dev-20261108-v1','evidence-first-remainder-20261108-v1'];
const rows=runs.flatMap(run=>fs.readFileSync(path.join(root,'runs',run,'responses.jsonl'),'utf8').trim().split('\n').map(s=>({...JSON.parse(s),run})));
const tasks=JSON.parse(fs.readFileSync(path.join(__dirname,'tasks.json'),'utf8'));
const wanted=process.argv.slice(2).map(Number);
for(const id of wanted){const t=tasks.find(t=>t.id===id);console.log('\nTASK '+id+'\n'+JSON.stringify(t));
 for(const r of rows.filter(r=>r.task_id===id&&(
   r.stage==='initial'||r.stage==='exchange'&&r.arm==='B_ordinary'||
   r.stage==='work'&&r.round===1&&r.arm!=='A_private'||
   r.stage==='work'&&r.round===2&&r.actor==='M1'&&r.arm!=='A_private'))){
  console.log(`\n[${r.call}] ${r.arm}/${r.actor}/${r.stage}/${r.round}\n${r.text}`);
 }
}
