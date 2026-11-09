// Read-only supplemental review. No model calls and no changes to official scores.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const HERE=__dirname,ROOT=path.resolve(HERE,'../..'),PRIOR=path.join(ROOT,'research/b1-dev80-analysis-20261106'),RUN=path.join(ROOT,'runs/b1-dev80-20261106-v1');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8')),hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const manifest=read(path.join(PRIOR,'ARTIFACT_HASHES.json'));
assert(Object.entries(manifest.files).every(([f,h])=>hash(path.join(PRIOR,f))===h));
const s=read(path.join(RUN,'checkpoints/080/scores.json')),rs=s.reports.filter(r=>r.complete),style={},traces=[];
for(let i=0;i<80;i++)traces.push(read(path.join(RUN,`trials/${String(i).padStart(3,'0')}.json`)));
for(const stage of ['initial','work','final'])for(const role of ['E','B']){
 const qs=traces.flatMap(t=>t.records).filter(q=>q.stage===stage&&q.status==='OK'&&((q.actor==='M1')===(role==='E')));
 style[stage+role]={n:qs.length,mean_output_tokens:qs.reduce((n,q)=>n+q.usage.output_tokens,0)/qs.length,at_most32_tokens:qs.filter(q=>q.usage.output_tokens<=32).length};
}
const categories={B:{12:'ANSWER_SURFACE_EQUIVALENCE_CANDIDATE',13:'PUBLIC_WRONG_INTERPRETATION_PRIVATE_FINAL_CORRECT',26:'PUBLIC_WRONG_INTERPRETATION_PRIVATE_FINAL_CORRECT',29:'PUBLIC_INSUFFICIENCY_PRIVATE_FINAL_CORRECT_WEAK_GOLD_BRIDGE',37:'PUBLIC_WRONG_INTERPRETATION_PRIVATE_FINAL_CORRECT',47:'PUBLIC_CORRECT_CANDIDATE_MIXED_WITH_DENIAL',59:'PUBLIC_WRONG_INTERPRETATION_PRIVATE_FINAL_CORRECT',69:'PUBLIC_CORRECT_TASK_MAPPING_LATER_PEERS_RETAIN_WRONG_VALUE',72:'ANSWER_SURFACE_EQUIVALENCE_CANDIDATE'},D:{13:'PUBLIC_TARGET_MENTION_WITH_UNRESOLVED_WRONG_BIRTHPLACE_BRIDGE',26:'PUBLIC_WRONG_INTERPRETATION_PRIVATE_FINAL_CORRECT',29:'PUBLIC_INSUFFICIENCY_PRIVATE_FINAL_CORRECT_WEAK_GOLD_BRIDGE',35:'PUBLIC_INSUFFICIENCY_PRIVATE_FINAL_CORRECT_WEAK_CORPORATE_BRIDGE',37:'PUBLIC_INSUFFICIENCY_PRIVATE_FINAL_CORRECT',50:'PUBLIC_IDENTITY_CONFUSION_PRIVATE_CORRECT_STRING_WEAK_SUPPLIED_BRIDGE'}};
const ledger=[];
for(const arm of ['B','D'])for(const r of rs){const v=r.arms[arm];if(v.expert_em!==1||v.expected_em===1)continue;const i=r.config.task_index,t=traces[i];assert(categories[arm][i]);ledger.push({index:i,question_number:i+1,id:r.id,arm,question:t.task.question,official_expected_em:v.expected_em,official_expert_em:v.expert_em,classification:categories[arm][i],reviewer:'assistant',independence:'none/provisional',finals:t.finals[arm],expert_work:t.records.filter(q=>q.arm===arm&&q.stage==='work'&&q.actor==='M1').map(q=>({request_id:q.request_id,text:q.raw_output})),note:'Expert work and final outputs reviewed; this classification is not a full-peer-history causal annotation.'});}
assert.equal(ledger.length,15);
const event_indices=new Set();const inventory=[];
for(const r of rs){const reasons=[];
 for(const a of ['A','B','C','D']){const v=r.arms[a];if(v.expert_harm)reasons.push(`${a}:E_INITIAL_CORRECT_FINAL_WRONG`);if(v.expert_correction)reasons.push(`${a}:E_INITIAL_WRONG_FINAL_CORRECT`);if(v.expert_em&&v.expected_em<1)reasons.push(`${a}:E_CORRECT_TEAM_EXPECTED_BELOW1`);if(!v.expert_em&&v.expected_em>0)reasons.push(`${a}:TEAM_CAN_OUTSCORE_E`);}
 for(const [l,h] of [['B','A'],['D','C']])if(r.arms[l].expected_em!==r.arms[h].expected_em||r.arms[l].expert_em!==r.arms[h].expert_em)reasons.push(`${l}-${h}:PAIRED_CHANGE`);
 if(reasons.length){event_indices.add(r.config.task_index);inventory.push({index:r.config.task_index,id:r.id,reasons});}
}
const out={scope:'SUPPLEMENTAL_ASSISTANT_REVIEW_NOT_INDEPENDENT_OR_CAUSAL',prior_artifacts_hash_verified:true,new_model_calls:0,style,readout_event_classifications:ledger,unique_flagged_tasks:event_indices.size,event_inventory:inventory,independent_baseline_comparison:{n:75,E0:s.initial_baseline.expert_em,EprivateA:s.arms.A.expert_em,EprivateC:s.arms.C.expert_em,Bteam:s.arms.B.expected_em,Dteam:s.arms.D.expected_em,Bteam_minus_EprivateA:s.arms.B.expected_em-s.arms.A.expert_em,Dteam_minus_EprivateC:s.arms.D.expected_em-s.arms.C.expert_em,note:'Different total compute; exploratory, not a cost-matched superiority test.'}};
fs.writeFileSync(path.join(HERE,'REVIEW_EVIDENCE.json'),JSON.stringify(out,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'INPUT_HASHES.json'),JSON.stringify({files:Object.fromEntries([path.join(PRIOR,'ARTIFACT_HASHES.json'),path.join(RUN,'checkpoints/080/scores.json'),...traces.map((_,i)=>path.join(RUN,`trials/${String(i).padStart(3,'0')}.json`))].map(p=>[p,hash(p)]))},null,2)+'\n');
console.log(JSON.stringify({prior_artifacts_verified:true,style,readout_paths:ledger.length,flagged_tasks:event_indices.size,indices:[...event_indices],baselines:out.independent_baseline_comparison}));
