const fs=require('fs'),path=require('path'),root=path.resolve(__dirname,'../..');
const read=p=>JSON.parse(fs.readFileSync(path.join(root,p),'utf8'));
const rows=fs.readFileSync(path.join(root,'runs/name-protocol-dev11-20261108-v1/responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const scores=read('runs/name-protocol-dev11-20261108-v1/scores.json');
const summary=read('research/name-protocol-dev11-20261108/SUMMARY.json');
const actors=['M1','M2','M3','M4'],arms=['A_private','B_ordinary','E_facts','F_facts_opinions'];
const workFinal=[];const table=[];
for(const s of scores){const subset=rows.filter(r=>r.task_id===s.task_id&&r.arm===s.arm);
 const item={task_id:s.task_id,arm:s.arm,team:s.final_vote.expected_accuracy,expert:s.expert_final_correct,last_work_correct:0,final_correct:0};
 for(const a of actors){const w=subset.find(r=>r.actor===a&&r.stage==='work'&&r.round===4),f=subset.find(r=>r.actor===a&&r.stage==='final');
  if(!w||!f)throw Error('incomplete');
  const known=w.answer!==null&&f.answer!==null;
  workFinal.push({task_id:s.task_id,arm:s.arm,actor:a,known,last_work:w.answer,final:f.answer,
   initial:s.initial_answers[a],last_work_correct:w.answer===null?null:w.answer===s.gold,
   final_correct:f.answer===s.gold,changed:known&&w.answer!==f.answer,
   last_work_call:w.call,final_call:f.call,inherited:f.inherited,
   exact_own_last_work_in_final:f.payload.user.includes(w.text)});
  item.last_work_correct+=w.answer===s.gold;item.final_correct+=f.answer===s.gold;
 }
 table.push(item);
}
const costs={};
for(const a of arms){const rs=rows.filter(r=>r.stage==='initial'||r.arm===a||(['E_facts','F_facts_opinions'].includes(a)&&r.arm==='FACTS_SHARED'));
 costs[a]={logical_calls:rs.length,input_tokens:rs.reduce((n,r)=>n+r.input_tokens,0),output_tokens:rs.reduce((n,r)=>n+r.output_tokens,0),
  generation_seconds:rs.reduce((n,r)=>n+r.elapsed_seconds,0)};
}
const m1Private=rows.filter(r=>r.actor==='M1'&&(r.stage==='initial'||r.arm==='A_private'));
costs.M1_private={logical_calls:m1Private.length,input_tokens:m1Private.reduce((n,r)=>n+r.input_tokens,0),output_tokens:m1Private.reduce((n,r)=>n+r.output_tokens,0),generation_seconds:m1Private.reduce((n,r)=>n+r.elapsed_seconds,0)};
const equalToExpert={};for(const a of arms)equalToExpert[a]=table.filter(r=>r.arm===a&&r.team===Number(r.expert)).map(r=>r.task_id);
const coverage=summary.planned_task_ids.map(id=>{const fact=rows.filter(r=>r.task_id===id&&r.stage==='facts');
 const got=[...new Set(fact.flatMap(r=>r.references.selected).filter(k=>k.startsWith('H')))];
 const s=scores.find(r=>r.task_id===id&&r.arm==='E_facts');return{task_id:id,selected_hidden:got.sort(),all_hidden:s.all_hidden_ids,complete_hidden_coverage:JSON.stringify(got.sort())===JSON.stringify(s.all_hidden_ids)};});
const result={table,work_final_paths:workFinal.length,readable_last_work_paths:workFinal.filter(r=>r.known).length,
 changed:workFinal.filter(r=>r.changed),unknown:workFinal.filter(r=>!r.known),
 correct_to_wrong:workFinal.filter(r=>r.last_work_correct===true&&!r.final_correct),
 wrong_to_correct:workFinal.filter(r=>r.last_work_correct===false&&r.final_correct),
 costs,cost_note:'Each standalone condition charged common initials and shared fact selectors fully; not additive actual wall time. Reused usage included as original cost. M1 private is seven calls per task, not equal total compute.',
 team_matches_expert_task_ids:equalToExpert,coverage,
 caution:'Formal named-answer changes, not causal belief or semantic-reasoning certification. Technical reused paths are not new repetitions.'};
fs.writeFileSync(path.join(__dirname,'PATH_ANALYSIS.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({work_final_paths:result.work_final_paths,readable:result.readable_last_work_paths,
 correct_to_wrong:result.correct_to_wrong,wrong_to_correct:result.wrong_to_correct,costs,equalToExpert,
 full_hidden_coverage:coverage.every(c=>c.complete_hidden_coverage)}));
