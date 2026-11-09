const fs=require('fs'),path=require('path');
const root=path.resolve(__dirname,'../..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rows=['evidence-first-dev-20261108-v1','evidence-first-remainder-20261108-v1'].flatMap(run=>fs.readFileSync(path.join(root,'runs',run,'responses.jsonl'),'utf8').trim().split('\n').map(x=>({...JSON.parse(x),run})));
const tasks=read('research/evidence-first-dev-20261108/tasks.json');
const labels=read('research/evidence-first-dev-20261108/labels.json');
const merged=read('research/evidence-first-dev-20261108/COMBINED_SUMMARY.json');
const arms=['A_private','B_ordinary','E_facts','F_facts_opinions'];
const ids=merged.complete_task_ids, actors=['M1','M2','M3','M4'];
const fmt=r=>r.answer===null?'?':(r.answer===labels[r.task_id].correct?'C':'W');
const table=ids.map(id=>{
 const task=tasks.find(t=>t.id===id),score=merged.scores.filter(s=>s.task_id===id&&s.complete);
 const initials=rows.filter(r=>r.task_id===id&&r.stage==='initial');
 const factRows=rows.filter(r=>r.task_id===id&&r.stage==='facts');
 const selected=[...new Set(factRows.flatMap(r=>r.references.selected))];
 const result={id,name:task.name,gold:labels[id].official_text,initial:Object.fromEntries(initials.map(r=>[r.actor,fmt(r)])),
  all_hidden:Object.keys(task.hidden),selected_hidden:selected.filter(k=>k.startsWith('H')),arms:{}};
 for(const s of score){
  const r=rows.filter(r=>r.task_id===id&&r.arm===s.arm);
  result.arms[s.arm]={team:s.final_vote.expected_accuracy,expert:s.expert_final_correct,
    finals:Object.fromEntries(actors.map(a=>[a,s.final_answers[a]===labels[id].correct?'C':'W'])),
    choices:s.final_answers,
    m1_path:r.filter(x=>x.actor==='M1').map(x=>({stage:x.stage,round:x.round,result:fmt(x)})),
    work_tokens:r.filter(x=>x.stage==='work').reduce((a,x)=>a+x.output_tokens,0),
    input_tokens:r.reduce((a,x)=>a+x.input_tokens,0),output_tokens:r.reduce((a,x)=>a+x.output_tokens,0),
    seconds:r.reduce((a,x)=>a+x.elapsed_seconds,0)};
 }
 return result;
});
const contrasts={};
for(const [a,b] of [['E_facts','B_ordinary'],['E_facts','F_facts_opinions'],['B_ordinary','A_private']]){
 contrasts[a+'-'+b]={team_gains:[],team_losses:[],expert_gains:[],expert_losses:[]};
 for(const t of table){const aa=t.arms[a],bb=t.arms[b],c=contrasts[a+'-'+b];
  if(aa.team>bb.team)c.team_gains.push({id:t.id,delta:aa.team-bb.team});
  if(aa.team<bb.team)c.team_losses.push({id:t.id,delta:aa.team-bb.team});
  if(aa.expert&&!bb.expert)c.expert_gains.push(t.id);
  if(!aa.expert&&bb.expert)c.expert_losses.push(t.id);
 }
}
const transitions={};
for(const arm of arms){
 const x={initial_right_final_right:[],initial_right_final_wrong:[],initial_wrong_final_right:[],initial_wrong_final_wrong:[],unreadable_initial:[]};
 for(const t of table){const c=t.initial.M1==='C',f=t.arms[arm].expert;
  if(t.initial.M1==='?')x.unreadable_initial.push(t.id);
  else x[`initial_${c?'right':'wrong'}_final_${f?'right':'wrong'}`].push(t.id);
 }
 transitions[arm]=x;
}
const costs={};
for(const arm of arms){
 const included=rows.filter(r=>ids.includes(r.task_id)&&(r.arm===arm||(arm.startsWith('E_')||arm.startsWith('F_'))&&r.arm==='FACTS_SHARED'));
 costs[arm]={n:included.length,input_tokens:included.reduce((a,r)=>a+r.input_tokens,0),output_tokens:included.reduce((a,r)=>a+r.output_tokens,0),seconds:included.reduce((a,r)=>a+r.elapsed_seconds,0)};
}
const result={table,contrasts,transitions,costs,cost_note:'E/F each charged full shared fact-selection cost; common initials excluded symmetrically. Branch initial selections counted as full selected statements, not semantic-use proof.'};
fs.writeFileSync(path.join(__dirname,'PATH_ANALYSIS.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify(result));
const wanted=ids.filter(id=>{const t=table.find(x=>x.id===id);return t.arms.E_facts.team!==t.arms.F_facts_opinions.team||t.arms.E_facts.team!==t.arms.B_ordinary.team;});
let transcript='';
for(const id of wanted){const task=tasks.find(t=>t.id===id);
 transcript+=`\n# TASK ${id} ${task.name}\n${JSON.stringify(task)}\nGOLD ${labels[id].official_text}\n`;
 for(const r of rows.filter(r=>r.task_id===id)){
  transcript+=`\n[${r.run} call ${r.call}] ${r.arm} ${r.actor} ${r.stage} ${r.round} ${fmt(r)}\n${r.text}\n`;
 }
}
fs.writeFileSync(path.join(__dirname,'DIFFERING_TASK_TRANSCRIPTS.txt'),transcript);
