// Derivations from all original cases. Work conclusions labeled by assistant after full reading.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const HERE=__dirname,ROOT=path.resolve(HERE,'../..'),RUN=path.join(ROOT,'runs/b1-fixed-prefix-20261106-v1');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const pack=read(path.join(RUN,'PREFIXES.json')),labels=read(path.join(RUN,'LABELS.json')).labels,cases=read(path.join(RUN,'CASES.json')),scores=read(path.join(RUN,'scores.json'));
const conditions=['P0','P1','P2'],norm=x=>x.toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const paths=['CASES.json','scores.json','PREFIXES.json','LABELS.json','responses.jsonl','ATTEMPTS.jsonl','RESULTS.json','FREEZE.json','APPROVAL.json'].map(f=>path.join(RUN,f));const before=Object.fromEntries(paths.map(p=>[p,hash(p)]));
const unique=read(path.join(HERE,'UNIQUE_WORK.json'));
const insufficient=new Set([11,13,15,18,32,33,36]);
const wrong=new Set([63,70,79,80,81,82,83,84,85,86,94,95,96,98,99,100,101,102,103]);
assert.equal(unique.length,134);const byCase={},workLabels=[];
for(const w of unique){
 let code=insufficient.has(w.work_id)?'INSUFFICIENT_OR_UNCOMMITTED':wrong.has(w.work_id)?'WRONG_CONCLUDING_CANDIDATE':'CORRECT_CONCLUDING_CANDIDATE';
 const row={work_id:w.work_id,text_sha256:crypto.createHash('sha256').update(w.text).digest('hex'),cases:w.ids,conclusion_code:code,reviewer:'assistant',independence:'none/provisional',definition:'Identifiable task answer endorsed at the end; correct candidate does not certify sound reasoning, source grounding, or absence of earlier contradictions.'};
 workLabels.push(row);for(const id of w.ids){assert.equal(cases[id].work_response.raw_output,w.text);byCase[id]=row;}
}
assert.equal(Object.keys(byCase).length,192);
const rows=[],changes=[],cost={};
for(const cond of conditions)cost[cond]={calls:0,input_tokens:0,output_tokens:0,generation_seconds:0,work_tokens:0,final_tokens:0};
for(const p of pack.prefixes)for(const rep of [0,1]){
 const original=JSON.parse(p.request.payload.user.slice('TASK_DATA\n'.length));
 const retained=original.history.filter((m,i)=>m.phase==='work'&&m.sender!==p.request.actor&&!p.remove_history_indices.includes(i)).length;
 const r={prefix:p.id,task_index:p.task_index,role:p.role,kind:p.kind,repeat:rep,semantic_primary:p.primary_semantic_subset,neutral:p.neutral_control,pre_state_correct:labels[p.id].pre_state_correct,retained_peer_work:retained,conditions:{}};
 for(const cond of conditions){
  const key=`${p.id}/${cond}/${rep}`,c=cases[key],official=scores.rows.find(r=>r.prefix===p.id&&r.repeat===rep).conditions[cond].metrics;
  r.conditions[cond]={work_id:byCase[key].work_id,work_code:byCase[key].conclusion_code,work_correct:Number(byCase[key].conclusion_code==='CORRECT_CONCLUDING_CANDIDATE'),final:c.final_output,final_metrics:official,output_tokens:c.work_response.usage.output_tokens+c.final_response.usage.output_tokens};
  for(const [stage,resp] of [['work',c.work_response],['final',c.final_response]]){let b=cost[cond],u=resp.usage;b.calls++;b.input_tokens+=u.input_tokens;b.output_tokens+=u.output_tokens;b.generation_seconds+=u.elapsed_seconds;b[stage+'_tokens']+=u.output_tokens;}
 }
 for(const [l,h] of [['P1','P0'],['P2','P1']]){
  const a=r.conditions[l],b=r.conditions[h];if(a.final_metrics.em!==b.final_metrics.em||a.work_code!==b.work_code)changes.push({prefix:p.id,task_index:p.task_index,role:p.role,repeat:rep,contrast:`${l}-${h}`,work_before:b.work_code,work_after:a.work_code,final_before:b.final,final_after:a.final,final_em_delta:a.final_metrics.em-b.final_metrics.em});
 }
 rows.push(r);
}
function summary(rs){
 const result={units:rs.length,unique_tasks:new Set(rs.map(r=>r.task_index)).size,conditions:{},contrasts:{}};
 for(const cond of conditions){
  const cs=rs.map(r=>r.conditions[cond]);result.conditions[cond]={final_correct:cs.filter(c=>c.final_metrics.em===1).length,work_correct_candidate:cs.filter(c=>c.work_correct).length,work_wrong_candidate:cs.filter(c=>c.work_code==='WRONG_CONCLUDING_CANDIDATE').length,work_insufficient:cs.filter(c=>c.work_code==='INSUFFICIENT_OR_UNCOMMITTED').length,correct_work_wrong_final:rs.filter(r=>r.conditions[cond].work_correct&&r.conditions[cond].final_metrics.em===0).map(r=>`${r.prefix}/${cond}/${r.repeat}`),wrong_work_correct_final:rs.filter(r=>r.conditions[cond].work_code==='WRONG_CONCLUDING_CANDIDATE'&&r.conditions[cond].final_metrics.em===1).map(r=>`${r.prefix}/${cond}/${r.repeat}`),insufficient_work_correct_final:rs.filter(r=>r.conditions[cond].work_code==='INSUFFICIENT_OR_UNCOMMITTED'&&r.conditions[cond].final_metrics.em===1).map(r=>`${r.prefix}/${cond}/${r.repeat}`)};
 }
 for(const [l,h] of [['P1','P0'],['P2','P1']]){
  result.contrasts[`${l}-${h}`]={final_gains:rs.filter(r=>r.conditions[l].final_metrics.em>r.conditions[h].final_metrics.em).map(r=>`${r.prefix}/${r.repeat}`),final_losses:rs.filter(r=>r.conditions[l].final_metrics.em<r.conditions[h].final_metrics.em).map(r=>`${r.prefix}/${r.repeat}`),work_gains:rs.filter(r=>r.conditions[l].work_correct>r.conditions[h].work_correct).map(r=>`${r.prefix}/${r.repeat}`),work_losses:rs.filter(r=>r.conditions[l].work_correct<r.conditions[h].work_correct).map(r=>`${r.prefix}/${r.repeat}`),same_work_text:rs.filter(r=>cases[`${r.prefix}/${l}/${r.repeat}`].work_response.raw_output===cases[`${r.prefix}/${h}/${r.repeat}`].work_response.raw_output).length,same_final_text:rs.filter(r=>r.conditions[l].final===r.conditions[h].final).length,same_final_normalized:rs.filter(r=>norm(r.conditions[l].final)===norm(r.conditions[h].final)).length};
 }
 return result;
}
const summaries={all:summary(rows),expert:summary(rows.filter(r=>r.role==='E')),ordinary:summary(rows.filter(r=>r.role==='B')),no_retained_peer_work:summary(rows.filter(r=>!r.retained_peer_work)),retained_peer_work:summary(rows.filter(r=>r.retained_peer_work)),semantic_primary:summary(rows.filter(r=>r.semantic_primary))};
let original_work={same:0,different:0},original_final={same:0,different:0},seed_diff={};
for(const p of pack.prefixes){const c=cases[`${p.id}/P1/0`],l=labels[p.id];original_work[c.work_response.raw_output===l.source_original_work?'same':'different']++;original_final[c.final_output===l.source_original_final?'same':'different']++;}
for(const cond of conditions){seed_diff[cond]={work_text_changes:0,final_text_changes:0,final_correctness_changes:0};for(const p of pack.prefixes){let a=cases[`${p.id}/${cond}/0`],b=cases[`${p.id}/${cond}/1`];seed_diff[cond].work_text_changes+=Number(a.work_response.raw_output!==b.work_response.raw_output);seed_diff[cond].final_text_changes+=Number(a.final_output!==b.final_output);const rs=rows.filter(r=>r.prefix===p.id);seed_diff[cond].final_correctness_changes+=Number(rs[0].conditions[cond].final_metrics.em!==rs[1].conditions[cond].final_metrics.em);}}
const analysis={scope:'EXPLORATORY_D16_LOCAL_RECEIVER_PROBE_ASSISTANT_SEMANTIC_REVIEW',new_model_calls:0,summaries,cost,original_comparison:{P1_seed0_work:original_work,P1_seed0_final:original_final,note:'Work payload/seed same, old batch2 vs new singleton; original final has different time/history/seed, so not a replication comparison.'},seed_diff,changes,rows};
fs.writeFileSync(path.join(HERE,'ANALYSIS.json'),JSON.stringify(analysis,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'WORK_CONCLUSION_LABELS.json'),JSON.stringify({scope:'ASSISTANT_DESCRIPTIVE_CONCLUSION_LABELS_NOT_INDEPENDENT_REASONING_ACCURACY',coverage:{work_messages:192,unique_full_texts_read:134,final_answers_read:192},labels:workLabels},null,2)+'\n');
fs.writeFileSync(path.join(HERE,'INPUT_HASHES.json'),JSON.stringify({files:before,original_files_unchanged:paths.every(p=>before[p]===hash(p))},null,2)+'\n');
for(const index of [2,18,34,38,52,69]){
 const ps=pack.prefixes.filter(p=>p.task_index===index),t=read(path.join(ROOT,ps[0].source_path));let md=`# Case index ${index} (question ${index+1})\n\n${t.task.question}\n\n`;
 const target=labels[ps[0].id].target;md+=`Official target: ${JSON.stringify(target)}\n\n## Supplied support paragraphs\n\n`;
 for(const p of t.task.paragraphs.filter(p=>target.paragraphs.some(x=>x.idx===p.idx&&x.is_supporting)))md+=`### ${p.idx}: ${p.title}\n\n${p.paragraph_text}\n\n`;
 for(const p of ps){md+=`## ${p.id}: ${p.kind}\n\nRemoved from P0: ${JSON.stringify(JSON.parse(p.request.payload.user.slice(10)).history.filter((_,i)=>p.remove_history_indices.includes(i)))}\n\n`;
  for(const rep of [0,1])for(const cond of conditions){let c=cases[`${p.id}/${cond}/${rep}`];md+=`### ${cond}, seed repeat ${rep}\n\n${c.work_response.raw_output}\n\n**Private final:** ${c.final_output}\n\n`;}}
 fs.writeFileSync(path.join(HERE,`CASE_${String(index).padStart(3,'0')}.md`),md);
}
console.log(JSON.stringify({summaries,cost,original_comparison:analysis.original_comparison,seed_diff,changes},null,2));
