const fs=require('fs'),path=require('path'),crypto=require('crypto');
const here=__dirname,root=path.resolve(here,'../..');
const source=path.join(root,'research/name-protocol-dev11-20261108/benchmark.json');
const sha=p=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const all=JSON.parse(fs.readFileSync(source,'utf8'));
const review=fs.readFileSync(path.join(root,'tools/audit_existing_task_fit_20261025.py'),'utf8');
const block=review.slice(review.indexOf('REVIEWS='),review.indexOf('BOUNDARIES='));
const prior=[...new Set([1,4,7,8,9,11,23,30,33,34,50,19,...Array.from(block.matchAll(/^\s*(\d+):/gm),m=>+m[1])])].sort((a,b)=>a-b);
const exposure=JSON.parse(fs.readFileSync(path.join(here,'REMOTE_EXPOSURE_AUDIT.json'),'utf8'));
if(exposure.source_sha256!==sha(source))throw Error('source_snapshot_mismatch');
const excluded=new Set([...prior,...exposure.matched_ids]);
const eligible=all.filter(t=>!excluded.has(t.id));
const selected=eligible.map(t=>({id:t.id,key:crypto.createHash('sha256').update('coreta-new-development32-20261108:'+t.id).digest('hex')})).sort((a,b)=>a.key.localeCompare(b.key)).slice(0,32).map(x=>x.id).sort((a,b)=>a-b);
if(selected.length!==32)throw Error('insufficient_eligible_tasks_do_not_silently_reuse');
const tasks=[],labels={};
for(const t of all.filter(t=>selected.includes(t.id))){
 if(![3,4].includes(t.hidden_information.length)||new Set(t.possible_answers).size!==t.possible_answers.length||!t.possible_answers.includes(t.correct_answer))throw Error('source_schema');
 tasks.push({id:t.id,name:t.name,description:t.description,shared:Object.fromEntries(t.shared_information.map((v,i)=>['S'+String(i+1).padStart(2,'0'),v])),hidden:Object.fromEntries(t.hidden_information.map((v,i)=>['H'+String(i+1).padStart(2,'0'),v])),options:Object.fromEntries(t.possible_answers.map(v=>[v,v]))});labels[t.id]={correct:t.correct_answer};
}
const config=JSON.parse(fs.readFileSync(path.join(root,'research/name-protocol-dev11-20261108/config.json'),'utf8'));
delete config.initial_cache;delete config.initial_cache_sha256;delete config.flow_task_ids;
config.seeds=[2026110910,2126110910];delete config.seed;
config.run_dir='runs/sources-expansion32-20261108-v1';config.purpose='PRESPECIFIED_32_SOURCE_TASK_TWO_SEED_B_E_S_DEVELOPMENT_EXPANSION';
const selection={selected_ids:selected,prior_content_exposure_ids:prior,available_log_exposed_ids:exposure.matched_ids,source_sha256:sha(source),selection_rule:'Exclude documented prior content-audit IDs and available-log full-description matches; SHA256("coreta-new-development32-20261108:"+id) order, first32; sort IDs for execution. No model results or gold used for ranking.',remaining_unallocated_ids:eligible.filter(t=>!selected.includes(t.id)).map(t=>t.id),historical_split_manifest_unavailable:true,not_secret_or_independent_holdout:true,scope:'New development allocation under current user authorization; no matches in available model logs, not a universal historical exposure guarantee.',n_tasks:32,n_seeds:2};
for(const [name,value] of Object.entries({'tasks.json':tasks,'labels.json':labels,'config.json':config,'SELECTION.json':selection}))fs.writeFileSync(path.join(here,name),JSON.stringify(value,null,2)+'\n');
console.log(JSON.stringify(selection));
