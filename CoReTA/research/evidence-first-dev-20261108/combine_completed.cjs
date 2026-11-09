const fs=require('fs'),path=require('path');
const here=__dirname,root=path.resolve(here,'../..');
const read=p=>JSON.parse(fs.readFileSync(p,'utf8'));
const first=path.join(root,'runs/evidence-first-dev-20261108-v1');
const rest=path.join(root,'runs/evidence-first-remainder-20261108-v1');
const cfg0=read(path.join(first,'manifest.json')).config,cfg1=read(path.join(rest,'manifest.json')).config;
for(const k of new Set([...Object.keys(cfg0),...Object.keys(cfg1)])){
 if(!['run_dir','purpose'].includes(k)&&JSON.stringify(cfg0[k])!==JSON.stringify(cfg1[k]))throw Error('config differs: '+k);
}
const s0=read(path.join(first,'STATUS.json')),s1=read(path.join(rest,'STATUS.json'));
if(s0.status!=='FAILED'||s1.status!=='COMPLETED')throw Error('unexpected final states');
const rows=[...read(path.join(first,'scores.json')),...read(path.join(rest,'scores.json'))];
const ids=[1,4,7,8,9,11,23,30,33,34,50],arms=['A_private','B_ordinary','E_facts','F_facts_opinions'];
const map=new Map();for(const r of rows){const k=r.task_id+'/'+r.arm;if(map.has(k))throw Error('overlap');map.set(k,r);}
const common=ids.filter(n=>arms.every(a=>{const r=map.get(n+'/'+a);return r?.complete&&r.final_vote!==null;}));
const missing=ids.filter(n=>!common.includes(n));
if(JSON.stringify(common)!==JSON.stringify([1,4,9,11,30,33,34,50]))throw Error('unexpected coverage');
const means={};for(const a of arms){const rr=common.map(n=>map.get(n+'/'+a));means[a]={
 n:rr.length,team_expected_accuracy:rr.reduce((s,r)=>s+r.final_vote.expected_accuracy,0)/rr.length,
 expert_final_accuracy:rr.reduce((s,r)=>s+Number(r.expert_final_correct),0)/rr.length};}
const a0=read(path.join(here,'COMPLETION_AUDIT.json'));
const a1=read(path.join(root,'research/evidence-first-remainder-20261108/COMPLETION_AUDIT.json'));
const result={original_n:11,complete_task_ids:common,missing_task_ids:missing,
 total_calls:s0.calls+s1.calls,active_seconds:s0.elapsed_seconds+s1.elapsed_seconds,
 output_tokens:a0.output_tokens+a1.output_tokens,non_eos:a0.non_eos+a1.non_eos,
 complete_arms:s0.complete_arms+s1.complete_arms,means,
 missing_reason:'One common independent initial hit the unchanged 256-token cap in each of IDs 7,8,23. No retry or zero imputation.',
 scope:'One-seed previously used development tasks; missingness not random; no population or method effectiveness conclusion.',
 scores:rows};
fs.writeFileSync(path.join(here,'COMBINED_SUMMARY.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({...result,scores:undefined}));
