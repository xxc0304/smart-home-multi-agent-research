// Candidate task selection only; no generation, frozen run, or outcome-based search.
const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const H=__dirname,ROOT=path.resolve(H,'../..');
const source='research/expert-composition100-20261109/INPUTS.json';
const buf=fs.readFileSync(path.join(ROOT,source)),units=JSON.parse(buf).units;
const tasks=units.filter(e=>e.cohort==='fresh'&&e.rep===0);
assert.equal(tasks.length,56);
const diagnostic=[6,17,24,49,43,27,28,45];
const excluded={1:'Same-title song/record-label target ambiguity',3:'Age/birthday timing and pre-existing semantic sensitivity',9:'three/3 known scoring boundary',10:'BBC date/programme scope sensitivity',13:'OS series/version/current-time boundary',15:'France/French known scoring boundary',26:'Region/capital mixed target and known output-limit history',38:'Region administrative granularity',44:'Composer/writer/arranger and sung-through wording',51:'Book topic/setting granularity',52:'Era phrasing known scoring boundary',53:'Multiple supplied Doure villages satisfy relation'};
const hash=s=>crypto.createHash('sha256').update(s).digest('hex');
const salt='expert-evidence-scale32-20261109/task-selection-v1';
const diag=diagnostic.map(i=>tasks.find(e=>e.source_index===i));
assert(diag.every(Boolean));const dg=new Set(diag.map(e=>e.group));assert.equal(dg.size,8);
// One representative per existing dependency group; neither scores nor answers enter ordering.
const grouped=new Map();
for(const e of tasks.filter(e=>!dg.has(e.group)&&!(e.source_index in excluded))){
 const rank=hash(salt+'/representative/'+e.id),prev=grouped.get(e.group);
 if(!prev||rank<prev.rank)grouped.set(e.group,{entry:e,rank});
}
const pool=[...grouped.values()].map(x=>x.entry).sort((a,b)=>hash(salt+'/group/'+a.group).localeCompare(hash(salt+'/group/'+b.group)));
assert(pool.length>=24);const background=pool.slice(0,24);
const clean=e=>({source_index:e.source_index,id:e.id,group:e.group,strict_training_answer_isolation:e.strict,question:e.task.question,source_task_file:e.source_path});
const all=[...diag,...background];assert.equal(new Set(all.map(e=>e.id)).size,32);assert.equal(new Set(all.map(e=>e.group)).size,32);
const result={status:'CANDIDATE_DESIGN_NOT_RUNNING_NOT_FROZEN',scope:'Existing D development pool; outcome-stratified diagnostics separate from deterministic background; not new holdout.',source,source_sha256:hash(buf),selection_salt:salt,diagnostic:diag.map(clean),background:background.map(clean),unselected_background_reserve:pool.slice(24).map(clean),exclusions:excluded,source_score_fields_consulted:false,group_count:32,questions:32,seeds_per_question:2,paired_units:64,primary_background_questions:24,primary_background_units:48,max_new_model_calls:2688,calls_per_unit:{common_initials:4,common_expert_private_work:1,common_expert_candidate:1,per_arm_work:8,per_arm_finals:4,arms:3,total:42},timing_prefix_units:2,timing_prefix_calls:84,no_auto_expansion:true};
fs.writeFileSync(path.join(H,'SELECTION.json'),JSON.stringify(result,null,2));
fs.writeFileSync(path.join(H,'TASKS.md'),['# 32题候选清单','','题号为既有fresh56的0起算index；不是新留出集。8诊断与24背景单列，32不同关联组。尚待逐题材料/评分口径检查及运行预检。','','|部分|index|关联组|问题|','|---|---|---|---|',...diag.map(e=>`|诊断|${e.source_index}|${e.group}|${e.task.question}|`),...background.map(e=>`|背景|${e.source_index}|${e.group}|${e.task.question}|`)].join('\n'));
console.log(JSON.stringify({diagnostic:diag.map(e=>e.source_index),background:background.map(e=>e.source_index),groups:32,units:64,max_calls:2688,status:result.status}));
