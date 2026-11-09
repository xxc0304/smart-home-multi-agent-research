const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert/strict');
const out=__dirname,root=path.resolve(out,'../..'),src=path.resolve(out,'../b1-audit-20261104');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const write=(name,x)=>fs.writeFileSync(path.join(out,name),JSON.stringify(x,null,2)+'\n','utf8');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const rel=p=>path.relative(root,p).replaceAll('\\','/');
const originals=[...['PROCESS_CASES.json','AUDIT.json','manifest.json'].map(n=>path.join(src,n)),...fs.readdirSync(path.join(src,'trials')).filter(n=>n.endsWith('.json')).sort().map(n=>path.join(src,'trials',n))];
const before=Object.fromEntries(originals.map(p=>[rel(p),hash(p)]));
const snapshot=path.join(out,'SOURCE_HASHES.json');
if(fs.existsSync(snapshot))assert.deepEqual(read(snapshot),before,'Original evidence changed since review snapshot');else write('SOURCE_HASHES.json',before);
const cases=read(path.join(src,'PROCESS_CASES.json')),judgments=require('./annotations.cjs'),audit=read(path.join(src,'AUDIT.json'));
const trials=fs.readdirSync(path.join(src,'trials')).filter(n=>n.endsWith('.json')).map(n=>({p:path.join(src,'trials',n),t:read(path.join(src,'trials',n))}));
assert.equal(cases.length,12);assert.equal(judgments.length,12);
let ledger=[];
for(let i=0;i<cases.length;i++){
 const c=cases[i],j=judgments[i];assert.equal(c.id,j.id);
 const {p,t}=trials.find(x=>x.t.task.id===c.id);assert.equal(t.complete,true);
 for(const arm of 'ABCD'){
  const [classes,tags,note]=j.arms[arm],score=c.score.arms[arm],work=c.messages[arm];
  assert.equal(work.length,8);assert.equal(work.filter(m=>m.actor==='M1').length,2);
  const initials=t.records.filter(r=>r.stage==='initial'),finals=t.records.filter(r=>r.stage==='final'&&r.arm===arm);
  assert.equal(initials.length,4);assert.equal(finals.length,4);
  const recordRef=r=>`${rel(p)}#/records/${t.records.indexOf(r)}`;
  const final=finals.find(r=>r.actor==='M1');
  const data=JSON.parse(final.payload.user.split('TASK_DATA\n')[1].split('\n\nAnswer the question above.')[0]);
  assert(data.history.every(h=>h.phase!=='final'));
  if('AC'.includes(arm))assert(data.history.every(h=>h.sender==='M1'));
  assert.equal(Boolean(data.team_information),'CD'.includes(arm));
  for(const r of finals){assert.equal(r.raw_output,score.members[r.actor].answer);assert.equal(r.usage.adapter_enabled,r.actor==='M1');}
  for(const m of work){const r=t.records.find(r=>r.request_id===m.request_id);assert.equal(r.raw_output,m.text);assert.equal(r.arm,arm);}
  assert.equal(tags.includes('READOUT_LOSS'),score.expert_correct_but_not_selected_expected>0);
  ledger.push({case_index:i,task_id:c.id,arm,question:c.question,
   review:{reviewer:'assistant',independence:'none/provisional',expert_work_reading:'both full texts',peer_work_reading:i===0&&arm==='B'||i===8&&'BD'.includes(arm)?'all six full texts':'all six head/tail excerpts; middle not exhaustively interpreted',causal_peer_influence:'UNPROVEN',uncertainty:'No independent semantic gold; event-selected sample; see classes and note'},
   source:{trial:rel(p),case_export:`${rel(path.join(src,'PROCESS_CASES.json'))}#/${i}`,trial_sha256:before[rel(p)],rules_sha256:hash(path.join(out,'SEMANTIC_RULES.md'))},
   gold_original:c.target.answer,aliases_original:c.target.answer_aliases,
   supporting_paragraphs:c.paragraphs.filter(p=>c.target.paragraphs.find(x=>x.idx===p.idx)?.is_supporting),
   initial_answers_original:c.initials,initial_request_refs:Object.fromEntries(initials.map(r=>[r.actor,recordRef(r)])),
   work_messages_original:work.map(m=>({...m,record_ref:recordRef(t.records.find(r=>r.request_id===m.request_id))})),
   finals_original:score.members,final_request_refs:Object.fromEntries(finals.map(r=>[r.actor,recordRef(r)])),
   expert_final_history_original:data.history,expert_sees_peers:'BD'.includes(arm),
   vote_original:score.vote,score_original:score,
   assistant_classification:{expert_final:classes,process_tags:tags,interpretation_boundary:j.context,note,confirmed_semantic_harm:score.expert_harm===1&&classes.includes('CLEAR_ERROR'),numeric_semantic_rescore:null}});
 }
}
assert.equal(ledger.length,48);assert.equal(new Set(ledger.map(r=>r.task_id+'|'+r.arm)).size,48);
for(const a of 'ABCD')for(const field of ['harm','correction','readout_loss']){
 const expected=audit.arms[a][field+'_ids'].slice().sort();
 const actual=ledger.filter(r=>r.arm===a&&(field==='readout_loss'?r.score_original.expert_correct_but_not_selected_expected>0:r.score_original['expert_'+field]===1)).map(r=>r.task_id).sort();
 assert.deepEqual(actual,expected,`Missing ${a}/${field} event`);
}
for(const r of ledger.filter(r=>r.assistant_classification.process_tags.includes('FINALIZATION_REVERSAL'))){assert('AC'.includes(r.arm));assert(r.expert_final_history_original.every(h=>h.text==='Alberta Gay'));}
const last=Object.fromEntries(originals.map(p=>[rel(p),hash(p)]));assert.deepEqual(last,before);
const countBy=(rows,fn)=>{const o={};for(const r of rows)for(const k of fn(r))o[k]=(o[k]||0)+1;return o;};
const validation={date:'2026-11-04',scope:'T1 existing 12 event tasks x 4 arms; assistant annotation, not independent adjudication',paths:ledger.length,tasks:cases.length,work_messages_preserved:ledger.reduce((s,r)=>s+r.work_messages_original.length,0),expert_work_full_texts_reviewed:96,peer_work_review:'288 bounded head/tail excerpts, 18 additionally full texts (case0 B and case8 B/D); no exhaustive peer semantic annotation claimed',all_original_event_ids_covered:true,all_final_refs_and_outputs_match:true,expert_final_visibility_and_adapter_checks:'PASS',original_files_unchanged:originals.length,original_sha256_unchanged:true,new_model_generations:0,new_C_H_reads:0,official_scores_changed:false,
 classes:countBy(ledger,r=>r.assistant_classification.expert_final),tags:countBy(ledger,r=>r.assistant_classification.process_tags),
 per_arm:Object.fromEntries([...'ABCD'].map(a=>{const rs=ledger.filter(r=>r.arm===a);return[a,{original_em_harm:rs.reduce((s,r)=>s+r.score_original.expert_harm,0),confirmed_semantic_harm:rs.filter(r=>r.assistant_classification.confirmed_semantic_harm).length,original_em_corrections:rs.reduce((s,r)=>s+r.score_original.expert_correction,0),original_readout_loss_paths:rs.filter(r=>r.score_original.expert_correct_but_not_selected_expected>0).length}]})),
 limitations:['Not blinded: seven cases previously read','All expert work texts read; most peer messages reviewed via explicitly omitted head/tail excerpts','Semantic labels are assistant opinions, not replacement EM or human gold','12 tasks selected by prior events; path counts not independent items or population rates'],
 stage_verdict:'PASS for bounded expert-centered T1 classification; REVISE for causal/independent-semantic claims'};
write('CASE_LEDGER.json',ledger);write('VALIDATION.json',validation);console.log(JSON.stringify(validation,null,2));
