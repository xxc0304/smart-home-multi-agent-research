const fs=require('fs'),path=require('path'),root=path.resolve(__dirname,'../..');
const rows=fs.readFileSync(path.join(root,'runs/name-protocol-dev11-20261108-v1/responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const tasks=JSON.parse(fs.readFileSync(path.join(__dirname,'tasks.json'),'utf8'));
for(const id of process.argv.slice(2).map(Number)){
 console.log('\nTASK '+id+'\n'+JSON.stringify(tasks.find(t=>t.id===id)));
 for(const r of rows.filter(r=>r.task_id===id&&(
  r.stage==='initial'||r.stage==='exchange'&&r.arm==='B_ordinary'||
  r.stage==='work'&&r.round===1&&r.arm!=='A_private'||
  r.stage==='work'&&r.round>=2&&r.actor==='M1'||
  r.stage==='final'))){
  console.log(`\n[call ${r.call}] ${r.arm}/${r.actor}/${r.stage}/${r.round}\n${r.text}`);
 }
}
