const fs=require('fs'),path=require('path');const root=path.resolve(__dirname,'../..');
const run=path.join(root,'runs/name-interface-tech-20261108-v2');
const rows=fs.readFileSync(path.join(run,'responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const scores=JSON.parse(fs.readFileSync(path.join(run,'scores.json'),'utf8'));
const arms=['A_private','B_ordinary','E_facts','F_facts_opinions'];
const table=[],changes=[],summaries={};
for(const s of scores){const group=rows.filter(r=>r.task_id===s.task_id&&r.arm===s.arm);
 const finals=group.filter(r=>r.stage==='final');let lastCorrect=0,finalCorrect=0;
 for(const f of finals){const w=group.find(r=>r.actor===f.actor&&r.stage==='work'&&r.round===4);
  if(!w)throw Error('missing final work');lastCorrect+=w.answer===s.gold;finalCorrect+=f.answer===s.gold;
  if(w.answer!==f.answer){
   const ownWork=group.filter(r=>r.actor===f.actor&&r.stage==='work');
   if(!f.payload.user.includes(w.text))throw Error('final omitted own last work');
   changes.push({task_id:s.task_id,arm:s.arm,actor:f.actor,last_work_call:w.call,final_call:f.call,
    initial:s.initial_answers[f.actor],last_work:w.answer,final:f.answer,
    own_work_path:ownWork.map(r=>r.answer),last_work_correct:w.answer===s.gold,final_correct:f.answer===s.gold,
    full_last_work_present_in_final_payload:true,last_work_text:w.text,final_text:f.text});
  }
 }
 table.push({task_id:s.task_id,arm:s.arm,team_expected:s.final_vote.expected_accuracy,
  expert_final:s.expert_final_correct,last_work_correct:lastCorrect,final_correct:finalCorrect,
  initial_answers:s.initial_answers,final_answers:s.final_answers});
}
for(const a of arms){const ss=scores.filter(s=>s.arm===a);summaries[a]={n_tasks:ss.length,
 team_expected_accuracy:ss.reduce((x,s)=>x+s.final_vote.expected_accuracy,0)/ss.length,
 expert_final_accuracy:ss.reduce((x,s)=>x+Number(s.expert_final_correct),0)/ss.length,
 ordinary_final_accuracy:ss.reduce((x,s)=>x+Object.entries(s.final_answers).filter(([k,v])=>k!=='M1'&&v===s.gold).length,0)/(3*ss.length),
 last_work_to_final_changes:changes.filter(c=>c.arm===a).length};}
const result={scope:'Purpose-selected technical cases 11/33, one seed, not method-effectiveness or frequency estimate.',table,summaries,
 last_work_final_paths_checked:table.length*4,changes,
 evidence_note:'All final payloads reconstructed in COMPLETION_AUDIT; changed paths additionally assert exact own last-work text is present. No inference of internal belief or unique causal mechanism.'};
fs.writeFileSync(path.join(__dirname,'RESULT_ANALYSIS.json'),JSON.stringify(result,null,2)+'\n');console.log(JSON.stringify(result));
