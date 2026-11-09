const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const here=__dirname,root=path.resolve(here,'../..'),run=path.join(root,'runs/expert-final-visibility-chain-20261109-v1');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8')),put=(n,v)=>fs.writeFileSync(path.join(here,n),JSON.stringify(v,null,2)+'\n');
const rows=fs.readFileSync(path.join(run,'responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse),scores=load(path.join(run,'scores.json')),plan=load(path.join(here,'PLAN.json'));
const labels=load(path.join(root,'research/expert-composition100-20261109/LABELS.json')).targets,rules=load(path.join(root,'research/b1-stage-advantage-review-20261107/rules.json'));
const arms=['N_self','P_expert_public_repeat','E_expert_final','O_ordinary_finals','EO_all_finals'],actors=['M1','M2','M3','M4'];
const clean=s=>s.trim().replace(/^(?:answer|答案)\s*[:：]\s*/i,'').trim();
const norm=s=>clean(s).toLowerCase().replace(/[!"#$%&'()*+,\-./:;<=>?@[\]\\^_`{|}~]/g,'').replace(/\b(a|an|the)\b/g,' ').trim().replace(/\s+/g,' ');
const mean=a=>a.reduce((s,x)=>s+x,0)/a.length;
function em(text,target,index,profile='official'){
 const permitted=[target.answer,...(target.answer_aliases||[])];
 if(profile!=='official')permitted.push(...(rules.strict['new:'+index]?.aliases||[]));
 if(profile==='lenient')permitted.push(...(rules.lenient_additional['new:'+index]?.aliases||[]));
 return +permitted.some(v=>norm(v)===norm(text));
}
function vote(ans,target,index,profile='official'){
 const groups=new Map();for(let v of Object.values(ans)){let k=norm(v);if(!groups.has(k))groups.set(k,{n:0,raw:v});groups.get(k).n++;}
 let max=Math.max(...[...groups.values()].map(x=>x.n)),w=[...groups.values()].filter(x=>x.n===max);
 return mean(w.map(x=>em(x.raw,target,index,profile)));
}
const cross=[],oldChanges=[],metrics={};
for(let s of scores){
 const target=labels[s.id];for(let arm of arms){let a=s.arms[arm];assert(a.complete);assert.equal(vote(a.finals,target,s.index),a.expected_em);for(let actor of actors)assert.equal(em(a.finals[actor],target,s.index),a.members[actor].em);}
 assert(arms.every(a=>s.arms[a].expected_em===s.old_B.expected_em));
 for(let actor of actors){let values=arms.map(a=>s.arms[a].finals[actor]);assert(arms.every(a=>s.arms[a].members[actor].em===s.arms.N_self.members[actor].em));if(new Set(values).size>1)cross.push({unit:s.unit,index:s.index,rep:s.rep,actor,answers:Object.fromEntries(arms.map((a,i)=>[a,values[i]]))});}
}
const dictionaries=new Map(),byUnit=new Map();let peerDifferences=0;
for(let r of rows){
 let e=plan.entries.find(e=>e.unit===r.unit),data=JSON.parse(r.payload.user.slice(10,-e.trial_config.answer_suffix.length));
 assert.equal(data.own_actor,r.actor);assert.equal(r.adapter_enabled,r.actor==='M1');
 assert.equal(em(r.raw_output,labels[r.task_id],r.index),em(data.own_sealed_answer,labels[r.task_id],r.index));
 if(r.raw_output!==data.own_sealed_answer)oldChanges.push({call:r.call,unit:r.unit,index:r.index,rep:r.rep,arm:r.arm,actor:r.actor,old:data.own_sealed_answer,now:r.raw_output,reused:r.reused});
 if(!dictionaries.has(r.raw_output))dictionaries.set(r.raw_output,[]);dictionaries.get(r.raw_output).push(r.call);
 if(!byUnit.has(r.unit))byUnit.set(r.unit,{});byUnit.get(r.unit)[r.actor]??={};byUnit.get(r.unit)[r.actor][r.arm]={row:r,data};
 const allowed=(r.arm==='N_self'?[]:r.arm==='E_expert_final'||r.arm==='P_expert_public_repeat'?['M1']:r.arm==='O_ordinary_finals'?actors.slice(1):actors).filter(a=>a!==r.actor);
 assert.deepEqual(data.additional_peer_records.map(x=>x.sender),allowed);
 for(let p of data.additional_peer_records)if(p.source_stage==='sealed_final')assert.equal(p.text,bySourceOwn(r.unit,p.sender));
}
function bySourceOwn(unit,actor){let r=rows.find(r=>r.unit===unit&&r.actor===actor),e=plan.entries.find(e=>e.unit===unit);return JSON.parse(r.payload.user.slice(10,-e.trial_config.answer_suffix.length)).own_sealed_answer;}
for(let group of byUnit.values())for(let actor of actors){let n=group[actor].N_self;for(let arm of arms){let q=group[actor][arm];assert.equal(q.row.seed,n.row.seed);assert.equal(q.row.max_new_tokens,n.row.max_new_tokens);assert.equal(q.row.adapter_enabled,n.row.adapter_enabled);let a=structuredClone(q.data),b=structuredClone(n.data);delete a.additional_peer_records;delete b.additional_peer_records;assert.deepEqual(a,b);if(JSON.stringify(q.data.additional_peer_records)!==JSON.stringify(n.data.additional_peer_records))peerDifferences++;}}
for(let profile of ['official','strict','lenient'])metrics[profile]=Object.fromEntries(arms.map(arm=>[arm,{team:mean(scores.map(s=>vote(s.arms[arm].finals,labels[s.id],s.index,profile))),M1:mean(scores.map(s=>em(s.arms[arm].finals.M1,labels[s.id],s.index,profile))),ordinary:mean(scores.flatMap(s=>actors.slice(1).map(a=>em(s.arms[arm].finals[a],labels[s.id],s.index,profile))))}]));
const subsets={all:scores,non_measurement:scores.filter(s=>![9,51].includes(s.index)),without_OS_and_country_boundaries:scores.filter(s=>![9,13,15,51].includes(s.index)),county_targets:scores.filter(s=>[6,17].includes(s.index)),expert_wrong_safety:scores.filter(s=>s.index===43)};
const subsetScores=Object.fromEntries(Object.entries(subsets).map(([name,ss])=>[name,{units:ss.length,team_by_arm:Object.fromEntries(arms.map(arm=>[arm,mean(ss.map(s=>s.arms[arm].expected_em))]))}]));
const newRows=rows.filter(r=>!r.reused),out={scope:'PURPOSE_SELECTED14_TASKS_TWO_SEEDS_DEVELOPMENT_NOT_POPULATION',n_tasks:14,n_units:28,n_actor_paths:112,n_raw_outputs:560,n_new_outputs:476,n_unique_response_texts:dictionaries.size,all28_unit_team_EM_exactly_equal_all5_and_original_B:true,all112_member_official_EM_equal_across_arms:true,cross_arm_text_changed_actor_paths:cross,changed_vs_original_B:oldChanges,unchanged_vs_original_B_logical:560-oldChanges.length,changed_vs_original_B_new_unique:oldChanges.filter(r=>!r.reused).length,metrics,subsetScores,F1:Object.fromEntries(arms.map(a=>[a,{team:mean(scores.map(s=>s.arms[a].expected_f1)),M1:mean(scores.map(s=>s.arms[a].members.M1.f1))}])),old_B_team:mean(scores.map(s=>s.old_B.expected_em)),old_M1:mean(scores.map(s=>s.old_M1.em)),delivery_check:{result:'PASS',all_group_differences_only_additional_peer_records:true,pairs_with_different_peer_records:peerDifferences,actual_route_and_tokens_audit:load(path.join(here,'RUN_AUDIT.json'))},cost:{seconds:load(path.join(run,'STATUS.json')).elapsed_seconds,new_input_tokens:newRows.reduce((s,r)=>s+r.usage.input_tokens,0),new_output_tokens:newRows.reduce((s,r)=>s+r.usage.output_tokens,0),new_generation_seconds:newRows.reduce((s,r)=>s+r.usage.elapsed_seconds,0)},prior_auxiliary_rules_sha256:crypto.createHash('sha256').update(fs.readFileSync(path.join(root,'research/b1-stage-advantage-review-20261107/rules.json'))).digest('hex')};
put('DETAILED_ANALYSIS.json',out);put('OUTPUT_READ_COVERAGE.json',{result:'ALL_560_OUTPUTS_COVERED',scope:'Full response texts deduplicated with every call mapped; not a claim of new semantic rereading of every upstream paragraph/history',dictionary:[...dictionaries].map(([text,calls])=>({text,calls}))});
fs.writeFileSync(path.join(here,'UNIT_TABLE.md'),['|题索引|seed|原B及五组团队EM|M1 EM|N组四人答案|','|---|---|---:|---:|---|',...scores.map(s=>'|'+[s.index,s.rep,s.arms.N_self.expected_em,s.arms.N_self.members.M1.em,actors.map(a=>a+': '+s.arms.N_self.finals[a]).join('; ')].join('|')+'|')].join('\n')+'\n');
console.log(JSON.stringify({cross,raw_changes:oldChanges.length,new_unique_changes:out.changed_vs_original_B_new_unique,metrics,subsetScores,F1:out.F1,delivery_check:out.delivery_check,cost:out.cost},null,2));
