const fs=require('fs'),path=require('path');const here=__dirname,root=path.resolve(here,'../..');
const load=p=>JSON.parse(fs.readFileSync(p,'utf8'));const tasks=load(path.join(here,'tasks.json')),labels=load(path.join(here,'labels.json'));
const rows=fs.readFileSync(path.join(root,'runs/sources-expansion32-20261108-v1/responses.jsonl'),'utf8').trim().split('\n').map(JSON.parse);
const scores=load(path.join(root,'runs/sources-expansion32-20261108-v1/scores.json'));
function norm(s){s=s.normalize('NFKC').replace(/[’‘]/g,"'").trim().replace(/\*\*/g,'');if(s.length>=2&&s[0]===s.at(-1)&&['"',"'",'`'].includes(s[0]))s=s.slice(1,-1).trim();return s.replace(/\s+/g,' ').toLowerCase();}
function match(v,t){const map=new Map(Object.keys(t.options).map(x=>[norm(x),x]));const s=norm(v);return map.get(s)||(s.endsWith('.')?map.get(s.slice(0,-1)):null)||null;}
function strict(text,t){const fields=text.split('\n').map(x=>x.trim().replace(/\*\*/g,'')).map(x=>/^ANSWER\s*:\s*(.*?)\s*$/i.exec(x)).filter(Boolean).map(x=>x[1]);if(fields.length>1)return null;const hit=match(fields.length?fields[0]:text,t);if(hit||fields.length)return hit;return match(text.split('\n').filter(x=>x.trim()).at(-1)||'',t);}
function explicit(text,t){const a=strict(text,t);if(a!==null)return {answer:a,mode:'strict'};const fields=[...text.replace(/\*\*/g,'').matchAll(/ANSWER\s*:\s*(.*?)\s*$/gmi)].map(m=>m[1]);return {answer:fields.length===1?match(fields[0],t):null,mode:'retrospective_unique_inline_field'};}
for(const r of rows.filter(r=>r.stage!=='facts')){const t=tasks.find(t=>t.id===r.task_id);if(strict(r.text,t)!==r.answer)throw Error('strict_parser_reconstruction '+r.call);}
const paths=[];
for(const f of rows.filter(r=>r.stage==='final')){
 const t=tasks.find(t=>t.id===f.task_id),gold=labels[t.id].correct;
 const hist=rows.filter(r=>r.task_id===f.task_id&&r.unit_seed===f.unit_seed&&r.arm===f.arm&&r.actor===f.actor&&r.stage==='work');
 const w=hist.at(-1),a=explicit(w.text,t),init=rows.find(r=>r.task_id===f.task_id&&r.unit_seed===f.unit_seed&&r.actor===f.actor&&r.stage==='initial');
 if(!f.payload.user.includes(w.text))throw Error('last_work_missing '+f.call);
 paths.push({task:t.id,seed:f.unit_seed,arm:f.arm,actor:f.actor,last_call:w.call,final_call:f.call,
   strict_last:w.answer,last:a.answer,last_mode:a.mode,final:f.answer,initial:init.answer,
   last_correct:a.answer===null?null:a.answer===gold,final_correct:f.answer===null?null:f.answer===gold,
   last_text:w.text,final_text:f.text,all_work_correct:hist.map(r=>{const x=explicit(r.text,t).answer;return x===null?null:x===gold;})});
}
const byArm={};for(const arm of ['B_ordinary','E_facts','S_same_sources_m1']){
 const ps=paths.filter(p=>p.arm===arm),known=ps.filter(p=>p.last!==null&&p.final!==null),changes=known.filter(p=>p.last!==p.final);
 byArm[arm]={paths:ps.length,strict_last_known:ps.filter(p=>p.strict_last!==null).length,explicit_last_known:ps.filter(p=>p.last!==null).length,both_known:known.length,
   changed:changes.length,correct_to_wrong:changes.filter(p=>p.last_correct&&!p.final_correct).length,wrong_to_correct:changes.filter(p=>!p.last_correct&&p.final_correct).length,
   wrong_to_wrong:changes.filter(p=>!p.last_correct&&!p.final_correct).length,changed_back_to_initial:changes.filter(p=>p.final===p.initial).length,
   harmful_source_tasks:[...new Set(changes.filter(p=>p.last_correct&&!p.final_correct).map(p=>p.task))],changes};
}
const formalTasks=new Set(tasks.map(t=>t.id).filter(n=>![38,62].includes(n)));
const main=scores.filter(s=>formalTasks.has(s.task_id));const member={};
for(const arm of ['B_ordinary','E_facts','S_same_sources_m1']){
 const ss=main.filter(s=>s.arm===arm);member[arm]={team: ss.reduce((s,x)=>s+x.score,0)/ss.length,M1:ss.filter(s=>s.M1_correct).length/ss.length,
   M1_correct_team_not_fully_correct:ss.filter(s=>s.M1_correct&&s.score<1).map(s=>[s.task_id,s.unit_seed]),
   M1_wrong_team_better:ss.filter(s=>s.M1_correct===false&&s.score>0).map(s=>[s.task_id,s.unit_seed]),
   ordinary:arm==='S_same_sources_m1'?null:ss.reduce((s,x)=>s+Object.entries(x.final_answers).filter(([a,v])=>a!=='M1'&&v===labels[x.task_id].correct).length,0)/(ss.length*3)};
}
const initial=rows.filter(r=>r.stage==='initial'&&formalTasks.has(r.task_id));
const initialStats={M1_n:initial.filter(r=>r.actor==='M1').length,M1_known:initial.filter(r=>r.actor==='M1'&&r.answer!==null).length,M1_correct:initial.filter(r=>r.actor==='M1'&&r.answer===labels[r.task_id].correct).length,
 ordinary_n:initial.filter(r=>r.actor!=='M1').length,ordinary_known:initial.filter(r=>r.actor!=='M1'&&r.answer!==null).length,ordinary_correct:initial.filter(r=>r.actor!=='M1'&&r.answer===labels[r.task_id].correct).length};
const coverage=scores.filter(s=>s.arm==='E_facts').map(s=>({task:s.task_id,seed:s.unit_seed,selected:s.selected_hidden_ids,total:Object.keys(tasks.find(t=>t.id===s.task_id).hidden)}));
const index=new Map(main.map(s=>[[s.task_id,s.unit_seed,s.arm].join(':'),s]));
const paired=main.filter(s=>s.arm==='E_facts').map(E=>({E,S:index.get([E.task_id,E.unit_seed,'S_same_sources_m1'].join(':')),B:index.get([E.task_id,E.unit_seed,'B_ordinary'].join(':'))}));
const decomposition={E_M1_improved_over_S:paired.filter(({E,S})=>E.M1_correct&&!S.M1_correct).map(({E})=>[E.task_id,E.unit_seed]),
 E_M1_worse_than_S:paired.filter(({E,S})=>!E.M1_correct&&S.M1_correct).map(({E})=>[E.task_id,E.unit_seed]),
 E_team_gain_over_B_with_B_M1_already_final_correct:paired.filter(({E,B})=>E.score>B.score&&B.M1_correct).map(({E})=>[E.task_id,E.unit_seed]),
 E_team_gain_over_B_with_M1_improvement:paired.filter(({E,B})=>E.score>B.score&&!B.M1_correct&&E.M1_correct).map(({E})=>[E.task_id,E.unit_seed])};
const result={strict_parser_reconstruction_pass:true,initialStats,member,decomposition,source_coverage:{all_units:coverage.length,all_hidden_selected:coverage.filter(x=>x.selected.length===x.total.length).length,missing:coverage.filter(x=>x.selected.length!==x.total.length)},byArm};
fs.writeFileSync(path.join(here,'PATH_METRICS.json'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({...result,byArm:Object.fromEntries(Object.entries(byArm).map(([k,v])=>[k,{...v,changes:v.changes.map(({last_text,final_text,all_work_correct,...p})=>p)}]))},null,2));
