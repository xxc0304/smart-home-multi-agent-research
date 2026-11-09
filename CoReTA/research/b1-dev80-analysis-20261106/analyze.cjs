// Offline derivations from frozen official scores and original responses.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const HERE=__dirname,ROOT=path.resolve(HERE,'../..'),RUN=path.join(ROOT,'runs/b1-dev80-20261106-v1');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const s=read(path.join(RUN,'checkpoints/080/scores.json')),inputs=read(path.join(RUN,'INPUTS.json'));
const arms=['A','B','C','D'],actors=['M1','M2','M3','M4'],base=actors.slice(1);
const norm=x=>x.toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const traces=Array.from({length:80},(_,i)=>read(path.join(RUN,`trials/${String(i).padStart(3,'0')}.json`)));
const targetFile=path.join(ROOT,'data/external/musique-v1.0-20261030/scoring/D_development.jsonl');
const targets=Object.fromEntries(fs.readFileSync(targetFile,'utf8').trim().split(/\r?\n/).map(x=>{let y=JSON.parse(x);return[y.id,y]}));
const freeze=read(path.join(RUN,'FREEZE.json'));
assert.equal(hash(targetFile),freeze.files['/data2/xiaoxinchen/agent-research/CoReTA/data/external/musique-v1.0-20261030/scoring/D_development.jsonl']);
const paths=[targetFile,path.join(RUN,'checkpoints/080/scores.json'),...traces.map((_,i)=>path.join(RUN,`trials/${String(i).padStart(3,'0')}.json`))];
const before=Object.fromEntries(paths.map(p=>[p,hash(p)]));
const complete=s.reports.filter(r=>r.complete),sum=(rs,fn)=>rs.reduce((a,r)=>a+fn(r),0);
let recordCount=0,outputTokens=0,privateRequests=0,publicRequests=0;const failures=[];
for(let i=0;i<80;i++){
 const t=traces[i],r=s.reports[i];assert.equal(t.task.id,r.id);assert.equal(t.task.id,inputs.tasks[i].id);assert.equal(t.complete,r.complete);
 for(const q of t.records){
  recordCount++;const u=q.usage;outputTokens+=u.output_tokens;
  assert.equal(u.adapter_enabled,q.actor==='M1');assert.equal(u.lora_layers,252);assert.equal(u.disabled_layers,q.actor==='M1'?0:252);
  if(u.batch_size===2)assert.equal(u.rng_seed,q.seed); // Singleton backend stores the seed in the request only.
  assert.equal(u.output_cap,q.max_new_tokens);assert(u.batch_size===1||u.batch_size===2);
  if(q.status==='OK'){assert.equal(u.finish_reason,'EOS');assert.equal(u.ended_with_eos,true);}
  else {const grams=u.output_ids.slice(0,-7).map((_,j)=>u.output_ids.slice(j,j+8).join(','));failures.push({index:i,question_number:i+1,id:t.task.id,actor:q.actor,arm:q.arm,stage:q.stage,tokens:u.output_tokens,status:q.status,repeated_8gram_fraction:1-new Set(grams).size/grams.length,output:q.raw_output});}
  if(q.arm){if(['A','C'].includes(q.arm))privateRequests++;else publicRequests++;}
 }
}
assert.equal(recordCount,4071);assert.equal(failures.length,5);
function stats(rs){
 const out={n:rs.length,initial:{expert:sum(rs,r=>r.initial.members.M1.em),base:Object.fromEntries(base.map(a=>[a,sum(rs,r=>r.initial.members[a].em)])),strata:{},base_same:0},arms:{},contrasts:{}};
 for(const r of rs){let e=r.initial.members.M1.em,b=base.some(a=>r.initial.members[a].em);let k=`E${e}_anyB${Number(b)}`;out.initial.strata[k]=(out.initial.strata[k]??0)+1;out.initial.base_same+=Number(new Set(base.map(a=>norm(traces[r.config.task_index].initials[a]))).size===1);}
 for(const a of arms){
  let ar=out.arms[a]={expert_correct:sum(rs,r=>r.arms[a].expert_em),team_expected_correct:sum(rs,r=>r.arms[a].expected_em),team_actual_correct:sum(rs,r=>r.arms[a].actual_em),oracle_correct:sum(rs,r=>Number(r.arms[a].oracle_hit)),base_correct:Object.fromEntries(base.map(b=>[b,sum(rs,r=>r.arms[a].members[b].em)])),base_same:0,all_same:0,expert_correct_team_loss:[],ordinary_rescues:[],harm_indices:[],correction_indices:[]};
  for(const r of rs){const v=r.arms[a],t=traces[r.config.task_index];ar.base_same+=Number(new Set(base.map(b=>norm(t.finals[a][b]))).size===1);ar.all_same+=Number(new Set(actors.map(b=>norm(t.finals[a][b]))).size===1);if(v.expert_harm)ar.harm_indices.push(r.config.task_index);if(v.expert_correction)ar.correction_indices.push(r.config.task_index);if(v.expert_em&&v.expected_em<1)ar.expert_correct_team_loss.push({index:r.config.task_index,expected:v.expected_em,actual:v.actual_em,finals:t.finals[a]});if(!v.expert_em&&v.expected_em>0)ar.ordinary_rescues.push({index:r.config.task_index,expected:v.expected_em,actual:v.actual_em,finals:t.finals[a]});}
 }
 for(const [label,l,r] of [['B-A','B','A'],['D-C','D','C'],['D-B','D','B'],['C-A','C','A']]){
  const c=out.contrasts[label]={team_gains:[],team_losses:[],expert_gains:[],expert_losses:[],expert_harm_both:[],expert_harm_discussion_only:[],expert_harm_private_only:[]};
  for(const q of rs){let i=q.config.task_index,x=q.arms[l],y=q.arms[r],dt=x.expected_em-y.expected_em,de=x.expert_em-y.expert_em;if(dt>0)c.team_gains.push({index:i,delta:dt});if(dt<0)c.team_losses.push({index:i,delta:dt});if(de>0)c.expert_gains.push(i);if(de<0)c.expert_losses.push(i);if(q.initial.members.M1.em){if(x.expert_harm&&y.expert_harm)c.expert_harm_both.push(i);else if(x.expert_harm)c.expert_harm_discussion_only.push(i);else if(y.expert_harm)c.expert_harm_private_only.push(i);}}
 }
 return out;
}
const full=stats(complete);
const sensitivity={arms:{},contrasts:{},note:'Arithmetic bounds on fixed 80 missing outcomes, not population confidence intervals or imputations.'};
for(const a of arms){let valid=s.reports.filter(r=>r.arms[a]?.complete);sensitivity.arms[a]={n:valid.length,expected_em:sum(valid,r=>r.arms[a].expected_em)/valid.length,expert_em:sum(valid,r=>r.arms[a].expert_em)/valid.length};}
for(const [label,l,r] of [['B-A','B','A'],['D-C','D','C'],['D-B','D','B'],['C-A','C','A']]){
 let both=s.reports.filter(q=>q.arms[l]?.complete&&q.arms[r]?.complete),lower=0,upper=0;
 for(const q of s.reports){let x=q.arms[l],y=q.arms[r];lower+=(x?.complete?x.expected_em:0)-(y?.complete?y.expected_em:1);upper+=(x?.complete?x.expected_em:1)-(y?.complete?y.expected_em:0);}
 sensitivity.contrasts[label]={pairwise_n:both.length,pairwise_difference:sum(both,q=>q.arms[l].expected_em-q.arms[r].expected_em)/both.length,fixed80_bounds:[lower/80,upper/80]};
}
const cases=s.reports.map((r,i)=>({index:i,number:i+1,id:r.id,question:traces[i].task.question,target:targets[r.id],complete:r.complete,initials:traces[i].initials,initial_scores:r.initial?.members,arms:Object.fromEntries(arms.map(a=>[a,{finals:traces[i].finals[a],score:r.arms[a]}]))}));
const analysis={scope:'EXPLORATORY_DEVELOPMENT_ASSISTANT_SELF_REVIEW_NOT_INDEPENDENT',new_model_calls:0,recordCount,outputTokens,privateRequests,publicRequests,full,sensitivity,failures,cases};
fs.writeFileSync(path.join(HERE,'ANALYSIS.json'),JSON.stringify(analysis,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'INPUT_HASHES.json'),JSON.stringify({files:before,original_files_unchanged:paths.every(p=>before[p]===hash(p))},null,2)+'\n');
const coverage=[[26,['B']],[34,['A','B']],[52,['B']],[66,['D']],[69,['B']],[71,['A','B']]];
for(const [i,selected] of coverage){
 const t=traces[i],c=cases[i];let md=`# Case ${i} (question ${i+1}): ${c.id}\n\n${c.question}\n\nOfficial scoring target (unchanged):\n\n\`\`\`json\n${JSON.stringify(c.target,null,2)}\n\`\`\`\n\n## All supplied paragraphs\n\n`;
 for(const p of t.task.paragraphs)md+=`### ${p.idx}: ${p.title}\n\n${p.paragraph_text}\n\n`;
 md+=`## Initials and all final answers\n\n\`\`\`json\n${JSON.stringify({initials:c.initials,arms:c.arms},null,2)}\n\`\`\`\n\n`;
 for(const arm of selected){md+=`## Arm ${arm} work messages\n\n`;for(const q of t.records.filter(q=>q.arm===arm&&q.stage==='work'))md+=`### ${q.request_id} | ${q.actor} | round ${q.round}\n\n${q.raw_output}\n\n`;}
 fs.writeFileSync(path.join(HERE,`CASE_${String(i).padStart(3,'0')}.md`),md);
}
fs.writeFileSync(path.join(HERE,'SEMANTIC_REVIEW_COVERAGE.json'),JSON.stringify({reviewer:'assistant',independence:'none/provisional',all_80_scores_programmatically_examined:true,full_work_messages_read:64,selected_work_paths:coverage.map(([index,arms])=>({index,question_number:index+1,arms})),supporting_paragraphs_read:13,all_supplied_paragraphs_exported_but_not_all_semantically_reviewed:true,remaining_work_messages_not_claimed_fully_reviewed:true,selection:'purposeful diagnostic examples, not prevalence sample'},null,2)+'\n');
for(const a of arms)assert(Math.abs(full.arms[a].team_expected_correct/75-s.arms[a].expected_em)<1e-12);
const short={...full,arms:Object.fromEntries(arms.map(a=>[a,{...full.arms[a],expert_correct_team_loss:full.arms[a].expert_correct_team_loss.map(x=>x.index),ordinary_rescues:full.arms[a].ordinary_rescues.map(x=>x.index)}]))};
console.log(JSON.stringify({full:short,sensitivity,failures:failures.map(({output,...v})=>v),recordCount,outputTokens},null,2));
