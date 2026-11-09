// Offline extraction from immutable V6 traces. No model/network calls.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const HERE=__dirname,ROOT=path.resolve(HERE,'../..'),RUN=path.join(ROOT,'runs/b1-longwork1024-fullflow-20261105-v1');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const targets=read(path.join(HERE,'D8_TARGETS.json'));
const freeze=read(path.join(RUN,'FREEZE.json'));
assert.equal(targets.source_sha256,freeze.files[targets.source],'D8 labels differ from frozen scoring source');
const actors=['M1','M2','M3','M4'],arms=['A','B','C','D'];
const normal=s=>s.toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const same=(a,b)=>JSON.stringify(a)===JSON.stringify(b);
const paths=[path.join(RUN,'RESULTS.json'),path.join(RUN,'config.json'),path.join(ROOT,'tools/b1_controls.py'),path.join(ROOT,'tools/b0_answers.py'),path.join(HERE,'D8_TARGETS.json')];
for(const e of ['serial','batch2']){paths.push(path.join(RUN,e,'scores.json'),path.join(RUN,e,'responses.jsonl'),path.join(RUN,e,'ATTEMPTS.jsonl'));for(let i=0;i<8;i++)paths.push(path.join(RUN,e,'trials',String(i).padStart(3,'0')+'.json'));}
const before=Object.fromEntries(paths.map(p=>[p,hash(p)]));
const traces={},scores={};
for(const e of ['serial','batch2']){scores[e]=read(path.join(RUN,e,'scores.json'));traces[e]=Array.from({length:8},(_,i)=>read(path.join(RUN,e,'trials',String(i).padStart(3,'0')+'.json')));}
const aggregate={paired_requests:0,same_payload:0,same_seed:0,same_raw:0,same_token_ids:0,by_stage:{},by_arm:{},private_visibility_requests:0,public_visibility_requests:0,initial_payloads:0,revealed_requests:0,initial_base_three_same_text:0,initial_base_three_same_normalized:0,final_base_three_same_normalized:{},expert_harm_events:[],readout_losses:[]};
const pairs=[],member_transitions=[],case_summaries=[];
for(let i=0;i<8;i++){
 const serial=traces.serial[i],batch=traces.batch2[i];assert.equal(serial.task.id,batch.task.id);assert.equal(serial.task.id,targets.ids[i]);
 assert.equal(serial.records.length,52);assert.equal(batch.records.length,52);assert(same(serial.task,batch.task));
 const commonInitial=same(serial.initials,batch.initials);
 if(new Set(['M2','M3','M4'].map(a=>serial.initials[a])).size===1)aggregate.initial_base_three_same_text++;
 if(new Set(['M2','M3','M4'].map(a=>normal(serial.initials[a]))).size===1)aggregate.initial_base_three_same_normalized++;
 for(let k=0;k<52;k++){
  const a=serial.records[k],b=batch.records[k];assert.equal(a.request_id,b.request_id);
  const p={index:i,request_id:a.request_id,stage:a.stage,arm:a.arm,actor:a.actor,round:a.round,same_payload:same(a.payload,b.payload),same_seed:a.seed===b.seed,same_raw:a.raw_output===b.raw_output,same_token_ids:same(a.usage.output_ids,b.usage.output_ids),serial_tokens:a.usage.output_tokens,batch2_tokens:b.usage.output_tokens,serial_batch:a.usage.batch_size,batch2_batch:b.usage.batch_size,serial_padded_input:a.usage.padded_input_tokens,batch2_padded_input:b.usage.padded_input_tokens};
  const as=a.usage.output_ids,bs=b.usage.output_ids;let prefix=0;while(prefix<Math.min(as.length,bs.length)&&as[prefix]===bs[prefix])prefix++;p.common_output_token_prefix=prefix;
  pairs.push(p);aggregate.paired_requests++;
  for(const key of ['same_payload','same_seed','same_raw','same_token_ids'])aggregate[key]+=Number(p[key]);
  for(const bucket of [aggregate.by_stage[a.stage]??=( {n:0,same_raw:0,same_payload:0}),aggregate.by_arm[a.arm??'initial']??=({n:0,same_raw:0,same_payload:0})]){bucket.n++;bucket.same_raw+=Number(p.same_raw);bucket.same_payload+=Number(p.same_payload);}
 }
 const cs={index:i,id:serial.task.id,question:serial.task.question,target:targets.targets[serial.task.id],initials:{serial:serial.initials,batch2:batch.initials},same_initials:commonInitial,arms:{},first_raw_difference:pairs.find(p=>p.index===i&&!p.same_raw)??null};
 for(const e of ['serial','batch2']){
  const t=traces[e][i],report=scores[e].reports[i];
  for(const q of t.records){
   let raw=q.payload.user.slice('TASK_DATA\n'.length);const suffix=t.config.answer_suffix;
   if(suffix&&raw.endsWith(suffix))raw=raw.slice(0,-suffix.length);
   const data=JSON.parse(raw);
   assert(same(data.paragraphs,t.task.paragraphs)&&data.question===t.task.question);
   if(q.stage==='initial'){assert.equal(data.history,undefined);assert.equal(data.team_information,undefined);aggregate.initial_payloads++;continue;}
   if(['A','C'].includes(q.arm)){assert(data.history.every(m=>m.sender===q.actor));assert.equal(data.work_visibility,'private_work');aggregate.private_visibility_requests++;}
   else{assert.equal(data.work_visibility,'team_message');aggregate.public_visibility_requests++;}
   assert.equal(Boolean(data.team_information),['C','D'].includes(q.arm));if(data.team_information)aggregate.revealed_requests++;
  }
  for(const arm of arms){
   const ar=report.arms[arm];
   const counts={};for(const ans of Object.values(t.finals[arm]))counts[normal(ans)]=(counts[normal(ans)]??0)+1;
   assert(same(Object.entries(counts).sort(),Object.entries(ar.vote.counts).sort()),'normalizer differs from frozen vote');
   const key=e+'/'+arm;aggregate.final_base_three_same_normalized[key]??=0;
   aggregate.final_base_three_same_normalized[key]+=Number(new Set(['M2','M3','M4'].map(a=>normal(t.finals[arm][a]))).size===1);
   cs.arms[arm]??={};cs.arms[arm][e]={finals:t.finals[arm],members:ar.members,expected_em:ar.expected_em,actual_em:ar.actual_em,vote:ar.vote,expert_harm:ar.expert_harm,expert_correction:ar.expert_correction};
   for(const actor of actors){
    const m={index:i,id:t.task.id,engine:e,arm,actor,initial:report.initial.members[actor],final:ar.members[actor],...ar.member_transitions[actor]};
    member_transitions.push(m);
    if(actor==='M1'&&m.harmful)aggregate.expert_harm_events.push(m);
   }
   if(ar.oracle_hit&&ar.expected_em<1)aggregate.readout_losses.push({index:i,engine:e,arm,expected_em:ar.expected_em,actual_em:ar.actual_em,correct_members:actors.filter(a=>ar.members[a].em===1),selected:ar.vote.answer});
  }
 }
 case_summaries.push(cs);
}
const changed=case_summaries.flatMap(c=>arms.filter(arm=>c.arms[arm].serial.expected_em!==c.arms[arm].batch2.expected_em||c.arms[arm].serial.actual_em!==c.arms[arm].batch2.actual_em).map(arm=>({index:c.index,id:c.id,arm,serial_expected:c.arms[arm].serial.expected_em,batch2_expected:c.arms[arm].batch2.expected_em,serial_actual:c.arms[arm].serial.actual_em,batch2_actual:c.arms[arm].batch2.actual_em})));
assert.deepEqual(changed.map(x=>[x.index,x.arm]),[[0,'A'],[0,'C'],[5,'C']]);
assert.equal(aggregate.same_seed,416);assert.equal(aggregate.initial_payloads,64);assert.equal(aggregate.private_visibility_requests,384);assert.equal(aggregate.public_visibility_requests,384);
const output={scope:'ASSISTANT_OBSERVATIONAL_PROCESS_ANALYSIS_NOT_CAUSAL_OR_INDEPENDENT',new_model_calls:0,aggregate,changed_team_cells:changed,cases:case_summaries,paired_requests:pairs,member_transitions};
fs.writeFileSync(path.join(HERE,'ANALYSIS.json'),JSON.stringify(output,null,2)+'\n');
for(const i of [0,1,5]){
 const c=case_summaries[i];let md=`# Case ${String(i).padStart(3,'0')}: ${c.id}\n\n${c.question}\n\nOfficial target/aliases (not modified):\n\n\`\`\`json\n${JSON.stringify(c.target,null,2)}\n\`\`\`\n\n`;
 md+='## Supplied task paragraphs\n\n';for(const p of traces.serial[i].task.paragraphs)md+=`### Paragraph ${p.idx}: ${p.title}\n\n${p.paragraph_text}\n\n`;
 for(const e of ['serial','batch2']){
  const t=traces[e][i];md+=`## ${e}\n\nInitials: ${JSON.stringify(t.initials)}\n\n`;
  for(const arm of arms){md+=`### Arm ${arm}\n\nFinals and scoring:\n\n\`\`\`json\n${JSON.stringify(c.arms[arm][e],null,2)}\n\`\`\`\n\n`;
   for(const q of t.records.filter(q=>q.arm===arm&&q.stage==='work'))md+=`#### ${q.request_id} | ${q.actor} | work round ${q.round}\n\n${q.raw_output}\n\n`;
  }
 }
 fs.writeFileSync(path.join(HERE,`CASE_${String(i).padStart(3,'0')}.md`),md);
}
assert(paths.every(p=>hash(p)===before[p]));
fs.writeFileSync(path.join(HERE,'INPUT_HASHES.json'),JSON.stringify({files:before,original_files_unchanged:true},null,2)+'\n');
console.log(JSON.stringify({aggregate,changed_team_cells:changed,first_differences:case_summaries.map(c=>({index:c.index,first:c.first_raw_difference})),targets:[0,1,5].map(i=>case_summaries[i].target)},null,2));
