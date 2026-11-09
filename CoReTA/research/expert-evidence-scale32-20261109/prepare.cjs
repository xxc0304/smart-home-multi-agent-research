const fs=require('fs'),path=require('path'),crypto=require('crypto'),assert=require('assert').strict;
const H=__dirname,R=path.resolve(H,'../..'),read=p=>JSON.parse(fs.readFileSync(path.join(R,p),'utf8'));
const selection=read('research/expert-evidence-scale32-20261109/SELECTION.json'),old=read('research/expert-composition100-20261109/INPUTS.json').units;
const labels=read('research/expert-composition100-20261109/LABELS.json').targets;
const config=read('research/expert-evidence-behavior4-20261109/config.json');
config.purpose='EARLY_EXPERT_CONTRIBUTION_SHARING32_MATCHED_FULL_DOWNSTREAM';config.run_dir='runs/expert-evidence-scale32-20261109-v1';config.wall_clock_cutoff=null;config.generation_retries=0;delete config.review_tokens;delete config.final_tokens;
const list=[...selection.diagnostic.map(e=>({...e,stratum:'diagnostic'})),...selection.background.map(e=>({...e,stratum:'background'}))];
// Fixed first two different tasks (one diagnostic/one background) are part of full sample.
const order=[list[0],list[8],...list.filter((_,i)=>i!==0&&i!==8)];
const entries=[];
for(const rep of [0,1])for(const x of order){const src=old.find(e=>e.cohort==='fresh'&&e.rep===0&&e.id===x.id);assert(src);entries.push({unit:entries.length,id:x.id,index:x.source_index,group:x.group,strict:x.strict_training_answer_isolation,stratum:x.stratum,rep,source_path:src.source_path,task:src.task});}
assert.equal(entries.length,64);assert.equal(new Set(entries.map(e=>e.id)).size,32);
const write=(p,v)=>fs.writeFileSync(path.join(H,p),typeof v==='string'?v:JSON.stringify(v,null,2)+'\n');
const targets=Object.fromEntries(list.map(x=>[x.id,labels[x.id]]));
write('config.json',config);write('INPUTS.json',{scope:'FIXED32_EXISTING_DEVELOPMENT_TWO_NEW_GENERATION_SEEDS',sources:[...new Set(['research/expert-composition100-20261109/INPUTS.json','research/expert-composition100-20261109/LABELS.json','research/b1-stage-advantage-review-20261107/rules.json',...entries.map(e=>e.source_path)])],entries});
write('LABELS.json',{scope:'SCORING_ONLY_NOT_MODEL_INPUT',targets});
const rules=read('research/b1-stage-advantage-review-20261107/rules.json');const aliases={};
for(const x of list){const a=rules.strict['new:'+x.source_index];if(a)aliases[x.source_index]=a.aliases;}
aliases[33]=['Four Sheriffs']; // Both names explicitly equated in supplied P4, fixed before new outputs.
write('SCORING.json',{primary:'Unchanged official EM/F1 and uniform highest-vote expected score',aliases,auxiliary:'Pre-existing strict aliases plus index33 Four Sheriffs explicitly equated with Four Policemen in supplied P4, fixed before outputs; symmetric all actors/stages, secondary, no substring scoring.',fixed_boundary_sensitivity_exclude_indices:[4,31,47,54,55],statistics:'Background24 tasks: average two seeds per task, paired C-B primary; B-A and C-A secondary. Fixed19 lower-boundary sensitivity. Diagnostic8 separate; missing/incomplete and common-readable denominators explicit.'});
write('MATERIALS.md',list.map(x=>{const e=entries.find(e=>e.id===x.id),t=targets[x.id];const support=new Set(t.paragraphs.filter(p=>p.is_supporting).map(p=>p.idx));return `## ${x.stratum} index${x.source_index} ${x.id}\nQ ${e.task.question}\nOfficial ${t.answer}; aliases ${JSON.stringify(t.answer_aliases)}; supplementary ${JSON.stringify(aliases[x.source_index]||[])}\n`+e.task.paragraphs.filter(p=>support.has(p.idx)).map(p=>`[P${p.idx} ${p.title}] ${p.paragraph_text}`).join('\n')+'\n';}).join('\n'));
console.log(JSON.stringify({entries:64,questions:32,groups:32,primary:24,aux_alias_indices:Object.keys(aliases),max_calls:2688}));
