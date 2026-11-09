// Recompute descriptive readings from immutable, already audited V6 D8 scores.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const HERE=__dirname,ROOT=path.resolve(HERE,'../..'),RUN=path.join(ROOT,'runs/b1-longwork1024-fullflow-20261105-v1');
const hash=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const sources=['AGENTS.md','README.md','RESEARCH_REVIEW_EXPERTISE_REVISION_20261028.md','RESEARCH_REVIEW_EXPERT_MECHANISM_20261030.md','research/expertise-preserving-collaboration-20261028/REVIEW.md','refine-logs/expert-mechanism-pilot-20261030/EXPERIMENT_PLAN.md','refine-logs/expert-mechanism-pilot-20261030/B1_CONTROL_DESIGN.md','refine-logs/expert-mechanism-pilot-20261030/B1_EVALUATION_AND_BATCH_PLAN.md','engineering/b0-first-run-20261103/C160_RESULTS.md','engineering/b1-semantic-review-20261104/RESULTS.md','research/b1-longwork1024-process-20261105/REPORT.md','research/b1-longwork1024-process-20261105/ANALYSIS.json','engineering/b1-longwork1024-fullflow-20261105/POST_RUN_AUDIT.json','runs/b1-longwork1024-fullflow-20261105-v1/config.json'];
const scorePaths=['serial','batch2'].map(e=>path.join(RUN,e,'scores.json'));
const before=Object.fromEntries([...sources.map(p=>path.join(ROOT,p)),...scorePaths].map(p=>[p,hash(p)]));
const output={scope:'DESCRIPTIVE_REPEATED_D8_NOT_CONFIRMATORY_OR_CAUSAL',new_model_calls:0,new_C_H_question_reads:0,calibration:{source:'engineering/b0-first-run-20261103/C160_RESULTS.md',status:'PREVIOUSLY_AUDITED_REPORT_NOT_REEVALUATED',base_em:22/160,expert_em:82/160,paired_difference:60/160,n:160,only_expert_correct:65,only_base_correct:5,both_correct:17,both_wrong:73,decoding:'greedy_short_answer',qualification:'TASK_ANSWER_ADVANTAGE_NOT_COMMUNICATION_EXPERTISE'},engines:{}};
const qual=fs.readFileSync(path.join(ROOT,output.calibration.source),'utf8');assert(qual.includes('22/160')&&qual.includes('82/160')&&qual.includes('onlyE65,onlyB5'));
for(const engine of ['serial','batch2']){
 const score=read(path.join(RUN,engine,'scores.json'));assert.equal(score.n_complete,8);assert.equal(score.reports.length,8);
 const n=score.reports.length,member_initial={};
 for(const actor of ['M1','M2','M3','M4'])member_initial[actor]=score.reports.reduce((s,r)=>s+r.initial.members[actor].em,0)/n;
 const strata={E_correct_B_any_correct:0,E_correct_B_all_wrong:0,E_wrong_B_any_correct:0,all_initial_wrong:0};
 for(const r of score.reports){const E=r.initial.members.M1.em===1,B=['M2','M3','M4'].some(a=>r.initial.members[a].em===1);strata[E?(B?'E_correct_B_any_correct':'E_correct_B_all_wrong'):(B?'E_wrong_B_any_correct':'all_initial_wrong')]++;}
 const arm={};
 for(const name of ['A','B','C','D']){
  const team=score.reports.reduce((s,r)=>s+r.arms[name].expected_em,0)/n;
  const expert=score.reports.reduce((s,r)=>s+r.arms[name].members.M1.em,0)/n;
  assert.equal(team,score.arms[name].expected_em);assert.equal(expert,score.arms[name].expert_em);
  arm[name]={team_expected_em:team,team_actual_em:score.arms[name].actual_em,expert_final_em:expert,expert_harm_n:score.arms[name].expert_harm_n,expert_correction_n:score.arms[name].expert_correction_n,members_final_em:Object.fromEntries(['M1','M2','M3','M4'].map(a=>[a,score.arms[name].members[a].final_em]))};
 }
 const comparisons={};
 for(const [talk,privateArm,label] of [['B','A','hidden'],['D','C','revealed']]){
  const gains=[],losses=[],expertGains=[],expertLosses=[];
  for(const [index,r] of score.reports.entries()){
   const delta=r.arms[talk].expected_em-r.arms[privateArm].expected_em;
   const ed=r.arms[talk].members.M1.em-r.arms[privateArm].members.M1.em;
   if(delta>0)gains.push({index,id:r.id,delta});if(delta<0)losses.push({index,id:r.id,delta});
   if(ed>0)expertGains.push({index,id:r.id});if(ed<0)expertLosses.push({index,id:r.id});
  }
  comparisons[label]={team_talk_minus_private:arm[talk].team_expected_em-arm[privateArm].team_expected_em,expert_talk_minus_private:arm[talk].expert_final_em-arm[privateArm].expert_final_em,team_gain_items:gains,team_loss_items:losses,expert_gain_items:expertGains,expert_loss_items:expertLosses};
 }
 output.engines[engine]={n_unique_development_questions:n,initial_expert_em:member_initial.M1,initial_members_em:member_initial,initial_team_expected_em:score.initial_baseline.team_expected_em,initial_correctness_strata:strata,arms:arm,comparisons,static_vote_minus_expert:score.initial_baseline.team_expected_em-member_initial.M1,hidden_discussion_minus_initial_vote:arm.B.team_expected_em-score.initial_baseline.team_expected_em,hidden_private_minus_initial_vote:arm.A.team_expected_em-score.initial_baseline.team_expected_em};
}
assert.equal(output.engines.batch2.comparisons.hidden.team_talk_minus_private,0);
assert.equal(output.engines.batch2.comparisons.revealed.team_talk_minus_private,0);
assert.equal(output.engines.batch2.initial_correctness_strata.E_wrong_B_any_correct,0);
for(const p of scorePaths)assert.equal(hash(p),before[p]);
fs.writeFileSync(path.join(HERE,'EVIDENCE.json'),JSON.stringify(output,null,2)+'\n');
fs.writeFileSync(path.join(HERE,'SOURCE_SNAPSHOTS.json'),JSON.stringify({purpose:'AUDIT_TIME_SNAPSHOTS_NOT_PERMANENT_HASH_LOCK_OF_LIVING_DOCUMENTS',files:before,score_artifacts_unchanged:true},null,2)+'\n');
console.log(JSON.stringify({n:8,batch2_initial_expert:output.engines.batch2.initial_expert_em,batch2_initial_vote:output.engines.batch2.initial_team_expected_em,batch2_contrasts:output.engines.batch2.comparisons,initial_strata:output.engines.batch2.initial_correctness_strata,new_generations:0}));
